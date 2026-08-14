do $$
begin
    lock table public.entries in share row exclusive mode;
end;
$$;

alter table public.entry_time_migration_audits
drop constraint entry_time_migration_audit_version;

alter table public.entry_time_migration_audits
add constraint entry_time_migration_audit_version
check (
    migration_version in ('20260807120000', '20260809120000')
);

insert into public.entry_time_migration_audits (
    entry_id,
    owner_id,
    original_entry_at,
    transformed_entry_at,
    transformation_reason,
    migration_version
)
select
    entries.id,
    entries.owner_id,
    entries.entry_at,
    entries.entry_at - interval '24 hours',
    'Taipei-safe upper-bound remediation: active Entry Time shifted exactly 24 hours earlier',
    '20260809120000'
from public.entries
where entries.entry_at
    > '9999-12-31 15:59:59.999999+00'::timestamptz
  and entries.entry_at
    <= '9999-12-31 23:59:59.999999+00'::timestamptz
on conflict (entry_id) do nothing;

update public.entries
set entry_at = entry_time_migration_audits.transformed_entry_at
from public.entry_time_migration_audits
where entries.id = entry_time_migration_audits.entry_id
  and entries.entry_at = entry_time_migration_audits.original_entry_at
  and entries.entry_at
    > '9999-12-31 15:59:59.999999+00'::timestamptz;

alter table public.entries
add constraint entries_entry_at_taipei_grouping_safe_range
check (
    entry_at >= '0001-01-01 00:00:00+00'::timestamptz
    and entry_at <= '9999-12-31 15:59:59.999999+00'::timestamptz
);

grant diary_edit_mutator to postgres;
grant create on schema public to diary_edit_mutator;
set role diary_edit_mutator;

create or replace function public.change_diary_entry_time(
    p_entry_id uuid,
    p_entry_at text default null
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
    v_entry_at timestamptz;
begin
    if p_entry_at is null or p_entry_at !~
        '(?:[zZ]|[+-][0-9]{2}:[0-9]{2})$'
    then
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
            '9999-12-31 15:59:59.999999+00'::timestamptz
    then
        raise exception using
            errcode = '22023',
            message = 'Entry Time is outside the supported Asia/Taipei grouping range';
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

    update public.entries
    set
        entry_at = v_entry_at,
        updated_at = clock_timestamp()
    where entries.id = v_entry.id
    returning * into v_entry;

    select entry_revisions.*
    into strict v_revision
    from public.entry_revisions
    where entry_revisions.entry_id = v_entry.id
      and entry_revisions.id = v_entry.current_revision_id;

    select ai_processing.*
    into strict v_processing
    from public.ai_processing
    where ai_processing.entry_revision_id = v_revision.id;

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

comment on function public.change_diary_entry_time(uuid, text) is
    'Atomically changes Entry Time within the Asia/Taipei-safe range.';

reset role;
revoke create on schema public from diary_edit_mutator;
revoke diary_edit_mutator from postgres;

create or replace function public.create_diary_entry(
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
                '9999-12-31 15:59:59.999999+00'::timestamptz
        then
            raise exception using
                errcode = '22023',
                message = 'Entry Time is outside the supported Asia/Taipei grouping range';
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

comment on function public.create_diary_entry(text, text, text) is
    'Atomically creates an Entry within the Asia/Taipei-safe range.';
