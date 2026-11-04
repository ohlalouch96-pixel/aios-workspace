"""
Instagram — carrousel-slides renderen (@insightance.ai)

Zet een spec (JSON) om naar slides van 1080x1350 in de goedgekeurde stijl
(04-11-2026, zie outputs/instagram-stijl/_overzicht-v2.png): cover met groot
vet Inter en een kernwoord in accentkleur, lichte binnenslides met label-pil
en markering, cijferslide met groot Playfair-cijfer, Myth Check-cover met
aanhalingsteken. Logo + @insightance.ai onderaan, serienaam + teller bovenaan.

Spec:
    {
      "onderwerp": "...", "serie": "AUTOMATION SIMPLIFIED", "kleurenset": "navy",
      "slides": [
        {"type": "cover",  "titel": "Is AI the same thing as *automation?*", "sub": "optioneel"},
        {"type": "citaat", "titel": "I'm not ready for this yet."},
        {"type": "tekst",  "label": "Automation", "titel": "*Follows a script.*", "tekst": "..."},
        {"type": "cijfer", "cijfer": "40%", "tekst": "...", "bron": "Source: ..."},
        {"type": "slot",   "titel": "Just automation with better *marketing.*", "knop": "Follow for AI without the hype ⚡"}
      ]
    }
*sterretjes* = kernwoord: accentkleur op cover/slot, markering op tekstslides.

Gebruik (CLI):
    python tools/instagram/render_carrousel.py spec.json            # naar .tmp/instagram/<naam>/
    python tools/instagram/render_carrousel.py spec.json --uit map/
"""

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HIER = Path(__file__).resolve().parent
WORKSPACE_ROOT = HIER.parent.parent
FONTS = (HIER / "fonts").as_uri()
TMP = WORKSPACE_ROOT / ".tmp" / "instagram"

# cover-achtergrond, cover-tekst, accent, binnen-achtergrond, binnen-tekst, lopende tekst, markering
KLEUREN = {
    "navy":  dict(cbg="#17345F", cfg="#FFFFFF", acc="#5B8CFF", ibg="#F5F8FC", ifg="#17345F", body="#3B5478", mark="#C9DAFF"),
    "zwart": dict(cbg="#111111", cfg="#FFFFFF", acc="#FF4D3D", ibg="#F7F4EF", ifg="#111111", body="#44403C", mark="#FFC9C2"),
    "blauw": dict(cbg="#1F5EFF", cfg="#FFFFFF", acc="#FFD84D", ibg="#FFFFFF", ifg="#17345F", body="#3B5478", mark="#FFEFA8"),
    "groen": dict(cbg="#153B2E", cfg="#FFFFFF", acc="#B6F36B", ibg="#F2F6EE", ifg="#153B2E", body="#3F5A4C", mark="#DDF7BD"),
    "creme": dict(cbg="#F3EDE2", cfg="#17345F", acc="#E2572B", ibg="#FBF8F3", ifg="#17345F", body="#4A4A4A", mark="#FFD9C9"),
    "rood":  dict(cbg="#C8372D", cfg="#FFFFFF", acc="#FFE1D6", ibg="#FFF7F3", ifg="#2A1512", body="#5A3A34", mark="#FFD2C4"),
    "paars": dict(cbg="#2D1B5A", cfg="#FFFFFF", acc="#F59BD0", ibg="#F7F4FD", ifg="#2D1B5A", body="#4E4470", mark="#F6CDE6"),
}


def logo(bar, curve, size=40):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 44 44" fill="none"><rect x="19" y="6" width="6" height="32" rx="1" fill="{bar}"/>'
            f'<path d="M8 36 Q14 28 22 22 Q30 16 36 8" stroke="{curve}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
            f'<circle cx="8" cy="36" r="2.8" fill="{curve}"/><circle cx="36" cy="8" r="2.8" fill="{curve}"/></svg>')


def css(k):
    return f"""
@font-face{{font-family:Inter;font-weight:100 900;src:url('{FONTS}/inter-latin.woff2')}}
@font-face{{font-family:Playfair;font-weight:400 900;src:url('{FONTS}/playfair-latin.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
.s{{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:Inter}}
.top,.bot{{position:absolute;left:90px;right:90px;display:flex;justify-content:space-between;align-items:center;font:600 26px Inter;letter-spacing:.14em}}
.top{{top:80px}} .bot{{bottom:76px}}
.brand{{display:flex;align-items:center;gap:14px;letter-spacing:.02em}}
.mid{{position:absolute;left:90px;right:90px;top:50%;transform:translateY(-50%)}}
.dark{{background:{k['cbg']};color:{k['cfg']}}} .dark .top,.dark .bot{{color:{k['cfg']};opacity:.8}}
.light{{background:{k['ibg']};color:{k['ifg']}}} .light .top,.light .bot{{color:{k['ifg']};opacity:.75}}
h1{{font-family:Inter;font-weight:800;line-height:1.0;letter-spacing:-.035em}}
h1 em{{font-style:normal;color:{k['acc']}}}
.q{{font:700 220px/0.6 Playfair;color:{k['acc']};height:110px}}
h1.myth{{font-family:Playfair;font-weight:700;line-height:1.08;letter-spacing:-.01em}}
h2{{font-family:Playfair;font-weight:700;line-height:1.1}}
h2 em{{font-style:normal;background:linear-gradient(transparent 62%, {k['mark']} 62%)}}
.lab{{display:inline-block;font:700 24px Inter;letter-spacing:.16em;text-transform:uppercase;color:{k['ibg']};background:{k['ifg']};padding:12px 22px;border-radius:40px;margin-bottom:38px}}
p{{line-height:1.45;margin-top:40px}}
.dark p{{opacity:.85}} .light p{{color:{k['body']}}}
.stat{{font:700 300px/1 Playfair}} .stat span{{color:{k['acc'] if k['cbg'] != k['ibg'] else k['ifg']};margin-left:16px}}
.light .stat span{{color:{k['ifg']};opacity:.35}}
.src{{font:400 24px Inter;margin-top:32px;opacity:.7}}
.pill{{display:inline-block;border:3px solid currentColor;border-radius:60px;padding:16px 30px;font:700 30px Inter;margin-top:56px}}
"""


