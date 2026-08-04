alter table public.entries
add constraint entries_entry_at_python_safe_utc_range
check (
    entry_at >= '0001-01-01 00:00:00+00'::timestamptz
    and entry_at <= '9999-12-31 23:59:59.999999+00'::timestamptz
);

drop function public.create_diary_entry(text, timestamptz, text);

create function public.create_diary_entry(
    p_original_content text,
    p_entry_at text default null,
    p_idempotency_key text default null
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
    v_entry_at timestamptz;
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

    if p_entry_at is null then
        v_entry_at := v_now;
    else
        if p_entry_at !~ '(?:[zZ]|[+-][0-9]{2}:[0-9]{2})$' then
            raise exception using
                errcode = '22023',
                message = 'Entry Time must include a UTC offset';
        end if;

        begin
            v_entry_at := p_entry_at::timestamptz;
        exception
            when invalid_datetime_format or datetime_field_overflow then
                raise exception using
                    errcode = '22023',
                    message = 'Entry Time is invalid';
        end;

        if v_entry_at < '0001-01-01 00:00:00+00'::timestamptz
            or v_entry_at >
                '9999-12-31 23:59:59.999999+00'::timestamptz
        then
            raise exception using
                errcode = '22023',
                message = 'Entry Time is outside the supported UTC range';
        end if;
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
        v_entry_at,
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

revoke all on function public.create_diary_entry(text, text, text)
    from public, anon;
grant execute on function public.create_diary_entry(text, text, text)
    to authenticated;

comment on function public.create_diary_entry(text, text, text) is
    'Atomically creates an Entry after Python-safe UTC Entry Time validation.';
