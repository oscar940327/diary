create role diary_edit_mutator
    nologin
    nosuperuser
    nocreatedb
    nocreaterole
    noinherit
    nobypassrls;

create function public.diary_request_uid()
returns uuid
language sql
stable
security invoker
set search_path = pg_catalog
as $$
    select coalesce(
        nullif(current_setting('request.jwt.claim.sub', true), ''),
        (
            nullif(current_setting('request.jwt.claims', true), '')::jsonb
            ->> 'sub'
        )
    )::uuid;
$$;

revoke all on function public.diary_request_uid()
    from public, anon;
grant execute on function public.diary_request_uid()
    to authenticated, diary_edit_mutator;

grant create on schema public to diary_edit_mutator;
grant select on table public.diary_owners to diary_edit_mutator;
grant select on table public.entries to diary_edit_mutator;
grant select, insert on table public.entry_revisions to diary_edit_mutator;
grant select, insert on table public.ai_processing to diary_edit_mutator;
grant update (current_revision_id, updated_at)
    on table public.entries
    to diary_edit_mutator;
grant update (stale_at, updated_at)
    on table public.ai_processing
    to diary_edit_mutator;

alter policy "configured owner can read own authorization"
on public.diary_owners
to authenticated, diary_edit_mutator
using ((select public.diary_request_uid()) = user_id);

alter policy "owner can read own entries"
on public.entries
to authenticated, diary_edit_mutator
using (
    owner_id = (select public.diary_request_uid())
    and exists (
        select 1
        from public.diary_owners
        where user_id = (select public.diary_request_uid())
    )
);
alter policy "owner can update own current revision"
on public.entries
to authenticated, diary_edit_mutator
using (
    owner_id = (select public.diary_request_uid())
    and exists (
        select 1
        from public.diary_owners
        where user_id = (select public.diary_request_uid())
    )
)
with check (
    owner_id = (select public.diary_request_uid())
    and exists (
        select 1
        from public.diary_owners
        where user_id = (select public.diary_request_uid())
    )
);

alter policy "owner can read own entry revisions"
on public.entry_revisions
to authenticated, diary_edit_mutator
using (
    exists (
        select 1
        from public.entries
        where entries.id = entry_revisions.entry_id
          and entries.owner_id = (select public.diary_request_uid())
    )
);
alter policy "owner can create own entry revisions"
on public.entry_revisions
to authenticated, diary_edit_mutator
with check (
    exists (
        select 1
        from public.entries
        where entries.id = entry_revisions.entry_id
          and entries.owner_id = (select public.diary_request_uid())
    )
);

alter policy "owner can read own processing obligations"
on public.ai_processing
to authenticated, diary_edit_mutator
using (
    exists (
        select 1
        from public.entry_revisions
        join public.entries
          on entries.id = entry_revisions.entry_id
        where entry_revisions.id = ai_processing.entry_revision_id
          and entries.owner_id = (select public.diary_request_uid())
    )
);
alter policy "owner can create own processing obligations"
on public.ai_processing
to authenticated, diary_edit_mutator
with check (
    exists (
        select 1
        from public.entry_revisions
        join public.entries
          on entries.id = entry_revisions.entry_id
        where entry_revisions.id = ai_processing.entry_revision_id
          and entries.owner_id = (select public.diary_request_uid())
    )
);
alter policy "owner can mark own processing stale"
on public.ai_processing
to authenticated, diary_edit_mutator
using (
    exists (
        select 1
        from public.entry_revisions
        join public.entries
          on entries.id = entry_revisions.entry_id
        where entry_revisions.id = ai_processing.entry_revision_id
          and entries.owner_id = (select public.diary_request_uid())
    )
)
with check (
    exists (
        select 1
        from public.entry_revisions
        join public.entries
          on entries.id = entry_revisions.entry_id
        where entry_revisions.id = ai_processing.entry_revision_id
          and entries.owner_id = (select public.diary_request_uid())
    )
);

create or replace function public.edit_diary_entry_original_content(
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
      and entries.owner_id = (select public.diary_request_uid())
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

alter function public.edit_diary_entry_original_content(uuid, uuid, text)
    security definer;
alter function public.edit_diary_entry_original_content(uuid, uuid, text)
    set row_security = on;
grant diary_edit_mutator to postgres;
alter function public.edit_diary_entry_original_content(uuid, uuid, text)
    owner to diary_edit_mutator;
revoke create on schema public from diary_edit_mutator;
revoke diary_edit_mutator from postgres;

revoke update (current_revision_id, updated_at)
    on table public.entries
    from authenticated;
revoke update (stale_at, updated_at)
    on table public.ai_processing
    from authenticated;

comment on role diary_edit_mutator is
    'No-login owner-scoped RLS principal for the atomic Original Content edit RPC.';
