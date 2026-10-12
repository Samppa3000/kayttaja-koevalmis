"""Build the deployable Koevalmis website into site/ (GitHub Pages ready).

Pages (6 languages): landing, "citizenship test 2027" facts hub, free practice questions
(index + 6 topics), vocabulary. Plus the app (/app/), privacy, terms, 404, sitemap with
hreflang alternates, robots.txt, llms.txt, favicons and a share image.

site_src/config.json holds business details and the waiting-list endpoint. While they are
empty, the footer omits the business line, legal pages are noindex, and the waiting-list
form is replaced by a short "opens soon" note. Languages not in strings.REVIEWED are noindex.
"""
import json, os, re, shutil, subprocess, sys, html as H, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")
sys.path.insert(0, os.path.join(ROOT, "site_src"))
import strings as ST  # noqa: E402

LANGS, RTL, NAMES, SLUGS, SRC = ST.LANGS, ST.RTL, ST.NAMES, ST.SLUGS, ST.SRC
TOPIC_ORDER = ["valtio", "oikeudet", "tasaarvo", "arki", "historia", "kulttuuri"]
TOPIC_SLUG = {"valtio": "state-and-democracy", "oikeudet": "rights", "tasaarvo": "equality",
              "arki": "law-and-everyday-life", "historia": "history", "kulttuuri": "culture"}
PUBLIC_PER_TOPIC = 6
PRICE = {"en": ("€9.90", "€14.90")}
EXAMPLE_FI = "Kenelle voi tehdä kantelun, jos epäilee viranomaisen toimineen lainvastaisesti?"
TODAY = ST.CHECKED
SRC_LABEL = {"migri": "Migri", "stt": "STT / Migri", "havm": "HaVM 10/2026", "yle_vote": "Yle", "bs": "Business Standard", "kurs": "kurs.com.ua"}

