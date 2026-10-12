-- Koevalmis paid access (applied to Supabase project "koevalmis", eu-north-1).
-- entitlements: who has paid (one row per buyer, written only by the Paddle webhook)
-- devices / device_claims: max 3 signed-in devices, max 8 new devices per 30 days
-- premium_questions: the paid question bank, readable only through get_premium_bank()
-- paddle_events: webhook log, also makes webhook handling idempotent
-- refund_history: refunds per email, for the "one refund per email" rule

create table public.entitlements (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  status text not null check (status in ('active', 'refunded')),
  paddle_transaction_id text unique,
  purchased_at timestamptz not null default now(),
  refunded_at timestamptz
);

create table public.refund_history (
  email text primary key,
  refunds int not null default 0,
  last_refund_at timestamptz
);

create table public.devices (
  user_id uuid not null references auth.users(id) on delete cascade,
  device_id text not null check (device_id ~ '^[A-Za-z0-9_-]{16,64}$'),
  first_seen timestamptz not null default now(),
  last_seen timestamptz not null default now(),
  primary key (user_id, device_id)
);

create table public.device_claims (
  user_id uuid not null references auth.users(id) on delete cascade,
  device_id text not null,
  claimed_at timestamptz not null default now()
);
create index device_claims_user_time on public.device_claims (user_id, claimed_at);

create table public.premium_questions (
  id text primary key,
  topic text not null,
  data jsonb not null,
  updated_at timestamptz not null default now()
);

create table public.paddle_events (
  event_id text primary key,
  event_type text not null,
  received_at timestamptz not null default now(),
  payload jsonb not null
);

-- Row level security on every table. The only policy lets a signed-in user read their own entitlement.
alter table public.entitlements enable row level security;
alter table public.refund_history enable row level security;
alter table public.devices enable row level security;
alter table public.device_claims enable row level security;
alter table public.premium_questions enable row level security;
alter table public.paddle_events enable row level security;

create policy "read own entitlement" on public.entitlements
  for select to authenticated using (user_id = (select auth.uid()));

-- Register this device for a signed-in buyer. Keeps the 3 most recently used devices,
-- and allows at most 8 new devices per 30 days so one account cannot be passed around a group.
create or replace function public.claim_device(p_device text)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  uid uuid := auth.uid();
  known boolean;
  recent int;
begin
  if uid is null then raise exception 'not_signed_in' using errcode = 'P0001'; end if;
  if p_device is null or p_device !~ '^[A-Za-z0-9_-]{16,64}$' then raise exception 'bad_device' using errcode = 'P0001'; end if;
  if not exists (select 1 from public.entitlements e where e.user_id = uid and e.status = 'active') then
    raise exception 'no_purchase' using errcode = 'P0001';
  end if;
  select exists (select 1 from public.devices d where d.user_id = uid and d.device_id = p_device) into known;
  if not known then
    select count(distinct c.device_id) into recent from public.device_claims c
      where c.user_id = uid and c.claimed_at > now() - interval '30 days';
    if recent >= 8 then raise exception 'device_quota' using errcode = 'P0001'; end if;
    insert into public.device_claims (user_id, device_id) values (uid, p_device);
  end if;
  insert into public.devices (user_id, device_id) values (uid, p_device)
    on conflict (user_id, device_id) do update set last_seen = now();
  delete from public.devices d
    where d.user_id = uid
      and d.device_id not in (select d2.device_id from public.devices d2 where d2.user_id = uid order by d2.last_seen desc limit 3);
  return 'ok';
end;
$$;

-- The paid question bank, for a buyer on a registered device only.
create or replace function public.get_premium_bank(p_device text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not_signed_in' using errcode = 'P0001'; end if;
  if not exists (select 1 from public.entitlements e where e.user_id = uid and e.status = 'active') then
    raise exception 'no_purchase' using errcode = 'P0001';
  end if;
  update public.devices d set last_seen = now() where d.user_id = uid and d.device_id = p_device;
  if not found then raise exception 'device_removed' using errcode = 'P0001'; end if;
  return coalesce((select jsonb_agg(q.data order by q.id) from public.premium_questions q), '[]'::jsonb);
end;
$$;

-- Table access: the browser key (anon / authenticated) gets nothing except reading its own entitlement.
revoke all on public.refund_history, public.devices, public.device_claims, public.premium_questions, public.paddle_events from anon, authenticated;
revoke all on public.entitlements from anon;
revoke insert, update, delete, truncate on public.entitlements from authenticated;

-- Functions: only signed-in users may call them.
revoke all on function public.claim_device(text) from public, anon;
revoke all on function public.get_premium_bank(text) from public, anon;
grant execute on function public.claim_device(text) to authenticated;
grant execute on function public.get_premium_bank(text) to authenticated;
