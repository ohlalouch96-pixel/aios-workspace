"""
Instagram: storybeeld "AI find of the week" (@insightance.ai, weekendstory op zaterdag, sinds 28-11-2026)

Eén staand beeld van 1080x1920 in de basiskleur (navy): label, titel met *kernwoord* in geel, korte uitleg,
2 tot 3 genummerde stappen en de bron. Alles binnen de veilige zone van stories (boven 250 px en onder 380 px vrij
voor de profielbalk en het antwoordveld). Logo altijd in de vaste merkkleuren.

Spec:
    {"titel": "ChatGPT can now *read your screen*", "uitleg": "...", "stappen": ["...", "..."], "bron_naam": "OpenAI"}

Gebruik (CLI):
    python tools/instagram/render_story.py spec.json --uit map/
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HIER = Path(__file__).resolve().parent
FONTS = (HIER / "fonts").as_uri()


def opmaak(tekst):
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(tekst))


def html_story(spec):
    stappen = "".join(f'<div class="stap"><b>{i}</b><span>{opmaak(s)}</span></div>' for i, s in enumerate(spec["stappen"][:3], 1))
    lengte = len(spec["titel"].replace("*", ""))
    grootte = 104 if lengte <= 28 else 90 if lengte <= 40 else 78
    return f"""<html><head><meta charset="utf-8"><style>
@font-face{{font-family:Inter;font-weight:100 900;src:url('{FONTS}/inter-latin.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;font-family:Inter;color:#fff;
  background:radial-gradient(ellipse 80% 45% at 50% 30%, #23497F 0%, #0F2547 70%)}}
.lab{{position:absolute;left:90px;top:270px;display:inline-flex;align-items:center;gap:14px;font:800 30px Inter;letter-spacing:.14em;
  color:#0F2547;background:#FFC93C;padding:14px 26px;border-radius:40px}}
h1{{position:absolute;left:90px;right:90px;top:380px;font:900 {grootte}px/1.02 Inter;letter-spacing:-.045em}}
h1 em{{font-style:normal;color:#FFC93C}}
.uitleg{{position:absolute;left:90px;right:90px;top:var(--u);font:500 42px/1.4 Inter;color:#C9D6EE}}
.stappen{{position:absolute;left:90px;right:90px;top:var(--s);display:flex;flex-direction:column;gap:22px}}
.stap{{display:flex;align-items:center;gap:26px;background:#fff;color:#101828;border-radius:28px;padding:26px 30px;font:700 38px/1.25 Inter;
  box-shadow:0 24px 50px rgba(0,0,0,.3)}}
.stap b{{flex:none;width:64px;height:64px;border-radius:50%;background:#1F5EFF;color:#fff;display:grid;place-items:center;font:900 34px Inter}}
.stap em{{font-style:normal;color:#1F5EFF}}
.voet{{position:absolute;left:90px;right:90px;top:1440px;display:flex;justify-content:space-between;align-items:center;font:600 30px Inter;color:#9DBBE3}}
.voet .h{{display:flex;align-items:center;gap:14px;color:#fff;font-weight:700}}
</style></head><body>
<div class="lab"><svg width="22" height="30" viewBox="0 0 22 30"><path d="M13 0 L0 17 H9 L7 30 L22 11 H12 Z" fill="#0F2547"/></svg>AI FIND OF THE WEEK</div>
<h1 id="t">{opmaak(spec["titel"])}</h1>
<div class="uitleg" id="u">{opmaak(spec["uitleg"])}</div>
<div class="stappen" id="s">{stappen}</div>
<div class="voet"><span>Source: {html.escape(spec["bron_naam"])}</span>
<span class="h"><svg width="46" height="46" viewBox="0 0 44 44" fill="none"><rect x="19" y="6" width="6" height="32" rx="1" fill="#FFFFFF"/><path d="M8 36 Q14 28 22 22 Q30 16 36 8" stroke="#9DBBE3" stroke-width="2.6" fill="none" stroke-linecap="round"/><circle cx="8" cy="36" r="2.8" fill="#9DBBE3"/><circle cx="36" cy="8" r="2.8" fill="#9DBBE3"/></svg>@insightance.ai</span></div>
<script>
  // uitleg en stappen schuiven mee met de hoogte van de titel (pas na het laden van het lettertype aanroepen);
  // geeft false als het niet boven de voet past
  window.__opmaak = () => {{
    const t = document.getElementById('t').getBoundingClientRect();
    document.body.style.setProperty('--u', (t.bottom + 40) + 'px');
    const ub = document.getElementById('u').getBoundingClientRect();
    document.body.style.setProperty('--s', (ub.bottom + 50) + 'px');
    return document.getElementById('s').getBoundingClientRect().bottom <= 1400;
  }};
</script>
</body></html>"""


def render(spec, uit):
    """Rendert story.png in map 'uit'. Geeft het pad terug; ValueError als de tekst niet binnen de veilige zone past."""
    uit.mkdir(parents=True, exist_ok=True)
    tmp = uit / "_story.html"
    tmp.write_text(html_story(spec), encoding="utf-8")
    pad = uit / "story.png"
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception:
            b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)
        pg.goto(tmp.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        past = pg.evaluate("window.__opmaak()")
        pg.screenshot(path=str(pad))
        b.close()
    tmp.unlink()
    Image.open(pad).resize((1080, 1920), Image.LANCZOS).save(pad, optimize=True)
    if not past:
        raise ValueError("Tekst te lang voor de veilige zone van de story")
    return pad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--uit", required=True)
    a = ap.parse_args()
    print(render(json.loads(Path(a.spec).read_text(encoding="utf-8")), Path(a.uit)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