CSS = """
:root{--bg:#F2F4F1;--surface:#FFFFFF;--ink:#16201B;--muted:#56635C;--line:#D3DAD5;--field:#78857E;--accent:#D9851E;--accent-ink:#1A1206;--accent-soft:#F6E3C6;--ok:#246B41;--ok-soft:#DCEFE3;--focus:#16201B;
--display:"Familjen Grotesk","Helvetica Neue",Arial,sans-serif;--body:"Atkinson Hyperlegible","Segoe UI",Roboto,"Noto Sans","Noto Sans Arabic",Tahoma,Arial,sans-serif;--r:10px}
@media (prefers-color-scheme: dark){:root{--bg:#111613;--surface:#1A211D;--ink:#E7EDE9;--muted:#9BA8A1;--line:#2D3832;--field:#738279;--accent:#E8A04A;--accent-soft:#3A2B17;--ok:#62C38D;--ok-soft:#173225;--focus:#E8A04A;color-scheme:dark}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.6;padding-inline:16px;padding-block:0 56px}
.wrap{max-width:780px;margin:0 auto}
main{display:flex;flex-direction:column;gap:52px;padding-top:28px}
.skip{position:absolute;inset-inline-start:-999px;top:8px;background:var(--surface);padding:8px 12px;border-radius:8px}
.skip:focus{inset-inline-start:16px;z-index:9}
header.top{display:flex;justify-content:space-between;align-items:center;padding-block:14px 0;gap:8px 16px;flex-wrap:wrap}
.brand{font-family:var(--display);font-weight:700;font-size:22px;display:flex;gap:10px;align-items:center;color:var(--ink);text-decoration:none;min-height:44px}
.brand .dot{width:14px;height:14px;border-radius:50%;background:var(--accent)}
nav.main{display:flex;gap:4px 14px;flex-wrap:wrap;font-size:15px;width:100%;border-bottom:1px solid var(--line)}
nav.main a{display:inline-block;padding-block:10px;min-height:44px;color:var(--muted);text-decoration:none}
nav.main a[aria-current]{color:var(--ink);font-weight:700;box-shadow:inset 0 -3px 0 var(--accent)}
nav.langs{display:flex;gap:2px 10px;flex-wrap:wrap;font-size:14px}
nav.langs a{display:inline-block;padding:10px 4px;min-height:44px;color:var(--muted)}
nav.langs a[aria-current]{color:var(--ink);font-weight:700;text-decoration:none}
.tag{font-size:14px;color:var(--muted)}
h1,h2,h3{font-family:var(--display);font-weight:700;letter-spacing:-.015em;text-wrap:balance;margin:0}
h1{font-size:clamp(30px,6.5vw,48px);line-height:1.08}h2{font-size:clamp(23px,4.2vw,29px);line-height:1.15}h3{font-size:19px}
p{margin:0;max-width:64ch}.muted{color:var(--muted)}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.hero,.sec{display:flex;flex-direction:column;gap:16px}
.pair{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:18px 20px;display:flex;flex-direction:column;gap:6px}
.pair .fi{font-weight:700;font-size:20px}.pair .tr{color:var(--muted)}
.lab{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700}
.cta{display:flex;gap:12px;flex-wrap:wrap}
.btn{font:inherit;font-weight:700;border-radius:var(--r);min-height:48px;padding:12px 22px;border:1.5px solid var(--ink);background:var(--ink);color:var(--bg);text-decoration:none;cursor:pointer;display:inline-flex;align-items:center}
.btn.acc{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.facts{display:grid;grid-template-columns:1fr;gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
@media(min-width:420px){.facts{grid-template-columns:repeat(2,1fr)}}
@media(min-width:700px){.facts{grid-template-columns:repeat(4,1fr)}}
.fact{background:var(--surface);padding:16px;display:flex;flex-direction:column;gap:4px;min-width:0}
.fact b{font-family:var(--display);font-size:22px;font-variant-numeric:tabular-nums}.fact span{font-size:15px;color:var(--muted)}
.feat{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:20px}.feat div{display:flex;flex-direction:column;gap:6px;min-width:0}
.price{background:var(--surface);border:2px solid var(--accent);border-radius:var(--r);padding:22px;display:flex;flex-direction:column;gap:12px}
.price .amt{font-family:var(--display);font-size:44px;font-weight:700;line-height:1}
.price ul{margin:0;padding-inline-start:20px;display:flex;flex-direction:column;gap:4px}
form{display:flex;gap:10px;flex-wrap:wrap}
input[type=email]{flex:1 1 220px;min-width:0;min-height:48px;font:inherit;padding:12px 14px;border-radius:var(--r);border:1.5px solid var(--field);background:var(--bg);color:var(--ink)}
::placeholder{color:var(--muted);opacity:1}
.consent{display:flex;gap:10px;align-items:flex-start;font-size:15px;color:var(--muted);flex-basis:100%}
.consent input{width:22px;height:22px;flex:none;margin-top:2px}
.formmsg{font-size:15px;flex-basis:100%}
details{border-bottom:1px solid var(--line)}
summary{cursor:pointer;font-weight:700;padding-block:12px;min-height:44px}
details>p,details>div{margin-bottom:12px}
.topics{display:flex;flex-wrap:wrap;gap:8px}.topics a,.topics span{border:1px solid var(--line);border-radius:999px;padding:8px 14px;font-size:15px;background:var(--surface);color:inherit;text-decoration:none}
.topics a:hover{border-color:var(--field)}
table{border-collapse:collapse;width:100%;font-size:16px}
th,td{text-align:start;vertical-align:top;padding:10px 8px;border-bottom:1px solid var(--line)}
th{font-size:13px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}tbody th{font-size:16px;letter-spacing:0;text-transform:none;color:var(--ink)}
.scroll{overflow-x:auto}
ol.time{list-style:none;margin:0;padding:0;border-inline-start:2px solid var(--line)}
ol.time li{padding:0 0 14px 18px;position:relative}
[dir=rtl] ol.time li{padding:0 18px 14px 0}
ol.time li::before{content:"";position:absolute;inset-inline-start:-7px;top:7px;width:12px;height:12px;border-radius:50%;background:var(--surface);border:2px solid var(--field)}
ol.time b{display:block}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px 18px;display:flex;flex-direction:column;gap:10px}
.q .qfi{font-weight:700;font-size:19px}
.q ol{margin:0;padding-inline-start:24px;display:flex;flex-direction:column;gap:2px}
.q details{border:0}
.ans{color:var(--ok);font-weight:700}
.note{background:var(--accent-soft);padding:10px 14px;border-radius:var(--r)}
.crumbs{font-size:14px;color:var(--muted)}.crumbs a{color:inherit}
footer{font-size:14px;color:var(--muted);border-top:1px solid var(--line);margin-top:56px;padding-top:16px;display:flex;flex-direction:column;gap:6px}
footer nav{display:flex;gap:4px 16px;flex-wrap:wrap}footer nav a{display:inline-block;padding-block:10px}
a{color:inherit}main a{overflow-wrap:anywhere}[dir=rtl] [lang=fi]{direction:ltr;unicode-bidi:isolate;text-align:left}
.doc{max-width:68ch;display:flex;flex-direction:column;gap:14px}.doc h2{margin-top:12px}.warn{background:var(--accent-soft);padding:10px 14px;border-radius:var(--r)}
"""


def e(s):
    return H.escape(str(s), quote=True)


def load_data():
    subprocess.run([sys.executable, os.path.join(ROOT, "build.py")], check=False, stdout=subprocess.DEVNULL)
    qs = []
    for f in sorted(os.listdir(os.path.join(ROOT, "data"))):
        if f.startswith("q_"):
            qs += json.load(open(os.path.join(ROOT, "data", f), encoding="utf-8"))
    tr = {l: {"q": {}, "topics": {}, "glossary": {}, "ui": {}} for l in LANGS}
    for f in sorted(os.listdir(os.path.join(ROOT, "data"))):
        m = re.match(r"tr_([a-z]+)_\d+\.json", f)
        if m and m.group(1) in tr:
            d = json.load(open(os.path.join(ROOT, "data", f), encoding="utf-8"))
            for k in tr[m.group(1)]:
                tr[m.group(1)][k].update(d.get(k, {}))
    gl = json.load(open(os.path.join(ROOT, "data", "glossary.json"), encoding="utf-8"))
    gl.sort(key=lambda g: g["fi"].lower())
    return qs, tr, gl


TOPIC_NAMES = {"fi": {"valtio": "Valtio ja demokratia", "oikeudet": "Perus- ja ihmisoikeudet", "tasaarvo": "Yhdenvertaisuus ja tasa-arvo",
                      "arki": "Laki ja arki", "historia": "Historia", "kulttuuri": "Kulttuuri ja tavat"},
               "en": {"valtio": "State and democracy", "oikeudet": "Fundamental and human rights", "tasaarvo": "Equality and non-discrimination",
                      "arki": "Law and everyday life", "historia": "History", "kulttuuri": "Culture and customs"}}


