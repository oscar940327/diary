create table public.diary_owners (
    user_id uuid primary key references auth.users (id) on delete cascade,
    created_at timestamptz not null default now()
);

comment on table public.diary_owners is
    'Administratively provisioned identities allowed to own Diary data.';

alter table public.diary_owners enable row level security;
alter table public.diary_owners force row level security;

revoke all on table public.diary_owners from anon, authenticated;
grant select on table public.diary_owners to authenticated;
grant select, insert, update, delete
    on table public.diary_owners
    to service_role;

create policy "configured owner can read own authorization"
on public.diary_owners
for select
to authenticated
using ((select auth.uid()) = user_id);
