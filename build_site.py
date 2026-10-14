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
import strings_sales as SS  # noqa: E402

LANGS, RTL, NAMES, SLUGS, SRC = ST.LANGS, ST.RTL, ST.NAMES, ST.SLUGS, ST.SRC
TOPIC_ORDER = ["valtio", "oikeudet", "tasaarvo", "arki", "historia", "kulttuuri"]
TOPIC_SLUG = {"valtio": "state-and-democracy", "oikeudet": "rights", "tasaarvo": "equality",
              "arki": "law-and-everyday-life", "historia": "history", "kulttuuri": "culture"}
from build import PUBLIC_PER_TOPIC  # noqa: E402
PRICE = {"en": ("€9.90", "€14.90")}
EXAMPLE_FI = "Kenelle voi tehdä kantelun, jos epäilee viranomaisen toimineen lainvastaisesti?"
TODAY = ST.CHECKED
SRC_LABEL = {"migri": "Migri", "stt": "STT / Migri", "havm": "HaVM 10/2026", "yle_vote": "Yle", "bs": "Business Standard", "kurs": "kurs.com.ua"}

CSS = """
:root{--paper:#F4F6F3;--card:#FFFFFF;--ink:#10201F;--muted:#4C5E5B;--line:#D4DCD9;--field:#7A8B88;
--lake:#0F3B3D;--lake-ink:#F2F6F4;--lake-muted:#A9C4C0;--lake-line:#2B5759;
--berry:#F3A43B;--berry-hover:#F7B85F;--berry-ink:#1C1405;--berry-soft:#FCEBD2;
--moss:#1F6B45;--moss-soft:#DDEFE4;--lingon:#B3343C;--lingon-soft:#F7E0E1;--focus:#10201F;
--font:"Koe Sans","Atkinson Hyperlegible Next","Segoe UI",Roboto,"Noto Sans",Tahoma,Arial,sans-serif;
--h1:clamp(34px,6.4vw,58px);--h2:clamp(26px,4vw,36px);--r:14px}
@media (prefers-color-scheme: dark){:root{--paper:#0C1B1C;--card:#13282A;--ink:#E4EDEB;--muted:#9FB3AF;--line:#25403F;--field:#6F8784;
--lake:#082B2D;--lake-line:#22494B;--berry:#F5B04F;--berry-hover:#F8C06F;--berry-soft:#3A2B17;--moss:#63C190;--moss-soft:#143326;--lingon:#F07D84;--lingon-soft:#3A1D20;--focus:#F5B04F;color-scheme:dark}}
*{box-sizing:border-box}[hidden]{display:none!important}html{-webkit-text-size-adjust:100%;overflow-x:clip}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font);font-size:17px;line-height:1.6}
[dir=rtl] body{line-height:1.85}
.wrap{max-width:1120px;margin:0 auto;padding-inline:16px}
@media(min-width:700px){.wrap{padding-inline:28px}}
.bleed{position:relative;isolation:isolate}
.bleed::before{content:"";position:absolute;z-index:-1;inset:0 calc(50% - 50vw);background:var(--bgc)}
header.site{z-index:5}
.lake{--bgc:var(--lake);--focus:var(--berry);color:var(--lake-ink)}
.lake a{color:inherit}.lake .muted{color:var(--lake-muted)}
a{color:inherit;text-underline-offset:.18em}main a{overflow-wrap:anywhere}
p{margin:0;max-width:66ch}.muted{color:var(--muted)}
:focus-visible{outline:3px solid var(--focus);outline-offset:3px;border-radius:4px}
.skip{position:absolute;inset-inline-start:-999px;top:8px;z-index:50;background:var(--card);color:var(--ink);padding:10px 14px;border-radius:8px}
.skip:focus{inset-inline-start:16px}
h1,h2,h3{font-weight:800;text-wrap:balance;margin:0}
h1{font-size:var(--h1);line-height:1.04;letter-spacing:-.028em;hyphens:auto;-webkit-hyphens:auto;overflow-wrap:break-word}
:lang(fi) h1,h1:lang(fi){font-size:clamp(32px,5.4vw,50px)}
h2{font-size:var(--h2);line-height:1.12;letter-spacing:-.02em}
h3{font-size:20px;line-height:1.25;letter-spacing:-.01em}
[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] h3{letter-spacing:0;line-height:1.35}
/* header */
header.site{display:flex;flex-wrap:wrap;align-items:center;gap:0 24px;padding-block:8px 0}
.brand{display:inline-flex;align-items:center;gap:10px;font-weight:800;font-size:21px;letter-spacing:-.01em;text-decoration:none;min-height:52px;margin-inline-end:auto}
.brand svg{width:28px;height:28px;flex:none}
nav.main{order:3;flex-basis:100%;display:flex;gap:2px 6px;overflow-x:auto;scrollbar-width:none;margin-inline:-16px;padding-inline:10px;border-top:1px solid var(--lake-line)}
nav.main::-webkit-scrollbar{display:none}
nav.main a{flex:none;padding:12px 8px;min-height:48px;text-decoration:none;color:var(--lake-muted);font-size:15px;white-space:nowrap}
nav.main a:hover{color:var(--lake-ink)}
nav.main a[aria-current]{color:var(--lake-ink);font-weight:700;box-shadow:inset 0 -3px 0 var(--berry)}
@media(min-width:960px){nav.main{order:0;flex-basis:auto;border:0;margin:0;padding:0}}
details.langs{position:relative}
details.langs summary{list-style:none;display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:8px 14px;border:1px solid var(--lake-line);border-radius:999px;cursor:pointer;font-size:15px}
details.langs summary:hover{border-color:var(--lake-muted)}
summary::-webkit-details-marker{display:none}
details.langs svg{width:18px;height:18px}
details.langs ul{position:absolute;inset-inline-end:0;top:calc(100% + 8px);z-index:40;list-style:none;margin:0;padding:6px;min-width:210px;background:var(--card);border:1px solid var(--line);border-radius:var(--r);box-shadow:0 18px 40px -10px rgba(5,25,26,.4)}
details.langs ul a{display:block;padding:10px 14px;border-radius:8px;text-decoration:none;color:var(--ink);min-height:44px}
details.langs ul a:hover{background:var(--paper)}
details.langs ul a[aria-current]{background:var(--berry-soft);font-weight:700}
/* buttons */
.cta{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.btn{font:inherit;font-weight:700;display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:52px;padding:12px 26px;border-radius:999px;border:2px solid transparent;text-decoration:none;cursor:pointer;text-align:center;transition:background-color .15s,border-color .15s,transform .1s}
.btn.primary{background:var(--berry);color:var(--berry-ink)}
.btn.primary:hover{background:var(--berry-hover)}
.btn:active{transform:translateY(1px)}
.btn.ghost{border-color:var(--lake-line);color:var(--lake-ink);background:transparent}
.btn.ghost:hover{border-color:var(--lake-muted)}
.btn.dark{background:var(--ink);color:var(--paper)}
.more{display:inline-flex;align-items:center;min-height:52px;padding-inline:8px;font-weight:700}
/* hero */
.hero{padding-block:28px 48px;display:grid;gap:36px;align-items:start}
@media(min-width:960px){.hero{grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:64px;padding-block:56px 88px;align-items:center}}
.intro{display:flex;flex-direction:column;gap:20px;min-width:0}
.tag{font-size:15px;color:var(--lake-muted);display:flex;gap:8px;align-items:center}
.tag svg{width:16px;height:16px;flex:none}
.lead{font-size:19px;color:var(--lake-muted);max-width:52ch}
.count{display:flex;gap:12px;align-items:center;color:var(--lake-muted);font-size:15px;padding-top:4px}
.count b{color:var(--lake-ink);font-size:26px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1}
.count svg{width:22px;height:22px;flex:none;color:var(--berry)}
.proof{font-size:15px;color:var(--lake-muted)}
/* question card (hero demo and practice pages) */
.qcard{position:relative;background:var(--card);color:var(--ink);border-radius:20px;padding:22px 20px 20px;display:flex;flex-direction:column;gap:14px;--focus:var(--ink)}
.hero .qcard{box-shadow:0 30px 60px -18px rgba(0,0,0,.55);animation:rise .7s .15s cubic-bezier(.2,.8,.2,1) both}
@media (prefers-color-scheme: dark){.qcard{--focus:var(--berry)}}
@keyframes rise{from{opacity:0;transform:translateY(22px) rotate(1.5deg)}}
.qhead{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.qhead .lbl{font-size:15px;font-weight:700;color:var(--muted)}
.tools{display:flex;gap:6px;flex-wrap:wrap}
.tool{font:inherit;font-size:15px;display:inline-flex;gap:6px;align-items:center;min-height:44px;padding:6px 14px;border:1px solid var(--line);border-radius:999px;background:var(--card);color:var(--ink);cursor:pointer}
.tool:hover{border-color:var(--field)}
.tool svg{width:18px;height:18px}
.tool[aria-pressed=true]{background:var(--ink);color:var(--card);border-color:var(--ink)}
.qtext{font-size:clamp(21px,2.6vw,25px);font-weight:800;line-height:1.3;letter-spacing:-.01em;margin:0}
.qtr,.otr{display:block;color:var(--muted);font-size:16px;font-weight:400;letter-spacing:0}
.opts{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.opt{width:100%;font:inherit;text-align:start;display:flex;gap:12px;align-items:flex-start;padding:12px 14px;min-height:54px;border:1.5px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);cursor:pointer;transition:border-color .15s,background-color .15s}
.opt:hover:not(:disabled){border-color:var(--ink)}
.opt .k{flex:none;width:28px;height:28px;border-radius:50%;border:1.5px solid var(--field);display:grid;place-items:center;font-weight:700;font-size:14px;margin-top:-1px}
.opt:disabled{cursor:default}
.opt:disabled:not(.ok):not(.no){opacity:.55}
.opt.ok{border-color:var(--moss);background:var(--moss-soft)}.opt.ok .k{background:var(--moss);border-color:var(--moss);color:var(--card)}
.opt.no{border-color:var(--lingon);background:var(--lingon-soft)}.opt.no .k{background:var(--lingon);border-color:var(--lingon);color:var(--card)}
.res{display:flex;flex-direction:column;gap:10px;padding-top:4px}
.res[hidden]{display:none}
.res .msg{font-weight:700}
.stamp{position:absolute;top:-16px;inset-inline-start:-6px;padding:4px 14px;border:3px solid currentColor;outline:1.5px solid currentColor;outline-offset:3px;border-radius:10px;font-weight:800;font-size:24px;letter-spacing:.08em;text-transform:uppercase;color:var(--moss);background:var(--card);transform:rotate(-7deg);opacity:0;pointer-events:none}
.qcard.done .qhead .lbl{visibility:hidden}
.qcard .muted{color:var(--muted)}
.stamp.no{color:var(--lingon)}
.stamp.on{opacity:1;animation:thump .45s cubic-bezier(.2,.9,.3,1.25) both}
@keyframes thump{0%{opacity:0;transform:rotate(-16deg) scale(2)}55%{opacity:1;transform:rotate(-6deg) scale(.92)}100%{opacity:1;transform:rotate(-7deg) scale(1)}}
.qcard.hit{animation:hit .32s .18s ease-out}
@keyframes hit{40%{transform:translateY(4px)}}
/* sections */
main>section{padding-top:72px}
main>section.hero,main>section.pagehead{padding-top:28px}
.sec{display:flex;flex-direction:column;gap:20px;max-width:760px}
.sec.wide{max-width:none}
.facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px 24px;margin:0}
@media(min-width:820px){.facts{grid-template-columns:repeat(4,minmax(0,1fr))}}
.fact{border-top:3px solid var(--ink);padding-top:12px;display:flex;flex-direction:column;gap:4px;min-width:0}
.fact b{font-size:24px;font-weight:800;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.fact span{font-size:15px;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips a,.chips span{display:inline-flex;align-items:center;min-height:44px;padding:8px 16px;border-radius:999px;background:var(--card);border:1px solid var(--line);text-decoration:none;color:var(--ink);font-size:15px}
.chips a:hover{border-color:var(--ink)}
ol.steps{list-style:none;margin:0;padding:0;display:grid;counter-reset:s}
ol.steps li{counter-increment:s;position:relative;padding-inline-start:64px;padding-bottom:28px;display:flex;flex-direction:column;gap:4px}
ol.steps li::before{content:counter(s);position:absolute;inset-inline-start:0;top:-6px;width:46px;height:46px;border-radius:50%;background:var(--lake);color:var(--lake-ink);display:grid;place-items:center;font-weight:800;font-size:19px}
ol.steps li:first-child::before{background:var(--berry);color:var(--berry-ink)}
ol.steps li::after{content:"";position:absolute;inset-inline-start:22px;top:46px;bottom:2px;width:2px;background:var(--line)}
ol.steps li:last-child::after{display:none}
ol.steps p{color:var(--muted)}
@media(min-width:860px){ol.steps{grid-template-columns:repeat(3,minmax(0,1fr));gap:32px}
 ol.steps li{padding:68px 0 0}ol.steps li::before{top:0}
 ol.steps li::after{top:22px;bottom:auto;inset-inline-start:58px;inset-inline-end:-26px;width:auto;height:2px}
 ol.steps li:last-child::after{display:none}}
dl.words{margin:0;display:grid;grid-template-columns:1fr;gap:0 40px}
@media(min-width:700px){dl.words{grid-template-columns:1fr 1fr}}
dl.words div{display:flex;align-items:baseline;gap:8px;padding-block:12px;border-bottom:1px solid var(--line)}
dl.words dt{font-weight:800;font-size:18px}
dl.words div::after{content:"";order:1;flex:1;border-bottom:2px dotted var(--line);min-width:16px;transform:translateY(-4px)}
dl.words dd{order:2;margin:0;color:var(--muted);text-align:end}
.buy{display:grid;gap:40px}
@media(min-width:900px){.buy{grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:56px;align-items:start}}
.price{background:var(--card);border:2px solid var(--ink);border-radius:20px;padding:26px 24px;display:flex;flex-direction:column;gap:16px}
.price .lbl{font-weight:700;color:var(--muted);font-size:15px}
.price .amt{font-size:clamp(48px,8vw,64px);font-weight:800;line-height:1;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.price .later{color:var(--muted);margin-top:-8px}
ul.ticks{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}
ul.ticks li{position:relative;padding-inline-start:32px}
ul.ticks li::before{content:"";position:absolute;inset-inline-start:0;top:.22em;width:20px;height:20px;border-radius:50%;background:var(--moss) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath d='M5.5 10.5l3 3 6-7' fill='none' stroke='white' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center/20px no-repeat}
.fee{font-size:15px;color:var(--muted)}
.guar{font-weight:700;color:var(--moss);display:flex;gap:10px;align-items:flex-start}
.guar::before{content:"";flex:none;width:22px;height:22px;margin-top:2px;background:currentColor;-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2.5l8 3.2v5.8c0 4.9-3.4 9-8 10-4.6-1-8-5.1-8-10V5.7z'/%3E%3C/svg%3E") center/contain no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2.5l8 3.2v5.8c0 4.9-3.4 9-8 10-4.6-1-8-5.1-8-10V5.7z'/%3E%3C/svg%3E") center/contain no-repeat}
.trust{display:flex;flex-direction:column;gap:20px}
form{display:flex;gap:10px;flex-wrap:wrap}
input[type=email]{flex:1 1 220px;min-width:0;min-height:52px;font:inherit;padding:12px 16px;border-radius:12px;border:1.5px solid var(--field);background:var(--paper);color:var(--ink)}
::placeholder{color:var(--muted);opacity:1}
.consent{display:flex;gap:10px;align-items:flex-start;font-size:15px;color:var(--muted);flex-basis:100%}
.consent input{width:22px;height:22px;flex:none;margin-top:2px}
.formmsg{font-size:15px;flex-basis:100%}
.note{background:var(--berry-soft);color:var(--ink);padding:12px 16px;border-radius:12px}
.lake .note{background:rgba(255,255,255,.08);color:var(--lake-ink)}
.faq details{border-bottom:1px solid var(--line)}
.faq summary,details.plain summary{list-style:none;cursor:pointer;font-weight:700;padding-block:16px;min-height:52px;display:flex;justify-content:space-between;gap:16px;align-items:center}
.faq summary::after,details.plain summary::after{content:"";flex:none;width:10px;height:10px;border-inline-end:2px solid currentColor;border-bottom:2px solid currentColor;transform:translateY(-3px) rotate(45deg);transition:transform .2s}
.faq details[open] summary::after,details.plain[open] summary::after{transform:translateY(3px) rotate(225deg)}
.faq details>p{padding-bottom:16px}
/* inner pages */
.pagehead{padding-bottom:44px;display:flex;flex-direction:column;gap:14px}
.pagehead h1{font-size:clamp(30px,5.2vw,48px)}
.pagehead p{color:var(--lake-muted)}
.pagehead .big{font-size:19px;color:var(--lake-ink)}
.crumbs{font-size:15px;color:var(--lake-muted)}.crumbs a{color:inherit}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px;display:flex;flex-direction:column;gap:12px}
.card h2{font-size:22px}
details.plain{border-top:1px solid var(--line)}
details.plain summary{padding-block:10px;min-height:44px;font-size:16px}
details.plain>div{padding-bottom:10px;display:flex;flex-direction:column;gap:8px}
details.plain ol{margin:0;padding-inline-start:24px}
.ans{color:var(--moss);font-weight:700}
table{border-collapse:collapse;width:100%;font-size:16px}
th,td{text-align:start;vertical-align:top;padding:12px 10px;border-bottom:1px solid var(--line)}
thead th{font-size:14px;color:var(--muted);font-weight:700}
tbody th{color:var(--ink)}
.scroll{overflow-x:auto}
@media(max-width:640px){table.vt thead{display:none}table.vt,table.vt tbody,table.vt tr,table.vt th,table.vt td{display:block}
 table.vt tr{padding-block:14px;border-bottom:1px solid var(--line)}table.vt th,table.vt td{border:0;padding:2px 0}
 table.vt th{font-size:19px}table.vt td:nth-child(2){color:var(--muted)}}
ol.time{list-style:none;margin:0;padding:0;border-inline-start:2px solid var(--line)}
ol.time li{padding:0 0 18px;padding-inline-start:20px;position:relative}
ol.time li::before{content:"";position:absolute;inset-inline-start:-8px;top:7px;width:14px;height:14px;border-radius:50%;background:var(--paper);border:3px solid var(--lake)}
ol.time b{display:block}
.doc-guide h2{margin-top:12px}
.doc{max-width:68ch;display:flex;flex-direction:column;gap:14px;padding-top:40px}.doc h2{margin-top:12px;font-size:26px}.warn{background:var(--berry-soft);padding:12px 16px;border-radius:12px}
[dir=rtl] [lang=fi]{direction:ltr;unicode-bidi:isolate;text-align:left}
[dir=rtl] .opt [lang=fi]{text-align:start}
/* footer + sticky bar */
footer.site{margin-top:88px;padding-block:36px 104px;display:flex;flex-direction:column;gap:12px;font-size:15px;color:var(--lake-muted)}
footer.site .brand{color:var(--lake-ink);min-height:0}
footer.site nav{display:flex;gap:4px 18px;flex-wrap:wrap}footer.site nav a{display:inline-block;padding-block:10px}
.sticky{position:fixed;inset-inline:12px;bottom:max(12px,env(safe-area-inset-bottom));z-index:30;display:flex;transform:translateY(150%);transition:transform .35s cubic-bezier(.2,.8,.2,1)}
.sticky.on{transform:none}
.sticky .btn{flex:1;box-shadow:0 14px 34px -8px rgba(5,25,26,.5)}
@media(min-width:960px){.sticky{display:none}}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
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


# ---------------------------------------------------------------- guides (site_src/guides/*.json)
GUIDE_SLUG = {"en": "/guides/", "fi": "/fi/oppaat/", "ru": "/ru/gid/", "ar": "/ar/dalil/"}
GUIDE_UI = {
    "en": {"nav": "Guides", "title": "Guides: Finnish Citizenship Test 2027 | Koevalmis", "h1": "Guides for the citizenship test",
           "intro": "Practical answers about the 2027 citizenship test, checked against official sources.", "published": "Published", "more": "More guides"},
    "fi": {"nav": "Oppaat", "title": "Oppaat: kansalaisuuskoe 2027 | Koevalmis", "h1": "Oppaat kansalaisuuskokeeseen",
           "intro": "Käytännön vastauksia vuoden 2027 kansalaisuuskokeesta, tarkistettu virallisista lähteistä.", "published": "Julkaistu", "more": "Muut oppaat"},
    "ru": {"nav": "Статьи", "title": "Статьи: экзамен на гражданство Финляндии 2027 | Koevalmis", "h1": "Статьи об экзамене на гражданство",
           "intro": "Практические ответы об экзамене на гражданство 2027 года, проверенные по официальным источникам.", "published": "Опубликовано", "more": "Другие статьи"},
    "ar": {"nav": "أدلة", "title": "أدلة: اختبار الجنسية الفنلندية 2027 | Koevalmis", "h1": "أدلة لاختبار الجنسية",
           "intro": "إجابات عملية عن اختبار الجنسية لعام 2027، مُراجَعة وفق المصادر الرسمية.", "published": "نُشر في", "more": "أدلة أخرى"},
}


def load_guides():
    d = os.path.join(ROOT, "site_src", "guides")
    out = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".json"):
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                out.append(json.load(fh))
    return sorted(out, key=lambda g: (g["date"], g["id"]), reverse=True)


GUIDES = load_guides()
GUIDE_BY_ID = {g["id"]: g for g in GUIDES}


def page_path(pid, lang):
    """Path of a page in a language, or None when that language has no such page."""
    if pid.startswith("qs-"):
        return SLUGS["qs"][lang] + TOPIC_SLUG[pid[3:]] + "/"
    if pid == "guides":
        return GUIDE_SLUG.get(lang) if GUIDES else None
    if pid.startswith("guide:"):
        g = GUIDE_BY_ID[pid[6:]]
        return GUIDE_SLUG[lang] + g["slug"][lang] + "/" if lang in g["lang"] and lang in GUIDE_SLUG else None
    return SLUGS[pid][lang]


def indexable(lang):
    return lang in ST.REVIEWED


def count_meta(cfg):
    """Public endpoint for the anonymous visit counter (Supabase count_view), when analytics is on."""
    if cfg.get("analytics") and cfg.get("supabase_url") and cfg.get("supabase_anon_key"):
        return f'<meta name="kv-count" content="{e(cfg["supabase_url"])}|{e(cfg["supabase_anon_key"])}">'
    return ""


def head(lang, pid, title, desc, cfg, jsonld=None, robots=None, path=None):
    base = cfg["base_url"].rstrip("/")
    path = path or page_path(pid, lang)
    if pid:
        alts = "".join(f'<link rel="alternate" hreflang="{l}" href="{base}{page_path(pid, l)}">' for l in LANGS if indexable(l) and page_path(pid, l))
        if page_path(pid, "en"):
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
            f'<link rel="apple-touch-icon" href="/apple-touch-icon.png"><meta name="theme-color" content="#0F3B3D">'
            f'<link rel="preload" href="/fonts/atkinson-hyperlegible-next-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="stylesheet" href="/fonts/fonts.css"><style>{CSS}</style>{count_meta(cfg)}<script src="/site.js" defer></script>{ld}</head><body>')


ICON = {
    "logo": '<svg viewBox="0 0 28 28" aria-hidden="true"><circle cx="14" cy="14" r="13" fill="#F3A43B"/><path d="M8.5 14.5l3.8 3.8 7.2-8.3" fill="none" stroke="#1C1405" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.6 3.9 5.6 3.9 9s-1.3 6.4-3.9 9c-2.6-2.6-3.9-5.6-3.9-9S9.4 5.6 12 3z"/></svg>',
    "sound": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4.2 4.2 0 0 1 0 6M18 6.5a7.8 7.8 0 0 1 0 11"/></svg>',
    "tr": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 5.5h9M8 3.5v2M5.5 5.5c.8 3.4 3 5.9 6 7.3M11 5.5c-.9 4.2-3.6 7.1-7 8.6"/><path d="M13 20.5l3.8-9 3.7 9M14.3 17.5h5"/></svg>',
    "cal": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.4-7.5 9.5-4.3-1.1-7.5-4.9-7.5-9.5V6z"/></svg>',
}


def header(lang, pid, S, langs=True):
    nav = [("home", S["navHome"]), ("hub", S["navHub"]), ("qs", S["navQs"]), ("voc", S["navVoc"])]
    if page_path("guides", lang):
        nav.append(("guides", GUIDE_UI[lang]["nav"]))
    cur = "qs" if pid.startswith("qs") else "guides" if pid.startswith("guide") else pid
    links = "".join(f'<a href="{page_path(p, lang)}"{" aria-current=\"page\"" if p == cur else ""}>{e(lbl)}</a>' for p, lbl in nav)
    links += f'<a href="/app/#{lang}">{e(S["navApp"])}</a>'
    menu = ""
    if langs:
        items = "".join(f'<li><a href="{page_path(pid, l) or page_path("home", l)}" hreflang="{l}" lang="{l}"{" aria-current=\"true\"" if l == lang else ""}>{e(NAMES[l])}</a></li>' for l in LANGS)
        menu = (f'<details class="langs"><summary aria-label="{e(S["langLabel"])}: {e(NAMES[lang])}">{ICON["globe"]}'
                f'<span lang="{lang}">{e(NAMES[lang])}</span></summary><ul>{items}</ul></details>')
    return (f'<a class="skip" href="#main">{e(S["skip"])}</a><div class="wrap"><header class="site bleed lake">'
            f'<a class="brand" href="{page_path("home", lang)}">{ICON["logo"]}Koevalmis</a>'
            f'<nav class="main" aria-label="Koevalmis">{links}</nav>{menu}</header><main id="main">')


def footer(lang, S, cfg, sticky=""):
    biz = ""
    if all(cfg.get(k) for k in ("business_name", "business_id", "email")):
        biz = f'<span>{e(cfg["business_name"])}, {e(cfg["business_id"])}, <span dir="ltr">{e(cfg["email"])}</span></span>'
    note = f'<span>{e(S["reviewNote"])}</span>' if S.get("reviewNote") else ""
    return (f'</main><footer class="site bleed lake"><span class="brand">{ICON["logo"]}Koevalmis</span><span>{e(S["foot1"])}</span>{biz}{note}'
            f'<nav aria-label="{e(S["privacy"])}"><a href="/privacy/">{e(S["privacy"])}</a><a href="/terms/">{e(S["terms"])}</a></nav>'
            f'</footer></div>{sticky}')


def pagehead(crumbs, h1, extra=""):
    return f'<section class="pagehead bleed lake"><p class="crumbs">{crumbs}</p><h1>{h1}</h1>{extra}</section>'


def num(s):
    return f'<bdi dir="ltr">{s}</bdi>'


# ---------------------------------------------------------------- landing
def days_left():
    return (datetime.date(2027, 3, 1) - datetime.date.fromisoformat(TODAY)).days


def demo_card(q, lang, S, tr, label, head_tag="p"):
    """A question card the visitor can answer. Used in the hero and on practice pages."""
    TL = tr_lang(lang)
    fi, tq = q["fi"], q_text(q, TL, tr)
    fo, to = options(q, "fi", tr, S), options(q, TL, tr, S)
    opts = "".join(
        f'<li><button type="button" class="opt" data-i="{i}"><span class="k" aria-hidden="true">{"ABCD"[i]}</span>'
        f'<span><span lang="fi">{e(o)}</span><span class="otr" lang="{TL}" hidden>{e(to[i])}</span></span></button></li>'
        for i, o in enumerate(fo))
    return f"""<div class="qcard" data-q data-a="{q['a']}" id="{q['id']}">
  <div class="qhead"><span class="lbl">{label}</span><div class="tools">
    <button type="button" class="tool" data-say hidden>{ICON['sound']}{e(S['listen'])}</button>
    <button type="button" class="tool" data-tr aria-pressed="false">{ICON['tr']}{e(S['showTr'])}</button></div></div>
  <{head_tag} class="qtext"><span lang="fi">{e(fi['q'])}</span><span class="qtr" lang="{TL}" hidden>{e(tq['q'])}</span></{head_tag}>
  <ol class="opts">{opts}</ol>
  <div class="res" hidden><p lang="fi">{e(fi['e'])}</p><p class="muted" lang="{TL}">{e(tq['e'])}</p>{{after}}</div>
  <span class="stamp" lang="fi" aria-hidden="true"></span>