def topic_name(lang, tp, tr):
    if lang in TOPIC_NAMES:
        return TOPIC_NAMES[lang][tp]
    return tr[lang]["topics"].get(tp) or TOPIC_NAMES["en"][tp]


def tr_lang(lang):
    """Language of the translation shown under Finnish text."""
    return "en" if lang == "fi" else lang


def q_text(q, lang, tr):
    if lang in ("fi", "en"):
        return q[lang]
    return tr[lang]["q"][q["id"]]


def options(q, lang, tr, S):
    if q["type"] == "tf":
        if lang == "fi":
            return ["Totta", "Väärin"]
        ui = tr[lang]["ui"] if lang not in ("en",) else {}
        return [ui.get("tTrue", "True"), ui.get("tFalse", "False")]
    return q_text(q, lang, tr)["o"]


# ---------------------------------------------------------------- page registry
PAGES = []   # (page_id, lang, path)


def page_path(pid, lang):
    if pid.startswith("qs-"):
        return SLUGS["qs"][lang] + TOPIC_SLUG[pid[3:]] + "/"
    return SLUGS[pid][lang]


def indexable(lang):
    return lang in ST.REVIEWED


def head(lang, pid, title, desc, cfg, jsonld=None, robots=None, path=None):
    base = cfg["base_url"].rstrip("/")
    path = path or page_path(pid, lang)
    if pid:
        alts = "".join(f'<link rel="alternate" hreflang="{l}" href="{base}{page_path(pid, l)}">' for l in LANGS if indexable(l))
        alts += f'<link rel="alternate" hreflang="x-default" href="{base}{page_path(pid, "en")}">'
    else:
        alts = ""
    if robots is None:
        robots = "index,follow" if indexable(lang) else "noindex,follow"
    og_alt = "".join(f'<meta property="og:locale:alternate" content="{ST.OG_LOCALE[l]}">' for l in LANGS if l != lang and indexable(l))
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (jsonld or []))
    return (f'<!doctype html><html lang="{lang}" dir="{"rtl" if lang in RTL else "ltr"}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>'
            f'<meta name="description" content="{e(desc)}"><meta name="robots" content="{robots}">'
            f'<link rel="canonical" href="{base}{path}">{alts}'
            f'<meta property="og:site_name" content="Koevalmis"><meta property="og:type" content="website">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{base}{path}"><meta property="og:image" content="{base}/og.png">'
            f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta property="og:locale" content="{ST.OG_LOCALE[lang]}">{og_alt}<meta name="twitter:card" content="summary_large_image">'
            f'<link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/favicon.svg" type="image/svg+xml">'
            f'<link rel="apple-touch-icon" href="/apple-touch-icon.png"><meta name="theme-color" content="#F2F4F1">'
            f'<link rel="preload" href="/fonts/atkinson-hyperlegible-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="stylesheet" href="/fonts/fonts.css"><style>{CSS}</style>{ld}</head><body>')


def header(lang, pid, S):
    nav = [("home", S["navHome"]), ("hub", S["navHub"]), ("qs", S["navQs"]), ("voc", S["navVoc"])]
    cur = "qs" if pid.startswith("qs") else pid
    links = "".join(f'<a href="{page_path(p, lang)}"{" aria-current=\"page\"" if p == cur else ""}>{e(lbl)}</a>' for p, lbl in nav)
    links += f'<a href="/app/#{lang}">{e(S["navApp"])}</a>'
    langs = "".join(f'<a href="{page_path(pid, l)}" hreflang="{l}" lang="{l}"{" aria-current=\"true\"" if l == lang else ""}>{e(NAMES[l])}</a>' for l in LANGS)
    return (f'<a class="skip" href="#main">{e(S["skip"])}</a><div class="wrap"><header class="top">'
            f'<a class="brand" href="{page_path("home", lang)}"><span class="dot" aria-hidden="true"></span>Koevalmis</a>'
            f'<nav class="langs" aria-label="{e(S["langLabel"])}">{langs}</nav>'
            f'<nav class="main" aria-label="Koevalmis">{links}</nav></header><main id="main">')


def footer(lang, S, cfg):
    biz = ""
    if all(cfg.get(k) for k in ("business_name", "business_id", "email")):
        biz = f'<span>{e(cfg["business_name"])} · {e(cfg["business_id"])} · <span dir="ltr">{e(cfg["email"])}</span></span>'
    note = f'<span>{e(S["reviewNote"])}</span>' if S.get("reviewNote") else ""
    return (f'</main><footer><span>{e(S["foot1"])}</span>{biz}{note}'
            f'<nav aria-label="{e(S["privacy"])}"><a href="/privacy/">{e(S["privacy"])}</a><a href="/terms/">{e(S["terms"])}</a></nav>'
            f'</footer></div>')


def num(s):
    return f'<bdi dir="ltr">{s}</bdi>'


