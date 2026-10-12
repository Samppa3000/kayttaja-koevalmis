"""Build Koevalmis: merge questions, translations and glossary into the single-file app.

Translation files: data/tr_<lang>_*.json with keys
  q        {question id: {"q", "o" (multiple choice only), "e"}}
  topics   {topic: name}           (optional, in any part)
  ui       {key: string}           (optional, in any part)
  glossary {finnish term: translation} (optional, in any part)
"""
import json, glob, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TOPIC_ORDER = ["valtio", "oikeudet", "tasaarvo", "arki", "historia", "kulttuuri"]
LANG_NAMES = {"en": "English", "fi": "Suomi", "ru": "Русский", "ar": "العربية",
              "uk": "Українська", "so": "Soomaali", "fa": "دری / فارسی", "et": "Eesti"}
RTL = {"ar", "fa"}
PUBLIC_PER_TOPIC = 6   # free questions per topic: shown on the practice pages and, with the paywall on, the only ones in the app
GOOGLE_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:ital,wght@0,400..800;1,400'
                '&family=Golos+Text:wght@400..800&family=Vazirmatn:wght@400..800&display=swap">')


def jload(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load():
    qs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "q_*.json"))):
        qs += jload(f)
    qs.sort(key=lambda q: (TOPIC_ORDER.index(q["t"]), q["id"]))
    by_id = {q["id"]: q for q in qs}
    gl = jload(os.path.join(ROOT, "data", "glossary.json"))
    gl.sort(key=lambda g: g["fi"].lower())
    gl_by_fi = {g["fi"]: g for g in gl}

    langs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "tr_*_*.json"))):
        lang = re.match(r"tr_([a-z]+)_", os.path.basename(f)).group(1)
        part = jload(f)
        L = langs.setdefault(lang, {"q": {}, "topics": {}, "ui": {}, "glossary": {}})
        for k in L:
            L[k].update(part.get(k, {}))

    errors = []
    ui_out, topics_out = {}, {}
    for lang, L in langs.items():
        for qid, tr in L["q"].items():
            q = by_id.get(qid)
            if not q:
                errors.append(f"{lang}: unknown question {qid}"); continue
            if q["type"] == "mc" and len(tr.get("o", [])) != 4:
                errors.append(f"{lang}: {qid} needs 4 options")
            q[lang] = tr
        missing = [q["id"] for q in qs if lang not in q]
        if missing:
            errors.append(f"{lang}: {len(missing)} questions untranslated, e.g. {missing[:3]}")
        for fi, tr in L["glossary"].items():
            if fi in gl_by_fi:
                gl_by_fi[fi][lang] = tr
            else:
                errors.append(f"{lang}: unknown glossary term {fi}")
        ui_out[lang] = L["ui"]
        topics_out[lang] = L["topics"]

    with open(os.path.join(ROOT, "data", "paywall_ui.json"), encoding="utf-8") as fh:
        for lang, strings in json.load(fh).items():
            ui_out.setdefault(lang, {}).update({k: v for k, v in strings.items() if k not in ui_out.get(lang, {})})
    available = ["en", "fi"] + sorted(l for l in langs if not any(e.startswith(l + ":") and "untranslated" in e for e in errors))
    return {"questions": qs, "glossary": gl, "ui": ui_out, "topics": topics_out,
            "langs": [{"code": c, "name": LANG_NAMES.get(c, c), "rtl": c in RTL} for c in available]}, errors


def public_questions(qs, tp):
    """The free questions of a topic (same set on the website's practice pages)."""
    pool = sorted([q for q in qs if q["t"] == tp], key=lambda q: q["id"])
    step = max(1, len(pool) // PUBLIC_PER_TOPIC)
    return pool[::step][:PUBLIC_PER_TOPIC]


def paid_config(qs):
    """Paid-access settings for the app, from site_src/config.json. Everything here is public."""
    with open(os.path.join(ROOT, "site_src", "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg.update(json.loads(os.environ.get("KOEVALMIS_CONFIG_OVERRIDE", "{}")))  # for tests only
    on = bool(cfg.get("paywall")) and bool(cfg.get("supabase_url") and cfg.get("supabase_anon_key"))
    return {"on": on, "supabaseUrl": cfg.get("supabase_url", ""), "anonKey": cfg.get("supabase_anon_key", ""),
            "paddleEnv": cfg.get("paddle_env", "sandbox"), "paddleToken": cfg.get("paddle_client_token", ""),
            "priceId": cfg.get("paddle_price_id", ""), "total": len(qs),
            "totals": {tp: len([q for q in qs if q["t"] == tp]) for tp in TOPIC_ORDER}}


def render(html, data):
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return html.replace("/*__DATA__*/", blob)


def main():
    data, errors = load()
    for e in errors:
        print("WARN", e)
    with open(os.path.join(ROOT, "src", "app.html"), encoding="utf-8") as fh:
        html = fh.read()
    qs = data["questions"]
    paid = paid_config(qs)
    # Preview (Claude artifact): everything, no paywall.
    out = render(html, dict(data, paid=dict(paid, on=False))).replace("<!--FONTS-->", GOOGLE_FONTS)
    # Website app: with the paywall on, only the free questions are in the page; the rest come from Supabase.
    site_data = dict(data, paid=paid)
    if paid["on"]:
        site_data["questions"] = [q for tp in TOPIC_ORDER for q in public_questions(qs, tp)]
    site_out = render(html, site_data).replace("<!--FONTS-->", '<link rel="stylesheet" href="/fonts/fonts.css">')
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    # Full bank for upload to Supabase (dist/ is not committed or published).
    with open(os.path.join(ROOT, "dist", "premium_bank.json"), "w", encoding="utf-8") as fh:
        json.dump(qs, fh, ensure_ascii=False)
    path = os.path.join(ROOT, "dist", "koevalmis.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    with open(os.path.join(ROOT, "dist", "app_site.html"), "w", encoding="utf-8") as fh:
        fh.write(site_out)
    print(f"{len(data['questions'])} questions, {len(data['glossary'])} terms, "
          f"languages {[l['code'] for l in data['langs']]} -> {path} ({len(out)//1024} KB)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