</div>"""


def landing(lang, S, cfg, tr, qs, gl):
    now, later = PRICE.get(lang, ("9,90 €", "14,90 €"))
    base = cfg["base_url"].rstrip("/")
    TL = tr_lang(lang)
    biz_ready = all(cfg.get(k) for k in ("business_name", "business_id", "email"))
    provider = cfg.get("waitlist_provider", "supabase")
    wl_ready = biz_ready and (provider == "netlify" or bool(cfg.get("waitlist_url") and cfg.get("waitlist_anon_key")))
    msgs = {k: S[k] for k in ("wlBad", "wlOk", "wlErr", "wlConsent")}
    if wl_ready:
        if provider == "netlify":
            wl = json.dumps({"provider": "netlify", "lang": lang, "msg": msgs}, ensure_ascii=False)
            attrs = 'name="waitlist" method="POST" data-netlify="true" netlify-honeypot="website"'
        else:
            wl = json.dumps({"provider": "supabase", "url": cfg["waitlist_url"], "key": cfg["waitlist_anon_key"], "lang": lang, "msg": msgs}, ensure_ascii=False)
            attrs = 'name="waitlist"'
        form = f"""<form id="wl" {attrs} novalidate>
      <input type="hidden" name="form-name" value="waitlist"><input type="hidden" name="lang" value="{lang}">
      <label for="email" class="muted" style="flex-basis:100%">{e(S['wlLabel'])}</label>
      <input id="email" name="email" type="email" autocomplete="email" placeholder="you@example.com" required aria-describedby="wlmsg">
      <button class="btn primary" type="submit">{e(S['wlBtn'])}</button>
      <label class="consent"><input id="consent" name="consent" type="checkbox" value="yes" required> <span>{e(S['consent'])} <a href="/privacy/">{e(S['privacy'])}</a></span></label>
      <span id="wlmsg" class="formmsg" role="status"></span>
      <input type="text" name="website" id="hp" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;inset-inline-start:-9999px">
    </form><script type="application/json" id="wl-config">{wl}</script>"""
    else:
        form = f'<p class="note">{e(S["wlClosed"])}</p>'
    by_id = {q["id"]: q for q in qs}
    after = (f'<p class="msg" data-ok="{e(S["afterOk"])}" data-no="{e(S["afterNo"])}"></p>'
             f'<div class="cta"><a class="btn primary" href="/app/#diag-{lang}">{e(S["cta1"])}</a></div>')
    card = demo_card(by_id[SS.DEMO_QID], lang, S, tr, e(S["tryLabel"])).replace("{after}", after)
    topics = "".join(f'<a href="{page_path("qs-" + tp, lang)}">{e(topic_name(lang, tp, tr))}</a>' for tp in TOPIC_ORDER)
    steps = "".join(f"<li><h3>{e(h)}</h3><p>{e(t)}</p></li>" for h, t in S["steps"])
    gl_by = {g["fi"]: g for g in gl}
    def tword(g):
        return g["en"] if TL == "en" else tr[TL]["glossary"].get(g["fi"], g["en"])
    words = "".join(f'<div><dt lang="fi">{e(w)}</dt><dd lang="{TL}">{e(tword(gl_by[w]))}</dd></div>' for w in SS.VOC_TEASER)
    trust = [t.replace("{date}", ST.CHECKED_FI) for t in S["trust"]]
    if cfg.get("reviewed_by_educator"):
        trust.insert(1, S["reviewed"])
    guarantee = ""
    if cfg.get("refund_days"):
        guarantee = f'<p class="guar">{e(S["refund"].replace("{n}", str(cfg["refund_days"])))}</p>'
        S = dict(S, faq=[list(x) for x in S["faq"]])
        S["faq"][4][1] = S["faqRefund"]
    count = e(S["count"]).replace("{n}", f'<b data-days>{days_left()}</b>')
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in S["faq"])
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
<section class="hero bleed lake">
  <div class="intro">
    <p class="tag">{ICON['shield']}{e(S['tag'])}</p>
    <h1>{e(S['heroH1'])}</h1>
    <p class="lead">{e(S['heroLead'])}</p>
    <div class="cta"><a class="btn primary" href="/app/#diag-{lang}">{e(S['cta1'])}</a><a class="more" href="#price">{e(S['ctaPrice'])}</a></div>
    <p class="count">{ICON['cal']}<span>{count}</span></p>
    <p class="proof">{e(S['proof'])}</p>
  </div>
  {card}
</section>
<section aria-labelledby="facts"><div class="sec wide"><h2 id="facts">{e(S['factsH'])}</h2>
  <div class="facts">
    <div class="fact"><b>{num('1.3.2027')}</b><span>{e(S['f1'])}</span></div>
    <div class="fact"><b>{num('18–64')}</b><span>{e(S['f2'])}</span></div>
    <div class="fact"><b>{num('FI / SV')}</b><span>{e(S['f3'])}</span></div>
    <div class="fact"><b>{e(S['f4n'])}</b><span>{e(S['f4'])}</span></div>
  </div>
  <p>{e(S['topicsIntro'])}</p>
  <div class="chips">{topics}</div>
  <p class="muted">{e(S['unknown'])} <a href="{SRC['migri']}">{e(S['src1'])}</a>, <a href="{SRC['stt']}">{e(S['src2'])}</a>. <a href="{page_path('hub', lang)}">{e(S['navHub'])}</a></p>
</div></section>
<section aria-labelledby="steps"><div class="sec wide"><h2 id="steps">{e(S['stepsH'])}</h2>
  <ol class="steps">{steps}</ol>
  <div class="cta"><a class="btn dark" href="/app/#diag-{lang}">{e(S['cta1'])}</a></div>
</div></section>
<section aria-labelledby="words"><div class="sec"><h2 id="words">{e(S['vocTeaserH'])}</h2><p>{e(S['vocTeaserP'])}</p>
  <dl class="words">{words}</dl>
  <p><a href="{page_path('voc', lang)}">{e(S['vocTeaserLink'])}</a></p>
</div></section>
<section id="price" aria-labelledby="pricing"><div class="buy">
  <div class="sec"><h2 id="pricing">{e(S['priceH'])}</h2>
    <div class="price"><span class="lbl">{e(S['priceNow'])}</span><span class="amt">{num(now)}</span><span class="later">{e(S['priceLaterShort'])}</span>
      <p>{e(S['priceNote'])}</p>
      <ul class="ticks">{''.join(f'<li>{e(x)}</li>' for x in S['li'])}</ul>
      {guarantee}
      {form}
    </div>
    <p class="fee">{e(S['feeNote'])} <a href="{SRC['havm']}">HaVM 10/2026</a></p>
  </div>
  <div class="trust"><h2>{e(S['trustH'])}</h2><ul class="ticks">{''.join(f'<li>{e(t)}</li>' for t in trust)}</ul></div>
</div></section>
<section class="faq" aria-labelledby="faq"><div class="sec"><h2 id="faq">{e(S['faqH'])}</h2><div>{faq}</div></div></section>"""
    sticky = f'<div class="sticky" inert><a class="btn primary" href="/app/#diag-{lang}">{e(S["cta1"])}</a></div>'
    return head(lang, "home", S["title"], S["desc"], cfg, jsonld) + header(lang, "home", S) + body + footer(lang, S, cfg, sticky) + "</body></html>"


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
    crumbs = f'<a href="{page_path("home", lang)}">{e(S["navHome"])}</a> › {e(S["navHub"])}'
    body = pagehead(crumbs, e(S['hubH1']), f'<p>{e(S["updated"])} <time datetime="{TODAY}">{num(ST.CHECKED_FI)}</time></p><p class="big">{e(S["hubAnswer"])}</p>'
                    f'<div class="cta"><a class="btn primary" href="/app/#diag-{lang}">{e(S["cta1"])}</a></div>') + f"""
<section><div class="sec wide"><h2>{e(S['factsH'])}</h2>
  <div class="scroll"><table><thead><tr>{''.join(f'<th scope="col">{e(h)}</th>' for h in S['factsTH'])}</tr></thead><tbody>{rows}</tbody></table></div>
</div></section>
<section><div class="sec"><h2>{e(S['notYetH'])} ({e(S['checkedLabel'])} {num(ST.CHECKED_FI)})</h2>
  <ul>{''.join(f'<li>{e(x)}</li>' for x in S['notYet'])}</ul>
  <h3>{e(S['reportedH'])}</h3><ul>{rep}</ul>
</div></section>
<section><div class="sec"><h2>{e(S['timelineH'])}</h2><ol class="time">{tl}</ol></div></section>
<section><div class="sec"><h2>{e(S['topicsH'])}</h2><div class="chips">{topics}</div>
  <div class="cta"><a class="btn dark" href="/app/#diag-{lang}">{e(S['cta1'])}</a></div></div></section>
<section class="faq"><div class="sec"><h2>{e(S['faqH'])}</h2><div>{faq}</div></div></section>
<section><div class="sec"><h2>{e(S['sourcesH'])}</h2><ul>{srcs}</ul><p class="muted">{e(S['notAdvice'])}</p></div></section>"""
    return head(lang, "hub", S["hubTitle"], S["hubDesc"], cfg, jsonld) + header(lang, "hub", S) + body + footer(lang, S, cfg) + "</body></html>"


