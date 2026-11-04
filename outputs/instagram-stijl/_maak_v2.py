"""Stijl v2 voor @insightance.ai (2026-11-04): mix van A, B en C met wisselende kleurensets.
Vast (de rode lijn): opbouw, letters, bovenbalk + teller, logo + handle onderaan. Navy komt het vaakst terug.
Wisselt per post: de kleurenset."""
import pathlib
from playwright.sync_api import sync_playwright

D = pathlib.Path(__file__).parent
FONTS = (D.parent.parent / 'docs' / 'fonts').as_uri()

# kleurensets: cover-achtergrond, cover-tekst, accent, binnen-achtergrond, binnen-tekst, lopende tekst, markering
PAL = {
    'navy':   dict(cbg='#17345F', cfg='#FFFFFF', acc='#5B8CFF', ibg='#F5F8FC', ifg='#17345F', body='#3B5478', mark='#C9DAFF'),
    'zwart':  dict(cbg='#111111', cfg='#FFFFFF', acc='#FF4D3D', ibg='#F7F4EF', ifg='#111111', body='#44403C', mark='#FFC9C2'),
    'blauw':  dict(cbg='#1F5EFF', cfg='#FFFFFF', acc='#FFD84D', ibg='#FFFFFF', ifg='#17345F', body='#3B5478', mark='#FFEFA8'),
    'groen':  dict(cbg='#153B2E', cfg='#FFFFFF', acc='#B6F36B', ibg='#F2F6EE', ifg='#153B2E', body='#3F5A4C', mark='#DDF7BD'),
    'creme':  dict(cbg='#F3EDE2', cfg='#17345F', acc='#E2572B', ibg='#FBF8F3', ifg='#17345F', body='#4A4A4A', mark='#FFD9C9'),
    'rood':   dict(cbg='#C8372D', cfg='#FFFFFF', acc='#FFE1D6', ibg='#FFF7F3', ifg='#2A1512', body='#5A3A34', mark='#FFD2C4'),
    'paars':  dict(cbg='#2D1B5A', cfg='#FFFFFF', acc='#F59BD0', ibg='#F7F4FD', ifg='#2D1B5A', body='#4E4470', mark='#F6CDE6'),
}


def logo(bar, curve, size=40):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 44 44" fill="none"><rect x="19" y="6" width="6" height="32" rx="1" fill="{bar}"/>'
            f'<path d="M8 36 Q14 28 22 22 Q30 16 36 8" stroke="{curve}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
            f'<circle cx="8" cy="36" r="2.8" fill="{curve}"/><circle cx="36" cy="8" r="2.8" fill="{curve}"/></svg>')


def css(p):
    return f"""
@font-face{{font-family:Inter;font-weight:100 900;src:url('{FONTS}/inter-latin.woff2')}}
@font-face{{font-family:Playfair;font-weight:400 900;src:url('{FONTS}/playfair-latin.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
.s{{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:Inter}}
.top,.bot{{position:absolute;left:90px;right:90px;display:flex;justify-content:space-between;align-items:center;font:600 26px Inter;letter-spacing:.14em}}
.top{{top:80px}} .bot{{bottom:76px}}
.brand{{display:flex;align-items:center;gap:14px;letter-spacing:.02em}}
.mid{{position:absolute;left:90px;right:90px;top:50%;transform:translateY(-50%)}}
.dark{{background:{p['cbg']};color:{p['cfg']}}} .dark .top,.dark .bot{{color:{p['cfg']};opacity:.8}}
.light{{background:{p['ibg']};color:{p['ifg']}}} .light .top,.light .bot{{color:{p['ifg']};opacity:.75}}
h1{{font:800 116px/1.0 Inter;letter-spacing:-.035em}}
h1 em{{font-style:normal;color:{p['acc']}}}
.q{{font:700 220px/0.6 Playfair;color:{p['acc']};height:110px}}
h1.myth{{font:700 104px/1.06 Playfair;letter-spacing:-.01em}}
h2{{font:700 84px/1.1 Playfair}}
mark{{background:linear-gradient(transparent 62%, {p['mark']} 62%);color:inherit}}
.lab{{display:inline-block;font:700 24px Inter;letter-spacing:.16em;text-transform:uppercase;color:{p['ibg']};background:{p['ifg']};padding:12px 22px;border-radius:40px;margin-bottom:38px}}
p{{font:400 40px/1.45 Inter;margin-top:40px}}
.dark p{{opacity:.85}} .light p{{color:{p['body']}}}
.stat{{font:700 300px/1 Playfair}} .stat span{{color:{p['acc']};margin-left:16px}}
.light .stat span{{color:{p['ifg']};opacity:.35}}
.src{{font:400 24px Inter;margin-top:32px;opacity:.7}}
.pill{{display:inline-block;border:3px solid currentColor;border-radius:60px;padding:16px 30px;font:700 30px Inter;margin-top:56px}}
"""


def frame(p, cls, label, i, n, inner, swipe=False):
    dark = cls == 'dark'
    bar, curve = (p['cfg'], p['acc']) if dark else (p['ifg'], p['ifg'])
    top = f'<div class="top"><span>{label}</span><span>{i}/{n}</span></div>' if n else f'<div class="top"><span>{label}</span><span></span></div>'
    bot = f'<div class="bot"><span class="brand">{logo(bar, curve)}@insightance.ai</span>{"<span>SWIPE →</span>" if swipe else ""}</div>'
    return f'<div class="s {cls}">{top}<div class="mid">{inner}</div>{bot}</div>'


