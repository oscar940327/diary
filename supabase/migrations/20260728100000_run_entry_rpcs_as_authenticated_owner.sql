grant insert on table public.entries to authenticated;
grant insert on table public.entry_revisions to authenticated;
grant insert on table public.ai_processing to authenticated;

create policy "owner can create own entries"
on public.entries
for insert
to authenticated
with check (
    owner_id = (select auth.uid())
    and exists (
        select 1
        from public.diary_owners
        where user_id = (select auth.uid())
    )
);

create policy "owner can create own entry revisions"
on public.entry_revisions
for insert
to authenticated
with check (
    exists (
        select 1
        from public.entries
        where entries.id = entry_revisions.entry_id
          and entries.owner_id = (select auth.uid())
    )
);

create policy "owner can create own processing obligations"
on public.ai_processing
for insert
to authenticated
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

create function public.create_diary_entry(
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
    v_owner_id uuid := auth.uid();
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

    if v_owner_id is null or not exists (
        select 1
        from public.diary_owners
        where user_id = v_owner_id
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
        v_owner_id,
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
        where existing_entry.owner_id = v_owner_id
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

create function public.list_diary_entries_for_date(
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
    where entries.owner_id = (select auth.uid())
      and entries.trashed_at is null
      and (entries.entry_at at time zone 'Asia/Taipei')::date =
          p_owner_date
    order by entries.entry_at desc, entries.id desc;
$$;

revoke all on function public.create_diary_entry(
    text,
    timestamptz,
    text
) from public, anon;
revoke all on function public.list_diary_entries_for_date(
    date
) from public, anon;

grant execute on function public.create_diary_entry(
    text,
    timestamptz,
    text
) to authenticated;
grant execute on function public.list_diary_entries_for_date(
    date
) to authenticated;