def breadcrumbs(base, lang, S, trail):
    items = [{"@type": "ListItem", "position": 1, "name": S["navHome"], "item": f"{base}{page_path('home', lang)}"}]
    for i, (pid, name) in enumerate(trail, start=2):
        items.append({"@type": "ListItem", "position": i, "name": name, "item": f"{base}{page_path(pid, lang)}"})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


# ---------------------------------------------------------------- practice questions
from build import public_questions  # noqa: E402  (one definition of the free set for site and app)


def question_card(q, lang, tr, S, n):
    TL = tr_lang(lang)
    fo = options(q, "fi", tr, S)
    tq = q_text(q, TL, tr)
    ans = (f'<details class="plain ans-d"><summary>{e(S["ansLabel"])}</summary><div>'
           f'<p class="ans">{e(S["correct"])}: {num("ABCD"[q["a"]])}, <span lang="fi">{e(fo[q["a"]])}</span></p>'
           f'<p lang="fi">{e(q["fi"]["e"])}</p><p class="muted" lang="{TL}">{e(tq["e"])}</p></div></details>')
    card = demo_card(q, lang, S, tr, f'{num(n)} / {num(PUBLIC_PER_TOPIC)}', head_tag="h2")
    card = re.sub(r'<div class="res" hidden>.*?\{after\}</div>', ans, card, flags=re.S)
    return card


