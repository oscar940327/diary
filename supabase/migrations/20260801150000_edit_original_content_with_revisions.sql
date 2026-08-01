alter table public.ai_processing
    add column stale_at timestamptz;

alter table public.ai_processing
    add constraint ai_processing_stale_after_creation
    check (stale_at is null or stale_at >= created_at);

grant update (current_revision_id, updated_at)
    on table public.entries
    to authenticated;
grant update (stale_at, updated_at)
    on table public.ai_processing
    to authenticated;

create policy "owner can update own current revision"
on public.entries
for update
to authenticated
using (
    owner_id = (select auth.uid())
    and exists (
        select 1
        from public.diary_owners
        where user_id = (select auth.uid())
    )
)
with check (
    owner_id = (select auth.uid())
    and exists (
        select 1
        from public.diary_owners
        where user_id = (select auth.uid())
    )
);

create policy "owner can mark own processing stale"
on public.ai_processing
for update
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
)
with check (
    exists (
        select 1
        from public.entry_revisions
        join public.entries
          on entries.id = entry_revisions.entry_id
        where entry_revisions.id = ai_processing.entry_revision_id
          and entries.owner_id = (select auth.uid())
    )
);

create function public.get_diary_entry(p_entry_id uuid)
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
     and ai_processing.stale_at is null
    where entries.id = p_entry_id
      and entries.owner_id = (select auth.uid())
      and entries.trashed_at is null;
$$;

create function public.list_diary_entry_revisions(p_entry_id uuid)
returns table (
    id uuid,
    entry_id uuid,
    revision_number integer,
    original_content text,
    created_at timestamptz,
    is_current boolean
)
language sql
stable
security invoker
set search_path = pg_catalog, public
as $$
    select
        entry_revisions.id,
        entry_revisions.entry_id,
        entry_revisions.revision_number,
        entry_revisions.original_content,
        entry_revisions.created_at,
        entry_revisions.id = entries.current_revision_id
    from public.entries
    join public.entry_revisions
      on entry_revisions.entry_id = entries.id
    where entries.id = p_entry_id
      and entries.owner_id = (select auth.uid())
      and entries.trashed_at is null
    order by entry_revisions.revision_number desc;
$$;

create function public.edit_diary_entry_original_content(
    p_entry_id uuid,
    p_expected_current_revision_id uuid,
    p_original_content text
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
    edit_applied boolean
)
language plpgsql
volatile
security invoker
set search_path = pg_catalog, public
as $$
declare
    v_entry public.entries%rowtype;
    v_current_revision public.entry_revisions%rowtype;
    v_new_revision public.entry_revisions%rowtype;
    v_processing public.ai_processing%rowtype;
    v_now timestamptz := clock_timestamp();
begin
    if char_length(btrim(p_original_content)) = 0 then
        raise exception using
            errcode = '22023',
            message = 'Original Content cannot be blank';
    end if;

    select entries.*
    into v_entry
    from public.entries
    where entries.id = p_entry_id
      and entries.owner_id = (select auth.uid())
      and entries.trashed_at is null
    for update;

    if not found then
        return;
    end if;

    select entry_revisions.*
    into strict v_current_revision
    from public.entry_revisions
    where entry_revisions.entry_id = v_entry.id
      and entry_revisions.id = v_entry.current_revision_id;

    if v_entry.current_revision_id <> p_expected_current_revision_id then
        select ai_processing.*
        into strict v_processing
        from public.ai_processing
        where ai_processing.entry_revision_id = v_current_revision.id;

        return query
        select
            v_entry.id,
            v_current_revision.id,
            v_current_revision.revision_number,
            v_current_revision.original_content,
            v_entry.entry_at,
            v_entry.created_at,
            (v_entry.entry_at at time zone 'Asia/Taipei')::date,
            v_processing.state,
            false;
        return;
    end if;

    update public.ai_processing
    set
        stale_at = v_now,
        updated_at = v_now
    where ai_processing.entry_revision_id = v_current_revision.id
      and ai_processing.stale_at is null;

    if not found then
        raise exception using
            errcode = 'P0001',
            message = 'Current revision processing obligation is missing';
    end if;

    insert into public.entry_revisions (
        id,
        entry_id,
        revision_number,
        original_content,
        created_at
    )
    values (
        gen_random_uuid(),
        v_entry.id,
        v_current_revision.revision_number + 1,
        p_original_content,
        v_now
    )
    returning * into v_new_revision;

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
        v_new_revision.id,
        'pending',
        true,
        true,
        0,
        v_now,
        v_now
    )
    returning * into v_processing;

    update public.entries
    set
        current_revision_id = v_new_revision.id,
        updated_at = v_now
    where entries.id = v_entry.id
    returning * into v_entry;

    return query
    select
        v_entry.id,
        v_new_revision.id,
        v_new_revision.revision_number,
        v_new_revision.original_content,
        v_entry.entry_at,
        v_entry.created_at,
        (v_entry.entry_at at time zone 'Asia/Taipei')::date,
        v_processing.state,
        true;
end;
$$;

revoke all on function public.get_diary_entry(uuid)
    from public, anon;
revoke all on function public.list_diary_entry_revisions(uuid)
    from public, anon;
revoke all on function public.edit_diary_entry_original_content(
    uuid,
    uuid,
    text
) from public, anon;

grant execute on function public.get_diary_entry(uuid)
    to authenticated;
grant execute on function public.list_diary_entry_revisions(uuid)
    to authenticated;
grant execute on function public.edit_diary_entry_original_content(
    uuid,
    uuid,
    text
) to authenticated;

comment on column public.ai_processing.stale_at is
    'When set, this obligation belongs to a superseded Entry Revision.';
comment on function public.get_diary_entry(uuid) is
    'Returns one active Entry with its current complete Original Content.';
comment on function public.list_diary_entry_revisions(uuid) is
    'Returns complete immutable revisions for one owner Entry, newest first.';
comment on function public.edit_diary_entry_original_content(
    uuid,
    uuid,
    text
) is
    'Atomically applies a revision-aware complete Original Content replacement.';
