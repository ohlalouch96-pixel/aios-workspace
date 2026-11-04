"""
Instagram — "out of the box"-beeld: schets op een wisselende ondergrond

Losse afbeelding van 1080x1350 met een schets (Venn-diagram of splitsing) en
een titel, op steeds een andere ondergrond, zodat deze posts niet op elkaar
gaan lijken:
    bureau   notitiekaart op een houten bureau, koffie en groene stift
    kantoor  ruitjespapier op een licht kantoorbureau, laptop, post-it en pen
    ipad     iPad met notitie-app en pencil op een donker bureau
    scherm   whiteboard-app op een monitor
    krant    zwart-wit krantenpagina met de schets als illustratie
Bedoeld als afwisseling naast de strakke carrousels, en voor The Fork.

Spec:
    {"type": "venn", "scene": "krant", "titel": "Where automation pays off first",
     "links": "Tasks you repeat every week", "rechts": "Tasks that follow clear rules", "midden": "start here"}
    {"type": "fork", "scene": "ipad", "titel": "...",
     "keuze_a": "...", "uitkomst_a": ["...", "..."], "keuze_b": "...", "uitkomst_b": "..."}
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

from playwright.sync_api import sync_playwright

HIER = Path(__file__).resolve().parent
FONTS = (HIER / "fonts").as_uri()
TMP = HIER.parent.parent / ".tmp" / "instagram"
SCENES = ["bureau", "kantoor", "ipad", "scherm", "krant"]


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


def vlak(spec):
    """Het tekenvlak (900x860): titel bovenaan, schets eronder."""
    inhoud = venn(spec) if spec["type"] == "venn" else fork(spec)
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
    raise ValueError(f"Onbekende scene: {scene}")


def pagina(spec, scene):
    return (f'<html><head><meta charset="utf-8"><style>{BASIS_CSS}{SCENE_CSS[scene]}</style></head><body>'
            f'<div class="s">{scene_html(scene, spec)}<div class="handle">@insightance.ai</div></div></body></html>')


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
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--uit")
    args = ap.parse_args()
    spec_pad = Path(args.spec)
    uit = (Path(args.uit) if args.uit else TMP / f"{spec_pad.stem}.png").resolve()
    print(render(json.loads(spec_pad.read_text(encoding="utf-8")), uit, args.scene))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