def qs_index(lang, S, cfg, tr, qs):
    base = cfg["base_url"].rstrip("/")
    blocks = []
    for tp in TOPIC_ORDER:
        sample = public_questions(qs, tp)[0]
        name = topic_name(lang, tp, tr)
        total = len([q for q in qs if q["t"] == tp])
        blocks.append(f'<div class="card"><h2><a href="{page_path("qs-" + tp, lang)}">{e(name)}</a></h2>'
                      f'<p lang="fi">{e(sample["fi"]["q"])}</p><p class="muted">{e(S["qCount"].format(n=total))}</p></div>')
    jsonld = [breadcrumbs(base, lang, S, [("qs", S["navQs"])])]
    crumbs = f'<a href="{page_path("home", lang)}">{e(S["navHome"])}</a> › {e(S["navQs"])}'
    body = pagehead(crumbs, e(S['qsH1']), f'<p class="big">{e(S["qsIntro"])}</p><p class="note">{e(S["qsDisc"])}</p>'
                    f'<div class="cta"><a class="btn primary" href="/app/#diag-{lang}">{e(S["cta1"])}</a></div>') + f"""
<section><div class="sec">{''.join(blocks)}</div></section>"""
    return head(lang, "qs", S["qsTitle"], S["qsDesc"], cfg, jsonld) + header(lang, "qs", S) + body + footer(lang, S, cfg) + "</body></html>"


