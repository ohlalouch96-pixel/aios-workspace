"""
Instagram — "out of the box"-beeld: schets op een wisselende ondergrond

Losse afbeelding van 1080x1350 met een schets (zie de soorten hieronder) en
een titel, op steeds een andere ondergrond, zodat deze posts niet op elkaar
gaan lijken:
    bureau   notitiekaart op een houten bureau, koffie en groene stift
    kantoor  ruitjespapier op een licht kantoorbureau, laptop, post-it en pen
    ipad     iPad met notitie-app en pencil op een donker bureau
    scherm   whiteboard-app op een monitor
    krant    zwart-wit krantenpagina met de schets als illustratie
    whiteboard  whiteboard op kantoor met markers en magneten
    servet   servetje in een café met koffie en een balpen
Bedoeld als afwisseling naast de strakke carrousels, en voor The Fork.

Spec:
    {"type": "venn", "scene": "krant", "titel": "Where automation pays off first",
     "links": "Tasks you repeat every week", "rechts": "Tasks that follow clear rules", "midden": "start here"}
    {"type": "fork", "scene": "ipad", "titel": "...",
     "keuze_a": "...", "uitkomst_a": ["...", "..."], "keuze_b": "...", "uitkomst_b": "..."}
    {"type": "lijst", "items": [{"tekst": "...", "ok": true}, {"tekst": "...", "ok": false}]}
    {"type": "voor_na", "links_kop": "Before", "links": ["..."], "rechts_kop": "After", "rechts": ["..."]}
    {"type": "stappen", "stappen": ["...", "...", "..."]}             (3 of 4)
    {"type": "grafiek", "lijn": "stijgend", "notitie": "...", "x": "...", "y": "..."}
    {"type": "loop", "stappen": ["...", "...", "..."], "midden": "optioneel"}
Zonder "scene" wordt er willekeurig een gekozen.

Gebruik (CLI):
    python tools/instagram/render_kaart.py spec.json [--scene kantoor] [--uit pad.png]
"""

import argparse
import html
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HIER = Path(__file__).resolve().parent
FONTS = (HIER / "fonts").as_uri()
TMP = HIER.parent.parent / ".tmp" / "instagram"
SCENES = ["bureau", "kantoor", "ipad", "scherm", "krant", "whiteboard", "servet"]


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


INK = 'style="stroke:var(--ink)" fill="none" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"'


def venn(spec):
    cx1, cx2, cy, r = 330, 570, 320, 205
    arceer = "".join(f'<line x1="{x}" y1="80" x2="{x - 260}" y2="600" style="stroke:var(--acc)" stroke-width="5" stroke-linecap="round"/>' for x in range(330, 900, 22))
    svg = f'''<svg width="900" height="710" viewBox="0 0 900 710" style="position:absolute;left:0;top:0">
      <defs><clipPath id="l"><circle cx="{cx1}" cy="{cy}" r="{r}"/></clipPath><clipPath id="r"><circle cx="{cx2}" cy="{cy}" r="{r}"/></clipPath></defs>
      <g clip-path="url(#l)"><g clip-path="url(#r)">{arceer}</g></g>
      <path d="{cirkel(cx1, cy, r, 1)}" {INK}/><path d="{cirkel(cx2, cy, r, 2)}" {INK}/>
      <path d="M450 600 L450 550 M432 570 L450 548 L470 570" {INK}/></svg>'''
    return (svg + f'<div class="hw" style="left:165px;top:235px;width:200px">{html.escape(spec["links"])}</div>'
            f'<div class="hw" style="left:535px;top:235px;width:200px">{html.escape(spec["rechts"])}</div>'
            f'<div class="hw acc" style="left:250px;top:605px;width:400px;font-size:1.26em">{html.escape(spec["midden"])}</div>')


