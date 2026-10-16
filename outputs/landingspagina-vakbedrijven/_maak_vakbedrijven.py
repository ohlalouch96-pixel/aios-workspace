"""Bouwt docs/vakbedrijven.html (landingspagina voor installateurs, loodgieters, schilders, stukadoors en aannemers).
Zelfde opbouw en stijl als webshops.html. Alleen Nederlands, geen taalknop.
Alleen lokaal als voorbeeld; niet committen zonder akkoord van Oussama."""
import pathlib, re

DOCS = pathlib.Path(r'C:\Users\oussa\Downloads\aios-starter-kit\aios-starter-kit\docs')
src = (DOCS / 'resultaten.html').read_text(encoding='utf-8')
ws = (DOCS / 'webshops.html').read_text(encoding='utf-8')

# ---------- onderdelen uit resultaten.html ----------
head = src[:src.rindex('</style>', 0, src.index('<body>'))]
header = src[src.index('<template id="logo-svg">'):src.index('<main>')]
footer = src[src.index('<footer>'):src.index('<script>', src.index('<footer>'))]
cookie = src[src.index('<div class="ck" id="ck"'):]

TITLE = 'Voor vakbedrijven | Insightance'
DESC = 'Offertes in één klik voor installateurs, loodgieters, schilders, stukadoors en aannemers. Insightance bouwt een offertetool met jouw logo, prijzen en voorwaarden.'
head = re.sub(r'<title>[^<]*</title>', f'<title>{TITLE}</title>', head)
head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{DESC}">', head)
head = head.replace('https://insightance.ai/resultaten.html', 'https://insightance.ai/vakbedrijven.html')
head = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{TITLE}">', head)
head = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{DESC}">', head)
head = head.replace('<meta property="og:locale" content="en_US">', '<meta property="og:locale" content="nl_NL">')
head = re.sub(r'\s*<meta property="og:locale:alternate" content="[^"]*">', '', head)
head = re.sub(r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{TITLE}">', head)
head = head.replace('https://insightance.ai/images/og-insightance.png', 'https://insightance.ai/images/og-vakbedrijven.png')
head = re.sub(r'<meta property="og:image:alt" content="[^"]*">', '<meta property="og:image:alt" content="Insightance voor vakbedrijven: offertes in één klik">', head)
head = re.sub(r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{DESC}">', head)

# alleen Nederlands: taalknop eruit
header = header.replace('href="./#services"', 'href="./"')
header = re.sub(r'\s*<div class="lang"[^>]*>.*?</div>', '', header)
assert 'class="lang"' not in header

# ---------- gedeelde stijl van de webshops-pagina (zonder de webshop-specifieke blokken) ----------
ws_css = ws[ws.index('  /* ===== webshops-landingspagina'):ws.rindex('</style>', 0, ws.index('<body>'))]
blocks = ws_css.split('\n\n')
SKIP = ('/* voorbeeldmail', '/* tijdlijn', '/* wat je krijgt', '/* bewijs */', '/* rekentool */')
shared = '\n\n'.join(b for b in blocks if not b.strip().startswith(SKIP) and not b.strip().startswith('@media'))
shared = shared.replace('/* ===== webshops-landingspagina (2026-10-13) ===== */', '/* ===== vakbedrijven-landingspagina (2026-10-13), basis gelijk aan webshops ===== */')

CSS = shared + r'''

  /* voorbeeldofferte van een verzonnen vakbedrijf "Klaverveld Vakwerk", eigen kleuren */
  .docwrap { justify-self: center; width: min(100%, 460px); display: grid; gap: 14px; position: relative; }
  .doc { --k: #1E4A3F; --k2: #E3A23B; --kt: #EEF4F1; background: #fff; border-radius: 14px; border: 1px solid #E3E8EF; box-shadow: 0 1px 0 rgba(23,52,95,.06), 0 30px 70px -40px rgba(23,52,95,.45); overflow: hidden; font-size: 13px; color: #2B3138; position: relative; }
  .doc-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 18px 22px 16px; border-bottom: 3px solid var(--k2); }
  .doc-logo { display: flex; align-items: center; gap: 10px; }
  .doc-logo i { width: 32px; height: 32px; border-radius: 8px; background: var(--k); color: var(--k2); display: grid; place-items: center; font: 700 16px var(--sans); font-style: normal; }
  .doc-logo b { display: block; font-size: 13px; letter-spacing: .14em; color: var(--k); font-weight: 700; }
  .doc-logo small { display: block; font-size: 10.5px; color: #8A9098; letter-spacing: .02em; }
  .doc-ttl { font: 700 15px var(--sans); letter-spacing: .24em; color: var(--k); }
  .doc-meta { display: grid; grid-template-columns: 1fr auto; gap: 4px 16px; padding: 14px 22px; font-size: 12px; color: #6B727B; }
  .doc-meta b { color: #2B3138; font-weight: 600; }
  .doc-meta .r { text-align: right; }
  .doc-lines { margin: 0 22px; border-top: 1px solid #E6EAEE; }
  .doc-line { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px; align-items: baseline; padding: 9px 0; border-bottom: 1px solid #EEF1F4; }
  .doc-line span { min-width: 0; }
  .doc-line small { color: #8A9098; font-size: 11.5px; white-space: nowrap; }
  .doc-line .q { color: #6B727B; font-size: 12px; white-space: nowrap; font-variant-numeric: tabular-nums; }
  .doc-line b { font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; min-width: 76px; text-align: right; }
  .doc-sum { display: grid; gap: 5px; padding: 12px 22px 16px; font-size: 12.5px; }
  .doc-sum div { display: flex; justify-content: space-between; color: #6B727B; }
  .doc-sum div b { color: #2B3138; font-weight: 600; font-variant-numeric: tabular-nums; }
  .doc-sum .tot { margin-top: 4px; padding: 10px 12px; border-radius: 8px; background: var(--kt); color: var(--k); font-size: 14px; }
  .doc-sum .tot b { color: var(--k); font-weight: 700; }
  .doc-foot { padding: 11px 22px; font-size: 11px; color: #8A9098; background: #FAFBFC; border-top: 1px solid #EEF1F4; }
  .docwrap .doc .doc-foot { padding-bottom: 38px; }
  .sentchip { position: relative; z-index: 2; justify-self: start; margin: -40px 0 0 -14px; display: flex; align-items: center; gap: 10px; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 10px 14px; box-shadow: 0 18px 36px -20px rgba(23,52,95,.45); font-size: 13px; }
  .sentchip .ok { width: 26px; height: 26px; border-radius: 50%; background: #2FAE68; color: #fff; display: grid; place-items: center; flex-shrink: 0; }
  .sentchip .ok svg { width: 14px; height: 14px; }
  .sentchip b { display: block; color: var(--navy); font-weight: 600; font-size: 13px; }
  .sentchip small { display: block; color: var(--muted); font-size: 12px; }
  .doccap { display: grid; grid-template-columns: 18px 1fr; gap: 10px; align-items: start; font-size: 13px; line-height: 1.5; color: var(--muted); background: var(--white); border: 1px dashed #C7D6EE; border-radius: 12px; padding: 12px 14px; }
  .doccap svg { width: 18px; height: 18px; color: var(--bright); margin-top: 1px; }
  .doccap b { color: var(--navy); font-weight: 600; }

  /* probeer het zelf */
  html { scroll-padding-top: 0; }
  #probeer, #rekentool { scroll-margin-top: 20px; }
  .try { display: grid; grid-template-columns: minmax(0, .92fr) minmax(0, 1.08fr); gap: 28px; align-items: start; }
  .tform { background: #fff; border: 1px solid var(--line); border-radius: 20px; padding: 28px; display: grid; gap: 18px; box-shadow: 0 40px 80px -60px rgba(23,52,95,.5); }
  .tf { display: grid; gap: 8px; }
  .tf > label, .tf > span { font-size: 12.5px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--faint); }
  .tf2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .tform input[type=text], .tform input[type=email] { width: 100%; font: 500 15px var(--sans); color: var(--navy); background: var(--soft); border: 1px solid var(--line); border-radius: 10px; padding: 11px 13px; outline: none; box-shadow: none; }
  .tform input[type=text]:focus, .tform input[type=email]:focus { border-color: var(--bright); background: #fff; box-shadow: 0 0 0 3px rgba(31,94,255,.15); }
  .jobs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .jobs button { display: flex; align-items: center; gap: 10px; text-align: left; font: 600 14px var(--sans); color: var(--navy); background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 11px 12px; cursor: pointer; transition: border-color .2s, background .2s; }
  .jobs button svg { width: 20px; height: 20px; color: var(--bright); flex-shrink: 0; }
  .jobs button small { display: block; font-size: 11.5px; font-weight: 500; color: var(--faint); }
  .jobs button[aria-pressed="true"] { border-color: var(--bright); background: var(--tint); box-shadow: inset 0 0 0 1px var(--bright); }
  .qty { display: flex; align-items: center; gap: 14px; }
  .qty input[type=range] { flex: 1; accent-color: var(--bright); height: 28px; border: 0; padding: 0; background: transparent; box-shadow: none; }
  .qty output { min-width: 72px; text-align: right; font: 600 16px var(--sans); color: var(--navy); font-variant-numeric: tabular-nums; }
  .tform .btn { width: 100%; justify-content: center; }
  .tform .btn[disabled] { opacity: .7; cursor: default; }
  .tnote { font-size: 12.5px; color: var(--faint); margin: 0; text-align: center; }
  .tprev { position: relative; }
  .tprev .doc { width: 100%; }
  .sent { position: absolute; inset: 0; z-index: 3; border-radius: 14px; background: rgba(255,255,255,.94); backdrop-filter: blur(3px); display: grid; place-content: center; justify-items: center; gap: 10px; padding: 28px; text-align: center; opacity: 0; visibility: hidden; transition: opacity .35s, visibility .35s; }
  .sent.on { opacity: 1; visibility: visible; }
  .sent .okbig { width: 64px; height: 64px; border-radius: 50%; background: #2FAE68; color: #fff; display: grid; place-items: center; box-shadow: 0 0 0 10px rgba(47,174,104,.15); transform: scale(.6); transition: transform .45s var(--ease); }
  .sent.on .okbig { transform: none; }
  .sent .okbig svg { width: 30px; height: 30px; }
  .sent h3 { font-family: var(--serif); font-size: 26px; color: var(--navy); margin-top: 6px; }
  .sent p { margin: 0; color: var(--muted); font-size: 15px; max-width: 34ch; }
  .sent p b { color: var(--navy); font-weight: 600; word-break: break-all; }
  .sent .again { margin-top: 8px; font: 600 14px var(--sans); color: var(--bright); background: none; border: 0; cursor: pointer; border-bottom: 1.5px solid rgba(31,94,255,.3); padding: 0 0 2px; }
  .sent small { font-size: 12px; color: var(--faint); }

  /* rekentool offertes */
  .calc { display: grid; grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr); gap: 0; border-radius: 22px; overflow: hidden; border: 1px solid var(--line); background: #fff; box-shadow: 0 40px 80px -60px rgba(23,52,95,.5); }
  .calc-in { padding: 34px 34px 30px; display: grid; gap: 22px; align-content: start; }
  .fld { display: grid; gap: 10px; }
  .fld label { font-size: 13px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--faint); }
  .fld .row { display: flex; align-items: center; gap: 14px; }
  .fld input[type=range] { flex: 1; accent-color: var(--bright); height: 28px; border: 0; padding: 0; background: transparent; box-shadow: none; }
  .fld .num { width: 110px; display: flex; align-items: center; border: 1px solid var(--line); border-radius: 10px; padding: 0 10px; background: var(--soft); }
  .fld .num span { color: var(--faint); font-weight: 600; font-size: 14px; white-space: nowrap; }
  .fld .num input { width: 100%; border: 0; background: none; font: 600 17px var(--sans); color: var(--navy); padding: 10px 4px; text-align: right; font-variant-numeric: tabular-nums; outline: none; box-shadow: none; }
  .calc-note { font-size: 12.5px; color: var(--faint); margin: 0; }
  .calc-out { background: var(--navy); color: #fff; padding: 34px; display: grid; gap: 18px; align-content: center; position: relative; isolation: isolate; }
  .calc-out::before { content: ""; position: absolute; inset: 0; z-index: -1; background: radial-gradient(70% 80% at 100% 0%, rgba(31,94,255,.45), transparent 70%); }
  .o-row { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,.14); font-size: 15px; color: rgba(255,255,255,.78); }
  .o-row b { font-size: 20px; color: #fff; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .o-big { display: grid; gap: 6px; }
  .o-big small { font-size: 12.5px; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; color: var(--mid-on-dark); }
  .o-big b { font-family: var(--serif); font-size: clamp(30px, 3.4vw, 42px); font-weight: 600; line-height: 1.1; font-variant-numeric: tabular-nums; }
  .o-big span { font-size: 14px; color: rgba(255,255,255,.7); }
  .calc-out .btn { justify-self: start; margin-top: 4px; }

  /* bewijs: één grote tegel met MHL en de quote van Mohammed */
  .mhl { position: relative; overflow: hidden; isolation: isolate; display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr); gap: 36px; align-items: stretch; background: var(--navy); color: #fff; border-radius: 22px; padding: 36px; }
  .mhl::before { content: ""; position: absolute; inset: 0; z-index: -1; background: radial-gradient(60% 70% at 100% 0%, rgba(31,94,255,.45), transparent 70%); }
  .mhl-l { display: grid; gap: 16px; align-content: start; }
  .mhl .k { display: block; font-size: 12px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--mid-on-dark); }
  .mhl-l > b { font-size: 21px; line-height: 1.35; color: #fff; }
  .mq { margin: 0; display: grid; gap: 14px; align-content: center; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.12); border-radius: 18px; padding: 32px; }
  .mq-n { font-family: var(--serif); font-size: 64px; line-height: 1; color: #fff; font-weight: 600; }
  .mq-l { font-size: 13px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--mid-on-dark); margin-top: -4px; }
  .mq blockquote { margin: 8px 0 0; font-family: var(--serif); font-style: italic; font-size: clamp(21px, 2vw, 25px); line-height: 1.4; color: #fff; }
  .mq blockquote::before { content: "“"; } .mq blockquote::after { content: "”"; }
  .mq figcaption { display: flex; align-items: center; gap: 12px; margin-top: 4px; }
  .mq .av { width: 40px; height: 40px; border-radius: 50%; background: var(--bright); color: #fff; display: grid; place-items: center; font-weight: 700; }
  .mq figcaption b { display: block; font-size: 15px; color: #fff; }
  .mq figcaption small { display: block; font-size: 13px; color: var(--mid-on-dark); }
  @media (max-width: 980px) { .mhl { grid-template-columns: 1fr; gap: 24px; } }
  @media (max-width: 560px) { .mhl { padding: 24px 20px; } .mq { padding: 24px 20px; } .mq-n { font-size: 52px; } }
  .mhl .ba { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 14px; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.12); border-radius: 14px; padding: 16px 18px; }
  .ba div { display: grid; gap: 2px; }
  .ba small { font-size: 11.5px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--mid-on-dark); }
  .ba b { font-family: var(--serif); font-size: 30px; line-height: 1.1; color: #fff; font-weight: 600; }
  .ba .was b { color: rgba(255,255,255,.55); text-decoration: line-through; text-decoration-thickness: 2px; text-decoration-color: rgba(255,255,255,.35); }
  .ba .arr { width: 34px; height: 34px; border-radius: 50%; background: var(--bright); display: grid; place-items: center; }
  .ba .arr svg { width: 16px; height: 16px; }
  .ba .now { text-align: right; }
  .mbuilt { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
  .mbuilt li { display: grid; grid-template-columns: 20px 1fr; gap: 10px; font-size: 14.5px; color: rgba(255,255,255,.85); }
  .mbuilt svg { width: 18px; height: 18px; color: #6FD39B; margin-top: 3px; }
  .mhl .go { color: #fff; text-decoration: none; border-bottom: 1.5px solid rgba(255,255,255,.35); justify-self: start; padding-bottom: 2px; }
  .mhl .go:hover { border-color: #fff; }

  /* dit kan ook */
  .also { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
  .al { background: linear-gradient(165deg, var(--tint) 0%, #fff 62%); border: 1px solid #CFDDF2; border-radius: 18px; padding: 24px; display: grid; gap: 10px; align-content: start; box-shadow: 0 22px 44px -38px rgba(23,52,95,.55); }
  .al .aic { width: 42px; height: 42px; border-radius: 12px; background: var(--bright); color: #fff; display: grid; place-items: center; }
  .al .aic svg { width: 21px; height: 21px; }
  .al h3 { font-family: var(--sans); font-size: 17px; font-weight: 600; margin-top: 4px; }
  .al p { font-size: 14.5px; color: var(--muted); margin: 0; }
  .al q { font-size: 13px; color: var(--navy); font-style: normal; background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 9px 11px; quotes: none; margin-top: 2px; }

  @media (max-width: 980px) {
    .facts, .try, .calc { grid-template-columns: 1fr; }
    .also { grid-template-columns: 1fr 1fr; }
    .sentchip { margin-left: 12px; }
  }
  @media (max-width: 560px) {
    .ws-sec { padding-block: 48px; }
    #probeer, #rekentool { scroll-margin-top: 44px; }
    .also, .tf2 { grid-template-columns: 1fr; }
    .tform { padding: 22px 18px; }
    .calc-in, .calc-out { padding: 24px 20px; }
    .fld .num { width: 104px; }
    .doc-top, .doc-meta, .doc-sum, .doc-foot { padding-left: 16px; padding-right: 16px; }
    .doc-lines { margin: 0 16px; }
    .doc-line { grid-template-columns: minmax(0, 1fr) auto; }
    .doc-line .q { grid-column: 1; grid-row: 2; }
    .doc-line b { grid-row: 1 / span 2; align-self: center; }
  }
'''

CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>'
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
INFO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>'
I_FLAME = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3c1 3.5 5 5.5 5 10a5 5 0 0 1-10 0c0-2.2 1-3.6 2.2-4.8.3 1.6 1 2.6 2 3 0-3 .3-5.6.8-8.2z"/></svg>'
I_DROP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3.5s6 6.4 6 10.5a6 6 0 0 1-12 0c0-4.1 6-10.5 6-10.5z"/></svg>'
I_BRUSH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="3" width="14" height="6" rx="1.5"/><path d="M18 6h2v5h-8v3"/><rect x="10.5" y="14" width="3" height="7" rx="1"/></svg>'
I_TROWEL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 15 14 4l6 6-11 11H3z"/><path d="M14 4l3-1 4 4-1 3"/></svg>'
I_INVOICE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l3 3v15l-2.5-1.5L13 21l-2.5-1.5L8 21l-2-1.5z"/><path d="M9 9h6M9 13h6"/></svg>'
I_BELL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20a2 2 0 0 0 4 0"/></svg>'
I_CHAT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/></svg>'
I_STAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"><path d="m12 3 2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8 6.6 19.7l1.1-6.1L3.2 9.4l6.1-.8z"/></svg>'

DOC_TOP = '''<div class="doc-top"><span class="doc-logo"><i>K</i><span><b>KLAVERVELD</b><small>Installatie · Onderhoud · Renovatie</small></span></span><span class="doc-ttl">OFFERTE</span></div>'''

MAIN = f'''<main>
  <svg class="dataline" id="dataline" aria-hidden="true"><path class="track" id="dl-track"/><path class="draw" id="dl-draw"/><g id="dl-dot"><circle class="halo" r="10"/><circle class="head" r="4.5"/></g></svg>
  <section class="rhero">
    <canvas class="bgflow"></canvas>
    <div class="wrap">
      <div class="rhero-copy">
        <div class="eyebrow eyebrow-lines">Voor vakbedrijven</div>
        <h1>Offertes in één klik. <em><span class="u">Zonder Word, Excel of overtypen.</span></em></h1>
        <p>Insightance bouwt een offertetool voor jouw vakbedrijf. Je vult een kort formulier in, drukt op één knop en je klant heeft een nette offerte in zijn inbox. Met jouw logo, prijzen, BTW en voorwaarden.</p>
        <div class="ctas"><a class="btn" href="#probeer">Probeer het zelf</a><a class="link" href="./#contact">Plan een gesprek →</a></div>
        <div class="works"><span>Voor</span><b>installateurs</b>·<b>loodgieters</b>·<b>schilders</b>·<b>stukadoors</b>·<b>aannemers</b></div>
      </div>
      <div class="docwrap rv">
        <div class="doc" aria-label="Voorbeeld van een offerte">
          {DOC_TOP}
          <div class="doc-meta"><span>Voor: <b>Fam. de Vries</b>, Utrecht</span><span class="r">Nr. <b>2026-0147</b></span><span>CV-ketel vervangen</span><span class="r" data-today></span></div>
          <div class="doc-lines">
            <div class="doc-line"><span>HR-combiketel incl. montagemateriaal</span><span class="q">1 ×</span><b>€ 1.495,00</b></div>
            <div class="doc-line"><span>Oude ketel afvoeren</span><span class="q">1 ×</span><b>€ 75,00</b></div>
            <div class="doc-line"><span>Arbeid installateur</span><span class="q">4 uur</span><b>€ 250,00</b></div>
          </div>
          <div class="doc-sum"><div><span>Subtotaal</span><b>€ 1.820,00</b></div><div><span>BTW 21%</span><b>€ 382,20</b></div><div class="tot"><span>Totaal</span><b>€ 2.202,20</b></div></div>
          <div class="doc-foot">Geldig 30 dagen · 50% bij akkoord, 50% na oplevering</div>
        </div>
        <div class="sentchip"><span class="ok">{CHECK}</span><span><b>Verstuurd naar de klant</b><small>1 klik, in plaats van 20 minuten</small></span></div>
        <div class="doccap">{INFO}<span><b>Dit is een voorbeeld.</b> Jouw offertes krijgen je eigen logo, prijzen, voorwaarden en huisstijl.</span></div>
      </div>
    </div>
  </section>

  <section class="ws-sec">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow">Het probleem</div><h2>Je bent vakman, geen typist</h2><p>Overdag sta je op de klus. Offertes maak je daarna: oud bestand openen, gegevens overtypen, prijzen opzoeken, BTW uitrekenen, PDF maken en mailen. Elke keer opnieuw.</p></div>
      <div class="facts">
        <div class="fact rv"><span class="n">20 min</span><b>handwerk per offerte</b><p>Zoveel kostte een offerte bij MHL Installatieservice, voordat er een tool voor kwam.</p></div>
        <div class="fact rv" style="--d:.08s"><span class="n">10–15 uur</span><b>per week terug</b><p>Zoveel winnen ondernemers gemiddeld terug als ze een paar handmatige taken automatiseren.</p></div>
        <div class="fact rv" style="--d:.16s"><span class="n blue">1 klik</span><b>van formulier naar inbox</b><p>Met een offertetool vul je alleen in wat per klus verschilt. De rest gaat vanzelf.</p></div>
      </div>
    </div>
  </section>

  <section class="ws-sec tint" id="probeer">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow">Probeer het zelf</div><h2>Maak in een paar seconden een offerte</h2><p>Kies een klus en vul de gegevens in. De offerte groeit meteen mee. Zo werkt jouw eigen tool straks ook, maar dan met jouw prijzen.</p></div>
      <div class="try">
        <form class="tform rv" id="tform" novalidate>
          <div class="tf2">
            <div class="tf"><label for="t-name">Klant</label><input type="text" id="t-name" value="Fam. Jansen" maxlength="40" autocomplete="off"></div>
            <div class="tf"><label for="t-city">Plaats</label><input type="text" id="t-city" value="Amersfoort" maxlength="30" autocomplete="off"></div>
          </div>
          <div class="tf"><label for="t-mail">E-mail van de klant</label><input type="email" id="t-mail" value="jansen@voorbeeld.nl" maxlength="60" autocomplete="off"></div>
          <div class="tf"><span>Soort klus</span>
            <div class="jobs" role="group" aria-label="Soort klus">
              <button type="button" data-job="ketel" aria-pressed="false">{I_FLAME}<span>CV-ketel<small>vervangen</small></span></button>
              <button type="button" data-job="lek" aria-pressed="false">{I_DROP}<span>Lekkage<small>verhelpen</small></span></button>
              <button type="button" data-job="schilder" aria-pressed="true">{I_BRUSH}<span>Schilderwerk<small>binnen</small></span></button>
              <button type="button" data-job="stuc" aria-pressed="false">{I_TROWEL}<span>Stucwerk<small>wanden</small></span></button>
            </div>
          </div>
          <div class="tf"><label for="t-q" id="t-ql">Arbeidsuren</label><div class="qty"><input type="range" id="t-q" min="4" max="80" step="1" value="16"><output id="t-qo" for="t-q">16 uur</output></div></div>
          <button class="btn" type="submit" id="t-send">Verstuur offerte</button>
          <p class="tnote">Dit is een demo. Er wordt niets echt verstuurd.</p>
        </form>
        <div class="tprev rv" style="--d:.08s">
          <div class="doc" id="t-doc" aria-live="polite">
            {DOC_TOP}
            <div class="doc-meta"><span>Voor: <b id="d-name"></b><span id="d-city"></span></span><span class="r">Nr. <b id="d-nr">2026-0148</b></span><span id="d-job"></span><span class="r" data-today></span></div>
            <div class="doc-lines" id="d-lines"></div>
            <div class="doc-sum" id="d-sum"></div>
            <div class="doc-foot" id="d-foot">Geldig 30 dagen · 50% bij akkoord, 50% na oplevering</div>
          </div>
          <div class="sent" id="t-sent" role="status">
            <span class="okbig">{CHECK}</span>
            <h3>Offerte verstuurd</h3>
            <p>naar <b id="s-mail"></b>, met logo, prijzen, BTW en voorwaarden.</p>
            <small>Zo snel gaat het met je eigen tool. (Demo: er is niets echt verstuurd.)</small>
            <button type="button" class="again" id="t-again">Nog een offerte maken</button>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="ws-sec" id="rekentool">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow">Rekentool</div><h2>Hoeveel tijd kosten offertes jou?</h2><p>Vul in hoeveel offertes je maakt en hoe lang je erover doet. Je ziet direct hoeveel tijd een offertetool je per jaar teruggeeft.</p></div>
      <div class="calc rv">
        <div class="calc-in">
          <div class="fld"><label for="c-n">Offertes per week</label><div class="row"><input type="range" id="r-n" min="1" max="40" step="1" value="5" aria-label="Offertes per week"><div class="num"><input id="c-n" inputmode="numeric" value="5" aria-label="Offertes per week"></div></div></div>
          <div class="fld"><label for="c-m">Minuten per offerte</label><div class="row"><input type="range" id="r-m" min="5" max="90" step="5" value="25" aria-label="Minuten per offerte"><div class="num"><input id="c-m" inputmode="numeric" value="25" aria-label="Minuten per offerte"><span>min</span></div></div></div>
          <div class="fld"><label for="c-r">Wat is een uur van jou waard?</label><div class="row"><input type="range" id="r-r" min="25" max="150" step="5" value="60" aria-label="Uurwaarde in euro"><div class="num"><span>€</span><input id="c-r" inputmode="numeric" value="60" aria-label="Uurwaarde in euro"></div></div></div>
          <p class="calc-note">Gerekend met 46 werkweken per jaar en 90% minder tijd per offerte. Dat is wat MHL Installatieservice haalde met hun offertetool. In een gesprek kijken we naar jouw situatie.</p>
        </div>
        <div class="calc-out" aria-live="polite">
          <div class="o-row"><span>Tijd aan offertes per jaar</span><b id="o-now">96 uur</b></div>
          <div class="o-row"><span>Met een offertetool</span><b id="o-tool">10 uur</b></div>
          <div class="o-big"><small>Je wint per jaar terug</small><b id="o-win">86 uur</b><span id="o-sub">Ruim 10 werkdagen, ter waarde van € 5.175</span></div>
          <a class="btn" href="./#contact">Bespreek jouw situatie</a>
        </div>
      </div>
    </div>
  </section>

  <section class="ws-sec tint">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow">Bewijs</div><h2>Al in gebruik bij een installatiebedrijf</h2><p>MHL Installatieservice maakte elke offerte met de hand. Nu kost het één klik.</p></div>
      <div class="mhl rv">
        <div class="mhl-l">
          <span class="k">Case · Installatietechniek</span>
          <b>MHL Installatieservice: van oud Word-bestand naar één knop.</b>
          <div class="ba"><div class="was"><small>Vroeger</small><b>20 min</b></div><span class="arr">{ARROW}</span><div class="now"><small>Nu</small><b>1 klik</b></div></div>
          <ul class="mbuilt">
            <li>{CHECK}<span>Een eenvoudig webformulier, ook op de telefoon</span></li>
            <li>{CHECK}<span>Standaardprijzen per soort werk</span></li>
            <li>{CHECK}<span>BTW automatisch berekend</span></li>
            <li>{CHECK}<span>PDF met logo, specificaties en betalingsvoorwaarden</span></li>
            <li>{CHECK}<span>Met één klik verstuurd naar de klant</span></li>
          </ul>
          <a class="go" href="resultaten.html#mhl">Lees het volledige verhaal →</a>
        </div>
        <figure class="mq">
          <span class="mq-n">90%</span><span class="mq-l">minder tijd per offerte</span>
          <blockquote>Nu vul ik het formulier in en druk op één knop. De klant heeft de offerte meteen in zijn inbox.</blockquote>
          <figcaption><span class="av">M</span><span><b>Mohammed</b><small>MHL Installatieservice</small></span></figcaption>
        </figure>
      </div>
    </div>
  </section>

  <section class="ws-sec">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow">Dit kan ook</div><h2>Na de offerte stopt het niet</h2><p>De offerte is vaak het begin. Dezelfde aanpak werkt voor ander werk dat elke week terugkomt.</p></div>
      <div class="also">
        <div class="al rv"><span class="aic">{I_INVOICE}</span><h3>Facturen</h3><p>Klus klaar? De factuur staat klaar met de gegevens uit de offerte. Niets meer overtypen.</p><q>Offerte akkoord → factuur klaar</q></div>
        <div class="al rv" style="--d:.06s"><span class="aic">{I_BELL}</span><h3>Onderhoudsherinneringen</h3><p>Klanten krijgen vanzelf bericht als hun ketel of installatie weer aan de beurt is.</p><q>Na 12 maanden → herinnering</q></div>
        <div class="al rv" style="--d:.12s"><span class="aic">{I_CHAT}</span><h3>Aanvragen en klantvragen</h3><p>Aanvragen komen compleet binnen, en vaste vragen worden direct beantwoord.</p><q>Nieuwe aanvraag → alles op een rij</q></div>
        <div class="al rv" style="--d:.18s"><span class="aic">{I_STAR}</span><h3>Reviews vragen</h3><p>Na elke klus vraagt een vriendelijk bericht om een review. Zonder dat jij eraan hoeft te denken.</p><q>Klus afgerond → reviewverzoek</q></div>
      </div>
    </div>
  </section>

  <section class="ws-sec tint">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow">Werkwijze</div><h2>Van gesprek tot werkende tool</h2><p>Je weet vooraf wat het kost. Je betaalt in twee delen, het laatste deel pas als alles werkt.</p></div>
      <div class="wsplit">
        <div class="wcard rv">
          <small>Stap 1</small>
          <b>Begin met een kennismaking</b>
          <p>Een vrijblijvend gesprek van een half uur over hoe jij nu offertes maakt. Je hoeft niets voor te bereiden.</p>
          <a class="btn" href="./#contact">Plan een gesprek</a>
          <span>30 minuten · Vrijblijvend</span>
          <span class="wpill"><span class="pulse"></span><span>Max. 3 nieuwe klanten per maand</span></span>
        </div>
        <ol class="wsteps rv" style="--d:.08s">
          <li><span class="n">1</span><b><span>Kennismaking</span> <span class="tag">Gratis · 30 min</span></b><p>We kijken samen hoe je nu offertes maakt, welke klussen je doet en wat je rekent.</p><small class="wget"><b>Je weet daarna:</b> <span>hoeveel tijd een offertetool jou scheelt.</span></small></li>
          <li><span class="n">2</span><b><span>Voorstel</span> <span class="tag">Gratis</span></b><p>Je krijgt een concreet plan: wat de tool doet, hoe hij eruitziet en wat het kost.</p><small class="wget"><b>Je krijgt:</b> <span>een vaste prijs. Je zit nergens aan vast tot je akkoord geeft.</span></small></li>
          <li><span class="n">3</span><b><span>Bouwen</span> <span class="tag">50% bij akkoord</span></b><p>Insightance bouwt de tool met jouw logo, prijzen en voorwaarden. Jij test hem voordat hij live gaat.</p></li>
          <li><span class="n">4</span><b><span>Live</span> <span class="tag">50% als alles werkt</span></b><p>Werkt alles en ben je tevreden, dan betaal je de tweede helft.</p><small class="wget"><b>Je krijgt:</b> <span>een tool die je elke dag gebruikt, op je laptop en je telefoon.</span></small></li>
        </ol>
      </div>
    </div>
  </section>

  <section class="ws-sec">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow">FAQ</div><h2>Je vragen beantwoord</h2></div>
      <div class="wfaq rv">
        <details><summary><span>Moet ik iets installeren?</span><i>+</i></summary><p>Nee. De tool werkt gewoon in je browser, op je laptop, tablet of telefoon. Dus ook even tussendoor in de bus.</p></details>
        <details><summary><span>Kan ik mijn eigen prijzen en voorwaarden gebruiken?</span><i>+</i></summary><p>Ja, dat is juist de bedoeling. Je standaardprijzen per soort klus staan erin, en per offerte pas je aan wat nodig is. Je logo, voorwaarden en betaalafspraken staan er automatisch op.</p></details>
        <details><summary><span>Rekent de tool ook met 9% BTW?</span><i>+</i></summary><p>Ja. Per regel staat het juiste tarief, bijvoorbeeld 9% op arbeid bij schilder- en stucwerk aan woningen ouder dan twee jaar, en 21% op materiaal. We stellen het in zoals jij het nu ook doet.</p></details>
        <details><summary><span>Hoe snel kan ik ermee werken?</span><i>+</i></summary><p>Meestal binnen enkele weken na akkoord. Hoe sneller ik je prijslijst, logo en voorwaarden heb, hoe sneller je je eerste offerte verstuurt.</p></details>
      </div>
    </div>
  </section>

  <section class="closing">
    <div class="wrap">
      <div class="cbox rv">
        <canvas class="cflow" aria-hidden="true"></canvas>
        <div class="ctext">
          <div class="eyebrow">Jouw vakbedrijf</div>
          <h2>Benieuwd hoeveel tijd jij terugwint?</h2>
          <p>In een gesprek van 30 minuten kijken we hoe jij nu offertes maakt, en laat ik zien hoe jouw tool eruit zou zien.</p>
          <div class="acts"><a class="btn" href="./#contact">Plan een gesprek</a><small>30 minuten · Vrijblijvend</small></div>
        </div>
        <a class="own" href="./#contact">
          <span class="own-plus"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></span>
          <b>Jouw bedrijf als volgende case</b>
          <span class="own-lines" aria-hidden="true"><i></i><i></i><i></i></span>
          <span class="own-go">Start hier</span>
        </a>
      </div>
    </div>
  </section>
</main>

'''

JS = r'''<script>
  try { history.scrollRestoration = 'manual'; } catch (e) {}
  if (!location.hash) { const toTop = () => window.scrollTo(0, 0); toTop(); window.addEventListener('load', toTop); }
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const inView = el => { const r = el.getBoundingClientRect(); return r.bottom > 0 && r.top < window.innerHeight; };
  const $ = id => document.getElementById(id);

  // logo
  const tpl = document.getElementById('logo-svg');
  document.querySelectorAll('.logo[data-bar]').forEach(el => {
    const svg = tpl.content.firstElementChild.cloneNode(true);
    svg.querySelector('.bar').setAttribute('fill', el.dataset.bar);
    svg.querySelector('.curve').setAttribute('stroke', el.dataset.curve);
    svg.querySelectorAll('.dot').forEach(d => d.setAttribute('fill', el.dataset.curve));
    el.prepend(svg);
  });

  const eur = n => '\u20ac\u00a0' + n.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const eur0 = n => '\u20ac\u00a0' + Math.round(n).toLocaleString('nl-NL');
  const fmtQ = q => q.toLocaleString('nl-NL', { maximumFractionDigits: 1 });
  document.querySelectorAll('[data-today]').forEach(el => el.textContent = new Date().toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' }));

  // probeer het zelf: verzonnen bedrijf Klaverveld, prijzen per soort klus
  // regel: [omschrijving, aantal (q = gekozen hoeveelheid), eenheid, prijs, btw]
  const JOBS = {
    ketel: { name: 'CV-ketel vervangen', label: 'Arbeidsuren', unit: 'uur', min: 2, max: 10, step: 1, def: 4,
      lines: q => [['HR-combiketel incl. montagemateriaal', 1, '\u00d7', 1495, 21], ['Oude ketel afvoeren', 1, '\u00d7', 75, 21], ['Arbeid installateur', q, 'uur', 62.5, 21]] },
    lek: { name: 'Lekkage verhelpen', label: 'Arbeidsuren', unit: 'uur', min: .5, max: 6, step: .5, def: 1.5,
      lines: q => [['Voorrijkosten', 1, '\u00d7', 45, 21], ['Lekkage opsporen en verhelpen', q, 'uur', 68, 21], ['Klein materiaal', 1, '\u00d7', 25, 21]] },
    schilder: { name: 'Schilderwerk binnen', label: 'Arbeidsuren', unit: 'uur', min: 4, max: 80, step: 1, def: 16,
      lines: q => [['Schilderwerk, arbeid', q, 'uur', 52.5, 9], ['Verf, kit en afplakmateriaal', 1, '\u00d7', Math.round(60 + q * 7.5), 21]] },
    stuc: { name: 'Wanden stucen', label: 'Aantal m\u00b2', unit: 'm\u00b2', min: 5, max: 200, step: 5, def: 35,
      lines: q => [['Wanden stucen, arbeid', q, 'm\u00b2', 14.5, 9], ['Stucmateriaal en afdekken', q, 'm\u00b2', 3.75, 21], ['Voorrijkosten', 1, '\u00d7', 35, 21]] },
  };
  let job = 'schilder', nr = 148;
  const range = $('t-q');
  function renderDoc() {
    const J = JOBS[job], q = parseFloat(range.value);
    $('t-qo').textContent = fmtQ(q) + ' ' + J.unit;
    $('d-name').textContent = $('t-name').value.trim() || 'Klant';
    const city = $('t-city').value.trim(); $('d-city').textContent = city ? ', ' + city : '';
    $('d-job').textContent = J.name; $('d-nr').textContent = '2026-0' + nr;
    const lines = J.lines(q), btw = {};
    let sub = 0;
    $('d-lines').innerHTML = '';
    lines.forEach(([desc, n, u, p, t]) => {
      const tot = n * p; sub += tot; btw[t] = (btw[t] || 0) + tot * t / 100;
      const row = document.createElement('div'); row.className = 'doc-line';
      const a = document.createElement('span'); a.textContent = desc + ' '; const s = document.createElement('small'); s.textContent = t + '%'; a.append(s);
      const b = document.createElement('span'); b.className = 'q'; b.textContent = u === '\u00d7' ? fmtQ(n) + ' \u00d7' : fmtQ(n) + ' ' + u + ' \u00e0 ' + eur(p);
      const c = document.createElement('b'); c.textContent = eur(tot);
      row.append(a, b, c); $('d-lines').append(row);
    });
    const vat = Object.keys(btw).sort((x, y) => x - y).map(t => `<div><span>BTW ${t}%</span><b>${eur(btw[t])}</b></div>`).join('');
    const total = sub + Object.values(btw).reduce((x, y) => x + y, 0);
    $('d-sum').innerHTML = `<div><span>Subtotaal</span><b>${eur(sub)}</b></div>${vat}<div class="tot"><span>Totaal</span><b>${eur(total)}</b></div>`;
  }
  function setJob(j) {
    job = j; const J = JOBS[j];
    document.querySelectorAll('.jobs button').forEach(b => b.setAttribute('aria-pressed', b.dataset.job === j));
    $('t-ql').textContent = J.label; range.min = J.min; range.max = J.max; range.step = J.step; range.value = J.def;
    renderDoc();
  }
  document.querySelectorAll('.jobs button').forEach(b => b.addEventListener('click', () => setJob(b.dataset.job)));
  ['t-name', 't-city'].forEach(id => $(id).addEventListener('input', renderDoc));
  range.addEventListener('input', renderDoc);
  $('tform').addEventListener('submit', e => {
    e.preventDefault();
    const btn = $('t-send'); btn.disabled = true; btn.textContent = 'Versturen\u2026';
    setTimeout(() => {
      $('s-mail').textContent = $('t-mail').value.trim() || 'de klant';
      $('t-sent').classList.add('on'); btn.disabled = false; btn.textContent = 'Verstuur offerte';
      // op mobiel staat de offerte onder het formulier: daarheen scrollen
      if (window.innerWidth <= 980) $('t-doc').scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
    }, reduce ? 0 : 700);
  });
  $('t-again').addEventListener('click', () => { $('t-sent').classList.remove('on'); nr++; renderDoc(); });
  setJob('schilder');

  // rekentool: offertes per week x minuten, 46 werkweken, 90% minder tijd (MHL)
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const num = id => parseFloat(($(id).value || '0').replace(',', '.').replace(/[^0-9.]/g, '')) || 0;
  function calc() {
    const n = clamp(num('c-n'), 0, 500), m = clamp(num('c-m'), 0, 600), r = clamp(num('c-r'), 0, 1000);
    const now = n * m * 46 / 60, tool = now * .1, win = now - tool, days = win / 8;
    $('o-now').textContent = Math.round(now).toLocaleString('nl-NL') + ' uur';
    $('o-tool').textContent = Math.round(tool).toLocaleString('nl-NL') + ' uur';
    $('o-win').textContent = Math.round(win).toLocaleString('nl-NL') + ' uur';
    const d = Math.floor(days), dt = days - d >= .25 ? 'Ruim ' + d : 'Zo\u2019n ' + Math.round(days);
    $('o-sub').textContent = (days < 1 ? 'Minder dan een werkdag' : dt + (Math.round(days) === 1 && d <= 1 ? ' werkdag' : ' werkdagen')) + ', ter waarde van ' + eur0(win * r);
  }
  [['r-n', 'c-n'], ['r-m', 'c-m'], ['r-r', 'c-r']].forEach(([r, c]) => {
    $(r).addEventListener('input', () => { $(c).value = $(r).value; calc(); });
    $(c).addEventListener('input', () => { const v = num(c); if (v) $(r).value = v; calc(); });
  });
  calc();

  // FAQ: één vraag tegelijk open
  document.querySelectorAll('.wfaq details').forEach(d => d.addEventListener('toggle', () => { if (d.open) document.querySelectorAll('.wfaq details[open]').forEach(o => { if (o !== d) o.open = false; }); }));

  // golvende achtergrond bovenaan + in het blauwe blok
  function waves(cv, dark) {
    const ctx = cv.getContext('2d'); let w = 0, h = 0;
    function size() { const r = cv.getBoundingClientRect(), d = Math.min(2, window.devicePixelRatio || 1); w = r.width; h = r.height; cv.width = w * d; cv.height = h * d; ctx.setTransform(d, 0, 0, d, 0, 0); }
    const yAt = (i, x, t) => h * (dark ? .3 + i * .12 : .25 + i * .1) + Math.sin(x / 160 + t / 2700 + i * .7) * (16 + i * 5) + Math.cos(x / 300 - t / 4000 + i) * 8;
    function draw(t) { ctx.clearRect(0, 0, w, h); for (let i = 0; i < (dark ? 5 : 6); i++) { ctx.beginPath(); for (let x = 0; x <= w; x += 10) { const y = yAt(i, x, t); x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.strokeStyle = dark ? `rgba(157,187,227,${.10 + i * .02})` : `rgba(31,94,255,${.05 + i * .012})`; ctx.lineWidth = 1.2; ctx.stroke(); } }
    size(); window.addEventListener('resize', size);
    if (reduce) { draw(0); return; }
    (function loop(t) { if (inView(cv)) draw(t); requestAnimationFrame(loop); })(0);
  }
  document.querySelectorAll('canvas.bgflow').forEach(cv => waves(cv, false));
  document.querySelectorAll('canvas.cflow').forEach(cv => waves(cv, true));

  // rode draad: start onder de hero, loopt in de lege rechtermarge en eindigt in het blauwe blok onderaan
  (function () {
    const main = document.querySelector('main'), dl = document.getElementById('dataline'), track = document.getElementById('dl-track'), drawP = document.getElementById('dl-draw'), dot = document.getElementById('dl-dot');
    let len = 0, on = false;
    function build() {
      // alleen als er rechts genoeg lege marge is, zodat de lijn nooit door tekst loopt
      on = window.innerWidth > 1100 && (main.clientWidth - 1280) / 2 > 56; dl.style.display = on ? '' : 'none'; if (!on) return;
      const W = main.clientWidth, H = main.offsetHeight, mt = main.getBoundingClientRect().top + window.scrollY, Y = r => r + window.scrollY - mt;
      dl.setAttribute('width', W); dl.setAttribute('height', H); dl.setAttribute('viewBox', `0 0 ${W} ${H}`);
      const R = W - Math.max(36, (W - 1280) / 2 - 44);
      const hero = document.querySelector('.rhero').getBoundingClientRect(), cb = document.querySelector('.cbox').getBoundingClientRect();
      const a0 = Y(hero.bottom) - 30, y2 = Y(cb.top) + cb.height / 2;
      const d = `M ${R} ${a0} L ${R} ${y2 - 60} C ${R} ${y2 - 10}, ${R - 20} ${y2}, ${cb.right - 1} ${y2}`;
      track.setAttribute('d', d); drawP.setAttribute('d', d); len = drawP.getTotalLength(); drawP.style.strokeDasharray = len; update();
    }
    function lenAtY(yy) { let lo = 0, hi = len; for (let k = 0; k < 22; k++) { const m = (lo + hi) / 2; if (drawP.getPointAtLength(m).y < yy) lo = m; else hi = m; } return lo; }
    function update() {
      if (!on || !len) return;
      // de kop van de lijn staat steeds op 60% van de schermhoogte: hij beweegt precies even snel als de pagina
      const mt = main.getBoundingClientRect().top + window.scrollY;
      const yStart = drawP.getPointAtLength(0).y, yEnd = drawP.getPointAtLength(len).y;
      const yHead = window.scrollY + window.innerHeight * .6 - mt;
      const l = yHead <= yStart ? 0 : (yHead >= yEnd ? len : lenAtY(yHead));
      drawP.style.strokeDashoffset = len - l; const pt = drawP.getPointAtLength(l);
      dot.querySelectorAll('circle').forEach(c => { c.setAttribute('cx', pt.x); c.setAttribute('cy', pt.y); }); dot.style.opacity = l > 2 ? 1 : 0;
    }
    window.addEventListener('scroll', update, { passive: true }); window.addEventListener('resize', build); window.addEventListener('load', build);
    if (document.fonts) document.fonts.ready.then(build);
    let lastH = 0; setInterval(() => { const h = main.offsetHeight; if (h !== lastH) { lastH = h; build(); } }, 800);
    build();
  })();

  // nav-rand en WhatsApp-knop
  const nav = document.getElementById('nav'), hero = document.querySelector('.rhero'), fab = document.getElementById('chatfab');
  let lastY = window.scrollY, up = false;
  function onScroll() {
    nav.classList.toggle('scrolled', window.scrollY > 10);
    if (window.scrollY < lastY - 2) up = true; else if (window.scrollY > lastY + 2) up = false; lastY = window.scrollY;
    const pastHero = hero.getBoundingClientRect().bottom < 0, atFooter = document.querySelector('footer').getBoundingClientRect().top < window.innerHeight - 40;
    fab.classList.toggle('show', pastHero && !atFooter && (window.innerWidth > 820 || up));
  }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // blokken schuiven zacht in beeld
  if (!reduce && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; io.unobserve(e.target); e.target.classList.add('rv-in'); setTimeout(() => e.target.classList.remove('rv-wait', 'rv-in'), 1200); }), { rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.rv').forEach(el => { if (el.getBoundingClientRect().top > window.innerHeight) { el.classList.add('rv-wait'); io.observe(el); } });
  }
</script>

'''

page = head + CSS + '</style>\n</head>\n<body>\n\n' + header + MAIN + footer + JS + cookie
out = DOCS / 'vakbedrijven.html'
out.write_text(page, encoding='utf-8', newline='')
print('ok', len(page))
