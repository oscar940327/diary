create function public.list_diary_history(
    p_anchor_date date,
    p_direction text,
    p_cursor_entry_at timestamptz,
    p_cursor_entry_id uuid,
    p_snapshot_at timestamptz,
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
    snapshot_at timestamptz
)
language plpgsql
volatile
security invoker
set search_path = pg_catalog, public
as $$
declare
    v_snapshot_at timestamptz;
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
        v_snapshot_at := clock_timestamp();
    else
        if (
            p_cursor_entry_at is null
            or p_cursor_entry_id is null
            or p_snapshot_at is null
        ) then
            raise exception using
                errcode = '22023',
                message = 'History cursor is incomplete';
        end if;
        v_snapshot_at := p_snapshot_at;
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
          and entries.created_at <= v_snapshot_at
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
        exists (
            select 1
            from eligible, bounds
            where (eligible.entry_at, eligible.id) <
                (bounds.oldest_entry_at, bounds.oldest_entry_id)
        ),
        exists (
            select 1
            from eligible, bounds
            where (eligible.entry_at, eligible.id) >
                (bounds.newest_entry_at, bounds.newest_entry_id)
        ),
        v_snapshot_at
    from page
    order by page.entry_at desc, page.id desc;
end;
$$;

revoke all on function public.list_diary_history(
    date,
    text,
    timestamptz,
    uuid,
    timestamptz,
    integer
) from public, anon;

grant execute on function public.list_diary_history(
    date,
    text,
    timestamptz,
    uuid,
    timestamptz,
    integer
) to authenticated;

comment on function public.list_diary_history(
    date,
    text,
    timestamptz,
    uuid,
    timestamptz,
    integer
) is
    'Returns one stable snapshot page of owner history in either direction.';
