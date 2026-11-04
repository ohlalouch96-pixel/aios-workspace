"""Drie stijlvoorbeelden voor Instagram-carrousels (@insightance.ai), 2026-11-04.
Zelfde post (Automation Simplified ep. 2) in drie stijlen, 1080x1350 (4:5)."""
import pathlib
from playwright.sync_api import sync_playwright

D = pathlib.Path(__file__).parent
FONTS = (D.parent.parent / 'docs' / 'fonts').as_uri()
NAVY, MID, BRIGHT, LIGHT, PALE, SOFT = '#17345F', '#3D6AA8', '#1F5EFF', '#9DBBE3', '#EAF1FB', '#F5F8FC'


def logo(bar, curve, size=44):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 44 44" fill="none"><rect x="19" y="6" width="6" height="32" rx="1" fill="{bar}"/>'
            f'<path d="M8 36 Q14 28 22 22 Q30 16 36 8" stroke="{curve}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
            f'<circle cx="8" cy="36" r="2.8" fill="{curve}"/><circle cx="36" cy="8" r="2.8" fill="{curve}"/></svg>')


BASE = f"""
@font-face{{font-family:Inter;font-weight:100 900;src:url('{FONTS}/inter-latin.woff2')}}
@font-face{{font-family:Playfair;font-weight:400 900;src:url('{FONTS}/playfair-latin.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
.s{{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:Inter;padding:96px 90px}}
.top,.bot{{position:absolute;left:90px;right:90px;display:flex;justify-content:space-between;align-items:center;font:600 26px Inter;letter-spacing:.14em}}
.top{{top:80px}} .bot{{bottom:76px}}
.brand{{display:flex;align-items:center;gap:14px;letter-spacing:.02em;font-weight:600}}
"""

# Inhoud: dezelfde vijf slides voor alle stijlen
SLIDES = [
    dict(kind='cover', title='Is AI the same thing as automation?', sub='Most people use the words interchangeably. They shouldn\'t.'),
    dict(kind='text', label='Automation', title='Follows a script.', body='Same steps, every time, no matter what. It sends the same reminder email to every customer on day three.'),
    dict(kind='text', label='AI', title='Makes a judgment call.', body='It looks at the situation first. It decides which customers actually need a reminder today, and writes each one a different message.'),
    dict(kind='stat', stat='40%', body='of self-proclaimed "AI startups" in Europe turned out to have barely any AI at all.', src='Source: MMC Ventures, 2,830 startups'),
    dict(kind='end', title='Just automation with better marketing.', body='Follow for AI automation without the hype ⚡'),
]


# ---------- Stijl A: navy, rustig, Playfair (doorlopend met LinkedIn) ----------
def style_a(sl, i, n):
    css = BASE + f"""
.s{{background:{NAVY};color:#fff}}
.top{{color:{LIGHT}}} .bot{{color:{LIGHT}}}
.mid{{position:absolute;left:90px;right:90px;top:50%;transform:translateY(-50%)}}
h1{{font:700 92px/1.08 Playfair;letter-spacing:-.01em}}
h2{{font:700 84px/1.1 Playfair}}
.lab{{display:inline-block;font:600 26px Inter;letter-spacing:.2em;text-transform:uppercase;color:{LIGHT};border-left:4px solid {BRIGHT};padding-left:18px;margin-bottom:36px}}
p{{font:400 40px/1.45 Inter;color:#D6E2F3;margin-top:40px}}
.stat{{font:700 300px/1 Playfair;color:#fff}} .stat span{{color:{BRIGHT};margin-left:18px}}
.src{{font:400 24px Inter;color:{LIGHT};margin-top:36px;letter-spacing:.02em}}
.swipe{{color:#fff;letter-spacing:.06em}}
"""
    top = f'<div class="top"><span>AUTOMATION SIMPLIFIED</span><span>{i}/{n}</span></div>'
    bot = f'<div class="bot"><span class="brand">{logo("#fff", LIGHT, 40)}@insightance.ai</span>{"<span class=swipe>SWIPE →</span>" if sl["kind"]=="cover" else ""}</div>'
    k = sl['kind']
    if k == 'cover':
        mid = f'<h1>{sl["title"]}</h1><p>{sl["sub"]}</p>'
    elif k == 'text':
        mid = f'<div class="lab">{sl["label"]}</div><h2>{sl["title"]}</h2><p>{sl["body"]}</p>'
    elif k == 'stat':
        mid = f'<div class="stat">40<span>%</span></div><p style="color:#fff;font-size:46px">{sl["body"]}</p><div class="src">{sl["src"]}</div>'
    else:
        mid = f'<h2>{sl["title"]}</h2><p>{sl["body"]}</p>'
    return css, f'<div class="s">{top}<div class="mid">{mid}</div>{bot}</div>'


