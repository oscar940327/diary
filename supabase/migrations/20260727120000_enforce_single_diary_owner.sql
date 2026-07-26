alter table public.diary_owners
    add column singleton_key boolean not null default true,
    add constraint diary_owners_singleton_key_must_be_true
        check (singleton_key);

alter table public.diary_owners
    drop constraint diary_owners_pkey,
    add constraint diary_owners_user_id_key unique (user_id),
    add constraint diary_owners_pkey primary key (singleton_key);

comment on column public.diary_owners.singleton_key is
    'Database-enforced singleton key; only the permanent Diary owner row may exist.';