def fork(spec):
    def pijl(x1, y1, x2, y2):
        return (f'<path d="M{x1} {y1} Q{(x1 + x2) / 2 + 10} {(y1 + y2) / 2 - 10} {x2} {y2}" {INK}/>'
                f'<circle cx="{x2}" cy="{y2}" r="7" style="fill:var(--ink)"/>')
    svg = f'<svg width="900" height="710" viewBox="0 0 900 710" style="position:absolute;left:0;top:0">{pijl(300, 190, 560, 140)}{pijl(300, 190, 560, 300)}{pijl(300, 520, 560, 540)}</svg>'
    ua = spec["uitkomst_a"]
    links = "text-align:left"
    return (svg + f'<div class="hw" style="left:40px;top:140px;width:260px;{links}">{html.escape(spec["keuze_a"])}</div>'
            f'<div class="hw acc" style="left:580px;top:95px;width:300px;{links}">{html.escape(ua[0])}</div>'
            f'<div class="hw acc" style="left:580px;top:255px;width:300px;{links}">{html.escape(ua[1])}</div>'
            f'<div class="hw" style="left:40px;top:470px;width:260px;{links}">{html.escape(spec["keuze_b"])}</div>'
            f'<div class="hw neg" style="left:580px;top:495px;width:300px;{links}">{html.escape(spec["uitkomst_b"])}</div>')


def lijn(punten, seed, wiebel=3):
    """Handgetekende lijn door punten: kleine afwijkingen per tussenpunt."""
    rnd = random.Random(seed)
    d = []
    for (x1, y1), (x2, y2) in zip(punten, punten[1:]):
        stappen = max(2, int(math.hypot(x2 - x1, y2 - y1) / 40))
        for i in range(stappen + 1):
            t = i / stappen
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            if 0 < i < stappen:
                x, y = x + rnd.uniform(-wiebel, wiebel), y + rnd.uniform(-wiebel, wiebel)
            d.append(f"{x:.1f},{y:.1f}")
    return "M" + " L".join(d)


def pijlpunt(x, y, hoek, maat=20):
    a1, a2 = hoek + 2.6, hoek - 2.6
    return f'<path d="M{x + maat * math.cos(a1):.1f} {y + maat * math.sin(a1):.1f} L{x} {y} L{x + maat * math.cos(a2):.1f} {y + maat * math.sin(a2):.1f}" {INK}/>'


def svg(inhoud):
    return f'<svg width="900" height="710" viewBox="0 0 900 710" style="position:absolute;left:0;top:0">{inhoud}</svg>'


def lijst(spec):
    """Afvinklijst: vakjes met vinkje (ok) of kruisje."""
    items = spec["items"][:5]
    stap = 600 / max(len(items), 1)
    teken, tekst = "", ""
    for i, it in enumerate(items):
        y = 40 + i * stap
        teken += f'<path d="{lijn([(120, y), (176, y), (176, y + 56), (120, y + 56), (120, y)], i)}" {INK}/>'
        if it.get("ok", True):
            teken += f'<path d="M128 {y + 26} L146 {y + 48} L196 {y - 12}" style="stroke:var(--acc)" fill="none" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
        else:
            teken += f'<path d="M128 {y + 6} L170 {y + 50} M170 {y + 6} L128 {y + 50}" style="stroke:var(--neg)" fill="none" stroke-width="7" stroke-linecap="round"/>'
        tekst += f'<div class="hw{"" if it.get("ok", True) else " neg"}" style="left:220px;top:{y - 2}px;width:620px;text-align:left">{html.escape(it["tekst"])}</div>'
    return svg(teken) + tekst


