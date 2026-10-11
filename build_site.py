"""Build the deployable Koevalmis website into site/ (GitHub Pages ready).

Reads site_src/config.json for business details and the waiting-list endpoint.
Empty values are allowed: pages then show placeholders and the waiting list
shows "opens soon" without saving anything.
"""
import json, os, re, shutil, subprocess, sys, html as H

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")
LANGS = ["en", "fi", "ru", "ar"]
RTL = {"ar"}
PRICE = {"en": ("€9.90", "€14.90")}
PRICE_DEFAULT = ("9,90 €", "14,90 €")
MIGRI = "https://migri.fi/en/-/finland-to-introduce-citizenship-test-as-changes-to-citizenship-act-take-effect-on-1-january-2027"
STT = "https://www.sttinfo.fi/tiedote/72399040/suomi-valmistautuu-ottamaan-kayttoon-kansalaisuuskokeen-oppimateriaalit-julkaistaan-vuodenvaihteessa"
EXAMPLE_FI = "Kenelle voi tehdä kantelun, jos epäilee viranomaisen toimineen lainvastaisesti?"
NAMES = {"en": "English", "fi": "Suomi", "ru": "Русский", "ar": "العربية"}

CSS = """
:root{--bg:#F2F4F1;--surface:#FFFFFF;--ink:#16201B;--muted:#56635C;--line:#D3DAD5;--accent:#D9851E;--accent-ink:#1A1206;--accent-soft:#F6E3C6;--ok:#2C7A4C;
--display:"Familjen Grotesk","Helvetica Neue",Arial,sans-serif;--body:"Atkinson Hyperlegible","Segoe UI",Roboto,Arial,sans-serif;--r:10px}
@media (prefers-color-scheme: dark){:root{--bg:#111613;--surface:#1A211D;--ink:#E7EDE9;--muted:#9BA8A1;--line:#2D3832;--accent:#E8A04A;--accent-soft:#3A2B17;--ok:#62C38D;color-scheme:dark}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.6;padding-inline:16px;padding-block:0 56px}
.wrap{max-width:760px;margin:0 auto;display:flex;flex-direction:column;gap:56px}
header{display:flex;justify-content:space-between;align-items:center;padding-block:18px 0;gap:12px;flex-wrap:wrap}
.brand{font-family:var(--display);font-weight:700;font-size:22px;display:flex;gap:10px;align-items:center;color:var(--ink);text-decoration:none}
.brand .dot{width:14px;height:14px;border-radius:50%;background:var(--accent)}
nav.langs{display:flex;gap:10px;flex-wrap:wrap;font-size:14px}
nav.langs a{color:var(--muted)}nav.langs a[aria-current]{color:var(--ink);font-weight:700;text-decoration:none}
.tag{font-size:13px;color:var(--muted)}
h1,h2,h3{font-family:var(--display);letter-spacing:-.015em;text-wrap:balance;margin:0}
h1{font-size:clamp(32px,7vw,52px);line-height:1.08}h2{font-size:clamp(24px,4.5vw,30px);line-height:1.15}h3{font-size:19px}
p{margin:0;max-width:62ch}.muted{color:var(--muted)}
.hero,.sec{display:flex;flex-direction:column;gap:16px}
.pair{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:18px 20px;display:flex;flex-direction:column;gap:6px}
.pair .fi{font-weight:700;font-size:20px}.pair .tr{color:var(--muted)}
.lab{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700}
.cta{display:flex;gap:12px;flex-wrap:wrap}
.btn{font:inherit;font-weight:700;border-radius:var(--r);padding:13px 22px;border:1.5px solid var(--ink);background:var(--ink);color:var(--bg);text-decoration:none;cursor:pointer;display:inline-block}
.btn.acc{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.btn:focus-visible,input:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.fact{background:var(--surface);padding:16px;display:flex;flex-direction:column;gap:4px;min-width:0}
.fact b{font-family:var(--display);font-size:22px;font-variant-numeric:tabular-nums}.fact span{font-size:15px;color:var(--muted)}
.feat{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:20px}.feat div{display:flex;flex-direction:column;gap:6px;min-width:0}
.price{background:var(--surface);border:2px solid var(--accent);border-radius:var(--r);padding:22px;display:flex;flex-direction:column;gap:12px}
.price .amt{font-family:var(--display);font-size:44px;font-weight:700;line-height:1}.price .amt s{font-size:22px;color:var(--muted);font-weight:500;margin-inline-start:8px}
.price ul{margin:0;padding-inline-start:20px;display:flex;flex-direction:column;gap:4px}
form{display:flex;gap:10px;flex-wrap:wrap}
input[type=email]{flex:1 1 220px;min-width:0;font:inherit;padding:12px 14px;border-radius:var(--r);border:1.5px solid var(--line);background:var(--bg);color:var(--ink)}
.consent{display:flex;gap:8px;align-items:flex-start;font-size:14px;color:var(--muted);flex-basis:100%}
.formmsg{font-size:15px;flex-basis:100%}
details{border-bottom:1px solid var(--line);padding-block:12px}summary{cursor:pointer;font-weight:700}details p{margin-top:8px}
.topics{display:flex;flex-wrap:wrap;gap:8px}.topics span{border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:15px;background:var(--surface)}
footer{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:16px;display:flex;flex-direction:column;gap:8px}
a{color:inherit}[dir=rtl] [lang=fi]{direction:ltr;unicode-bidi:isolate;text-align:left}
.doc{max-width:68ch;display:flex;flex-direction:column;gap:14px}.doc h2{margin-top:12px}.warn{background:var(--accent-soft);padding:10px 14px;border-radius:var(--r)}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@500;600;700&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&display=swap">')


def e(s):
    return H.escape(str(s), quote=True)


def path_for(lang):
    return "/" if lang == "en" else f"/{lang}/"


def head(lang, title, desc, canonical_path, cfg, alternates=True, css=True):
    base = cfg["base_url"].rstrip("/")
    alt = ""
    if alternates:
        alt = "".join(f'<link rel="alternate" hreflang="{l}" href="{base}{path_for(l)}">' for l in LANGS)
        alt += f'<link rel="alternate" hreflang="x-default" href="{base}/">'
    return (f'<!doctype html><html lang="{lang}" dir="{"rtl" if lang in RTL else "ltr"}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>'
            f'<meta name="description" content="{e(desc)}"><link rel="canonical" href="{base}{canonical_path}">{alt}'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:type" content="website"><meta property="og:url" content="{base}{canonical_path}">'
            f'<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3E%3Ccircle cx=%278%27 cy=%278%27 r=%277%27 fill=%27%23D9851E%27/%3E%3C/svg%3E">'
            + (f'{FONTS}<style>{CSS}</style>' if css else '') + '</head><body>')


def landing(lang, S, cfg):
    now, full = PRICE.get(lang, PRICE_DEFAULT)
    langs_nav = "".join(f'<a href="{path_for(l)}" hreflang="{l}" lang="{l}"{" aria-current=\"page\"" if l == lang else ""}>{NAMES[l]}</a>' for l in LANGS)
    tr = S["exTr"]
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in S["faq"])
    wl = json.dumps({"url": cfg.get("waitlist_url", ""), "key": cfg.get("waitlist_anon_key", ""), "lang": lang,
                     "msg": {k: S[k] for k in ("wlBad", "wlOk", "wlSoon", "wlErr")}}, ensure_ascii=False)
    return head(lang, S["title"], S["desc"], path_for(lang), cfg) + f"""
