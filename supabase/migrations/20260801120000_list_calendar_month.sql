create function public.list_diary_calendar_month(
    p_month date
)
returns table (
    owner_date date,
    entry_count bigint
)
language sql
stable
security invoker
set search_path = pg_catalog, public
as $$
    select
        (entries.entry_at at time zone 'Asia/Taipei')::date,
        count(*)
    from public.entries
    where p_month = date_trunc('month', p_month)::date
      and entries.owner_id = (select auth.uid())
      and entries.trashed_at is null
      and entries.entry_at >= (
          p_month::timestamp at time zone 'Asia/Taipei'
      )
      and entries.entry_at < (
          (p_month + interval '1 month')::timestamp
          at time zone 'Asia/Taipei'
      )
    group by (entries.entry_at at time zone 'Asia/Taipei')::date
    order by 1;
$$;

revoke all on function public.list_diary_calendar_month(date)
    from public, anon;

grant execute on function public.list_diary_calendar_month(date)
    to authenticated;

comment on function public.list_diary_calendar_month(date) is
    'Counts active Entries by Asia/Taipei date without reading Entry content.';
