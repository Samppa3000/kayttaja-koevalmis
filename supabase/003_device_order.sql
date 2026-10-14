-- Optional hardening (2026-10-14). Run in the Supabase SQL editor together with the Paddle setup.
-- Uses the exact clock time when a device signs in, so "keep the 3 most recent devices" is exact
-- even if several devices sign in within the same database transaction. In normal use every
-- sign-in is its own request, so the behaviour is already correct without this.
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
  insert into public.devices (user_id, device_id, first_seen, last_seen) values (uid, p_device, clock_timestamp(), clock_timestamp())
    on conflict (user_id, device_id) do update set last_seen = clock_timestamp();
  delete from public.devices d
    where d.user_id = uid
      and d.device_id not in (select d2.device_id from public.devices d2 where d2.user_id = uid
                              order by d2.last_seen desc, d2.first_seen desc limit 3);
  return 'ok';
end;
$$;

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
  update public.devices d set last_seen = clock_timestamp() where d.user_id = uid and d.device_id = p_device;
  if not found then raise exception 'device_removed' using errcode = 'P0001'; end if;
  return coalesce((select jsonb_agg(q.data order by q.id) from public.premium_questions q), '[]'::jsonb);
end;
$$;

revoke all on function public.claim_device(text) from public, anon;
revoke all on function public.get_premium_bank(text) from public, anon;
grant execute on function public.claim_device(text) to authenticated;
grant execute on function public.get_premium_bank(text) to authenticated;