def voor_na(spec):
    """Twee kolommen: links (doorgestreept) tegenover rechts."""
    teken = f'<path d="{lijn([(450, 20), (450, 660)], 7, 4)}" {INK}/>'
    teken += (f'<path d="{lijn([(60, 110), (400, 110)], 8)}" style="stroke:var(--neg)" fill="none" stroke-width="4"/>'
              f'<path d="{lijn([(500, 110), (840, 110)], 9)}" style="stroke:var(--acc)" fill="none" stroke-width="4"/>')
    tekst = (f'<div class="hw neg" style="left:40px;top:30px;width:380px;font-size:1.2em">{html.escape(spec["links_kop"])}</div>'
             f'<div class="hw acc" style="left:480px;top:30px;width:380px;font-size:1.2em">{html.escape(spec["rechts_kop"])}</div>')
    for i, t in enumerate(spec["links"][:5]):
        y = 150 + i * 122
        tekst += f'<div class="hw" style="left:50px;top:{y}px;width:360px">{html.escape(t)}</div>'
        teken += f'<path d="{lijn([(80, y + 32), (380, y + 26)], 20 + i, 2)}" style="stroke:var(--neg)" fill="none" stroke-width="4" opacity=".8"/>'
    for i, t in enumerate(spec["rechts"][:5]):
        tekst += f'<div class="hw" style="left:490px;top:{150 + i * 122}px;width:360px">{html.escape(t)}</div>'
    return svg(teken) + tekst


def stappen(spec):
    """Genummerde stappen als kaders met pijlen ertussen (zigzag)."""
    st = spec["stappen"][:4]
    pos = [(70, 30), (480, 190), (70, 350), (480, 510)][:len(st)]
    teken, tekst = "", ""
    for i, (x, y) in enumerate(pos):
        teken += f'<path d="{lijn([(x, y), (x + 350, y), (x + 350, y + 140), (x, y + 140), (x, y)], 30 + i)}" {INK}/>'
        tekst += (f'<div class="hw acc" style="left:{x + 14}px;top:{y + 8}px;width:60px;font-size:1.3em;text-align:left">{i + 1}</div>'
                  f'<div class="hw" style="left:{x + 60}px;top:{y + 22}px;width:280px;text-align:left">{html.escape(st[i])}</div>')
        if i + 1 < len(pos):
            x2, y2 = pos[i + 1]
            a, b = ((x + 350, y + 100), (x2 + 40, y2)) if x < x2 else ((x, y + 100), (x2 + 310, y2))
            teken += f'<path d="{lijn([a, b], 40 + i, 2)}" {INK}/>' + pijlpunt(b[0], b[1], math.atan2(b[1] - a[1], b[0] - a[0]))
    return svg(teken) + tekst


def grafiek(spec):
    """Handgetekende grafiek: assen, een stijgende of dalende lijn en een notitie bij de knik."""
    teken = f'<path d="{lijn([(110, 40), (110, 600), (840, 600)], 50)}" {INK}/>' + pijlpunt(110, 40, -math.pi / 2) + pijlpunt(840, 600, 0)
    stijgend = spec.get("lijn", "stijgend") == "stijgend"
    pts = [(140, 560 if stijgend else 120), (330, 520 if stijgend else 170), (470, 470 if stijgend else 260),
           (580, 330 if stijgend else 430), (800, 100 if stijgend else 560)]
    teken += (f'<path d="M{pts[0][0]} {pts[0][1]} ' + " ".join(f"T{x} {y}" for x, y in pts[1:])
              + '" style="stroke:var(--acc)" fill="none" stroke-width="7" stroke-linecap="round"/>')
    kx, ky = pts[2]
    teken += (f'<circle cx="{kx}" cy="{ky}" r="12" style="fill:var(--neg)"/>'
              f'<path d="{lijn([(kx - 60, ky - 160), (kx - 10, ky - 24)], 52, 2)}" {INK}/>' + pijlpunt(kx - 10, ky - 24, math.atan2(136, 50)))
    return (svg(teken) + f'<div class="hw" style="left:{kx - 300}px;top:{ky - 270}px;width:340px">{html.escape(spec["notitie"])}</div>'
            f'<div class="hw" style="left:540px;top:615px;width:320px;text-align:right;font-size:.85em">{html.escape(spec["x"])}</div>'
            f'<div class="hw" style="left:130px;top:20px;width:260px;text-align:left;font-size:.85em">{html.escape(spec["y"])}</div>')