def qs_topic(lang, S, cfg, tr, qs, tp):
    base = cfg["base_url"].rstrip("/")
    name = topic_name(lang, tp, tr)
    total = len([q for q in qs if q["t"] == tp])
    cards = "".join(question_card(q, lang, tr, S, i + 1) for i, q in enumerate(public_questions(qs, tp)))
    others = "".join(f'<a href="{page_path("qs-" + o, lang)}">{e(topic_name(lang, o, tr))}</a>' for o in TOPIC_ORDER if o != tp)
    pid = "qs-" + tp
    jsonld = [breadcrumbs(base, lang, S, [("qs", S["navQs"]), (pid, name)])]
    crumbs = (f'<a href="{page_path("home", lang)}">{e(S["navHome"])}</a> › <a href="{page_path("qs", lang)}">{e(S["navQs"])}</a> › {e(name)}')
    body = pagehead(crumbs, e(S['topicH1'].format(topic=name)),
                    f'<p>{e(S["updated"])} <time datetime="{TODAY}">{num(ST.CHECKED_FI)}</time></p><p class="note">{e(S["qsDisc"])}</p>') + f"""
<section><div class="sec qlist">{cards}
  <div class="cta"><a class="btn primary" href="/app/#{lang}">{e(S['ctaApp'].format(n=len(qs)))}</a></div></div></section>
<section><div class="sec"><h2>{e(S['otherTopics'])}</h2><div class="chips">{others}</div></div></section>"""
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
    crumbs = f'<a href="{page_path("home", lang)}">{e(S["navHome"])}</a> › {e(S["navVoc"])}'
    body = pagehead(crumbs, e(S['vocH1']), f'<p class="big">{e(S["vocIntro"])}</p>'
                    f'<div class="cta"><a class="btn primary" href="/app/#gloss-{lang}">{e(S["navApp"])}</a></div>') + f"""
<section><div class="sec wide">
  <div class="scroll"><table class="vt"><thead><tr><th scope="col">{e(S['colFi'])}</th><th scope="col">{e(S['colTr'])}</th><th scope="col">{e(S['colDef'])}</th></tr></thead><tbody>{rows}</tbody></table></div>
</div></section>"""
    return head(lang, "voc", S["vocTitle"], S["vocDesc"], cfg, jsonld) + header(lang, "voc", S) + body + footer(lang, S, cfg) + "</body></html>"


