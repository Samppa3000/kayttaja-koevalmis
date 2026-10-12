# Koevalmis

Practice app and website for the Finnish citizenship test (required for applications from 1 March 2027).

## Structure

- `data/q_*.json` – questions in Finnish and English, one file per topic
- `data/tr_<lang>_*.json` – translations (questions, topic names, interface, word list)
- `data/glossary.json` – word list
- `src/app.html` – the practice app (single file, data injected at build)
- `site_src/` – landing page texts, privacy notice, terms of sale and `config.json`
- `supabase/` – database migration for the waiting list
- `build.py` – builds the app into `dist/koevalmis.html`
- `build_site.py` – builds the whole website into `site/`

## Build

```
python3 build_site.py
```

Pushing to `main` deploys `site/` to GitHub Pages through `.github/workflows/pages.yml`.
Netlify can build the same site from this repository (`netlify.toml`, `requirements.txt`) once the
repository is linked to the `koevalmis` Netlify project. Both temporary addresses (github.io and
netlify.app) are built with `noindex`; set `NOINDEX` off when koevalmis.fi points to the host.

Design: lake-green hero, birch-white paper, cloudberry accent for actions. One font family,
"Koe Sans" (Atkinson Hyperlegible Next for Latin, Golos Text for Cyrillic, Vazirmatn for Arabic
script), self-hosted. The hero question card (`demo_card` in `build_site.py`, logic in
`site_src/site.js`) is the one animated moment: the "Oikein!" stamp after an answer.
Sales copy lives in `site_src/strings_sales.py`; optional `reviewed_by_educator` and `refund_days` in
`site_src/config.json` add a trust line once they are true.

## Before sales open

Fill `site_src/config.json`: business name, business ID (Y-tunnus), contact email and the waiting-list endpoint. Until then the legal pages show a draft notice and are not indexed, and the waiting-list form saves nothing.

Koevalmis is an independent service and is not affiliated with the Finnish Immigration Service (Migri).
