// Paddle webhook for Koevalmis.
// transaction.completed            -> the buyer (custom_data.user_id) gets an active entitlement
// adjustment.created / .updated    -> an approved full refund ends access and is counted per email
// Every event is stored once in paddle_events, so Paddle's retries are harmless.
//
// Secrets (Supabase > Edge Functions > Secrets):
//   PADDLE_WEBHOOK_SECRET  the endpoint's secret key from Paddle > Developer tools > Notifications
//   PADDLE_PRICE_IDS       optional, comma-separated price ids that unlock Koevalmis
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase.
import { createClient } from "npm:@supabase/supabase-js@2";

const SECRET = Deno.env.get("PADDLE_WEBHOOK_SECRET") ?? "";
const PRICE_IDS = (Deno.env.get("PADDLE_PRICE_IDS") ?? "").split(",").map((s) => s.trim()).filter(Boolean);
const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const enc = new TextEncoder();

async function hmacHex(key: string, msg: string): Promise<string> {
  const k = await crypto.subtle.importKey("raw", enc.encode(key), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(msg)));
  return [...sig].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function sameText(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

// Paddle-Signature: ts=1671552777;h1=<hex>[;h1=<hex> while the secret is being rotated]
async function verified(header: string | null, body: string): Promise<boolean> {
  if (!SECRET || !header) return false;
  let ts = "";
  const sigs: string[] = [];
  for (const part of header.split(";")) {
    const [k, v] = part.split("=");
    if (k === "ts") ts = v ?? "";
    if (k === "h1" && v) sigs.push(v);
  }
  const age = Math.abs(Date.now() / 1000 - Number(ts));
  if (!ts || !Number.isFinite(age) || age > 300) return false;
  const want = await hmacHex(SECRET, `${ts}:${body}`);
  return sigs.some((s) => sameText(s, want));
}

const reply = (status: number, msg: string) => new Response(msg, { status, headers: { "Content-Type": "text/plain" } });

async function onTransactionCompleted(tx: any): Promise<string> {
  const uid = tx?.custom_data?.user_id;
  if (typeof uid !== "string" || !UUID.test(uid)) return "no user_id in custom_data";
  if (PRICE_IDS.length && !(tx.items ?? []).some((i: any) => PRICE_IDS.includes(i?.price?.id))) return "other product";
  const { data, error } = await db.auth.admin.getUserById(uid);
  if (error || !data?.user?.email) return "unknown user";
  const { error: upErr } = await db.from("entitlements").upsert({
    user_id: uid,
    email: data.user.email.toLowerCase(),
    status: "active",
    paddle_transaction_id: tx.id,
    purchased_at: tx.billed_at ?? tx.updated_at ?? new Date().toISOString(),
    refunded_at: null,
  });
  if (upErr) throw upErr;
  return "access granted";
}

async function onAdjustment(adj: any): Promise<string> {
  if (adj?.action !== "refund" || adj?.status !== "approved") return "ignored adjustment";
  if (adj?.type === "partial") return "partial refund, access kept";
  const { data: ent, error } = await db.from("entitlements").select("user_id,email,status")
    .eq("paddle_transaction_id", adj.transaction_id).maybeSingle();
  if (error) throw error;
  if (!ent) return "no matching purchase";
  if (ent.status === "refunded") return "already refunded";
  const now = new Date().toISOString();
  const { error: e1 } = await db.from("entitlements").update({ status: "refunded", refunded_at: now }).eq("user_id", ent.user_id);
  if (e1) throw e1;
  await db.from("devices").delete().eq("user_id", ent.user_id);
  const { data: hist } = await db.from("refund_history").select("refunds").eq("email", ent.email).maybeSingle();
  await db.from("refund_history").upsert({ email: ent.email, refunds: (hist?.refunds ?? 0) + 1, last_refund_at: now });
  return "access ended";
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return reply(405, "POST only");
  const body = await req.text();
  if (!(await verified(req.headers.get("Paddle-Signature"), body))) return reply(401, "bad signature");
  let ev: any;
  try { ev = JSON.parse(body); } catch { return reply(400, "bad json"); }
  if (typeof ev?.event_id !== "string" || typeof ev?.event_type !== "string") return reply(400, "not a Paddle event");

  const { error: dup } = await db.from("paddle_events").insert({ event_id: ev.event_id, event_type: ev.event_type, payload: ev });
  if (dup) {
    if (dup.code === "23505") return reply(200, "duplicate");
    return reply(500, "could not log event");
  }
  try {
    let result = "ignored";
    if (ev.event_type === "transaction.completed") result = await onTransactionCompleted(ev.data);
    else if (ev.event_type === "adjustment.created" || ev.event_type === "adjustment.updated") result = await onAdjustment(ev.data);
    return reply(200, result);
  } catch (err) {
    // let Paddle retry: forget the event so the retry is processed again
    await db.from("paddle_events").delete().eq("event_id", ev.event_id);
    console.error(err);
    return reply(500, "error");
  }
});
