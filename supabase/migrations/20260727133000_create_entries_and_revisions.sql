create table public.entries (
    id uuid primary key,
    owner_id uuid not null
        references auth.users (id) on delete restrict,
    entry_at timestamptz not null,
    current_revision_id uuid not null,
    idempotency_key text not null,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    trashed_at timestamptz,
    constraint entries_idempotency_key_not_blank
        check (
            char_length(btrim(idempotency_key)) between 1 and 200
        ),
    constraint entries_updated_after_creation
        check (updated_at >= created_at),
    constraint entries_owner_idempotency_key_unique
        unique (owner_id, idempotency_key)
);

create table public.entry_revisions (
    id uuid primary key,
    entry_id uuid not null
        references public.entries (id) on delete cascade,
    revision_number integer not null,
    original_content text not null,
    created_at timestamptz not null,
    constraint entry_revisions_positive_revision
        check (revision_number > 0),
    constraint entry_revisions_original_content_not_blank
        check (char_length(btrim(original_content)) > 0),
    constraint entry_revisions_entry_sequence_unique
        unique (entry_id, revision_number),
    constraint entry_revisions_entry_id_id_unique
        unique (entry_id, id)
);

alter table public.entries
    add constraint entries_current_revision_belongs_to_entry
    foreign key (id, current_revision_id)
    references public.entry_revisions (entry_id, id)
    deferrable initially deferred;

create table public.ai_processing (
    id uuid primary key,
    entry_revision_id uuid not null
        references public.entry_revisions (id) on delete cascade,
    state text not null default 'pending',
    draft_required boolean not null default true,
    embedding_required boolean not null default true,
    attempt_count integer not null default 0,
    created_at timestamptz not null,
    updated_at timestamptz not null,
    constraint ai_processing_one_obligation_per_revision
        unique (entry_revision_id),
    constraint ai_processing_known_state
        check (
            state in (
                'pending',
                'processing',
                'ready',
                'failed',
                'blocked_budget'
            )
        ),
    constraint ai_processing_nonnegative_attempt_count
        check (attempt_count >= 0),
    constraint ai_processing_has_required_work
        check (draft_required or embedding_required),
    constraint ai_processing_updated_after_creation
        check (updated_at >= created_at)
);

create index entries_owner_active_history_idx
    on public.entries (owner_id, entry_at desc, id desc)
    where trashed_at is null;

create function public.reject_entry_revision_update()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
begin
    raise exception using
        errcode = 'P0001',
        message = 'Entry Revisions are immutable';
end;
$$;

create trigger entry_revisions_reject_update
before update on public.entry_revisions
for each row
execute function public.reject_entry_revision_update();

revoke all on function public.reject_entry_revision_update() from public;

alter table public.entries enable row level security;
alter table public.entries force row level security;
alter table public.entry_revisions enable row level security;
alter table public.entry_revisions force row level security;
alter table public.ai_processing enable row level security;
alter table public.ai_processing force row level security;

revoke all on table public.entries from anon, authenticated;
revoke all on table public.entry_revisions from anon, authenticated;
revoke all on table public.ai_processing from anon, authenticated;

grant select on table public.entries to authenticated;
grant select on table public.entry_revisions to authenticated;
grant select on table public.ai_processing to authenticated;

grant select, insert, update, delete
    on table public.entries
    to service_role;
grant select, insert, update, delete
    on table public.entry_revisions
    to service_role;
grant select, insert, update, delete
    on table public.ai_processing
    to service_role;

create policy "owner can read own entries"
on public.entries
for select
to authenticated
using (
    owner_id = (select auth.uid())
    and exists (
        select 1
        from public.diary_owners
        where user_id = (select auth.uid())
    )
);

create policy "owner can read own entry revisions"
on public.entry_revisions
for select
to authenticated
using (
    exists (
        select 1
        from public.entries
        where entries.id = entry_revisions.entry_id
          and entries.owner_id = (select auth.uid())
    )
);

create policy "owner can read own processing obligations"
on public.ai_processing
for select
to authenticated
using (
    exists (
        select 1
        from public.entry_revisions
        join public.entries
          on entries.id = entry_revisions.entry_id
        where entry_revisions.id = ai_processing.entry_revision_id
          and entries.owner_id = (select auth.uid())
    )
);

create or replace function public.create_diary_entry(
    p_owner_id uuid,
    p_original_content text,
    p_entry_at timestamptz,
    p_idempotency_key text
)
returns table (
    id uuid,
    current_revision_id uuid,
    revision_number integer,
    original_content text,
    entry_at timestamptz,
    created_at timestamptz,
    owner_date date,
    processing_state text,
    was_created boolean
)
language plpgsql
security invoker
set search_path = pg_catalog, public
as $$
declare
    v_entry public.entries%rowtype;
    v_revision public.entry_revisions%rowtype;
    v_processing public.ai_processing%rowtype;
    v_entry_id uuid := gen_random_uuid();
    v_revision_id uuid := gen_random_uuid();
    v_now timestamptz := clock_timestamp();
