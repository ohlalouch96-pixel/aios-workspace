"""
Instagram — "out of the box"-beeld: handgeschreven systeemkaart op een bureau

Losse afbeelding van 1080x1350: een gelinieerde notitiekaart met
handgeschreven tekst en een schets (Venn-diagram of splitsing), schuin op een
houten bureau met een stift ernaast. Bedoeld als afwisseling naast de strakke
carrousels, en voor The Fork.

Spec:
    {"type": "venn", "titel": "Where automation pays off first",
     "links": "Tasks you repeat every week", "rechts": "Tasks that follow clear rules", "midden": "start here"}
    {"type": "fork", "titel": "...",
     "keuze_a": "...", "uitkomst_a": ["...", "..."], "keuze_b": "...", "uitkomst_b": "..."}

Gebruik (CLI):
    python tools/instagram/render_kaart.py spec.json [--uit pad.png]
"""

import argparse
import html
import json
import math
import random
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HIER = Path(__file__).resolve().parent
FONTS = (HIER / "fonts").as_uri()
TMP = HIER.parent.parent / ".tmp" / "instagram"
INKT, GROEN = "#1d1d1f", "#1f9d55"


def cirkel(cx, cy, r, seed):
    """Handgetekende cirkel: licht golvend en net niet gesloten."""
    rnd = random.Random(seed)
    fase, start = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
    pts = []
    for i in range(0, 375, 5):
        t = start + math.radians(i)
        rr = r * (1 + 0.012 * math.sin(3 * t + fase) + 0.006 * math.sin(7 * t))
        pts.append(f"{cx + rr * math.cos(t):.1f},{cy + rr * math.sin(t):.1f}")
    return "M" + " L".join(pts)


def venn(spec):
    cx1, cx2, cy, r = 330, 570, 320, 205
    a, b = cirkel(cx1, cy, r, 1), cirkel(cx2, cy, r, 2)
    arceer = "".join(f'<line x1="{x}" y1="180" x2="{x - 260}" y2="700" stroke="{GROEN}" stroke-width="5" stroke-linecap="round"/>' for x in range(330, 900, 22))
    svg = f'''<svg width="900" height="760" viewBox="0 0 900 760" style="position:absolute;left:0;top:0">
      <defs><clipPath id="l"><circle cx="{cx1}" cy="{cy}" r="{r}"/></clipPath><clipPath id="r"><circle cx="{cx2}" cy="{cy}" r="{r}"/></clipPath></defs>
      <g clip-path="url(#l)"><g clip-path="url(#r)">{arceer}</g></g>
      <path d="{a}" fill="none" stroke="{INKT}" stroke-width="5" stroke-linecap="round"/>
      <path d="{b}" fill="none" stroke="{INKT}" stroke-width="5" stroke-linecap="round"/>
      <path d="M450 600 L450 550 M432 570 L450 548 L470 570" fill="none" stroke="{INKT}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>'''
    tekst = (f'<div class="hw" style="left:165px;top:235px;width:200px">{html.escape(spec["links"])}</div>'
             f'<div class="hw" style="left:535px;top:235px;width:200px">{html.escape(spec["rechts"])}</div>'
             f'<div class="hw groen" style="left:300px;top:605px;width:300px;font-size:58px">{html.escape(spec["midden"])}</div>')
    return svg + tekst


def fork(spec):
    pijl = lambda x1, y1, x2, y2: (f'<path d="M{x1} {y1} Q{(x1 + x2) / 2 + 10} {(y1 + y2) / 2 - 10} {x2} {y2}" fill="none" stroke="{INKT}" stroke-width="5" stroke-linecap="round"/>'
                                   f'<circle cx="{x2}" cy="{y2}" r="7" fill="{INKT}"/>')
    svg = f'''<svg width="900" height="760" viewBox="0 0 900 760" style="position:absolute;left:0;top:0">
      {pijl(300, 190, 560, 140)}{pijl(300, 190, 560, 300)}{pijl(300, 520, 560, 540)}</svg>'''
    ua = spec["uitkomst_a"]
    return (svg + f'<div class="hw" style="left:40px;top:140px;width:260px;text-align:left">{html.escape(spec["keuze_a"])}</div>'
            f'<div class="hw groen" style="left:580px;top:95px;width:300px;text-align:left">{html.escape(ua[0])}</div>'
            f'<div class="hw groen" style="left:580px;top:255px;width:300px;text-align:left">{html.escape(ua[1])}</div>'
            f'<div class="hw" style="left:40px;top:470px;width:260px;text-align:left">{html.escape(spec["keuze_b"])}</div>'
            f'<div class="hw rood" style="left:580px;top:495px;width:300px;text-align:left">{html.escape(spec["uitkomst_b"])}</div>')