# ---------------------------------------------------------------- landing
def landing(lang, S, cfg, tr):
    now, later = PRICE.get(lang, ("9,90 €", "14,90 €"))
    base = cfg["base_url"].rstrip("/")
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in S["faq"])
    wl_ready = bool(cfg.get("waitlist_url") and cfg.get("waitlist_anon_key"))
    if wl_ready:
        wl = json.dumps({"url": cfg["waitlist_url"], "key": cfg["waitlist_anon_key"], "lang": lang,
                         "msg": {k: S[k] for k in ("wlBad", "wlOk", "wlErr", "wlConsent")}}, ensure_ascii=False)
        form = f"""<form id="wl" novalidate>
      <label for="email" class="muted" style="flex-basis:100%">{e(S['wlLabel'])}</label>
      <input id="email" type="email" autocomplete="email" placeholder="you@example.com" required aria-describedby="wlmsg">
      <button class="btn acc" type="submit">{e(S['wlBtn'])}</button>
      <label class="consent"><input id="consent" type="checkbox" required> <span>{e(S['consent'])} <a href="/privacy/">{e(S['privacy'])}</a></span></label>
      <span id="wlmsg" class="formmsg" role="status"></span>
      <input type="text" name="website" id="hp" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;inset-inline-start:-9999px">
    </form>
    <script>(function(){{const C={wl};const f=document.getElementById("wl"),m=document.getElementById("wlmsg"),em=document.getElementById("email"),cb=document.getElementById("consent");
f.addEventListener("submit",async ev=>{{ev.preventDefault();if(document.getElementById("hp").value)return;const v=em.value.trim();
const bad=!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(v);em.setAttribute("aria-invalid",bad);
if(bad){{m.textContent=C.msg.wlBad;em.focus();return;}}if(!cb.checked){{m.textContent=C.msg.wlConsent;cb.focus();return;}}
try{{const r=await fetch(C.url+"/rest/v1/waitlist",{{method:"POST",headers:{{"apikey":C.key,"Authorization":"Bearer "+C.key,"Content-Type":"application/json","Prefer":"return=minimal"}},body:JSON.stringify({{email:v,lang:C.lang,consent:true}})}});
m.textContent=(r.ok||r.status===409)?C.msg.wlOk:C.msg.wlErr;if(r.ok||r.status===409)f.reset();}}catch(err){{m.textContent=C.msg.wlErr;}}}});}})();</script>"""
    else:
        form = f'<p class="note">{e(S["wlClosed"])} <a href="/app/#diag-{lang}">{e(S["cta1"])}</a></p>'
    tr_ex = S.get("exTr", "")
    topics = "".join(f'<a href="{page_path("qs-" + tp, lang)}">{e(topic_name(lang, tp, tr))}</a>' for tp in TOPIC_ORDER)
    jsonld = [{
        "@context": "https://schema.org", "@graph": [
            {"@type": "Organization", "@id": f"{base}/#org", "name": "Koevalmis", "url": f"{base}/", "logo": f"{base}/logo.png",
             **({"email": cfg["email"]} if cfg.get("email") else {})},
            {"@type": "WebSite", "@id": f"{base}/#site", "name": "Koevalmis", "url": f"{base}/", "publisher": {"@id": f"{base}/#org"},
             "inLanguage": [l for l in LANGS if indexable(l)]},
            {"@type": "WebApplication", "name": "Koevalmis", "url": f"{base}/app/", "applicationCategory": "EducationalApplication",
             "operatingSystem": "Any (web browser)", "inLanguage": lang, "publisher": {"@id": f"{base}/#org"},
             "offers": {"@type": "Offer", "price": "9.90", "priceCurrency": "EUR", "availability": "https://schema.org/PreOrder", "url": f"{base}{page_path('home', lang)}#price"}},
            {"@type": "FAQPage", "inLanguage": lang, "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in S["faq"]]},
        ]}]
    body = f"""
<section class="hero">
  <span class="tag">{e(S['tag'])}</span>
  <h1>{e(S['h1'])}</h1>
  <p class="muted">{e(S['lead'])}</p>
  <div class="pair"><span class="lab">{e(S['exLabel'])}</span><span class="fi" lang="fi">{e(EXAMPLE_FI)}</span>{f'<span class="tr">{e(tr_ex)}</span>' if tr_ex else ''}</div>
  <div class="cta"><a class="btn acc" href="/app/#diag-{lang}">{e(S['cta1'])}</a><a class="btn" href="#price">{e(S['cta2'])}</a></div>
</section>
<section class="sec" aria-labelledby="facts"><h2 id="facts">{e(S['factsH'])}</h2>
  <div class="facts">
    <div class="fact"><b>{num('1.3.2027')}</b><span>{e(S['f1'])}</span></div>
    <div class="fact"><b>{num('18–64')}</b><span>{e(S['f2'])}</span></div>
    <div class="fact"><b>{num('FI / SV')}</b><span>{e(S['f3'])}</span></div>
    <div class="fact"><b>{e(S['f4n'])}</b><span>{e(S['f4'])}</span></div>
  </div>
  <p>{e(S['topicsIntro'])}</p>
  <div class="topics">{topics}</div>
  <p class="muted">{e(S['unknown'])} <a href="{SRC['migri']}">{e(S['src1'])}</a>, <a href="{SRC['stt']}">{e(S['src2'])}</a>. <a href="{page_path('hub', lang)}">{e(S['navHub'])} →</a></p>
</section>
<section class="sec" aria-labelledby="how"><h2 id="how">{e(S['howH'])}</h2>
  <div class="feat"><div><h3>{e(S['h3a'])}</h3><p>{e(S['pa'])}</p></div><div><h3>{e(S['h3b'])}</h3><p>{e(S['pb'])}</p></div><div><h3>{e(S['h3c'])}</h3><p>{e(S['pc'])}</p></div></div>
</section>
<section class="sec" id="price" aria-labelledby="pricing"><h2 id="pricing">{e(S['priceH'])}</h2>
  <div class="price"><div class="amt">{num(now)}</div><p>{e(S['priceNote'])} {e(S['priceLater'])}</p>
    <ul>{''.join(f'<li>{e(x)}</li>' for x in S['li'])}</ul>
    {form}
  </div>
</section>
<section class="sec" aria-labelledby="faq"><h2 id="faq">{e(S['faqH'])}</h2><div>{faq}</div></section>"""
    return head(lang, "home", S["title"], S["desc"], cfg, jsonld) + header(lang, "home", S) + body + footer(lang, S, cfg) + "</body></html>"


# ---------------------------------------------------------------- hub
def hub(lang, S, cfg, tr):
    base = cfg["base_url"].rstrip("/")
    rows = "".join(f'<tr><th scope="row">{e(k)}</th><td>{e(v)}</td><td><a href="{SRC[s]}">{e(SRC_LABEL[s])}</a></td></tr>' for k, v, s in S["facts"])
    rep = "".join(f'<li>{e(t)} (<a href="{SRC[s]}">{e(lbl)}</a>)</li>' for t, s, lbl in S["reported"])
    tl = "".join(f'<li><b>{e(d)}</b>{e(t)} · <a href="{SRC[s]}">{e(SRC_LABEL[s])}</a></li>' for d, t, s in S["timeline"])
    topics = "".join(f'<a href="{page_path("qs-" + tp, lang)}">{e(topic_name(lang, tp, tr))}</a>' for tp in TOPIC_ORDER)
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in S["faq"][:4])
    srcs = "".join(f'<li><a href="{u}">{e(u)}</a></li>' for u in dict.fromkeys(SRC[s] for _, _, s in S["facts"] + [(0, 0, x[1]) for x in S["reported"]] + [(0, 0, x[2]) for x in S["timeline"]]))
    jsonld = [{"@context": "https://schema.org", "@type": "Article", "headline": S["hubH1"], "description": S["hubDesc"],
               "inLanguage": lang, "datePublished": "2026-10-12", "dateModified": TODAY,
               "author": {"@type": "Organization", "name": "Koevalmis", "url": f"{base}/"},
               "publisher": {"@type": "Organization", "name": "Koevalmis", "logo": {"@type": "ImageObject", "url": f"{base}/logo.png"}},
               "mainEntityOfPage": f"{base}{page_path('hub', lang)}", "image": f"{base}/og.png",
               "citation": list(dict.fromkeys(SRC.values()))},
              breadcrumbs(base, lang, S, [("hub", S["navHub"])])]
    body = f"""
<section class="sec">
  <p class="crumbs"><a href="{page_path('home', lang)}">{e(S['navHome'])}</a> › {e(S['navHub'])}</p>
  <h1>{e(S['hubH1'])}</h1>
  <p class="muted">{e(S['updated'])} <time datetime="{TODAY}">{num(ST.CHECKED_FI)}</time></p>
  <p style="font-size:19px">{e(S['hubAnswer'])}</p>
</section>
<section class="sec"><h2>{e(S['factsH'])}</h2>
  <div class="scroll"><table><thead><tr>{''.join(f'<th scope="col">{e(h)}</th>' for h in S['factsTH'])}</tr></thead><tbody>{rows}</tbody></table></div>
</section>
<section class="sec"><h2>{e(S['notYetH'])} ({e(S['checkedLabel'])} {num(ST.CHECKED_FI)})</h2>
  <ul>{''.join(f'<li>{e(x)}</li>' for x in S['notYet'])}</ul>
  <h3>{e(S['reportedH'])}</h3><ul>{rep}</ul>
</section>
<section class="sec"><h2>{e(S['timelineH'])}</h2><ol class="time">{tl}</ol></section>
<section class="sec"><h2>{e(S['topicsH'])}</h2><div class="topics">{topics}</div>
  <div class="cta"><a class="btn acc" href="/app/#diag-{lang}">{e(S['cta1'])}</a></div></section>
<section class="sec"><h2>{e(S['faqH'])}</h2><div>{faq}</div></section>
<section class="sec"><h2>{e(S['sourcesH'])}</h2><ul>{srcs}</ul><p class="muted">{e(S['notAdvice'])}</p></section>"""
    return head(lang, "hub", S["hubTitle"], S["hubDesc"], cfg, jsonld) + header(lang, "hub", S) + body + footer(lang, S, cfg) + "</body></html>"