def loop(spec):
    """Kringloop: 3 of 4 punten rond een cirkel met pijlen ertussen."""
    st = spec["stappen"][:4]
    n, cx, cy, r = len(st), 450, 345, 245
    teken, tekst = "", ""
    for i in range(n):
        a1 = -math.pi / 2 + 2 * math.pi * i / n + 0.62
        a2 = -math.pi / 2 + 2 * math.pi * (i + 1) / n - 0.62
        boog = [(cx + r * math.cos(a1 + (a2 - a1) * t / 12), cy + r * math.sin(a1 + (a2 - a1) * t / 12)) for t in range(13)]
        teken += f'<path d="{lijn(boog, 60 + i, 2)}" {INK}/>' + pijlpunt(boog[-1][0], boog[-1][1], a2 + math.pi / 2)
        a = -math.pi / 2 + 2 * math.pi * i / n
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        tekst += f'<div class="hw{" acc" if i == 0 else ""}" style="left:{x - 150:.0f}px;top:{y - 40:.0f}px;width:300px">{html.escape(st[i])}</div>'
    if spec.get("midden"):
        tekst += f'<div class="hw acc" style="left:300px;top:{cy - 30}px;width:300px;font-size:1.2em">{html.escape(spec["midden"])}</div>'
    return svg(teken) + tekst


def vlak(spec):
    """Het tekenvlak (900x860): titel bovenaan, schets eronder."""
    makers = {"venn": venn, "fork": fork, "lijst": lijst, "voor_na": voor_na, "stappen": stappen, "grafiek": grafiek, "loop": loop}
    inhoud = makers[spec["type"]](spec)
    return f'<div class="vlak"><div class="titel">{html.escape(spec["titel"])}</div><div class="schets">{inhoud}</div></div>'


def nep_tekst(regels, breedte, seed):
    """Grijze balkjes als krantentekst (geen leesbare nep-inhoud)."""
    rnd = random.Random(seed)
    return "".join(f'<i style="width:{breedte if i % 7 != 6 else rnd.randint(30, 70)}%"></i>' for i in range(regels))