# ---------------------------------------------------------------- guide pages
def guide_blocks(blocks):
    out = []
    for kind, val in blocks:
        if kind == "h2":
            out.append(f"<h2>{e(val)}</h2>")
        elif kind == "p":
            out.append(f"<p>{e(val)}</p>")
        elif kind == "ul":
            out.append('<ul class="ticks">' + "".join(f"<li>{e(x)}</li>" for x in val) + "</ul>")
        elif kind == "note":
            out.append(f'<p class="note">{e(val)}</p>')
    return "\n".join(out)


def guide_page(g, lang, S, cfg):
    base = cfg["base_url"].rstrip("/")
    G, U = g["lang"][lang], GUIDE_UI[lang]
    pid = "guide:" + g["id"]
    day = ".".join(str(int(x)) for x in reversed(g["date"].split("-")))
    srcs = "".join(f'<li><a href="{SRC[k]}">{e(SRC_LABEL[k])}</a></li>' for k in g["sources"])
    others = "".join(f'<li><a href="{page_path("guide:" + o["id"], lang)}">{e(o["lang"][lang]["h1"])}</a></li>'
                     for o in GUIDES if o["id"] != g["id"] and lang in o["lang"])
    more = f'<h2>{e(U["more"])}</h2><ul>{others}</ul>' if others else ""
    crumbs = f'<a href="{page_path("home", lang)}">{e(S["navHome"])}</a> › <a href="{page_path("guides", lang)}">{e(U["nav"])}</a>'
    jsonld = [{"@context": "https://schema.org", "@type": "Article", "headline": G["h1"], "description": G["desc"], "inLanguage": lang,
               "datePublished": g["date"], "dateModified": g.get("updated", g["date"]),
               "author": {"@type": "Organization", "name": "Koevalmis", "url": f"{base}/"},
               "publisher": {"@type": "Organization", "name": "Koevalmis", "logo": {"@type": "ImageObject", "url": f"{base}/logo.png"}},
               "mainEntityOfPage": f"{base}{page_path(pid, lang)}", "image": f"{base}/og.png", "citation": [SRC[k] for k in g["sources"]]},
              breadcrumbs(base, lang, S, [("guides", U["nav"]), (pid, G["h1"])])]
    body = pagehead(crumbs, e(G["h1"]), f'<p>{e(U["published"])} <time datetime="{g["date"]}">{num(day)}</time></p><p class="big">{e(G["lead"])}</p>') + f"""
<section><div class="sec doc-guide">{guide_blocks(G["blocks"])}
  <div class="cta"><a class="btn primary" href="/app/#diag-{lang}">{e(S['cta1'])}</a></div>
  <h2>{e(S['sourcesH'])}</h2><ul>{srcs}</ul>
  {more}
</div></section>"""
    return head(lang, pid, G["title"], G["desc"], cfg, jsonld) + header(lang, pid, S) + body + footer(lang, S, cfg) + "</body></html>"