def opmaak(tekst):
    """Escapen en *kernwoord* omzetten naar <em>."""
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(tekst))


def maat(tekst, basis, tekens, minimum):
    """Lettergrootte die meekrimpt met langere teksten."""
    n = len(re.sub(r"\*", "", tekst))
    return int(max(minimum, min(basis, basis * math.sqrt(tekens / max(n, 1)))))


def slide_html(sl, k, serie, i, n):
    t = sl["type"]
    donker = t in ("cover", "citaat", "slot")
    if t == "cover":
        mid = f'<h1 style="font-size:{maat(sl["titel"], 116, 40, 76)}px">{opmaak(sl["titel"])}</h1>'
        if sl.get("sub"):
            mid += f'<p style="font-size:40px">{opmaak(sl["sub"])}</p>'
    elif t == "citaat":
        mid = f'<div class="q">“</div><h1 class="myth" style="font-size:{maat(sl["titel"], 104, 34, 70)}px">{opmaak(sl["titel"])}</h1>'
    elif t == "tekst":
        mid = (f'<div class="lab">{html.escape(sl["label"])}</div>' if sl.get("label") else "")
        mid += f'<h2 style="font-size:{maat(sl["titel"], 84, 26, 60)}px">{opmaak(sl["titel"])}</h2>'
        if sl.get("tekst"):
            mid += f'<p style="font-size:{40 if len(sl["tekst"]) < 170 else 35}px">{opmaak(sl["tekst"])}</p>'
    elif t == "cijfer":
        m = re.match(r"^([\d.,]+)(.*)$", sl["cijfer"])
        getal = f'{m.group(1)}<span>{html.escape(m.group(2))}</span>' if m and m.group(2) else html.escape(sl["cijfer"])
        mid = f'<div class="stat">{getal}</div><p style="font-size:46px;font-weight:600;color:{k["ifg"]}">{opmaak(sl["tekst"])}</p>'
        if sl.get("bron"):
            mid += f'<div class="src">{html.escape(sl["bron"])}</div>'
    elif t == "slot":
        mid = f'<h1 style="font-size:{maat(sl["titel"], 104, 40, 72)}px">{opmaak(sl["titel"])}</h1>'
        if sl.get("knop"):
            mid += f'<div class="pill">{html.escape(sl["knop"])}</div>'
    else:
        raise ValueError(f"Onbekend slide-type: {t}")
    bar, curve = (k["cfg"], k["acc"]) if donker else (k["ifg"], k["ifg"])
    swipe = "<span>SWIPE →</span>" if i == 1 and n > 1 else ""
    return (f'<div class="s {"dark" if donker else "light"}">'
            f'<div class="top"><span>{html.escape(serie)}</span><span>{f"{i}/{n}" if n > 1 else ""}</span></div>'
            f'<div class="mid">{mid}</div>'
            f'<div class="bot"><span class="brand">{logo(bar, curve)}@insightance.ai</span>{swipe}</div></div>')


def render(spec, uit):
    k = KLEUREN[spec.get("kleurenset", "navy")]
    uit.mkdir(parents=True, exist_ok=True)
    stijl = css(k)
    n = len(spec["slides"])
    paden = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1350})
        tmp = uit / "_tmp.html"
        for i, sl in enumerate(spec["slides"], 1):
            tmp.write_text(f'<html><head><meta charset="utf-8"><style>{stijl}</style></head><body>{slide_html(sl, k, spec["serie"], i, n)}</body></html>', encoding="utf-8")
            pg.goto(tmp.as_uri())
            pg.evaluate("document.fonts.ready")
            pad = uit / f"slide-{i}.png"
            pg.locator(".s").screenshot(path=str(pad))
            paden.append(pad)
        tmp.unlink()
        browser.close()
    return paden


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--uit")
    args = ap.parse_args()
    spec_pad = Path(args.spec)
    spec = json.loads(spec_pad.read_text(encoding="utf-8"))
    uit = Path(args.uit) if args.uit else TMP / spec_pad.stem
    for pad in render(spec, uit):
        print(pad)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
