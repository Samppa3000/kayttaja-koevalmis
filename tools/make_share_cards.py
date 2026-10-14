"""Shareable images (1080x1350) for WhatsApp, Telegram and Facebook, one per language.

Usage: python3 tools/make_share_cards.py FONT_DIR OUT_DIR
FONT_DIR must contain full TTF files (npm @expo-google-fonts/*):
  AtkinsonHyperlegibleNext_400Regular.ttf, AtkinsonHyperlegibleNext_800ExtraBold.ttf,
  GolosText_400Regular.ttf, GolosText_800ExtraBold.ttf, Vazirmatn_400Regular.ttf, Vazirmatn_800ExtraBold.ttf
Text comes from site_src/strings*.py, so the cards say exactly what the site says.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site_src"))
import strings as ST  # noqa: E402

FONT_DIR, OUT = sys.argv[1], sys.argv[2]
FAMILY = {"ru": "GolosText", "ar": "Vazirmatn", "fa": "Vazirmatn"}
LAKE, PAPER, INK, MUTED, BERRY, LAKE_MUTED = (15, 59, 61), (244, 246, 243), (16, 32, 31), (76, 94, 91), (243, 164, 59), (169, 196, 192)
W, H, M = 1080, 1350, 80


def font(lang, size, bold=False):
    fam = FAMILY.get(lang, "AtkinsonHyperlegibleNext")
    name = f"{fam}_{'800ExtraBold' if bold else '400Regular'}.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size, layout_engine=ImageFont.Layout.RAQM)


def wrap(draw, text, f, width, rtl):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f, direction="rtl" if rtl else "ltr") <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, lang, text, f, y, fill, width=W - 2 * M, gap=1.25, numeric=False):
    rtl = lang in ST.RTL
    for line in wrap(draw, text, f, width, rtl and not numeric):
        if rtl and numeric:   # numbers such as 18–64 keep their left-to-right order, aligned right
            draw.text((W - M, y), line, font=f, fill=fill, anchor="ra", direction="ltr")
        elif rtl:
            draw.text((W - M, y), line, font=f, fill=fill, anchor="ra", direction="rtl", language=lang)
        else:
            draw.text((M, y), line, font=f, fill=fill, anchor="la")
        y += int(f.size * gap)
    return y


def logo(draw, x, y, r):
    draw.ellipse((x, y, x + 2 * r, y + 2 * r), fill=BERRY)
    k = r / 14
    draw.line([(x + 8.5 * k, y + 14.5 * k), (x + 12.3 * k, y + 18.3 * k), (x + 19.5 * k, y + 10 * k)], fill=(28, 20, 5), width=int(2.8 * k), joint="curve")


def card(lang, S):
    # Long titles (e.g. Russian) get smaller type so the facts never reach the bottom band.
    for title_size, small_size in ((72, 34), (64, 32), (58, 30), (52, 28)):
        img, end = draw_card(lang, S, title_size, small_size)
        if end <= H - 270:
            return img
    return img


def draw_card(lang, S, title_size, small_size):
    img = Image.new("RGB", (W, H), LAKE)
    d = ImageDraw.Draw(img)
    rtl = lang in ST.RTL
    # brand row
    lf = ImageFont.truetype(os.path.join(FONT_DIR, "AtkinsonHyperlegibleNext_800ExtraBold.ttf"), 44)
    if rtl:
        logo(d, W - M - 56, 76, 28)
        d.text((W - M - 76, 80), "Koevalmis", font=lf, fill=PAPER, anchor="ra")
    else:
        logo(d, M, 76, 28)
        d.text((M + 76, 80), "Koevalmis", font=lf, fill=PAPER, anchor="la")
    y = text_block(d, lang, S["hubH1"], font(lang, title_size, True), 190, PAPER, gap=1.18)
    # four facts
    y += 40
    facts = [("1.3.2027", S["f1"]), ("18–64", S["f2"]), ("FI / SV", S["f3"]), (S["f4n"], S["f4"])]
    for big, small in facts:
        d.line([(M, y), (W - M, y)], fill=(43, 87, 89), width=2)
        y += 26
        y = text_block(d, lang, big, font(lang, 48, True), y, BERRY, gap=1.2, numeric=any(c.isdigit() for c in big) and big[0].isdigit() and " " not in big.strip())
        y = text_block(d, lang, small, font(lang, small_size), y + 4, LAKE_MUTED, gap=1.3) + 18
    end = y
    # bottom band
    band = H - 250
    d.rectangle((0, band, W, H), fill=PAPER)
    text_block(d, lang, S["cta1"], font(lang, 46, True), band + 50, INK)
    url = "koevalmis.fi"
    uf = ImageFont.truetype(os.path.join(FONT_DIR, "AtkinsonHyperlegibleNext_800ExtraBold.ttf"), 46)
    if rtl:
        d.text((W - M, band + 130), url, font=uf, fill=(31, 107, 69), anchor="ra")
    else:
        d.text((M, band + 130), url, font=uf, fill=(31, 107, 69), anchor="la")
    text_block(d, lang, S["tag"], font(lang, 26), band + 196, MUTED)
    return img, end


def main():
    os.makedirs(OUT, exist_ok=True)
    ALL = ST.load()
    for lang in ST.LANGS:
        path = os.path.join(OUT, f"koevalmis-2027-{lang}.png")
        card(lang, ALL[lang]).save(path, optimize=True)
        print(path)


if __name__ == "__main__":
    main()