# volledige carrousel (Automation Simplified ep. 2)
def carousel(p):
    L, n = 'AUTOMATION SIMPLIFIED', 5
    return [
        frame(p, 'dark', L, 1, n, '<h1>Is AI the same thing as <em>automation?</em></h1><p>Most people use the words interchangeably. They shouldn\'t.</p>', swipe=True),
        frame(p, 'light', L, 2, n, '<div class="lab">Automation</div><h2><mark>Follows a script.</mark></h2><p>Same steps, every time, no matter what. It sends the same reminder email to every customer on day three.</p>'),
        frame(p, 'light', L, 3, n, '<div class="lab">AI</div><h2><mark>Makes a judgment call.</mark></h2><p>It looks at the situation first. It decides which customers actually need a reminder today, and writes each one a different message.</p>'),
        frame(p, 'light', L, 4, n, '<div class="stat">40<span>%</span></div><p style="font-size:46px;font-weight:600">of self-proclaimed "AI startups" in Europe turned out to have barely any AI at all.</p><div class="src">Source: MMC Ventures, 2,830 startups</div>'),
        frame(p, 'dark', L, 5, n, '<h1>Just automation with better <em>marketing.</em></h1><div class="pill">Follow for AI without the hype ⚡</div>'),
    ]


# covers voor het profielgrid (bestaande LinkedIn-onderwerpen)
GRID = [
    ('navy',  'as',   'Is AI the same thing as <em>automation?</em>'),
    ('zwart', 'myth', 'AI automation isn\'t secure enough.'),
    ('groen', 'as',   'The 80/20 of your <em>busywork.</em>'),
    ('creme', 'myth', 'I\'m not ready for this yet.'),
    ('navy',  'as',   'A spreadsheet hack isn\'t a <em>system.</em>'),
    ('blauw', 'as',   'No, AI is not coming for your <em>job.</em>'),
    ('rood',  'as',   'Automation isn\'t <em>"set and forget."</em>'),
    ('navy',  'myth', 'It\'s too expensive for a business my size.'),
    ('paars', 'as',   'The hidden cost of <em>free</em> tools.'),
]


def cover(pal, kind, title):
    p = PAL[pal]
    if kind == 'myth':
        return css(p), frame(p, 'dark', 'MYTH CHECK', 1, 0, f'<div class="q">“</div><h1 class="myth">{title}</h1>', swipe=True)
    return css(p), frame(p, 'dark', 'AUTOMATION SIMPLIFIED', 1, 0, f'<h1>{title}</h1>', swipe=True)


def shoot(pg, style, body, path):
    tmp = D / '_tmp.html'
    tmp.write_text(f'<html><head><meta charset="utf-8"><style>{style}</style></head><body>{body}</body></html>', encoding='utf-8')
    pg.goto(tmp.as_uri()); pg.wait_for_timeout(200)
    pg.locator('.s').screenshot(path=str(path))


OUT = D / 'v2'
OUT.mkdir(exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome')
    pg = b.new_page(viewport={'width': 1080, 'height': 1350})
    for k, (pal, kind, title) in enumerate(GRID, 1):
        st, body = cover(pal, kind, title)
        shoot(pg, st, body, OUT / f'grid-{k}.png')
    for pal in ('navy', 'zwart', 'groen'):
        for i, body in enumerate(carousel(PAL[pal]), 1):
            shoot(pg, css(PAL[pal]), body, OUT / f'carrousel-{pal}-{i}.png')

    def img(name, w):
        return f'<img style="width:{w}px" src="{(OUT / name).as_uri()}">'
    # profielgrid (zoals Instagram het toont: 3 kolommen, 4:5)
    grid = ''.join(img(f'grid-{k}.png', 300) for k in range(1, 10))
    car = ''.join(f'<div class="t">Carrousel in kleurenset "{pal}"</div><div class="row">' + ''.join(img(f'carrousel-{pal}-{i}.png', 230) for i in range(1, 6)) + '</div>' for pal in ('navy', 'zwart', 'groen'))
    page = f'''<html><head><style>body{{margin:0;background:#E9EDF3;font:600 30px Segoe UI;color:#17345F}}
.w{{display:flex;gap:60px;padding:40px}} .g{{display:grid;grid-template-columns:repeat(3,300px);gap:4px;background:#fff;padding:4px}}
.row{{display:flex;gap:12px;margin-bottom:30px}} .row img{{border-radius:8px}} .t{{margin:0 0 14px 2px}}</style></head>
<body><div class="w"><div><div class="t">Zo ziet je profiel eruit</div><div class="g">{grid}</div></div><div>{car}</div></div></body></html>'''
    (D / '_tmp.html').write_text(page, encoding='utf-8')
    pg = b.new_page(viewport={'width': 2300, 'height': 1500})
    pg.goto((D / '_tmp.html').as_uri()); pg.wait_for_timeout(600)
    pg.locator('.w').screenshot(path=str(D / '_overzicht-v2.png'))
    b.close()
(D / '_tmp.html').unlink()
