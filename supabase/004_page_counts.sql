-- Anonymous visit counter (2026-10-14). No cookies, no IP addresses, no personal data:
-- only daily totals per page path and per source site (e.g. "facebook.com", "google", "direct").
-- Run once in the Supabase SQL editor of project "koevalmis".
create table public.page_counts (
  day date not null,
  path text not null check (length(path) <= 120),
  source text not null check (length(source) <= 60),
  views integer not null default 0,
  primary key (day, path, source)
);
alter table public.page_counts enable row level security;
revoke all on public.page_counts from anon, authenticated;

-- Adds one view. Paths are site paths ("/fi/") or app events ("event:diag_done").
create or replace function public.count_view(p_path text, p_source text default 'direct')
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  d date := (now() at time zone 'Europe/Helsinki')::date;
  src text := coalesce(nullif(lower(p_source), ''), 'direct');
begin
  if p_path is null or p_path !~ '^(/[A-Za-z0-9/_.-]{0,118}|event:[a-z_]{1,40})$' then return; end if;
  if src !~ '^[a-z0-9._-]{1,60}$' then src := 'other'; end if;
  insert into public.page_counts (day, path, source, views) values (d, p_path, src, 1)
    on conflict (day, path, source) do update set views = public.page_counts.views + 1;
end;
$$;
revoke all on function public.count_view(text, text) from public;
grant execute on function public.count_view(text, text) to anon, authenticated;