SCENE_CSS = {
    "bureau": """
.s{background:repeating-linear-gradient(91deg,rgba(60,30,10,.10) 0 2px,transparent 2px 23px),repeating-linear-gradient(89.4deg,rgba(255,230,190,.07) 0 1px,transparent 1px 57px),linear-gradient(180deg,#a8743f,#8f5f31 60%,#7d5229);
  --ink:#1d1d1f;--acc:#1f9d55;--neg:#c0392b;--font:Hand}
.mok{position:absolute;left:-120px;top:-140px;width:360px;height:360px;border-radius:50%;background:radial-gradient(circle,#3b2516 0 52%,#efe9df 53% 66%,#d8d0c4 67% 70%,transparent 71%);box-shadow:20px 30px 40px rgba(0,0,0,.25)}
.papier{position:absolute;left:90px;top:250px;width:900px;height:860px;transform:rotate(-1.6deg);
  background:repeating-linear-gradient(180deg,transparent 0 59px,#b9cde6 59px 61px) 0 150px/100% calc(100% - 150px) no-repeat,#fbfaf4;box-shadow:0 2px 2px rgba(0,0,0,.15),0 30px 60px rgba(0,0,0,.35)}
.papier:before{content:'';position:absolute;left:0;right:0;top:148px;height:3px;background:#e7a3a3}
.stift{position:absolute;right:40px;bottom:120px;width:46px;height:330px;transform:rotate(18deg);border-radius:10px;background:linear-gradient(90deg,#14532d,#1f9d55 45%,#14532d);box-shadow:12px 16px 24px rgba(0,0,0,.35)}
.stift:before{content:'';position:absolute;left:0;right:0;top:-70px;height:80px;border-radius:12px 12px 4px 4px;background:linear-gradient(90deg,#0f3d22,#1a7f45 45%,#0f3d22)}
.handle{color:rgba(255,240,220,.75)}""",
    "kantoor": """
.s{background:radial-gradient(ellipse at 30% 20%,#f4f1ec,#e3ddd3 70%,#d6cfc3);--ink:#1b2a59;--acc:#e8590c;--neg:#b42318;--font:Hand}
.laptop{position:absolute;right:-180px;top:-60px;width:620px;height:400px;border-radius:26px;background:linear-gradient(160deg,#c9ccd1,#a9adb4);transform:rotate(-12deg);box-shadow:0 30px 50px rgba(0,0,0,.2)}
.laptop:before{content:'';position:absolute;inset:40px 50px 110px;border-radius:10px;background:repeating-linear-gradient(90deg,#2d3036 0 44px,#a9adb4 44px 50px),#2d3036;opacity:.9}
.laptop:after{content:'';position:absolute;left:190px;right:190px;bottom:28px;height:62px;border-radius:10px;background:#b8bcc2;box-shadow:inset 0 0 0 2px #9da1a8}
.postit{position:absolute;left:60px;top:70px;width:230px;height:220px;background:linear-gradient(170deg,#ffe66d,#fbd94a);transform:rotate(-5deg);box-shadow:0 16px 24px rgba(0,0,0,.18);font:700 40px/1.1 Hand;color:#1b2a59;padding:34px 26px}
.papier{position:absolute;left:100px;top:300px;width:900px;height:860px;transform:rotate(1.2deg);background:linear-gradient(90deg,#dfe6f1 1px,transparent 1px) 0 0/30px 30px,linear-gradient(#dfe6f1 1px,transparent 1px) 0 0/30px 30px,#fdfdfb;box-shadow:0 2px 3px rgba(0,0,0,.12),0 26px 50px rgba(0,0,0,.18)}
.stift{position:absolute;left:40px;bottom:110px;width:22px;height:380px;transform:rotate(-28deg);border-radius:12px;background:linear-gradient(90deg,#0d1b45,#2c3f8f 50%,#0d1b45);box-shadow:10px 14px 20px rgba(0,0,0,.25)}
.stift:before{content:'';position:absolute;left:5px;right:5px;top:-34px;height:40px;clip-path:polygon(50% 0,100% 100%,0 100%);background:#c9ccd1}
.handle{color:rgba(27,42,89,.6)}""",
    "ipad": """
.s{background:radial-gradient(ellipse at 50% 30%,#3a3f47,#1f2328 75%);--ink:#111;--acc:#1F5EFF;--neg:#d92d20;--font:Hand}
.tablet{position:absolute;left:60px;top:150px;width:960px;height:1080px;border-radius:64px;background:#0c0c0e;box-shadow:0 0 0 3px #2b2e33,0 40px 80px rgba(0,0,0,.55)}
.scherm{position:absolute;inset:34px;border-radius:34px;overflow:hidden;background:radial-gradient(#d4d7dc 1.6px,transparent 1.8px) 0 0/34px 34px,#fff}
.balk{position:absolute;left:0;right:0;top:0;height:76px;border-bottom:1px solid #e6e8eb;background:rgba(250,250,251,.95);display:flex;align-items:center;gap:22px;padding:0 34px}
.balk b{width:30px;height:30px;border-radius:8px;background:#d5d8dd}.balk b:nth-child(3){background:var(--acc)}.balk span{margin-left:auto;font:600 24px Inter,sans-serif;color:#8a8f98}
.papier{position:absolute;left:0;top:110px;width:900px;height:860px;transform:scale(.99)}
.stift{position:absolute;right:30px;bottom:40px;width:22px;height:520px;transform:rotate(24deg);border-radius:11px;background:linear-gradient(90deg,#e9eaec,#fff 45%,#d9dbde);box-shadow:10px 16px 26px rgba(0,0,0,.45)}
.stift:before{content:'';position:absolute;left:3px;right:3px;top:-30px;height:34px;clip-path:polygon(50% 0,100% 100%,0 100%);background:#f2f3f5}
.handle{color:rgba(255,255,255,.55)}""",
    "scherm": """
.s{background:linear-gradient(180deg,#d9d4cc 0,#cfc8bd 62%,#8b7258 62%,#7a6249);--ink:#1d1d1f;--acc:#12b76a;--neg:#d92d20;--font:Hand}
.monitor{position:absolute;left:40px;top:170px;width:1000px;height:760px;border-radius:26px;background:#141518;box-shadow:0 40px 70px rgba(0,0,0,.35)}
.scherm{position:absolute;inset:26px 26px 26px;border-radius:8px;overflow:hidden;background:#fff}
.balk{position:absolute;left:0;right:0;top:0;height:54px;background:#f1f2f4;border-bottom:1px solid #e1e3e6;display:flex;align-items:center;gap:12px;padding:0 20px}
.balk b{width:16px;height:16px;border-radius:50%;background:#ff5f57}.balk b:nth-child(2){background:#febc2e}.balk b:nth-child(3){background:#28c840}
.balk span{margin:0 auto;font:500 20px Inter,sans-serif;color:#6b7280;transform:translateX(-30px)}
.papier{position:absolute;left:132px;top:58px;width:900px;height:860px;transform:scale(.76);transform-origin:0 0}
.voet{position:absolute;left:460px;top:930px;width:160px;height:150px;background:linear-gradient(90deg,#9aa0a8,#c9ced5 50%,#9aa0a8)}
.voet:after{content:'';position:absolute;left:-120px;right:-120px;bottom:-26px;height:34px;border-radius:50%/40%;background:linear-gradient(#c9ced5,#8d939b);box-shadow:0 18px 30px rgba(0,0,0,.35)}
.handle{color:rgba(255,240,220,.75)}""",
    "krant": """
.s{background:#2a2622;--ink:#111;--acc:#555;--neg:#111;--font:Playfair}
.papier{position:absolute;left:30px;top:20px;width:1020px;height:1310px;transform:rotate(-1deg);background:#efebe1;box-shadow:0 30px 60px rgba(0,0,0,.5);padding:46px 52px;filter:grayscale(1)}
.kop{font:900 92px/1 Playfair;text-align:center;letter-spacing:-.01em;color:#111;border-bottom:4px double #111;padding-bottom:16px}
.datum{display:flex;justify-content:space-between;font:600 20px Inter,sans-serif;letter-spacing:.12em;color:#333;border-bottom:1px solid #111;padding:10px 0;margin-bottom:26px}
.kolommen{display:grid;grid-template-columns:140px 1fr 140px;gap:24px;height:860px;overflow:hidden}
.kol i{display:block;height:11px;background:#9d978c;margin:0 0 12px;border-radius:2px}
.krantvlak{position:relative;height:860px;overflow:hidden}
.krantvlak .art{position:absolute;left:0;right:0;top:590px;columns:2;column-gap:22px}
.krantvlak .schets{font-size:38px}
.krantvlak .vlak{transform:scale(.65);transform-origin:0 0}
.krantvlak .titel{font:900 70px/1.05 Playfair;letter-spacing:-.01em}
.krantvlak .hw{font-style:italic;font-weight:600}
.onder{margin-top:24px;border-top:1px solid #111;padding-top:18px;display:grid;grid-template-columns:repeat(3,1fr);gap:26px}
.handle{display:none}""",
    "whiteboard": """
.s{background:linear-gradient(180deg,#e9e6e1,#dcd8d1);--ink:#1b2a59;--acc:#d92d20;--neg:#d92d20;--font:Hand}
.bord{position:absolute;left:40px;top:110px;width:1000px;height:990px;border-radius:10px;background:linear-gradient(135deg,#fdfdfd,#f1f3f5 60%,#e9ecef);box-shadow:inset 0 0 0 16px #c5c9cf,inset 0 0 0 18px #9aa0a8,0 30px 60px rgba(0,0,0,.18)}
.bord:after{content:'';position:absolute;left:30px;right:30px;top:30px;bottom:30px;background:linear-gradient(115deg,transparent 30%,rgba(255,255,255,.12) 36%,transparent 42%);pointer-events:none}
.papier{position:absolute;left:50px;top:70px;width:900px;height:860px}
.goot{position:absolute;left:120px;right:120px;top:1100px;height:30px;border-radius:0 0 8px 8px;background:linear-gradient(#b9bec5,#8f959d)}
.marker{position:absolute;top:1072px;width:170px;height:30px;border-radius:15px 6px 6px 15px}
.marker.m1{left:300px;background:linear-gradient(#24356b,#1b2a59)} .marker.m2{left:520px;background:linear-gradient(#e84a3f,#b42318);transform:rotate(-3deg)}
.magneet{position:absolute;width:44px;height:44px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#ffd84d,#e0a800);box-shadow:3px 6px 8px rgba(0,0,0,.25)}
.handle{color:rgba(27,42,89,.55)}""",
    "servet": """
.s{background:radial-gradient(ellipse at 60% 40%,#5a3b28,#2e1d13 80%);--ink:#16307a;--acc:#16307a;--neg:#16307a;--font:Hand}
.kopje{position:absolute;right:-90px;top:-70px;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,#c79a6b 0 20%,#7a4a2a 34% 48%,#f4efe6 49% 62%,#e5ddd0 63% 66%,transparent 67%);box-shadow:-20px 30px 40px rgba(0,0,0,.4)}
.papier{position:absolute;left:80px;top:230px;width:920px;height:920px;transform:rotate(3deg);padding:30px 10px;
  background:radial-gradient(circle at 30% 70%,rgba(0,0,0,.05),transparent 40%),linear-gradient(90deg,transparent 49.6%,rgba(0,0,0,.06) 50%,transparent 50.4%),linear-gradient(transparent 49.6%,rgba(0,0,0,.06) 50%,transparent 50.4%),#fbfaf7;
  box-shadow:inset 0 0 0 26px #fbfaf7,inset 0 0 0 30px #ece8e1,0 24px 50px rgba(0,0,0,.45)}
.pen{position:absolute;left:60px;bottom:90px;width:20px;height:400px;transform:rotate(-58deg);border-radius:10px;background:linear-gradient(90deg,#d8dbe0,#fff 45%,#c2c6cc);box-shadow:8px 14px 20px rgba(0,0,0,.4)}
.pen:before{content:'';position:absolute;left:3px;right:3px;top:-28px;height:32px;clip-path:polygon(50% 0,100% 100%,0 100%);background:#9aa0a8}
.handle{color:rgba(255,240,220,.55)}""",
}

