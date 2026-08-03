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
            '9999-12-31 23:59:59.999999+00'::timestamptz
    then
        raise exception using
            errcode = '22023',
            message = 'Entry Time is outside the supported UTC range';
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
    'Atomically changes Entry Time within the Python-safe UTC range.';

reset role;
revoke create on schema public from diary_edit_mutator;
revoke diary_edit_mutator from postgres;
