grant create on schema public to diary_edit_mutator;

create function public.restore_diary_entry_revision(
    p_entry_id uuid,
    p_selected_revision_id uuid,
    p_expected_current_revision_id uuid
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
    restore_applied boolean
)
language plpgsql
volatile
security definer
set search_path = pg_catalog, public
set row_security = on
as $$
declare
    v_entry public.entries%rowtype;
    v_current_revision public.entry_revisions%rowtype;
    v_selected_revision public.entry_revisions%rowtype;
    v_new_revision public.entry_revisions%rowtype;
    v_processing public.ai_processing%rowtype;
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
    into strict v_current_revision
    from public.entry_revisions
    where entry_revisions.entry_id = v_entry.id
      and entry_revisions.id = v_entry.current_revision_id;

    select entry_revisions.*
    into v_selected_revision
    from public.entry_revisions
    where entry_revisions.entry_id = v_entry.id
      and entry_revisions.id = p_selected_revision_id
      and entry_revisions.id <> v_entry.current_revision_id;

    if not found then
        return;
    end if;

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

    select ai_processing.*
    into strict v_processing
    from public.ai_processing
    where ai_processing.entry_revision_id = v_current_revision.id
      and ai_processing.stale_at is null;

    update public.ai_processing
    set
        stale_at = v_now,
        updated_at = v_now
    where ai_processing.entry_revision_id in (
        select entry_revisions.id
        from public.entry_revisions
        where entry_revisions.entry_id = v_entry.id
    )
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
        v_selected_revision.original_content,
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

revoke all on function public.restore_diary_entry_revision(
    uuid,
    uuid,
    uuid
) from public, anon;

grant execute on function public.restore_diary_entry_revision(
    uuid,
    uuid,
    uuid
) to authenticated;

comment on function public.restore_diary_entry_revision(uuid, uuid, uuid) is
    'Atomically copies one historical revision into a new current revision.';

grant diary_edit_mutator to postgres;
alter function public.restore_diary_entry_revision(uuid, uuid, uuid)
    owner to diary_edit_mutator;
revoke create on schema public from diary_edit_mutator;
revoke diary_edit_mutator from postgres;