# ---------- Stijl B: licht, zoals de website, blauwe markering ----------
def style_b(sl, i, n):
    css = BASE + f"""
.s{{background:{SOFT};color:{NAVY}}}
.s:before{{content:'';position:absolute;left:90px;top:0;bottom:0;width:3px;background:{BRIGHT};opacity:.9}}
.top{{color:{MID};left:130px}} .bot{{color:{NAVY};left:130px}}
.mid{{position:absolute;left:130px;right:90px;top:50%;transform:translateY(-50%)}}
h1{{font:700 90px/1.1 Playfair}}
h2{{font:700 82px/1.12 Playfair}}
mark{{background:linear-gradient(transparent 62%, #C9DAFF 62%);color:inherit}}
.lab{{display:inline-block;font:600 24px Inter;letter-spacing:.16em;text-transform:uppercase;color:#fff;background:{BRIGHT};padding:12px 22px;border-radius:40px;margin-bottom:38px}}
p{{font:400 40px/1.45 Inter;color:#3B5478;margin-top:40px}}
.card{{background:#fff;border:1px solid #DCE6F4;border-radius:28px;padding:64px 60px;box-shadow:0 20px 50px rgba(23,52,95,.08)}}
.stat{{font:800 260px/1 Inter;color:{BRIGHT};letter-spacing:-.04em}}
.src{{font:400 24px Inter;color:{MID};margin-top:30px}}
.swipe{{color:{BRIGHT}}}
"""
    top = f'<div class="top"><span>AUTOMATION SIMPLIFIED</span><span>{i}/{n}</span></div>'
    bot = f'<div class="bot"><span class="brand">{logo(NAVY, BRIGHT, 40)}@insightance.ai</span>{"<span class=swipe>SWIPE →</span>" if sl["kind"]=="cover" else ""}</div>'
    k = sl['kind']
    if k == 'cover':
        mid = '<h1>Is AI the same thing as <mark>automation?</mark></h1>' + f'<p>{sl["sub"]}</p>'
    elif k == 'text':
        mid = f'<div class="lab">{sl["label"]}</div><h2><mark>{sl["title"]}</mark></h2><p>{sl["body"]}</p>'
    elif k == 'stat':
        mid = f'<div class="card"><div class="stat">40%</div><p style="color:{NAVY};font-size:44px;margin-top:24px">{sl["body"]}</p><div class="src">{sl["src"]}</div></div>'
    else:
        mid = f'<h2>Just automation with better <mark>marketing.</mark></h2><p>{sl["body"]}</p>'
    return css, f'<div class="s">{top}<div class="mid">{mid}</div>{bot}</div>'


