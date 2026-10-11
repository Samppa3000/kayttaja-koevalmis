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
              "uk": "Українська", "so": "Soomaali", "fa": "فارسی", "et": "Eesti"}
RTL = {"ar", "fa"}


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

    available = ["en", "fi"] + sorted(l for l in langs if not any(e.startswith(l + ":") and "untranslated" in e for e in errors))
    return {"questions": qs, "glossary": gl, "ui": ui_out, "topics": topics_out,
            "langs": [{"code": c, "name": LANG_NAMES.get(c, c), "rtl": c in RTL} for c in available]}, errors


def main():
    data, errors = load()
    for e in errors:
        print("WARN", e)
    with open(os.path.join(ROOT, "src", "app.html"), encoding="utf-8") as fh:
        html = fh.read()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = html.replace("/*__DATA__*/", blob)
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    path = os.path.join(ROOT, "dist", "koevalmis.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"{len(data['questions'])} questions, {len(data['glossary'])} terms, "
          f"languages {[l['code'] for l in data['langs']]} -> {path} ({len(out)//1024} KB)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