<div class="wrap">
<header><a class="brand" href="{path_for(lang)}"><span class="dot" aria-hidden="true"></span>Koevalmis</a>
<nav class="langs" aria-label="{e(S['langLabel'])}">{langs_nav}</nav></header>
<section class="hero">
  <span class="tag">{e(S['tag'])}</span>
  <h1>{e(S['h1'])}</h1>
  <p class="muted">{e(S['lead'])}</p>
  <div class="pair"><span class="lab">{e(S['exLabel'])}</span><span class="fi" lang="fi">{e(EXAMPLE_FI)}</span>{f'<span class="tr">{e(tr)}</span>' if tr else ''}</div>
  <div class="cta"><a class="btn acc" href="/app/#diag-{lang}">{e(S['cta1'])}</a><a class="btn" href="#price">{e(S['cta2'])}</a></div>
</section>
<section class="sec"><h2>{e(S['factsH'])}</h2>
  <div class="facts">
    <div class="fact"><b>1.3.2027</b><span>{e(S['f1'])}</span></div>
    <div class="fact"><b>18–64</b><span>{e(S['f2'])}</span></div>
    <div class="fact"><b>FI / SV</b><span>{e(S['f3'])}</span></div>
    <div class="fact"><b>{e(S['f4n'])}</b><span>{e(S['f4'])}</span></div>
  </div>
  <p>{e(S['topicsIntro'])}</p>
  <div class="topics">{''.join(f'<span>{e(t)}</span>' for t in S['topics'])}</div>
  <p class="muted">{e(S['unknown'])} <a href="{MIGRI}">{e(S['src1'])}</a>, <a href="{STT}">{e(S['src2'])}</a>.</p>
</section>
<section class="sec"><h2>{e(S['howH'])}</h2>
  <div class="feat"><div><h3>{e(S['h3a'])}</h3><p>{e(S['pa'])}</p></div><div><h3>{e(S['h3b'])}</h3><p>{e(S['pb'])}</p></div><div><h3>{e(S['h3c'])}</h3><p>{e(S['pc'])}</p></div></div>
</section>
<section class="sec" id="price"><h2>{e(S['priceH'])}</h2>
  <div class="price"><div class="amt"><bdi dir="ltr">{now}</bdi> <s><bdi dir="ltr">{full}</bdi></s></div><p>{e(S['priceNote'])}</p>
    <ul>{''.join(f'<li>{e(x)}</li>' for x in S['li'])}</ul>
    <form id="wl" novalidate>
      <label for="email" class="muted" style="flex-basis:100%">{e(S['wlLabel'])}</label>
      <input id="email" type="email" autocomplete="email" placeholder="you@example.com" required>
      <button class="btn acc" type="submit">{e(S['wlBtn'])}</button>
      <label class="consent"><input id="consent" type="checkbox" required> <span>{e(S['consent'])} <a href="/privacy/">{e(S['privacy'])}</a></span></label>
      <span id="wlmsg" class="formmsg" role="status"></span>
    </form></div>
