"""Linkvoorbeeld-afbeelding (Open Graph, 1200x630) voor insightance.ai. Lijn loopt onder de tekst, nooit erdoor."""
import pathlib
from playwright.sync_api import sync_playwright
R = pathlib.Path(__file__).resolve().parents[2]
F = (R / 'docs/fonts').as_uri()
ICON = ('<svg width="64" height="64" viewBox="0 0 44 44" fill="none"><rect x="19" y="6" width="6" height="32" rx="1" fill="#fff"/>'
        '<path d="M8 36 Q14 28 22 22 Q30 16 36 8" stroke="#9DBBE3" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
        '<circle cx="8" cy="36" r="2.8" fill="#9DBBE3"/><circle cx="36" cy="8" r="2.8" fill="#9DBBE3"/></svg>')
HTML = f'''<html><head><style>
@font-face{{font-family:Inter;font-weight:400 700;src:url('{F}/inter-latin.woff2')}}
@font-face{{font-family:Playfair;font-weight:500 700;src:url('{F}/playfair-latin.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}} body{{width:1200px;height:630px;overflow:hidden}}
.c{{position:relative;width:1200px;height:630px;background:radial-gradient(70% 110% at 88% 0%,#2A5BA3 0%,#17345F 62%);color:#fff;font-family:Inter;padding:84px 96px}}
</style></head><body><div class="c">
<svg style="position:absolute;inset:0" width="1200" height="630" fill="none"><path d="M-20 560 C 300 560, 640 540, 860 500 C 1000 474, 1080 400, 1220 300" stroke="#9DBBE3" stroke-opacity=".55" stroke-width="4"/></svg>
<div style="display:flex;align-items:center;gap:18px">{ICON}<span style="font:600 26px Inter;letter-spacing:.24em">INSIGHTANCE</span></div>
<div style="margin-top:62px;font:600 74px/1.08 Playfair;letter-spacing:-.01em">Less manual work.<br>More room to grow.</div>
<div style="margin-top:30px;font:500 28px/1.4 Inter;color:#C9D9EF;max-width:1000px">AI systems that take over the repetitive work in your business.</div>
<div style="position:absolute;left:96px;bottom:84px;font:600 24px Inter;color:#9DBBE3;letter-spacing:.04em">insightance.ai</div>
</div></body></html>'''
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); pg = b.new_page(viewport={'width': 1200, 'height': 630})
    t = pathlib.Path(__file__).parent / '_og.html'; t.write_text(HTML, encoding='utf-8')
    pg.goto(t.as_uri()); pg.wait_for_timeout(600)
    pg.screenshot(path=str(R / 'docs/images/og-insightance.png')); b.close(); t.unlink()
print('ok')
