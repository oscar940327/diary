grant update (entry_at, updated_at)
    on table public.entries
    to diary_edit_mutator;

grant create on schema public to diary_edit_mutator;

create function public.change_diary_entry_time(
    p_entry_id uuid,
    p_entry_at text
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

revoke all on function public.change_diary_entry_time(uuid, text)
    from public, anon;

grant execute on function public.change_diary_entry_time(uuid, text)
    to authenticated;

comment on function public.change_diary_entry_time(uuid, text) is
    'Atomically changes owner-selected Entry Time without changing revisions.';

grant diary_edit_mutator to postgres;
alter function public.change_diary_entry_time(uuid, text)
    owner to diary_edit_mutator;
revoke create on schema public from diary_edit_mutator;
revoke diary_edit_mutator from postgres;

create table public.entry_history_positions (
    entry_id uuid not null
        references public.entries (id) on delete cascade,
    entry_at timestamptz not null,
    valid_from_xid xid8 not null,
    valid_until_xid xid8,
    primary key (entry_id, valid_from_xid),
    constraint entry_history_position_validity_changes
        check (
            valid_until_xid is null
            or valid_until_xid <> valid_from_xid
        )
);

comment on table public.entry_history_positions is
    'Snapshot-visible Entry Time positions; not Original Content revisions.';

-- Keep the backfill and trigger installation in one explicit Create exclusion
-- window, including when this migration runs beside the previous application.
do $$
begin
    lock table public.entries in share row exclusive mode;
end;
$$;

insert into public.entry_history_positions (
    entry_id,
    entry_at,
    valid_from_xid
)
select
    entries.id,
    entries.entry_at,
    entries.history_membership_xid
from public.entries;

create unique index entry_history_positions_one_current_idx
    on public.entry_history_positions (entry_id)
    where valid_until_xid is null;

create index entry_history_positions_snapshot_order_idx
    on public.entry_history_positions (entry_at desc, entry_id desc);

alter table public.entry_history_positions enable row level security;
alter table public.entry_history_positions force row level security;

revoke all on table public.entry_history_positions
    from anon, authenticated;
grant select on table public.entry_history_positions to authenticated;
grant select, insert, update, delete
    on table public.entry_history_positions
    to service_role;

create policy "owner can read own history positions"
on public.entry_history_positions
for select
to authenticated
using (
    exists (
        select 1
        from public.entries
        where entries.id = entry_history_positions.entry_id
          and entries.owner_id = (select auth.uid())
    )
);

create function public.capture_initial_entry_history_position()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
begin
    insert into public.entry_history_positions (
        entry_id,
        entry_at,
        valid_from_xid
    )
    values (
        new.id,
        new.entry_at,
        new.history_membership_xid
    );
    return new;
end;
$$;

create trigger entries_capture_initial_history_position
after insert on public.entries
for each row
execute function public.capture_initial_entry_history_position();

revoke all on function public.capture_initial_entry_history_position()
    from public;

create function public.capture_changed_entry_history_position()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
    v_change_xid xid8 := pg_current_xact_id();
begin
    update public.entry_history_positions
    set valid_until_xid = v_change_xid
    where entry_history_positions.entry_id = old.id
      and entry_history_positions.valid_until_xid is null;

    if not found then
        raise exception using
            errcode = 'P0001',
            message = 'Current Entry history position is missing';
    end if;

    insert into public.entry_history_positions (
        entry_id,
        entry_at,
        valid_from_xid
    )
    values (
        new.id,
        new.entry_at,
        v_change_xid
    );
    return new;
end;
$$;

create trigger entries_capture_changed_history_position
after update of entry_at on public.entries
for each row
when (old.entry_at is distinct from new.entry_at)
execute function public.capture_changed_entry_history_position();

revoke all on function public.capture_changed_entry_history_position()
    from public;

create function public.list_diary_history_v5(
    p_anchor_date date,
    p_direction text,
    p_cursor_entry_at timestamptz,
    p_cursor_entry_id uuid,
    p_snapshot text,
    p_limit integer
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
    has_older boolean,
    has_newer boolean,
    older_cursor_entry_at timestamptz,
    older_cursor_entry_id uuid,
    newer_cursor_entry_at timestamptz,
    newer_cursor_entry_id uuid,
    snapshot text
)
language plpgsql
volatile
security invoker
set search_path = pg_catalog, public
as $$
declare
    v_snapshot pg_snapshot;
begin
    if p_direction not in ('initial', 'older', 'newer') then
        raise exception using
            errcode = '22023',
            message = 'History direction is invalid';
    end if;

    if p_limit not between 1 and 50 then
        raise exception using
            errcode = '22023',
            message = 'History limit is invalid';
    end if;

    if p_direction = 'initial' then
        if p_anchor_date is null then
            raise exception using
                errcode = '22023',
                message = 'History anchor date is required';
        end if;
        v_snapshot := pg_current_snapshot();
    else
        if (
            p_cursor_entry_at is null
            or p_cursor_entry_id is null
            or p_snapshot is null
        ) then
            raise exception using
                errcode = '22023',
                message = 'History cursor is incomplete';
        end if;
        begin
            v_snapshot := p_snapshot::pg_snapshot;
        exception
            when invalid_text_representation then
                raise exception using
                    errcode = '22023',
                    message = 'History snapshot is invalid';
        end;
    end if;

    return query
    with eligible as (
        select
            entries.id,
            entries.current_revision_id,
            entry_revisions.revision_number,
            entry_revisions.original_content,
            entry_history_positions.entry_at,
            entries.created_at,
            (
                entry_history_positions.entry_at
                at time zone 'Asia/Taipei'
            )::date as owner_date,
            ai_processing.state as processing_state
        from public.entries
        join public.entry_history_positions
          on entry_history_positions.entry_id = entries.id
        join public.entry_revisions
          on entry_revisions.entry_id = entries.id
         and entry_revisions.id = entries.current_revision_id
        join public.ai_processing
          on ai_processing.entry_revision_id = entry_revisions.id
        where entries.owner_id = (select auth.uid())
          and entries.trashed_at is null
          and pg_visible_in_snapshot(
              entries.history_membership_xid,
              v_snapshot
          )
          and pg_visible_in_snapshot(
              entry_history_positions.valid_from_xid,
              v_snapshot
          )
          and (
              entry_history_positions.valid_until_xid is null
              or not pg_visible_in_snapshot(
                  entry_history_positions.valid_until_xid,
                  v_snapshot
              )
          )
    ),
    page as materialized (
        select *
        from eligible
        where case p_direction
            when 'initial' then
                eligible.entry_at < (
                    (p_anchor_date + 1)::timestamp
                    at time zone 'Asia/Taipei'
                )
            when 'older' then
                (eligible.entry_at, eligible.id) <
                (p_cursor_entry_at, p_cursor_entry_id)
            when 'newer' then
                (eligible.entry_at, eligible.id) >
                (p_cursor_entry_at, p_cursor_entry_id)
            else false
        end
        order by
            case when p_direction = 'newer'
                then eligible.entry_at end asc,
            case when p_direction = 'newer'
                then eligible.id end asc,
            case when p_direction <> 'newer'
                then eligible.entry_at end desc,
            case when p_direction <> 'newer'
                then eligible.id end desc
        limit p_limit
    ),
    bounds as (
        select
            (
                select page.entry_at
                from page
                order by page.entry_at desc, page.id desc
                limit 1
            ) as newest_entry_at,
            (
                select page.id
                from page
                order by page.entry_at desc, page.id desc
                limit 1
            ) as newest_entry_id,
            (
                select page.entry_at
                from page
                order by page.entry_at asc, page.id asc
                limit 1
            ) as oldest_entry_at,
            (
                select page.id
                from page
                order by page.entry_at asc, page.id asc
                limit 1
            ) as oldest_entry_id
    ),
    metadata as (
        select
            case
                when bounds.oldest_entry_at is null then false
                else exists (
                    select 1
                    from eligible
                    where (eligible.entry_at, eligible.id) <
                        (
                            bounds.oldest_entry_at,
                            bounds.oldest_entry_id
                        )
                )
            end as has_older,
            case
                when bounds.newest_entry_at is not null then exists (
                    select 1
                    from eligible
                    where (eligible.entry_at, eligible.id) >
                        (
                            bounds.newest_entry_at,
                            bounds.newest_entry_id
                        )
                )
                when p_direction = 'initial' then exists (
                    select 1
                    from eligible
                    where (eligible.entry_at, eligible.id) >
                        (
                            (
                                (p_anchor_date + 1)::timestamp
                                at time zone 'Asia/Taipei'
                            ) - interval '1 microsecond',
                            'ffffffff-ffff-ffff-ffff-ffffffffffff'::uuid
                        )
                )
                else false
            end as has_newer,
            bounds.oldest_entry_at,
            bounds.oldest_entry_id,
            case
                when bounds.newest_entry_at is not null
                    then bounds.newest_entry_at
                when p_direction = 'initial' then
                    (
                        (p_anchor_date + 1)::timestamp
                        at time zone 'Asia/Taipei'
                    ) - interval '1 microsecond'
                else null
            end as newest_entry_at,
            case
                when bounds.newest_entry_id is not null
                    then bounds.newest_entry_id
                when p_direction = 'initial' then
                    'ffffffff-ffff-ffff-ffff-ffffffffffff'::uuid
                else null
            end as newest_entry_id
        from bounds
    )
    select
        page.id,
        page.current_revision_id,
        page.revision_number,
        page.original_content,
        page.entry_at,
        page.created_at,
        page.owner_date,
        page.processing_state,
        metadata.has_older,
        metadata.has_newer,
        case when metadata.has_older
            then metadata.oldest_entry_at end,
        case when metadata.has_older
            then metadata.oldest_entry_id end,
        case when metadata.has_newer
            then metadata.newest_entry_at end,
        case when metadata.has_newer
            then metadata.newest_entry_id end,
        v_snapshot::text
    from page
    cross join metadata

    union all

    select
        null::uuid,
        null::uuid,
        null::integer,
        null::text,
        null::timestamptz,
        null::timestamptz,
        null::date,
        null::text,
        metadata.has_older,
        metadata.has_newer,
        null::timestamptz,
        null::uuid,
        case when metadata.has_newer
            then metadata.newest_entry_at end,
        case when metadata.has_newer
            then metadata.newest_entry_id end,
        v_snapshot::text
    from metadata
    where not exists (select 1 from page)
      and exists (
          select 1
          from public.diary_owners
          where diary_owners.user_id = (select auth.uid())
      )

    order by entry_at desc nulls last, id desc nulls last;
end;
$$;

revoke all on function public.list_diary_history_v5(
    date,
    text,
    timestamptz,
    uuid,
    text,
    integer
) from public, anon;

grant execute on function public.list_diary_history_v5(
    date,
    text,
    timestamptz,
    uuid,
    text,
    integer
) to authenticated;

comment on function public.list_diary_history_v5(
    date,
    text,
    timestamptz,
    uuid,
    text,
    integer
) is
    'Returns History pages with snapshot-stable Entry membership and time positions.';

comment on role diary_edit_mutator is
    'No-login owner-scoped RLS principal for controlled atomic Entry mutations.';
