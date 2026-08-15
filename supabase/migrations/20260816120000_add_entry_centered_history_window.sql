create function public.get_diary_entry_history_window_v1(
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
stable
security invoker
set search_path = pg_catalog, public
as $$
declare
    v_snapshot pg_snapshot := pg_current_snapshot();
begin
    return query
    with eligible as not materialized (
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
    target as materialized (
        select *
        from eligible
        where eligible.id = p_entry_id
    ),
    nearest_newer_pool as materialized (
        select eligible.*
        from eligible
        cross join target
        where (eligible.entry_at, eligible.id) >
            (target.entry_at, target.id)
        order by eligible.entry_at asc, eligible.id asc
        limit 19
    ),
    target_and_older_pool as materialized (
        select eligible.*
        from eligible
        cross join target
        where (eligible.entry_at, eligible.id) <=
            (target.entry_at, target.id)
        order by eligible.entry_at desc, eligible.id desc
        limit 20
    ),
    availability as (
        select
            (select count(*) from nearest_newer_pool)::integer
                as newer_available,
            (select count(*) from target_and_older_pool)::integer
                as target_and_older_available
    ),
    allocation as (
        select
            least(
                target_and_older_available,
                20 - least(newer_available, 9)
            ) as target_and_older_take,
            least(
                newer_available,
                20 - least(
                    target_and_older_available,
                    20 - least(newer_available, 9)
                )
            ) as newer_take
        from availability
    ),
    page as materialized (
        (
            select *
            from nearest_newer_pool
            order by entry_at asc, id asc
            limit (select newer_take from allocation)
        )
        union all
        (
            select *
            from target_and_older_pool
            order by entry_at desc, id desc
            limit (select target_and_older_take from allocation)
        )
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
            exists (
                select 1
                from eligible
                where (eligible.entry_at, eligible.id) <
                    (bounds.oldest_entry_at, bounds.oldest_entry_id)
            ) as has_older,
            exists (
                select 1
                from eligible
                where (eligible.entry_at, eligible.id) >
                    (bounds.newest_entry_at, bounds.newest_entry_id)
            ) as has_newer,
            bounds.oldest_entry_at,
            bounds.oldest_entry_id,
            bounds.newest_entry_at,
            bounds.newest_entry_id
        from bounds
        where exists (select 1 from target)
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
    order by entry_at desc, id desc;
end;
$$;

revoke all on function public.get_diary_entry_history_window_v1(uuid)
    from public, anon;

grant execute on function public.get_diary_entry_history_window_v1(uuid)
    to authenticated;

comment on function public.get_diary_entry_history_window_v1(uuid) is
    'Returns one fixed 20-Entry snapshot window guaranteed to contain the active owner Entry.';