def guides_index(lang, S, cfg):
    base = cfg["base_url"].rstrip("/")
    U = GUIDE_UI[lang]
    cards = "".join(f'<div class="card"><h2><a href="{page_path("guide:" + g["id"], lang)}">{e(g["lang"][lang]["h1"])}</a></h2>'
                    f'<p class="muted">{e(g["lang"][lang]["desc"])}</p></div>' for g in GUIDES if lang in g["lang"])
    crumbs = f'<a href="{page_path("home", lang)}">{e(S["navHome"])}</a> › {e(U["nav"])}'
    body = pagehead(crumbs, e(U["h1"]), f'<p class="big">{e(U["intro"])}</p>') + f'<section><div class="sec">{cards}</div></section>'
    jsonld = [breadcrumbs(base, lang, S, [("guides", U["nav"])])]
    return head(lang, "guides", U["title"], U["intro"], cfg, jsonld) + header(lang, "guides", S) + body + footer(lang, S, cfg) + "</body></html>"


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
            + header("fi", "home", S, langs=False)
            + f'<div class="doc">{warn}{body}</div>' + footer("fi", S, cfg) + "</body></html>")


def page_404(cfg, ALL):
    links = "".join(f'<li><a href="{page_path("home", l)}" lang="{l}">{e(NAMES[l])}</a> · <a href="{page_path("qs", l)}" lang="{l}">{e(ALL[l]["navQs"])}</a></li>' for l in LANGS)
    return (head("en", None, "Page not found | Koevalmis", "Page not found", cfg, robots="noindex", path="/404.html")
            + header("en", "home", ALL["en"]) + pagehead("Koevalmis", "Page not found. Sivua ei löytynyt.") + f'<section><div class="sec"><ul>{links}</ul></div></section>'
            + footer("en", ALL["en"], cfg) + "</body></html>")