</section>
<section class="sec"><h2>{e(S['faqH'])}</h2><div>{faq}</div></section>
<footer><span>{e(S['foot1'])}</span><span>{e(cfg.get('business_name') or '[toiminimi]')} · {e(cfg.get('business_id') or '[Y-tunnus]')} · {e(cfg.get('email') or '[sähköposti]')}</span>
<span><a href="/privacy/">{e(S['privacy'])}</a> · <a href="/terms/">{e(S['terms'])}</a></span></footer>
</div>
<script>
(function(){{const C={wl};const f=document.getElementById("wl"),m=document.getElementById("wlmsg");
f.addEventListener("submit",async ev=>{{ev.preventDefault();const v=document.getElementById("email").value.trim();
if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(v)||!document.getElementById("consent").checked){{m.textContent=C.msg.wlBad;return;}}
if(!C.url||!C.key){{m.textContent=C.msg.wlSoon;return;}}
try{{const r=await fetch(C.url+"/rest/v1/waitlist",{{method:"POST",headers:{{"apikey":C.key,"Authorization":"Bearer "+C.key,"Content-Type":"application/json","Prefer":"return=minimal"}},body:JSON.stringify({{email:v,lang:C.lang,consent:true}})}});
m.textContent=(r.ok||r.status===409)?C.msg.wlOk:C.msg.wlErr;if(r.ok)f.reset();}}catch(err){{m.textContent=C.msg.wlErr;}}}});}})();
</script></body></html>"""


def legal_page(kind, cfg):
    name = cfg.get("business_name") or "[toiminimi]"
    bid = cfg.get("business_id") or "[Y-tunnus]"
    mail = cfg.get("email") or "[sähköposti]"
    ready = all(cfg.get(k) for k in ("business_name", "business_id", "email"))
    warn = "" if ready else '<p class="warn">Luonnos: täydennetään yrityksen tiedoilla ennen myynnin avaamista. Draft: business details will be added before sales open.</p>'
    with open(os.path.join(ROOT, "site_src", f"{kind}.html"), encoding="utf-8") as fh:
        body = fh.read().replace("{{NAME}}", e(name)).replace("{{ID}}", e(bid)).replace("{{EMAIL}}", e(mail))
    title = {"privacy": "Tietosuojaseloste – Privacy notice | Koevalmis", "terms": "Myyntiehdot – Terms of sale | Koevalmis"}[kind]
    robots = "" if ready else '<meta name="robots" content="noindex">'
    return (head("fi", title, title, f"/{kind}/", cfg, alternates=False).replace("</title>", "</title>" + robots, 1)
            + f'<div class="wrap"><header><a class="brand" href="/"><span class="dot" aria-hidden="true"></span>Koevalmis</a></header><main class="doc">{warn}{body}</main></div></body></html>')


def app_page(cfg):
    subprocess.run([sys.executable, os.path.join(ROOT, "build.py")], check=False, stdout=subprocess.DEVNULL)
    with open(os.path.join(ROOT, "dist", "koevalmis.html"), encoding="utf-8") as fh:
        app = fh.read()
    title = re.search(r"<title>(.*?)</title>", app).group(1)
    app = app.replace(f"<title>{title}</title>", "", 1)
    desc = "Practise for the Finnish citizenship test: questions in Finnish with translations, audio and mock exams."
    return head("en", "Koevalmis – practice app", desc, "/app/", cfg, alternates=False, css=False) + app + "</body></html>"


def write(rel, content):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content)


def main():
    with open(os.path.join(ROOT, "site_src", "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    with open(os.path.join(ROOT, "site_src", "landing_strings.json"), encoding="utf-8") as fh:
        strings = json.load(fh)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for lang in LANGS:
        write(("" if lang == "en" else lang + "/") + "index.html", landing(lang, strings[lang], cfg))
    write("app/index.html", app_page(cfg))
    write("privacy/index.html", legal_page("privacy", cfg))
    write("terms/index.html", legal_page("terms", cfg))
    base = cfg["base_url"].rstrip("/")
    urls = [path_for(l) for l in LANGS] + ["/app/"]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{base}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    write("CNAME", cfg["base_url"].split("//")[1].strip("/") + "\n")
    write(".nojekyll", "")
    missing = [k for k in ("business_name", "business_id", "email", "waitlist_url", "waitlist_anon_key") if not cfg.get(k)]
    print("site built:", sorted(os.path.relpath(os.path.join(d, f), OUT) for d, _, fs in os.walk(OUT) for f in fs))
    if missing:
        print("placeholders still empty:", missing)


if __name__ == "__main__":
    main()
