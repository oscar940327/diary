begin;

create function public.capture_changed_entry_trash_history_position()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
    v_change_xid xid8 := pg_current_xact_id();
begin
    if old.trashed_at is null and new.trashed_at is not null then
        update public.entry_history_positions
        set valid_until_xid = v_change_xid
        where entry_history_positions.entry_id = old.id
          and entry_history_positions.valid_until_xid is null;

        if not found then
            raise exception using
                errcode = 'P0001',
                message = 'Current Entry history position is missing';
        end if;
    elsif old.trashed_at is not null and new.trashed_at is null then
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
    end if;

    return new;
end;
$$;

revoke all on function public.capture_changed_entry_trash_history_position()
    from public, anon, authenticated;

comment on function public.capture_changed_entry_trash_history_position() is
    'Tracks Trash and Restore as snapshot-visible History membership generations.';

-- Prevent a Trash or Restore write between reconciling pre-migration Trash
-- state and installing the lifecycle trigger.
lock table public.entries in share row exclusive mode;

update public.entry_history_positions
set valid_until_xid = pg_current_xact_id()
from public.entries
where entries.id = entry_history_positions.entry_id
  and entries.trashed_at is not null
  and entry_history_positions.valid_until_xid is null;

create trigger entries_capture_changed_trash_history_position
after update of trashed_at on public.entries
for each row
when (old.trashed_at is distinct from new.trashed_at)
execute function public.capture_changed_entry_trash_history_position();

commit;