begin
    if char_length(btrim(p_original_content)) = 0 then
        raise exception using
            errcode = '22023',
            message = 'Original Content cannot be blank';
    end if;

    if char_length(btrim(p_idempotency_key)) not between 1 and 200 then
        raise exception using
            errcode = '22023',
            message = 'Idempotency key is invalid';
    end if;

    if not exists (
        select 1
        from public.diary_owners
        where user_id = p_owner_id
    ) then
        raise exception using
            errcode = '42501',
            message = 'Diary owner is not provisioned';
    end if;

    insert into public.entries (
        id,
        owner_id,
        entry_at,
        current_revision_id,
        idempotency_key,
        created_at,
        updated_at
    )
    values (
        v_entry_id,
        p_owner_id,
        coalesce(p_entry_at, v_now),
        v_revision_id,
        p_idempotency_key,
        v_now,
        v_now
    )
    on conflict (owner_id, idempotency_key) do nothing
    returning * into v_entry;

    if not found then
        select *
        into strict v_entry
        from public.entries as existing_entry
        where existing_entry.owner_id = p_owner_id
          and existing_entry.idempotency_key = p_idempotency_key;

        select *
        into strict v_revision
        from public.entry_revisions as existing_revision
        where existing_revision.entry_id = v_entry.id
          and existing_revision.id = v_entry.current_revision_id;

        select *
        into strict v_processing
        from public.ai_processing as existing_processing
        where existing_processing.entry_revision_id = v_revision.id;

        return query
        select
            v_entry.id,
            v_revision.id,
            v_revision.revision_number,
            v_revision.original_content,
            v_entry.entry_at,
            v_entry.created_at,
            (v_entry.entry_at at time zone 'Asia/Taipei')::date,
            v_processing.state,
            false;
        return;
    end if;

    insert into public.entry_revisions (
        id,
        entry_id,
        revision_number,
        original_content,
        created_at
    )
    values (
        v_revision_id,
        v_entry.id,
        1,
        p_original_content,
        v_now
    )
    returning * into v_revision;

    insert into public.ai_processing (
        id,
        entry_revision_id,
        state,
        draft_required,
        embedding_required,
        attempt_count,
        created_at,
        updated_at
    )
    values (
        gen_random_uuid(),
        v_revision.id,
        'pending',
        true,
        true,
        0,
        v_now,
        v_now
    )
    returning * into v_processing;

    return query
    select
        v_entry.id,
        v_revision.id,
        v_revision.revision_number,
        v_revision.original_content,
        v_entry.entry_at,
        v_entry.created_at,
        (v_entry.entry_at at time zone 'Asia/Taipei')::date,
        v_processing.state,
        true;
end;
$$;

create or replace function public.list_diary_entries_for_date(
    p_owner_id uuid,
    p_owner_date date
)
returns table (
    id uuid,
    current_revision_id uuid,
    revision_number integer,
    original_content text,
    entry_at timestamptz,
    created_at timestamptz,
    owner_date date,
    processing_state text
)
language sql
stable
security invoker
set search_path = pg_catalog, public
as $$
    select
        entries.id,
        entry_revisions.id,
        entry_revisions.revision_number,
        entry_revisions.original_content,
        entries.entry_at,
        entries.created_at,
        (entries.entry_at at time zone 'Asia/Taipei')::date,
        ai_processing.state
    from public.entries
    join public.entry_revisions
      on entry_revisions.entry_id = entries.id
     and entry_revisions.id = entries.current_revision_id
    join public.ai_processing
      on ai_processing.entry_revision_id = entry_revisions.id
    where entries.owner_id = p_owner_id
      and entries.trashed_at is null
      and (entries.entry_at at time zone 'Asia/Taipei')::date =
          p_owner_date
    order by entries.entry_at desc, entries.id desc;
$$;

revoke all on function public.create_diary_entry(
    uuid,
    text,
    timestamptz,
    text
) from public, anon, authenticated;
revoke all on function public.list_diary_entries_for_date(
    uuid,
    date
) from public, anon, authenticated;

grant execute on function public.create_diary_entry(
    uuid,
    text,
    timestamptz,
    text
) to service_role;
grant execute on function public.list_diary_entries_for_date(
    uuid,
    date
) to service_role;

comment on table public.entries is
    'Stable Diary Entry identity and owner-controlled Entry Time.';
comment on table public.entry_revisions is
    'Immutable complete Original Content revisions for Diary Entries.';
comment on table public.ai_processing is
    'Durable Draft and embedding obligations for each Entry Revision.';
