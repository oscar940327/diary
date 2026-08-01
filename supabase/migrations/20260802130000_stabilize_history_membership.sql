alter table public.entries
    add column history_membership_xid xid8
    not null
    default pg_current_xact_id();

create function public.reject_history_membership_xid_update()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
begin
    if new.history_membership_xid is distinct from old.history_membership_xid then
        raise exception using
            errcode = '55000',
            message = 'History membership transaction identity is immutable';
    end if;
    return new;
end;
$$;

create trigger entries_history_membership_xid_is_immutable
before update of history_membership_xid
on public.entries
for each row
execute function public.reject_history_membership_xid_update();

revoke all on function public.reject_history_membership_xid_update()
    from public;

comment on column public.entries.history_membership_xid is
    'Immutable creation transaction identity used for History snapshot membership.';

create function public.list_diary_history_v4(
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
            entries.entry_at,
            entries.created_at,
            (entries.entry_at at time zone 'Asia/Taipei')::date
                as owner_date,
            ai_processing.state as processing_state
        from public.entries
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

revoke all on function public.list_diary_history_v4(
    date,
    text,
    timestamptz,
    uuid,
    text,
    integer
) from public, anon;

grant execute on function public.list_diary_history_v4(
    date,
    text,
    timestamptz,
    uuid,
    text,
    integer
) to authenticated;

comment on function public.list_diary_history_v4(
    date,
    text,
    timestamptz,
    uuid,
    text,
    integer
) is
    'Returns snapshot-stable History pages using immutable Entry membership.';