BASIS_CSS = f"""
@font-face{{font-family:Hand;font-weight:500;src:url('{FONTS}/caveat-500.woff2')}}
@font-face{{font-family:Hand;font-weight:700;src:url('{FONTS}/caveat-700.woff2')}}
@font-face{{font-family:Playfair;font-weight:400 900;src:url('{FONTS}/playfair-latin.woff2')}}
@font-face{{font-family:Inter;font-weight:100 900;src:url('{FONTS}/inter-latin.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
.s{{width:1080px;height:1350px;position:relative;overflow:hidden}}
.vlak{{position:relative;width:900px;height:860px;color:var(--ink);font-family:var(--font)}}
.titel{{position:absolute;left:0;right:0;top:40px;text-align:center;font-weight:700;font-size:74px;line-height:1}}
.schets{{position:absolute;left:0;top:150px;width:900px;height:710px;font-size:46px}}
.hw{{position:absolute;font-weight:700;font-size:1em;line-height:1.05;text-align:center}}
.acc{{color:var(--acc)}} .neg{{color:var(--neg)}}
.handle{{position:absolute;left:0;right:0;bottom:46px;text-align:center;font:600 26px Inter,sans-serif;letter-spacing:.06em}}
"""


def scene_html(scene, spec):
    v = vlak(spec)
    if scene == "bureau":
        return f'<div class="mok"></div><div class="papier">{v}</div><div class="stift"></div>'
    if scene == "kantoor":
        return f'<div class="laptop"></div><div class="postit">this week:<br>fix one thing</div><div class="papier">{v}</div><div class="stift"></div>'
    if scene == "ipad":
        return f'<div class="tablet"><div class="scherm"><div class="balk"><b></b><b></b><b></b><b></b><span>Notes</span></div><div class="papier">{v}</div></div></div><div class="stift"></div>'
    if scene == "scherm":
        return f'<div class="monitor"><div class="scherm"><div class="balk"><b></b><b></b><b></b><span>Whiteboard</span></div><div class="papier">{v}</div></div></div><div class="voet"></div>'
    if scene == "krant":
        return (f'<div class="papier"><div class="kop">The Weekly Brief</div>'
                f'<div class="datum"><span>AUTOMATION EDITION</span><span>@INSIGHTANCE.AI</span></div>'
                f'<div class="kolommen"><div class="kol">{nep_tekst(56, 100, 1)}</div><div class="krantvlak">{v}<div class="art kol">{nep_tekst(22, 100, 6)}</div></div><div class="kol">{nep_tekst(56, 100, 2)}</div></div>'
                f'<div class="onder"><div class="kol">{nep_tekst(6, 100, 3)}</div><div class="kol">{nep_tekst(6, 100, 4)}</div><div class="kol">{nep_tekst(6, 100, 5)}</div></div></div>')
    if scene == "whiteboard":
        return (f'<div class="bord"><div class="papier">{v}</div></div><div class="magneet" style="left:110px;top:150px"></div>'
                f'<div class="magneet" style="left:930px;top:170px"></div><div class="goot"></div><div class="marker m1"></div><div class="marker m2"></div>')
    if scene == "servet":
        return f'<div class="kopje"></div><div class="papier">{v}</div><div class="pen"></div>'
    raise ValueError(f"Onbekende scene: {scene}")


