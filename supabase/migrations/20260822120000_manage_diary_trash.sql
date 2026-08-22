grant update (trashed_at, updated_at)
    on table public.entries
    to diary_edit_mutator;

grant create on schema public to diary_edit_mutator;

create function public.move_diary_entry_to_trash(
    p_entry_id uuid
)
returns table (
    id uuid,
    current_revision_id uuid,
    revision_number integer,
    revision_count integer,
    original_content text,
    entry_at timestamptz,
    created_at timestamptz,
    owner_date date,
    processing_state text,
    trashed_at timestamptz
)
language plpgsql
volatile
security definer
set search_path = pg_catalog, public
set row_security = on
as $$
declare
    v_entry public.entries%rowtype;
    v_revision public.entry_revisions%rowtype;
    v_processing public.ai_processing%rowtype;
    v_revision_count integer;
    v_now timestamptz := clock_timestamp();
begin
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
    into strict v_revision
    from public.entry_revisions
    where entry_revisions.entry_id = v_entry.id
      and entry_revisions.id = v_entry.current_revision_id;

    select ai_processing.*
    into strict v_processing
    from public.ai_processing
    where ai_processing.entry_revision_id = v_revision.id;

    select count(*)::integer
    into v_revision_count
    from public.entry_revisions
    where entry_revisions.entry_id = v_entry.id;

    update public.entries
    set
        trashed_at = v_now,
        updated_at = v_now
    where entries.id = v_entry.id
    returning * into strict v_entry;

    return query
    select
        v_entry.id,
        v_revision.id,
        v_revision.revision_number,
        v_revision_count,
        v_revision.original_content,
        v_entry.entry_at,
        v_entry.created_at,
        (v_entry.entry_at at time zone 'Asia/Taipei')::date,
        v_processing.state,
        v_entry.trashed_at;
end;
$$;

revoke all on function public.move_diary_entry_to_trash(uuid)
    from public, anon;
grant execute on function public.move_diary_entry_to_trash(uuid)
    to authenticated;

comment on function public.move_diary_entry_to_trash(uuid) is
    'Moves one active owner-owned Entry to recoverable Trash.';

grant diary_edit_mutator to postgres;
alter function public.move_diary_entry_to_trash(uuid)
    owner to diary_edit_mutator;
revoke create on schema public from diary_edit_mutator;
revoke diary_edit_mutator from postgres;

grant delete on table public.entries to diary_edit_mutator;

create policy "owner can permanently delete own trashed entries"
on public.entries
for delete
to diary_edit_mutator
using (
    owner_id = (select public.diary_request_uid())
    and trashed_at is not null
    and exists (
        select 1
        from public.diary_owners
        where diary_owners.user_id = (select public.diary_request_uid())
    )
);

grant create on schema public to diary_edit_mutator;

create function public.permanently_delete_diary_entry(
    p_entry_id uuid,
    p_confirmation text
)
returns table (
    deleted boolean
)
language plpgsql
volatile
security definer
set search_path = pg_catalog, public
set row_security = on
as $$
begin
    if p_confirmation is distinct from 'PERMANENTLY DELETE' then
        raise exception using
            errcode = '22023',
            message = 'Permanent deletion confirmation is invalid';
    end if;

    delete from public.entries
    where entries.id = p_entry_id
      and entries.owner_id = (select public.diary_request_uid())
      and entries.trashed_at is not null;

    if not found then
        return;
    end if;

    return query select true;
end;
$$;

revoke all on function public.permanently_delete_diary_entry(uuid, text)
    from public, anon;
grant execute on function public.permanently_delete_diary_entry(uuid, text)
    to authenticated;

comment on function public.permanently_delete_diary_entry(uuid, text) is
    'Permanently deletes one confirmed owner-owned trashed Entry and cascades its dependent records.';

grant diary_edit_mutator to postgres;
alter function public.permanently_delete_diary_entry(uuid, text)
    owner to diary_edit_mutator;
revoke create on schema public from diary_edit_mutator;
revoke diary_edit_mutator from postgres;

create function public.list_diary_trash()
returns table (
    id uuid,
    current_revision_id uuid,
    revision_number integer,
    revision_count integer,
    original_content text,
    entry_at timestamptz,
    created_at timestamptz,
    owner_date date,
    processing_state text,
    trashed_at timestamptz
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
        (
            select count(*)::integer
            from public.entry_revisions as counted_revisions
            where counted_revisions.entry_id = entries.id
        ),
        entry_revisions.original_content,
        entries.entry_at,
        entries.created_at,
        (entries.entry_at at time zone 'Asia/Taipei')::date,
        ai_processing.state,
        entries.trashed_at
    from public.entries
    join public.entry_revisions
      on entry_revisions.entry_id = entries.id
     and entry_revisions.id = entries.current_revision_id
    join public.ai_processing
      on ai_processing.entry_revision_id = entry_revisions.id
    where entries.owner_id = (select auth.uid())
      and entries.trashed_at is not null
      and exists (
          select 1
          from public.diary_owners
          where diary_owners.user_id = (select auth.uid())
      )
    order by entries.trashed_at desc, entries.id desc;
$$;

revoke all on function public.list_diary_trash()
    from public, anon;
grant execute on function public.list_diary_trash()
    to authenticated;

comment on function public.list_diary_trash() is
    'Lists recoverable trashed Entries for the authenticated Diary owner.';

grant create on schema public to diary_edit_mutator;

create function public.restore_diary_entry_from_trash(
    p_entry_id uuid
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
language plpgsql
volatile
security definer
set search_path = pg_catalog, public
set row_security = on
as $$
declare
    v_entry public.entries%rowtype;
    v_revision public.entry_revisions%rowtype;
    v_processing public.ai_processing%rowtype;
    v_now timestamptz := clock_timestamp();
begin
    select entries.*
    into v_entry
    from public.entries
    where entries.id = p_entry_id
      and entries.owner_id = (select public.diary_request_uid())
      and entries.trashed_at is not null
    for update;

    if not found then
        return;
    end if;

    select entry_revisions.*
    into strict v_revision
    from public.entry_revisions
    where entry_revisions.entry_id = v_entry.id
      and entry_revisions.id = v_entry.current_revision_id;

    select ai_processing.*
    into v_processing
    from public.ai_processing
    where ai_processing.entry_revision_id = v_revision.id;

    if not found then
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
    end if;

    update public.entries
    set
        trashed_at = null,
        updated_at = v_now
    where entries.id = v_entry.id
    returning * into strict v_entry;

    return query
    select
        v_entry.id,
        v_revision.id,
        v_revision.revision_number,
        v_revision.original_content,
        v_entry.entry_at,
        v_entry.created_at,
        (v_entry.entry_at at time zone 'Asia/Taipei')::date,
        v_processing.state;
end;
$$;

revoke all on function public.restore_diary_entry_from_trash(uuid)
    from public, anon;
grant execute on function public.restore_diary_entry_from_trash(uuid)
    to authenticated;

comment on function public.restore_diary_entry_from_trash(uuid) is
    'Restores one owner-owned Entry from Trash without changing revisions.';

grant diary_edit_mutator to postgres;
alter function public.restore_diary_entry_from_trash(uuid)
    owner to diary_edit_mutator;
revoke create on schema public from diary_edit_mutator;
revoke diary_edit_mutator from postgres;
