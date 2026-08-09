begin;

create table if not exists public.entry_time_migration_audits (
    entry_id uuid primary key,
    owner_id uuid not null,
    original_entry_at timestamptz not null,
    transformed_entry_at timestamptz not null,
    transformation_reason text not null,
    migration_version text not null,
    migrated_at timestamptz not null default statement_timestamp(),
    constraint entry_time_migration_audit_exact_shift
        check (
            transformed_entry_at
                = original_entry_at - interval '24 hours'
        ),
    constraint entry_time_migration_audit_original_range
        check (
            original_entry_at
                > '9999-12-31 15:59:59.999999+00'::timestamptz
            and original_entry_at
                <= '9999-12-31 23:59:59.999999+00'::timestamptz
        ),
    constraint entry_time_migration_audit_transformed_range
        check (
            transformed_entry_at
                >= '0001-01-01 00:00:00+00'::timestamptz
            and transformed_entry_at
                <= '9999-12-31 15:59:59.999999+00'::timestamptz
        ),
    constraint entry_time_migration_audit_reason
        check (
            transformation_reason =
                'Taipei-safe upper-bound remediation: active Entry Time shifted exactly 24 hours earlier'
        ),
    constraint entry_time_migration_audit_version
        check (migration_version = '20260807120000')
);

comment on table public.entry_time_migration_audits is
    'Immutable evidence for the authorized Taipei-safe Entry Time migration.';
comment on column public.entry_time_migration_audits.original_entry_at is
    'Exact preceding-version Entry Time retained without overwrite or deletion.';
comment on column public.entry_time_migration_audits.transformed_entry_at is
    'Active Entry Time after the authorized exact 24-hour subtraction.';

alter table public.entry_time_migration_audits enable row level security;
alter table public.entry_time_migration_audits force row level security;

revoke all on table public.entry_time_migration_audits
    from public, anon, authenticated;
grant select on table public.entry_time_migration_audits to authenticated;
grant select on table public.entry_time_migration_audits to service_role;

do $$
begin
    if not exists (
        select 1
        from pg_catalog.pg_policies
        where schemaname = 'public'
          and tablename = 'entry_time_migration_audits'
          and policyname = 'owner can read own Entry Time migration audits'
    ) then
        create policy "owner can read own Entry Time migration audits"
        on public.entry_time_migration_audits
        for select
        to authenticated
        using (owner_id = (select auth.uid()));
    end if;
end;
$$;

create or replace function public.reject_entry_time_migration_audit_mutation()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
begin
    raise exception using
        errcode = '55000',
        message = 'Entry Time migration audit evidence is immutable';
end;
$$;

revoke all on function public.reject_entry_time_migration_audit_mutation()
    from public, anon, authenticated;

do $$
begin
    if not exists (
        select 1
        from pg_catalog.pg_trigger
        where tgrelid = 'public.entry_time_migration_audits'::regclass
          and tgname = 'entry_time_migration_audits_are_immutable'
          and not tgisinternal
    ) then
        create trigger entry_time_migration_audits_are_immutable
        before update or delete
        on public.entry_time_migration_audits
        for each row
        execute function public.reject_entry_time_migration_audit_mutation();
    end if;
end;
$$;

lock table public.entries in share row exclusive mode;

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
    '20260807120000'
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

commit;