def pagina(spec):
    inhoud = venn(spec) if spec["type"] == "venn" else fork(spec)
    return f'''<html><head><meta charset="utf-8"><style>
@font-face{{font-family:Hand;font-weight:500;src:url('{FONTS}/caveat-500.woff2')}}
@font-face{{font-family:Hand;font-weight:700;src:url('{FONTS}/caveat-700.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
.s{{width:1080px;height:1350px;position:relative;overflow:hidden;
  background:
    repeating-linear-gradient(91deg, rgba(60,30,10,.10) 0 2px, transparent 2px 23px),
    repeating-linear-gradient(89.4deg, rgba(255,230,190,.07) 0 1px, transparent 1px 57px),
    linear-gradient(180deg,#a8743f,#8f5f31 60%,#7d5229)}}
.s:before{{content:'';position:absolute;inset:0;filter:url(#korrel);opacity:.35;background:#7a4e25}}
.mok{{position:absolute;left:-120px;top:-140px;width:360px;height:360px;border-radius:50%;background:radial-gradient(circle at 50% 50%,#3b2516 0 52%,#efe9df 53% 66%,#d8d0c4 67% 70%,transparent 71%);box-shadow:20px 30px 40px rgba(0,0,0,.25)}}
.kaart{{position:absolute;left:90px;top:250px;width:900px;height:860px;transform:rotate(-1.6deg);
  background:repeating-linear-gradient(180deg,transparent 0 59px,#b9cde6 59px 61px) 0 150px/100% calc(100% - 150px) no-repeat,#fbfaf4;
  box-shadow:0 2px 2px rgba(0,0,0,.15),0 30px 60px rgba(0,0,0,.35)}}
.kaart:before{{content:'';position:absolute;left:0;right:0;top:148px;height:3px;background:#e7a3a3}}
.titel{{position:absolute;left:0;right:0;top:40px;text-align:center;font:700 74px/1 Hand;color:{INKT}}}
.vlak{{position:absolute;left:0;top:150px;width:900px;height:710px}}
.hw{{position:absolute;font:700 46px/1.05 Hand;color:{INKT};text-align:center}}
.groen{{color:{GROEN}}} .rood{{color:#c0392b}}
.stift{{position:absolute;right:40px;bottom:120px;width:46px;height:330px;transform:rotate(18deg);border-radius:10px;
  background:linear-gradient(90deg,#14532d,#1f9d55 45%,#14532d);box-shadow:12px 16px 24px rgba(0,0,0,.35)}}
.stift:before{{content:'';position:absolute;left:0;right:0;top:-70px;height:80px;border-radius:12px 12px 4px 4px;background:linear-gradient(90deg,#0f3d22,#1a7f45 45%,#0f3d22)}}
.handle{{position:absolute;left:0;right:0;bottom:46px;text-align:center;font:600 26px Inter, sans-serif;letter-spacing:.06em;color:rgba(255,240,220,.75)}}
</style></head><body><div class="s">
<svg width="0" height="0"><filter id="korrel"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .6 0"/></filter></svg>
<div class="mok"></div>
<div class="kaart"><div class="titel">{html.escape(spec["titel"])}</div><div class="vlak">{inhoud}</div></div>
<div class="stift"></div><div class="handle">@insightance.ai</div>
</div></body></html>'''


def render(spec, uit):
    uit.parent.mkdir(parents=True, exist_ok=True)
    tmp = uit.with_suffix(".html")
    tmp.write_text(pagina(spec), encoding="utf-8")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(tmp.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(200)
        pg.locator(".s").screenshot(path=str(uit))
        browser.close()
    tmp.unlink()
    return uit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--uit")
    args = ap.parse_args()
    spec_pad = Path(args.spec)
    uit = Path(args.uit) if args.uit else TMP / f"{spec_pad.stem}.png"
    print(render(json.loads(spec_pad.read_text(encoding="utf-8")), uit))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