# ---------- Stijl C: brutaal, groot Inter, felblauwe cover (meer schuren) ----------
def style_c(sl, i, n):
    k = sl['kind']
    dark = k in ('cover', 'end')
    bg, fg, sub = (BRIGHT, '#fff', '#DCE6FF') if dark else ('#fff', NAVY, '#3B5478')
    css = BASE + f"""
.s{{background:{bg};color:{fg}}}
.top,.bot{{color:{fg};opacity:.85}}
.mid{{position:absolute;left:90px;right:90px;top:50%;transform:translateY(-50%)}}
h1{{font:800 112px/1.0 Inter;letter-spacing:-.035em}}
h2{{font:800 100px/1.02 Inter;letter-spacing:-.03em}}
.num{{font:800 30px Inter;color:{BRIGHT};letter-spacing:.1em;margin-bottom:28px}}
p{{font:500 40px/1.42 Inter;color:{sub};margin-top:44px}}
.stat{{font:900 340px/0.9 Inter;letter-spacing:-.06em;color:{NAVY}}} .stat span{{color:{BRIGHT}}}
.src{{font:500 24px Inter;color:#6B7F9E;margin-top:30px}}
.bar{{width:120px;height:14px;background:{BRIGHT};margin-bottom:46px}}
.pill{{display:inline-block;border:3px solid #fff;border-radius:60px;padding:16px 30px;font:700 30px Inter;margin-top:56px}}
"""
    top = f'<div class="top"><span>AUTOMATION SIMPLIFIED</span><span>{i}/{n}</span></div>'
    bot = f'<div class="bot"><span class="brand">{logo(fg, "#fff" if dark else BRIGHT, 40)}@insightance.ai</span>{"<span>SWIPE →</span>" if k=="cover" else ""}</div>'
    if k == 'cover':
        mid = f'<h1>Is AI the same thing as automation?</h1><p>{sl["sub"]}</p>'
    elif k == 'text':
        mid = f'<div class="bar"></div><div class="num">{sl["label"].upper()}</div><h2>{sl["title"]}</h2><p>{sl["body"]}</p>'
    elif k == 'stat':
        mid = f'<div class="stat">40<span>%</span></div><p style="color:{NAVY};font-size:46px;font-weight:600">{sl["body"]}</p><div class="src">{sl["src"]}</div>'
    else:
        mid = f'<h2>Just automation with better marketing.</h2><div class="pill">Follow for AI without the hype ⚡</div>'
    return css, f'<div class="s">{top}<div class="mid">{mid}</div>{bot}</div>'


STYLES = {'A-navy': style_a, 'B-licht': style_b, 'C-brutaal': style_c}

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    pg = b.new_page(viewport={'width': 1080, 'height': 1350})
    for name, fn in STYLES.items():
        out = D / name
        out.mkdir(exist_ok=True)
        for i, sl in enumerate(SLIDES, 1):
            css, body = fn(sl, i, len(SLIDES))
            tmp = D / '_tmp.html'
            tmp.write_text(f'<html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>', encoding='utf-8')
            pg.goto(tmp.as_uri()); pg.wait_for_timeout(250)
            pg.locator('.s').screenshot(path=str(out / f'slide-{i}.png'))
    # overzicht: per stijl een rij van 5 slides
    rows = ''.join(
        f'<div class="r"><div class="t">Stijl {n[0]}: {n[2:]}</div><div class="g">' +
        ''.join(f'<img src="{(D / n / f"slide-{i}.png").as_uri()}">' for i in range(1, 6)) + '</div></div>'
        for n in STYLES)
    ov = D / '_tmp.html'
    ov.write_text(f'<html><head><style>body{{margin:0;background:#E9EDF3;font:600 34px Segoe UI}} .w{{padding:40px}} .r{{margin-bottom:46px}} .t{{margin:0 0 16px 6px;color:#17345F}} .g{{display:flex;gap:18px}} img{{width:360px;border-radius:10px;box-shadow:0 6px 20px rgba(0,0,0,.12)}}</style></head><body><div class="w">{rows}</div></body></html>', encoding='utf-8')
    pg = b.new_page(viewport={'width': 1960, 'height': 1600})
    pg.goto(ov.as_uri()); pg.wait_for_timeout(600)
    pg.locator('.w').screenshot(path=str(D / '_overzicht.png'))
    b.close()
(D / '_tmp.html').unlink()