def breadcrumbs(base, lang, S, trail):
    items = [{"@type": "ListItem", "position": 1, "name": S["navHome"], "item": f"{base}{page_path('home', lang)}"}]
    for i, (pid, name) in enumerate(trail, start=2):
        items.append({"@type": "ListItem", "position": i, "name": name, "item": f"{base}{page_path(pid, lang)}"})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


# ---------------------------------------------------------------- practice questions
def public_questions(qs, tp):
    pool = sorted([q for q in qs if q["t"] == tp], key=lambda q: q["id"])
    step = max(1, len(pool) // PUBLIC_PER_TOPIC)
    return pool[::step][:PUBLIC_PER_TOPIC]


def question_card(q, lang, tr, S, n):
    TL = tr_lang(lang)
    fi = q["fi"]
    fo = options(q, "fi", tr, S)
    to = options(q, TL, tr, S)
    tq = q_text(q, TL, tr)
    letters = "ABCD"
    opts = "".join(f'<li><span lang="fi">{e(o)}</span></li>' for o in fo)
    tr_opts = "".join(f"<li>{e(o)}</li>" for o in to)
    return f"""<article class="card q" id="{q['id']}">
  <p class="qfi" lang="fi">{num(n)}. {e(fi['q'])}</p>
  <ol type="A" lang="fi">{opts}</ol>
  <details><summary>{e(S['trLabel'])}</summary><div lang="{TL}"><p>{e(tq['q'])}</p><ol type="A">{tr_opts}</ol></div></details>
  <details><summary>{e(S['ansLabel'])}</summary><div>
    <p class="ans">{e(S['correct'])}: {num(letters[q['a']])} – <span lang="fi">{e(fo[q['a']])}</span></p>
    <p lang="fi">{e(fi['e'])}</p>
    <p lang="{TL}" class="muted">{e(tq['e'])}</p></div></details>
</article>"""


def qs_index(lang, S, cfg, tr, qs):
    base = cfg["base_url"].rstrip("/")
    blocks = []
    for tp in TOPIC_ORDER:
        sample = public_questions(qs, tp)[0]
        name = topic_name(lang, tp, tr)
        total = len([q for q in qs if q["t"] == tp])
        blocks.append(f'<div class="card"><h2><a href="{page_path("qs-" + tp, lang)}">{e(name)}</a></h2>'
                      f'<p lang="fi">{e(sample["fi"]["q"])}</p><p class="muted">{e(S["qCount"].format(n=total))} · '
                      f'<a href="{page_path("qs-" + tp, lang)}">{num(PUBLIC_PER_TOPIC)} →</a></p></div>')
    jsonld = [breadcrumbs(base, lang, S, [("qs", S["navQs"])])]
    body = f"""<section class="sec">
  <p class="crumbs"><a href="{page_path('home', lang)}">{e(S['navHome'])}</a> › {e(S['navQs'])}</p>
  <h1>{e(S['qsH1'])}</h1><p>{e(S['qsIntro'])}</p><p class="note">{e(S['qsDisc'])}</p>
  <div class="cta"><a class="btn acc" href="/app/#diag-{lang}">{e(S['cta1'])}</a></div>
</section><section class="sec">{''.join(blocks)}</section>"""
    return head(lang, "qs", S["qsTitle"], S["qsDesc"], cfg, jsonld) + header(lang, "qs", S) + body + footer(lang, S, cfg) + "</body></html>"


def qs_topic(lang, S, cfg, tr, qs, tp):
    base = cfg["base_url"].rstrip("/")
    name = topic_name(lang, tp, tr)
    total = len([q for q in qs if q["t"] == tp])
    cards = "".join(question_card(q, lang, tr, S, i + 1) for i, q in enumerate(public_questions(qs, tp)))
    others = "".join(f'<a href="{page_path("qs-" + o, lang)}">{e(topic_name(lang, o, tr))}</a>' for o in TOPIC_ORDER if o != tp)
    pid = "qs-" + tp
    jsonld = [breadcrumbs(base, lang, S, [("qs", S["navQs"]), (pid, name)])]
    body = f"""<section class="sec">
  <p class="crumbs"><a href="{page_path('home', lang)}">{e(S['navHome'])}</a> › <a href="{page_path('qs', lang)}">{e(S['navQs'])}</a> › {e(name)}</p>
  <h1>{e(S['topicH1'].format(topic=name))}</h1>
  <p class="muted">{e(S['updated'])} <time datetime="{TODAY}">{num(ST.CHECKED_FI)}</time></p>
  <p class="note">{e(S['qsDisc'])}</p>
</section>
<section class="sec">{cards}
  <div class="cta"><a class="btn acc" href="/app/#{lang}">{e(S['ctaApp'].format(n=len(qs)))}</a></div></section>
<section class="sec"><h2>{e(S['otherTopics'])}</h2><div class="topics">{others}</div></section>"""
    return (head(lang, pid, S["topicTitle"].format(topic=name), S["topicDesc"].format(topic=name), cfg, jsonld)
            + header(lang, pid, S) + body + footer(lang, S, cfg) + "</body></html>")


# ---------------------------------------------------------------- vocabulary
def vocab(lang, S, cfg, tr, gl):
    base = cfg["base_url"].rstrip("/")
    TL = tr_lang(lang)
    def tword(g):
        return g["en"] if TL == "en" else tr[TL]["glossary"].get(g["fi"], g["en"])
    rows = "".join(f'<tr><th scope="row" lang="fi">{e(g["fi"])}</th><td lang="{TL}">{e(tword(g))}</td><td lang="fi">{e(g["d"])}</td></tr>' for g in gl)
    jsonld = [{"@context": "https://schema.org", "@type": "DefinedTermSet", "name": S["vocH1"], "inLanguage": ["fi", TL],
               "url": f"{base}{page_path('voc', lang)}",
               "hasDefinedTerm": [{"@type": "DefinedTerm", "name": g["fi"], "alternateName": tword(g), "description": g["d"]} for g in gl]},
              breadcrumbs(base, lang, S, [("voc", S["navVoc"])])]
    body = f"""<section class="sec">
  <p class="crumbs"><a href="{page_path('home', lang)}">{e(S['navHome'])}</a> › {e(S['navVoc'])}</p>
  <h1>{e(S['vocH1'])}</h1><p>{e(S['vocIntro'])}</p>
  <div class="scroll"><table><thead><tr><th scope="col">{e(S['colFi'])}</th><th scope="col">{e(S['colTr'])}</th><th scope="col">{e(S['colDef'])}</th></tr></thead><tbody>{rows}</tbody></table></div>
  <div class="cta"><a class="btn acc" href="/app/#gloss-{lang}">{e(S['navApp'])}</a></div>
</section>"""
    return head(lang, "voc", S["vocTitle"], S["vocDesc"], cfg, jsonld) + header(lang, "voc", S) + body + footer(lang, S, cfg) + "</body></html>"


# ---------------------------------------------------------------- app, legal, 404
def app_page(cfg):
    with open(os.path.join(ROOT, "dist", "app_site.html"), encoding="utf-8") as fh:
        app = fh.read()
    app = re.sub(r"^<title>.*?</title>", "", app, count=1)
    base = cfg["base_url"].rstrip("/")
    links = "".join(f'<li><a href="{page_path("qs", l)}" lang="{l}">{e(NAMES[l])}</a></li>' for l in LANGS)
    app = app.replace('<main id="app"><h1>Koevalmis</h1><p>Practice questions for the Finnish citizenship test, in Finnish with translations. This app needs JavaScript.</p></main>',
                      f'<main id="app"><h1>Koevalmis</h1><p>Practice app for the Finnish citizenship test. It needs JavaScript. Free practice questions as plain pages:</p><ul>{links}</ul></main>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Koevalmis – practice app</title><meta name="robots" content="noindex,follow">'
            f'<link rel="canonical" href="{base}/app/"><link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/favicon.svg" type="image/svg+xml">'
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png"></head><body>' + app + "</body></html>")


def legal_page(kind, cfg, S):
    name = cfg.get("business_name") or "[toiminimi]"
    bid = cfg.get("business_id") or "[Y-tunnus]"
    mail = cfg.get("email") or "[sähköposti]"
    ready = all(cfg.get(k) for k in ("business_name", "business_id", "email"))
    warn = "" if ready else '<p class="warn">Luonnos: täydennetään yrityksen tiedoilla ennen myynnin avaamista. Draft: business details will be added before sales open.</p>'
    with open(os.path.join(ROOT, "site_src", f"{kind}.html"), encoding="utf-8") as fh:
        body = fh.read().replace("{{NAME}}", e(name)).replace("{{ID}}", e(bid)).replace("{{EMAIL}}", e(mail))
    body = body.replace('<h1 lang="en">', '<h2 lang="en" style="font-size:clamp(26px,5vw,34px)">', 1)
    body = re.sub(r'(<h2 lang="en"[^>]*>[^<]*)</h1>', r"\1</h2>", body, count=1)
    title = {"privacy": "Tietosuojaseloste – Privacy notice | Koevalmis", "terms": "Myyntiehdot – Terms of sale | Koevalmis"}[kind]
    return (head("fi", None, title, title, cfg, robots="index,follow" if ready else "noindex,follow", path=f"/{kind}/")
            + header("fi", "home", S).replace('<nav class="langs"', '<nav hidden class="langs"')
            + f'<div class="doc">{warn}{body}</div>' + footer("fi", S, cfg) + "</body></html>")


def page_404(cfg, ALL):
    links = "".join(f'<li><a href="{page_path("home", l)}" lang="{l}">{e(NAMES[l])}</a> · <a href="{page_path("qs", l)}" lang="{l}">{e(ALL[l]["navQs"])}</a></li>' for l in LANGS)
    return (head("en", None, "Page not found | Koevalmis", "Page not found", cfg, robots="noindex", path="/404.html")
            + header("en", "home", ALL["en"]) + f'<section class="sec"><h1>Page not found · Sivua ei löytynyt</h1><ul>{links}</ul></section>'
            + footer("en", ALL["en"], cfg) + "</body></html>")


# ---------------------------------------------------------------- assets
def make_images(out):
    from PIL import Image, ImageDraw, ImageFont
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    def font(path, size):  # build servers without DejaVu fall back to Pillow's bundled font
        return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default(size=size)
    bg, ink, muted, acc = (242, 244, 241), (22, 32, 27), (86, 99, 92), (217, 133, 30)
    img = Image.new("RGB", (1200, 630), bg)
    d = ImageDraw.Draw(img)
    d.ellipse((80, 92, 128, 140), fill=acc)
    d.text((150, 84), "Koevalmis", font=font(bold, 56), fill=ink)
    d.text((80, 200), "Finnish citizenship test 2027", font=font(bold, 64), fill=ink)
    d.text((80, 290), "Practice questions in Finnish, with translations", font=font(reg, 38), fill=muted)
    d.text((80, 340), "EN · FI · RU · AR · FA · SO", font=font(reg, 38), fill=muted)
    d.rounded_rectangle((80, 430, 1120, 540), radius=16, fill=(255, 255, 255), outline=(211, 218, 213), width=2)
    d.text((110, 462), "Kuka säätää Suomen lait?  A) Eduskunta", font=font(bold, 36), fill=ink)
    img.save(os.path.join(out, "og.png"), optimize=True)
    for size, name in ((180, "apple-touch-icon.png"), (512, "logo.png"), (192, "icon-192.png")):
        ic = Image.new("RGB", (size, size), bg)
        di = ImageDraw.Draw(ic)
        m = size * 0.22
        di.ellipse((m, m, size - m, size - m), fill=acc)
        ic.save(os.path.join(out, name), optimize=True)
    ico = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(ico).ellipse((4, 4, 60, 60), fill=acc + (255,))
    ico.save(os.path.join(out, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    with open(os.path.join(out, "favicon.svg"), "w") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="#D9851E"/></svg>')


# Set by the deploy workflow when the site is served from a sub-path such as
# https://samppa3000.github.io/kayttaja-koevalmis/ instead of its own domain.
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")


def apply_base_path(out):
    """Prefix root-relative links for a sub-path preview and keep the preview out of search engines."""
    attr = re.compile(r'(\b(?:href|src|action)=")/(?!/)')
    for d, _, fs in os.walk(out):
        for f in fs:
            if not f.endswith((".html", ".css")):
                continue
            p = os.path.join(d, f)
            with open(p, encoding="utf-8") as fh:
                t = fh.read()
            t = attr.sub(lambda m: m.group(1) + BASE_PATH + "/", t)
            t = t.replace("url(/fonts/", f"url({BASE_PATH}/fonts/")
            t = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex,nofollow">', t)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(t)


def write(rel, content):
    p = os.path.join(OUT, rel.lstrip("/"))
    if p.endswith("/"):
        p += "index.html"
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content)


def sitemap(cfg):
    base = cfg["base_url"].rstrip("/")
    ids = ["home", "hub", "qs", "voc"] + ["qs-" + t for t in TOPIC_ORDER]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    langs = [l for l in LANGS if indexable(l)]
    for pid in ids:
        for l in langs:
            out.append(f"  <url><loc>{base}{page_path(pid, l)}</loc><lastmod>{TODAY}</lastmod>")
            for a in langs:
                out.append(f'    <xhtml:link rel="alternate" hreflang="{a}" href="{base}{page_path(pid, a)}"/>')
            out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{base}{page_path(pid, "en")}"/>')
            out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def llms_txt(cfg, ALL):
    base = cfg["base_url"].rstrip("/")
    S = ALL["en"]
    facts = "\n".join(f"- {k}: {v} (source: {SRC[s]})" for k, v, s in S["facts"])
    return f"""# Koevalmis

> Independent practice service for the Finnish citizenship test (knowledge of Finnish society), required for most citizenship applications submitted from 1 March 2027. Not affiliated with the Finnish Immigration Service (Migri). Facts checked {ST.CHECKED}.

## Key facts
{facts}
- Not published yet (as of {ST.CHECKED}): number of questions, pass mark, fee, exact test dates.

## Key pages
- [Finnish citizenship test 2027: what is known]({base}{page_path('hub', 'en')}): facts, timeline and sources
- [Free practice questions]({base}{page_path('qs', 'en')}): example questions in Finnish with translation, answer and explanation
- [Vocabulary]({base}{page_path('voc', 'en')}): 64 key Finnish terms with definitions
- [Practice app]({base}/app/): level test, timed mock exam, translations in English, Russian, Arabic, Dari/Persian and Somali

## Other languages
""" + "\n".join(f"- {NAMES[l]}: {base}{page_path('hub', l)}" for l in LANGS if indexable(l) and l != "en") + f"""

## Official sources
- Finnish Immigration Service (Migri): {SRC['migri']}
- Migri press release (STT): {SRC['stt']}
"""


def main():
    with open(os.path.join(ROOT, "site_src", "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    ALL = ST.load()
    qs, tr, gl = load_data()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for lang in LANGS:
        S = ALL[lang]
        write(page_path("home", lang), landing(lang, S, cfg, tr))
        write(page_path("hub", lang), hub(lang, S, cfg, tr))
        write(page_path("qs", lang), qs_index(lang, S, cfg, tr, qs))
        for tp in TOPIC_ORDER:
            write(page_path("qs-" + tp, lang), qs_topic(lang, S, cfg, tr, qs, tp))
        write(page_path("voc", lang), vocab(lang, S, cfg, tr, gl))
    write("/app/", app_page(cfg))
    write("/privacy/", legal_page("privacy", cfg, ALL["fi"]))
    write("/terms/", legal_page("terms", cfg, ALL["fi"]))
    write("/404.html", page_404(cfg, ALL))
    write("/sitemap.xml", sitemap(cfg))
    write("/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {cfg['base_url'].rstrip('/')}/sitemap.xml\n")
    write("/llms.txt", llms_txt(cfg, ALL))
    if not BASE_PATH:
        write("/CNAME", cfg["base_url"].split("//")[1].strip("/") + "\n")
    write("/.nojekyll", "")
    shutil.copytree(os.path.join(ROOT, "site_src", "fonts"), os.path.join(OUT, "fonts"))
    shutil.copy(os.path.join(ROOT, "site_src", "fonts.css"), os.path.join(OUT, "fonts", "fonts.css"))
    make_images(OUT)
    if BASE_PATH:
        apply_base_path(OUT)
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    missing = [k for k in ("business_name", "business_id", "email", "waitlist_url", "waitlist_anon_key") if not cfg.get(k)]
    print(f"site built: {n} files")
    if missing:
        print("not yet configured:", missing)


if __name__ == "__main__":
    main()