# ---------------------------------------------------------------- assets
def make_images(out):
    """Share image (1200x630) and icons in the site's colours, drawn with the site font when Pillow can read it."""
    from PIL import Image, ImageDraw, ImageFont
    woff = os.path.join(ROOT, "site_src", "fonts", "atkinson-hyperlegible-next-latin-wght-normal.woff2")
    dejavu = {800: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 400: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"}

    def font(size, weight=400):
        try:
            f = ImageFont.truetype(woff, size)
            f.set_variation_by_axes([weight])
            return f
        except Exception:  # Pillow without WOFF2 support: DejaVu, then Pillow's bundled font
            path = dejavu[800 if weight >= 600 else 400]
            return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default(size=size)

    lake, paper, ink, muted, berry, moss, line = (15, 59, 61), (244, 246, 243), (16, 32, 31), (169, 196, 192), (243, 164, 59), (31, 107, 69), (212, 220, 217)
    S = 2  # draw at 2x, then downsample for smooth edges
    img = Image.new("RGB", (1200 * S, 630 * S), lake)
    d = ImageDraw.Draw(img)

    def logo(x, y, r):
        d.ellipse((x, y, x + 2 * r, y + 2 * r), fill=berry)
        k = r / 14
        d.line([(x + 8.5 * k, y + 14.5 * k), (x + 12.3 * k, y + 18.3 * k), (x + 19.5 * k, y + 10 * k)], fill=(28, 20, 5), width=int(2.8 * k), joint="curve")

    logo(80 * S, 70 * S, 22 * S)
    d.text((136 * S, 72 * S), "Koevalmis", font=font(40 * S, 800), fill=paper)
    d.text((80 * S, 178 * S), "Be ready for the", font=font(58 * S, 800), fill=paper)
    d.text((80 * S, 244 * S), "Finnish citizenship", font=font(58 * S, 800), fill=paper)
    d.text((80 * S, 310 * S), "test 2027", font=font(58 * S, 800), fill=paper)
    d.text((80 * S, 420 * S), "Practice questions in Finnish", font=font(30 * S), fill=muted)
    d.text((80 * S, 462 * S), "with translations in 6 languages", font=font(30 * S), fill=muted)
    d.text((80 * S, 540 * S), "EN  FI  RU  AR  FA  SO", font=font(26 * S, 700), fill=berry)
    # question card with the answer stamped
    cx, cy, cw, ch = 700 * S, 190 * S, 420 * S, 330 * S
    d.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=24 * S, fill=(255, 255, 255))
    d.text((cx + 28 * S, cy + 30 * S), "Mitä jokamiehenoikeus", font=font(28 * S, 800), fill=ink)
    d.text((cx + 28 * S, cy + 66 * S), "sallii?", font=font(28 * S, 800), fill=ink)
    rows = [("A", "Puiden kaatamisen", False), ("B", "Metsästämisen ilman lupaa", False), ("C", "Marjojen poimimisen", True)]
    for i, (k, t, ok) in enumerate(rows):
        y = cy + (122 + i * 64) * S
        d.rounded_rectangle((cx + 24 * S, y, cx + cw - 24 * S, y + 52 * S), radius=12 * S,
                            fill=(221, 239, 228) if ok else (255, 255, 255), outline=moss if ok else line, width=3 * S if ok else 2 * S)
        d.ellipse((cx + 38 * S, y + 12 * S, cx + 66 * S, y + 40 * S), fill=moss if ok else None, outline=moss if ok else (122, 139, 136), width=2 * S)
        d.text((cx + 52 * S, y + 26 * S), k, font=font(15 * S, 700), fill=(255, 255, 255) if ok else ink, anchor="mm")
        d.text((cx + 80 * S, y + 13 * S), t, font=font(21 * S), fill=ink)
    # rubber stamp
    st = Image.new("RGBA", (250 * S, 90 * S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((6 * S, 6 * S, 244 * S, 84 * S), radius=12 * S, outline=moss + (255,), width=5 * S, fill=(255, 255, 255, 255))
    sd.rounded_rectangle((14 * S, 14 * S, 236 * S, 76 * S), radius=8 * S, outline=moss + (255,), width=2 * S)
    sd.text((125 * S, 45 * S), "OIKEIN!", font=font(40 * S, 800), fill=moss + (255,), anchor="mm")
    st = st.rotate(8, resample=Image.BICUBIC, expand=True)
    img.paste(st, (cx + cw - 236 * S, cy - 92 * S), st)
    img.resize((1200, 630), Image.LANCZOS).save(os.path.join(out, "og.png"), optimize=True)

    for size, name in ((180, "apple-touch-icon.png"), (512, "logo.png"), (192, "icon-192.png")):
        ic = Image.new("RGB", (size * S, size * S), lake)
        d = ImageDraw.Draw(ic)
        r = size * S * 0.36
        logo(size * S / 2 - r, size * S / 2 - r, r)
        ic.resize((size, size), Image.LANCZOS).save(os.path.join(out, name), optimize=True)
    ico = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(ico)
    logo(4, 4, 60)
    ico.resize((64, 64), Image.LANCZOS).save(os.path.join(out, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    with open(os.path.join(out, "favicon.svg"), "w") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28"><circle cx="14" cy="14" r="13" fill="#F3A43B"/>'
                 '<path d="M8.5 14.5l3.8 3.8 7.2-8.3" fill="none" stroke="#1C1405" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')


# Netlify response headers (GitHub Pages ignores this file)
HEADERS = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
/fonts/*
  Cache-Control: public, max-age=31536000, immutable
"""


# Set by the deploy workflow when the site is served from a sub-path such as
# https://samppa3000.github.io/kayttaja-koevalmis/ instead of its own domain.
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
# NOINDEX=1 keeps a temporary address (github.io, netlify.app) out of search engines until koevalmis.fi is live.
NOINDEX = bool(BASE_PATH) or os.environ.get("NOINDEX") == "1"


def apply_base_path(out):
    """Prefix root-relative links for a sub-path preview (if any) and keep the preview out of search engines."""
    attr = re.compile(r'(\b(?:href|src|action)=")/(?!/)')
    for d, _, fs in os.walk(out):
        for f in fs:
            if not f.endswith((".html", ".css")):
                continue
            p = os.path.join(d, f)
            with open(p, encoding="utf-8") as fh:
                t = fh.read()
            if BASE_PATH:
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
    for pid in ["guides"] + ["guide:" + g["id"] for g in GUIDES]:
        have = [l for l in langs if page_path(pid, l)]
        for l in have:
            mod = GUIDE_BY_ID[pid[6:]]["date"] if pid.startswith("guide:") else TODAY
            out.append(f"  <url><loc>{base}{page_path(pid, l)}</loc><lastmod>{mod}</lastmod>")
            for a in have:
                out.append(f'    <xhtml:link rel="alternate" hreflang="{a}" href="{base}{page_path(pid, a)}"/>')
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

## Guides
""" + "\n".join(f"- {g['lang']['en']['h1']}: {base}{page_path('guide:' + g['id'], 'en')}" for g in GUIDES if 'en' in g['lang']) + f"""

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
        write(page_path("home", lang), landing(lang, S, cfg, tr, qs, gl))
        write(page_path("hub", lang), hub(lang, S, cfg, tr))
        write(page_path("qs", lang), qs_index(lang, S, cfg, tr, qs))
        for tp in TOPIC_ORDER:
            write(page_path("qs-" + tp, lang), qs_topic(lang, S, cfg, tr, qs, tp))
        write(page_path("voc", lang), vocab(lang, S, cfg, tr, gl))
        if page_path("guides", lang):
            write(page_path("guides", lang), guides_index(lang, S, cfg))
            for g in GUIDES:
                if page_path("guide:" + g["id"], lang):
                    write(page_path("guide:" + g["id"], lang), guide_page(g, lang, S, cfg))
    write("/app/", app_page(cfg))
    write("/privacy/", legal_page("privacy", cfg, ALL["fi"]))
    write("/terms/", legal_page("terms", cfg, ALL["fi"]))
    write("/404.html", page_404(cfg, ALL))
    write("/sitemap.xml", sitemap(cfg))
    write("/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {cfg['base_url'].rstrip('/')}/sitemap.xml\n")
    write("/llms.txt", llms_txt(cfg, ALL))
    write("/_headers", HEADERS)
    if not NOINDEX:
        write("/CNAME", cfg["base_url"].split("//")[1].strip("/") + "\n")
    write("/.nojekyll", "")
    shutil.copytree(os.path.join(ROOT, "site_src", "fonts"), os.path.join(OUT, "fonts"))
    shutil.copy(os.path.join(ROOT, "site_src", "fonts.css"), os.path.join(OUT, "fonts", "fonts.css"))
    shutil.copy(os.path.join(ROOT, "site_src", "site.js"), os.path.join(OUT, "site.js"))
    make_images(OUT)
    if NOINDEX:
        apply_base_path(OUT)
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    missing = [k for k in ("business_name", "business_id", "email", "waitlist_url", "waitlist_anon_key") if not cfg.get(k)]
    print(f"site built: {n} files")
    if missing:
        print("not yet configured:", missing)


if __name__ == "__main__":
    main()
