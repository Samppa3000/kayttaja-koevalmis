-- Koevalmis waiting list. Visitors may only insert; nobody can read rows with the public key.
create table if not exists public.waitlist (
  id          bigint generated always as identity primary key,
  email       text not null,
  lang        text not null default 'en' check (lang in ('en','fi','ru','ar','uk','so','fa','et')),
  consent     boolean not null check (consent),
  created_at  timestamptz not null default now(),
  constraint waitlist_email_format check (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$' and length(email) <= 254)
);

create unique index if not exists waitlist_email_unique on public.waitlist (lower(email));

alter table public.waitlist enable row level security;

drop policy if exists "anon can join waitlist" on public.waitlist;
create policy "anon can join waitlist"
  on public.waitlist for insert
  to anon
  with check (consent = true);

-- No select/update/delete policies: the public key cannot read or change the list.
-- Supabase grants table-level rights by default; remove them so only the three columns below can be written.
revoke all on public.waitlist from anon, authenticated;
grant insert (email, lang, consent) on public.waitlist to anon;