def pagina(spec, scene):
    return (f'<html><head><meta charset="utf-8"><style>{BASIS_CSS}{SCENE_CSS[scene]}</style></head><body>'
            f'<div class="s">{scene_html(scene, spec)}<div class="handle">@insightance.ai</div></div></body></html>')


def scherp(pad):
    """Op dubbele resolutie gerenderd, netjes terug naar 1080x1350: strakkere letters en lijnen."""
    Image.open(pad).resize((1080, 1350), Image.LANCZOS).save(pad, optimize=True)


def render(spec, uit, scene=None):
    scene = scene or spec.get("scene") or random.choice(SCENES)
    uit.parent.mkdir(parents=True, exist_ok=True)
    tmp = uit.with_suffix(".html")
    tmp.write_text(pagina(spec, scene), encoding="utf-8")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=2)
        pg.goto(tmp.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(200)
        pg.locator(".s").screenshot(path=str(uit))
        scherp(uit)
        browser.close()
    tmp.unlink()
    return uit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--uit")
    args = ap.parse_args()
    spec_pad = Path(args.spec)
    uit = (Path(args.uit) if args.uit else TMP / f"{spec_pad.stem}.png").resolve()
    print(render(json.loads(spec_pad.read_text(encoding="utf-8")), uit, args.scene))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
