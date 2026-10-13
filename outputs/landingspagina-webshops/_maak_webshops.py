"""Bouwt docs/webshops.html (landingspagina voor webshops) op basis van de stijl van resultaten.html.
Alleen lokaal als voorbeeld; niet committen zonder akkoord van Oussama."""
import json, pathlib, re

DOCS = pathlib.Path(r'C:\Users\oussa\Downloads\aios-starter-kit\aios-starter-kit\docs')
src = (DOCS / 'resultaten.html').read_text(encoding='utf-8')

# ---------- onderdelen uit resultaten.html ----------
head = src[:src.rindex('</style>', 0, src.index('<body>'))]
header = src[src.index('<template id="logo-svg">'):src.index('<main>')]
footer = src[src.index('<footer>'):src.index('<script>', src.index('<footer>'))]
cookie = src[src.index('<div class="ck" id="ck"'):]

# kop van de pagina aanpassen
TITLE_NL = 'Voor webshops | Insightance'
TITLE_EN = 'For online stores | Insightance'
DESC_NL = 'Zo\u2019n 70% van de winkelmandjes wordt nooit afgerekend. Insightance bouwt automatische mails in Klaviyo die een deel van die klanten terughalen.'
DESC_EN = 'Around 70% of shopping carts are never checked out. Insightance builds automated Klaviyo emails that win part of those customers back.'
head = re.sub(r'<title>[^<]*</title>', f'<title>{TITLE_NL}</title>', head)
head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{DESC_NL}">', head)
head = head.replace('https://insightance.ai/resultaten.html', 'https://insightance.ai/webshops.html')
head = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{TITLE_EN}">', head)
head = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{DESC_EN}">', head)
header = header.replace('href="./#services"', 'href="./"')

CSS = r'''
  /* ===== webshops-landingspagina (2026-10-13) ===== */
  .ws-sec { padding-block: 72px; }
  .rhero { padding-block: clamp(28px, 5vh, 56px) clamp(24px, 4vh, 40px); }
  .rhero-copy { gap: 24px; }
  .rhero h1 { font-size: clamp(34px, 4.2vw, 50px); line-height: 1.06; letter-spacing: -.01em; }
  .rhero h1 em { display: block; font-style: italic; font-weight: 500; }
  .rhero h1 em .u { background: linear-gradient(transparent 72%, rgba(31,94,255,.18) 72%); }
  .rhero-copy > p { max-width: 54ch; }
  .ws-sec.tint { background: var(--soft); }
  .ws-head { display: grid; gap: 14px; margin-bottom: 28px; }
  .ws-head h2 { font-size: clamp(28px, 3.4vw, 38px); text-wrap: wrap; }
  .ws-head p { color: var(--muted); font-size: 17px; max-width: 60ch; }
  html { scroll-padding-top: 0; }
  #rekentool { scroll-margin-top: 20px; }
  .rhero .ctas { display: flex; flex-wrap: wrap; align-items: center; gap: 14px 22px; margin-top: 6px; }
  .rhero .link { color: var(--navy); font-weight: 600; text-decoration: none; border-bottom: 1.5px solid rgba(23,52,95,.25); padding-bottom: 2px; }
  .rhero .link:hover { color: var(--bright); border-color: var(--bright); }
  .works { display: flex; flex-wrap: wrap; gap: 8px 10px; align-items: center; font-size: 13px; color: var(--faint); margin-top: 6px; }
  .works b { font-weight: 600; color: var(--muted); }

  /* voorbeeldmail in de hero: verzonnen webshop "Saelvo" (linnen kleding), eigen kleuren */
  .mailwrap { justify-self: center; width: min(100%, 440px); display: grid; gap: 14px; }
  .mail { --shop: #2F3A2B; --sand: #EFE8DC; --sand2: #E2D7C5; --ink2: #4D5148; background: #fff; border-radius: 16px; box-shadow: 0 1px 0 rgba(23,52,95,.06), 0 30px 70px -40px rgba(23,52,95,.45); border: 1px solid #E3E8EF; overflow: hidden; }
  .mail-meta { display: grid; gap: 3px; padding: 13px 20px; border-bottom: 1px solid #EEF1F5; font-size: 12.5px; color: var(--faint); background: #FBFCFD; }
  .mail-meta b { color: var(--ink); font-weight: 600; }
  .mail-brand { background: var(--shop); color: var(--sand); text-align: center; padding: 16px 0 14px; font: 400 19px Georgia, "Times New Roman", serif; letter-spacing: .34em; }
  .mail-body { padding: 24px 26px 22px; display: grid; gap: 15px; background: #fff; }
  .mail-body h3 { font-family: Georgia, "Times New Roman", serif; font-size: 25px; font-weight: 400; color: var(--shop); text-align: center; line-height: 1.15; }
  .mail-body > p { font-size: 14px; color: var(--ink2); margin: 0; text-align: center; line-height: 1.55; }
  .item { display: grid; grid-template-columns: 84px 1fr auto; gap: 14px; align-items: center; padding: 14px 0; border-top: 1px solid #ECE6DB; border-bottom: 1px solid #ECE6DB; }
  .item .ph { width: 84px; height: 96px; border-radius: 6px; background: linear-gradient(160deg, var(--sand), var(--sand2)); display: grid; place-items: center; overflow: hidden; }
  .item .ph img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .item b { font-size: 14px; color: var(--shop); display: block; font-weight: 600; }
  .item small { display: block; font-size: 12.5px; color: #8A877F; margin-top: 2px; }
  .item .pr { font-weight: 600; color: var(--shop); font-size: 14.5px; font-variant-numeric: tabular-nums; }
  .tot { display: flex; justify-content: space-between; font-size: 13.5px; color: var(--ink2); }
  .tot b { color: var(--shop); font-variant-numeric: tabular-nums; }
  .mail-btn { display: block; text-align: center; background: var(--shop); color: var(--sand); font-weight: 600; font-size: 14px; letter-spacing: .04em; padding: 14px; border-radius: 4px; }
  .mail-foot { font-size: 11.5px; color: #9A978F; text-align: center; }
  .mailcap { display: grid; grid-template-columns: 18px 1fr; gap: 10px; align-items: start; font-size: 13px; line-height: 1.5; color: var(--muted); background: var(--white); border: 1px dashed #C7D6EE; border-radius: 12px; padding: 12px 14px; }
  .mailcap svg { width: 18px; height: 18px; color: var(--bright); margin-top: 1px; }
  .mailcap b { color: var(--navy); font-weight: 600; }

  /* het probleem */
  .facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
  .fact { background: linear-gradient(165deg, var(--tint) 0%, #fff 62%); border: 1px solid #CFDDF2; box-shadow: 0 22px 44px -38px rgba(23,52,95,.55); border-radius: 18px; padding: 26px 24px; display: grid; gap: 8px; align-content: start; }
  .fact .n { font-family: var(--serif); font-size: 44px; line-height: 1; color: var(--navy); font-variant-numeric: tabular-nums; }
  .fact .n.blue { color: var(--bright); }
  .fact b { font-size: 16px; color: var(--navy); }
  .fact p { font-size: 14.5px; color: var(--muted); margin: 0; }

  /* rekentool */
  .calc { display: grid; grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr); gap: 0; border-radius: 22px; overflow: hidden; border: 1px solid var(--line); background: #fff; box-shadow: 0 40px 80px -60px rgba(23,52,95,.5); }
  .calc-in { padding: 34px 34px 30px; display: grid; gap: 22px; align-content: start; }
  .fld { display: grid; gap: 10px; }
  .fld label { font-size: 13px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--faint); }
  .fld .row { display: flex; align-items: center; gap: 14px; }
  .fld input[type=range] { flex: 1; accent-color: var(--bright); height: 28px; }
  .fld .num { width: 110px; display: flex; align-items: center; border: 1px solid var(--line); border-radius: 10px; padding: 0 10px; background: var(--soft); }
  .fld .num span { color: var(--faint); font-weight: 600; }
  .fld .num input { width: 100%; border: 0; background: none; font: 600 17px var(--sans); color: var(--navy); padding: 10px 4px; text-align: right; font-variant-numeric: tabular-nums; outline: none; }
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

  /* tijdlijn met drie mails */
  .flow { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; position: relative; }
  .step { background: linear-gradient(165deg, var(--tint) 0%, #fff 62%); border: 1px solid #CFDDF2; border-radius: 18px; padding: 24px; display: grid; gap: 10px; align-content: start; position: relative; box-shadow: 0 22px 44px -38px rgba(23,52,95,.55); }
  .step .bignr { position: absolute; top: 14px; right: 20px; font-family: var(--serif); font-size: 46px; line-height: 1; color: rgba(31,94,255,.12); font-weight: 600; }
  .step .when { display: inline-flex; align-items: center; gap: 8px; font-size: 12.5px; font-weight: 600; color: #fff; background: var(--bright); border-radius: 100px; padding: 5px 12px; justify-self: start; }
  .step .when svg { width: 14px; height: 14px; }
  .step h3 { font-family: var(--sans); font-size: 18px; font-weight: 600; }
  .step p { font-size: 14.5px; color: var(--muted); margin: 0; }
  .mini { display: grid; grid-template-columns: 30px 1fr; gap: 10px; align-items: center; background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; margin-top: 4px; }
  .mini .av { width: 30px; height: 30px; border-radius: 50%; background: #2F3A2B; color: #EFE8DC; display: grid; place-items: center; font: 400 14px Georgia, serif; }
  .mini small { display: block; font-size: 11.5px; color: var(--faint); }
  .mini b { display: block; font-size: 13px; color: var(--ink); font-weight: 600; line-height: 1.35; }
  .step q { font-size: 13.5px; color: var(--navy); font-style: italic; background: var(--soft); border-radius: 10px; padding: 10px 12px; quotes: "\201C" "\201D"; }
  .flow-note { margin-top: 22px; font-size: 15px; color: var(--muted); }

  /* wat je krijgt */
  .get { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 40px; align-items: start; }
  .get ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 12px; }
  .get li { display: grid; grid-template-columns: 26px 1fr; gap: 12px; align-items: start; font-size: 15.5px; color: var(--ink); }
  .get li svg { width: 22px; height: 22px; color: var(--bright); margin-top: 1px; }
  .plat { background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 26px; display: grid; gap: 14px; }
  .plat h3 { font-family: var(--sans); font-size: 17px; font-weight: 600; }
  .plat .chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .plat .chips span { font-size: 13.5px; font-weight: 600; color: var(--navy); background: var(--soft); border: 1px solid var(--line); border-radius: 100px; padding: 7px 14px; }
  .plat p { font-size: 14.5px; color: var(--muted); margin: 0; }

  /* bewijs */
  .proof { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) minmax(0, 1fr); gap: 14px; }
  .pf { border-radius: 18px; padding: 26px; display: grid; gap: 10px; align-content: start; text-decoration: none; border: 1px solid var(--line); background: #fff; transition: transform .25s var(--ease), border-color .25s; }
  a.pf:hover { transform: translateY(-3px); border-color: var(--bright); }
  .pf.main { background: var(--navy); border-color: var(--navy); color: #fff; }
  .pf .k { font-size: 12px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--bright); }
  .pf.main .k { color: var(--mid-on-dark); }
  .pf .n { font-family: var(--serif); font-size: 40px; line-height: 1; color: var(--navy); }
  .pf b { font-size: 16px; color: var(--navy); }
  .pf.main b { color: #fff; font-size: 19px; line-height: 1.35; }
  .pf p { font-size: 14.5px; color: var(--muted); margin: 0; }
  .pf.main p { color: rgba(255,255,255,.78); }
  .pf .go { font-size: 13.5px; font-weight: 600; color: var(--bright); margin-top: 4px; }

  /* bewijs, uitgebreid */
  .proof2 { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; }
  .pf2-side { display: grid; gap: 14px; }
  .pf2 { border-radius: 18px; padding: 26px; display: grid; gap: 12px; align-content: start; text-decoration: none; border: 1px solid var(--line); background: #fff; transition: transform .25s var(--ease), border-color .25s; }
  a.pf2:hover { transform: translateY(-3px); border-color: var(--bright); }
  .pf2.main { position: relative; overflow: hidden; isolation: isolate; background: var(--navy); border-color: var(--navy); color: #fff; gap: 16px; }
  .pf2.main::before { content: ""; position: absolute; inset: 0; z-index: -1; background: radial-gradient(70% 60% at 100% 0%, rgba(31,94,255,.45), transparent 70%); }
  .pf2 .k { display: block; font-size: 12px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--bright); }
  .pf2.main .k { color: var(--mid-on-dark); }
  .pf2.main > b { font-size: 20px; line-height: 1.35; color: #fff; }
  .pf2.main > p { color: rgba(255,255,255,.75); font-size: 14.5px; margin: 0; }
  .seq { list-style: none; margin: 4px 0; padding: 0; display: grid; gap: 0; position: relative; }
  .seq::before { content: ""; position: absolute; left: 6px; top: 12px; bottom: 12px; width: 2px; background: linear-gradient(rgba(157,187,227,.35), rgba(157,187,227,.9)); }
  .seq li { display: grid; grid-template-columns: 14px 1fr auto; gap: 14px; align-items: center; padding: 9px 0; font-size: 14.5px; color: #fff; position: relative; }
  .seq .d { width: 14px; height: 14px; border-radius: 50%; background: var(--bright); box-shadow: 0 0 0 4px rgba(31,94,255,.25); z-index: 1; }
  .seq .d.o { background: transparent; border: 2px solid var(--mid-on-dark); box-shadow: none; }
  .seq .d.ok { background: #2FAE68; box-shadow: 0 0 0 4px rgba(47,174,104,.25); }
  .seq em { font-style: normal; font-size: 12.5px; color: var(--mid-on-dark); }
  .pf2 .top { display: flex; align-items: center; gap: 16px; }
  .pf2 .n { font-family: var(--serif); font-size: 42px; line-height: 1; color: var(--navy); }
  .pf2 .top b { display: block; font-size: 15.5px; color: var(--navy); margin-top: 3px; }
  .pf2 blockquote { margin: 0; padding-left: 14px; border-left: 2px solid var(--bright); font-size: 14.5px; line-height: 1.55; color: var(--ink); font-style: italic; }
  .pf2 .who { font-size: 13px; color: var(--muted); }
  .pf2 .go { font-size: 13.5px; font-weight: 600; color: var(--bright); }
  @media (max-width: 980px) { .proof2 { grid-template-columns: 1fr; } }

  /* werkwijze: zelfde onderdeel als op de homepage */
  .wsplit { display: grid; grid-template-columns: minmax(0, .85fr) minmax(0, 1.15fr); gap: 48px; align-items: center; }
  .wcard { position: relative; overflow: hidden; display: grid; gap: 12px; padding: 30px; border-radius: 20px; background: linear-gradient(160deg, var(--tint), var(--white) 75%); border: 1px solid var(--line); box-shadow: 0 22px 44px -34px rgba(23,52,95,.5); }
  .wcard small { font-size: 11px; font-weight: 600; letter-spacing: .16em; text-transform: uppercase; color: var(--bright); }
  .wcard b { font-size: 22px; font-weight: 600; color: var(--navy); line-height: 1.25; }
  .wcard p { color: var(--muted); font-size: 15px; margin: 0; }
  .wcard .btn { justify-self: start; margin-top: 6px; }
  .wcard > span { font-size: 13px; color: var(--muted); }
  .wcard .wpill { justify-self: start; margin-top: 4px; display: inline-flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--navy); background: var(--white); border: 1px solid #CFDDF2; padding: 5px 12px; border-radius: 100px; }
  .pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--bright); animation: ping 1.8s infinite; display: inline-block; flex-shrink: 0; }
  @keyframes ping { 0% { box-shadow: 0 0 0 0 rgba(31,94,255,.5); } 70% { box-shadow: 0 0 0 8px rgba(31,94,255,0); } 100% { box-shadow: 0 0 0 0 rgba(31,94,255,0); } }
  .wsteps { list-style: none; margin: 0; padding: 0; display: grid; position: relative; }
  .wsteps::before { content: ""; position: absolute; left: 21px; top: 26px; bottom: 26px; width: 2px; background: linear-gradient(var(--bright), var(--line)); }
  .wsteps li { display: grid; grid-template-columns: 44px 1fr; gap: 2px 18px; padding: 12px 0; position: relative; }
  .wsteps .n { grid-row: span 3; width: 44px; height: 44px; border-radius: 50%; display: grid; place-items: center; background: var(--white); border: 2px solid var(--bright); color: var(--bright); font-weight: 700; font-size: 16px; z-index: 1; }
  .wsteps li:first-child .n { background: var(--bright); color: #fff; box-shadow: 0 0 0 6px rgba(31,94,255,.12); }
  .wsteps b { font-size: 17px; color: var(--navy); padding-top: 3px; }
  .wsteps p { margin: 0; font-size: 14.5px; color: var(--muted); max-width: 56ch; }
  .wsteps .tag { display: inline-block; margin-left: 8px; padding: 3px 10px; border-radius: 100px; background: var(--tint); color: var(--bright); font-size: 12px; font-weight: 600; vertical-align: 2px; white-space: nowrap; }
  .wsteps .wget { display: block; margin-top: 6px; font-size: 13.5px; line-height: 1.5; color: var(--navy); max-width: 56ch; }
  .wsteps .wget b { font-size: inherit; font-weight: 600; padding: 0; color: var(--bright); }
  @media (min-width: 901px) { .wcard { position: sticky; top: 104px; } }
  @media (max-width: 900px) { .wsplit { grid-template-columns: 1fr; gap: 24px; } .wsteps { order: -1; } }

  /* faq */
  .wfaq { display: grid; gap: 0; max-width: 820px; border-top: 1px solid var(--line); }
  .wfaq details { border-bottom: 1px solid var(--line); }
  .wfaq summary { list-style: none; cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 20px 2px; font-weight: 600; font-size: 16.5px; color: var(--navy); }
  .wfaq summary::-webkit-details-marker { display: none; }
  .wfaq summary i { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: var(--tint); color: var(--bright); display: grid; place-items: center; font-style: normal; font-size: 18px; transition: transform .25s, background .25s, color .25s; }
  .wfaq details[open] summary i { transform: rotate(45deg); background: var(--bright); color: #fff; }
  .wfaq details p { margin: 0 0 20px; color: var(--muted); font-size: 15.5px; max-width: 70ch; }

  @media (max-width: 980px) {
    .facts, .flow, .proof { grid-template-columns: 1fr; }
    .calc, .get { grid-template-columns: 1fr; }
  }
  @media (max-width: 560px) {
    .ws-sec { padding-block: 48px; }
    #rekentool { scroll-margin-top: 44px; }
    .calc-in, .calc-out { padding: 24px 20px; }
    .fld .num { width: 96px; }
    .item { grid-template-columns: 52px 1fr auto; }
    .item .ph { width: 52px; height: 52px; }
  }
'''

CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>'
CLOCK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
BAG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M9 3 4 5.5 2.5 10l3 1.2V21h13v-9.8l3-1.2L20 5.5 15 3a3 3 0 0 1-6 0z"/></svg>'

MAIN = f'''<main>
  <svg class="dataline" id="dataline" aria-hidden="true"><path class="track" id="dl-track"/><path class="draw" id="dl-draw"/><g id="dl-dot"><circle class="halo" r="10"/><circle class="head" r="4.5"/></g></svg>
  <section class="rhero">
    <canvas class="bgflow"></canvas>
    <div class="wrap">
      <div class="rhero-copy">
        <div class="eyebrow eyebrow-lines" data-i18n>Voor webshops</div>
        <h1 data-i18n-html>7 van de 10 winkelmandjes worden nooit afgerekend. <em><span class="u">Haal die omzet terug.</span></em></h1>
        <p data-i18n>Met een reeks automatische mails haal je een deel van die klanten alsnog binnen. Zonder extra advertentiebudget, in jouw huisstijl, en het loopt vanzelf.</p>
        <div class="ctas"><a class="btn" href="#rekentool" data-i18n>Bereken wat je laat liggen</a><a class="link" href="./#contact" data-i18n>Plan een gesprek →</a></div>
        <div class="works"><span data-i18n>Gebouwd in Klaviyo · werkt met</span><b>Shopify</b>·<b>WooCommerce</b>·<b>Magento</b>·<b data-i18n>en meer</b></div>
      </div>
      <div class="mailwrap rv">
        <div class="mail" aria-label="Voorbeeld van een herinneringsmail van een verzonnen webshop">
          <div class="mail-meta"><span><span data-i18n>Van:</span> <b>Saelvo</b></span><span><span data-i18n>Onderwerp:</span> <b data-i18n>Lotte, je mandje staat nog klaar</b></span></div>
          <div class="mail-brand">SAELVO</div>
          <div class="mail-body">
            <h3 data-i18n>Je bent iets vergeten</h3>
            <p data-i18n>Hoi Lotte, je overhemd ligt nog voor je klaar. We houden je maat nog even voor je vast.</p>
            <div class="item"><span class="ph"><img src="images/saelvo-overhemd.jpg" alt="" width="84" height="96" loading="lazy"></span><div><b data-i18n>Linnen overhemd Ravi</b><small data-i18n>Kleur: ecru · Maat M</small><small data-i18n>Aantal: 1</small></div><span class="pr">€ 69,95</span></div>
            <div class="tot"><span data-i18n>Verzending</span><b data-i18n>Gratis</b></div>
            <span class="mail-btn" data-i18n>Rond je bestelling af</span>
            <span class="mail-foot" data-i18n>Gratis verzending en retour · Vragen? Antwoord gewoon op deze mail</span>
          </div>
        </div>
        <div class="mailcap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg><span><b data-i18n>Dit is een voorbeeld.</b> <span data-i18n>Jouw mails krijgen je eigen logo, kleuren, producten en toon.</span></span></div>
      </div>
    </div>
  </section>

  <section class="ws-sec">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow" data-i18n>Het probleem</div><h2 data-i18n>Je betaalt voor bezoekers die vlak voor de kassa afhaken</h2><p data-i18n>Advertenties, social media en tijd: daarmee krijg je mensen in je webshop. De meesten leggen iets in hun mandje en gaan dan weg. Zonder opvolging zie je ze nooit meer terug.</p></div>
      <div class="facts">
        <div class="fact rv"><span class="n">70%</span><b data-i18n>van de mandjes wordt verlaten</b><p data-i18n>Dat is het gemiddelde over tientallen onderzoeken naar webshops wereldwijd.</p></div>
        <div class="fact rv" style="--d:.08s"><span class="n">80%</span><b data-i18n>op mobiel</b><p data-i18n>Op een telefoon haken nog meer mensen af. Vaak willen ze later verder, maar vergeten ze het.</p></div>
        <div class="fact rv" style="--d:.16s"><span class="n blue">€0</span><b data-i18n>extra advertentiebudget</b><p data-i18n>Je haalt meer uit bezoekers die je al hebt. Dit zijn mensen die al interesse toonden.</p></div>
      </div>
    </div>
  </section>

  <section class="ws-sec tint" id="rekentool">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow" data-i18n>Rekentool</div><h2 data-i18n>Wat laat jouw webshop liggen?</h2><p data-i18n>Vul twee getallen in. Je ziet direct hoeveel omzet er in verlaten mandjes zit, en wat een goede mailreeks daarvan terughaalt.</p></div>
      <div class="calc rv">
        <div class="calc-in">
          <div class="fld"><label for="c-orders" data-i18n>Bestellingen per maand</label><div class="row"><input type="range" id="r-orders" min="10" max="2000" step="10" value="150" aria-label="Bestellingen per maand"><div class="num"><input id="c-orders" inputmode="numeric" value="150" aria-label="Bestellingen per maand"></div></div></div>
          <div class="fld"><label for="c-aov" data-i18n>Gemiddeld orderbedrag</label><div class="row"><input type="range" id="r-aov" min="10" max="300" step="5" value="60" aria-label="Gemiddeld orderbedrag"><div class="num"><span>€</span><input id="c-aov" inputmode="decimal" value="60" aria-label="Gemiddeld orderbedrag"></div></div></div>
          <p class="calc-note" data-i18n>Een schatting op basis van gemiddelden: 70% van de mandjes wordt verlaten, en een goede reeks van drie mails haalt daar 5 tot 10% van terug. In een gesprek kijken we naar jouw echte cijfers.</p>
        </div>
        <div class="calc-out" aria-live="polite">
          <div class="o-row"><span data-i18n>Verlaten mandjes per maand</span><b id="o-carts">350</b></div>
          <div class="o-row"><span data-i18n>Omzet in die mandjes</span><b id="o-lost">€ 21.000</b></div>
          <div class="o-big"><small data-i18n>Terug te halen per maand</small><b id="o-month">€ 1.050 – € 2.100</b><span id="o-year">€ 12.600 – € 25.200 per jaar</span></div>
          <a class="btn" href="./#contact" data-i18n>Bespreek jouw cijfers</a>
        </div>
      </div>
    </div>
  </section>

  <section class="ws-sec">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow" data-i18n>Hoe het werkt</div><h2 data-i18n>Drie mails, precies op het goede moment</h2><p data-i18n>Iemand legt iets in zijn mandje en rekent niet af. Vanaf dat moment loopt de reeks vanzelf, tot die persoon alsnog bestelt.</p></div>
      <div class="flow">
        <div class="step rv"><span class="when">{CLOCK}<span data-i18n>Na 1 uur</span></span><h3 data-i18n>De herinnering</h3><p data-i18n>Een vriendelijke mail met precies de producten uit het mandje en een knop om direct af te rekenen.</p><div class="mini"><span class="av">S</span><span><small>Saelvo</small><b data-i18n>Lotte, je mandje staat nog klaar</b></span></div><span class="bignr" aria-hidden="true">1</span></div>
        <div class="step rv" style="--d:.08s"><span class="when">{CLOCK}<span data-i18n>Na 1 dag</span></span><h3 data-i18n>Het vertrouwen</h3><p data-i18n>Twijfel wegnemen: reviews van andere klanten, verzending en retourbeleid, en een antwoord op veelgestelde vragen.</p><div class="mini"><span class="av">S</span><span><small>Saelvo</small><b data-i18n>Dit zeggen anderen over het Ravi-overhemd</b></span></div><span class="bignr" aria-hidden="true">2</span></div>
        <div class="step rv" style="--d:.16s"><span class="when">{CLOCK}<span data-i18n>Na 3 dagen</span></span><h3 data-i18n>Het laatste duwtje</h3><p data-i18n>Een korte laatste mail. Eventueel met een kleine korting of gratis verzending, maar dat is jouw keuze.</p><div class="mini"><span class="av">S</span><span><small>Saelvo</small><b data-i18n>Nog even voor je bewaard, Lotte</b></span></div><span class="bignr" aria-hidden="true">3</span></div>
      </div>
      <p class="flow-note rv" data-i18n>Alles in jouw huisstijl en jouw toon, met de echte producten en prijzen uit het mandje. Bestelt iemand tussendoor, dan stopt de reeks automatisch.</p>
    </div>
  </section>

  <section class="ws-sec tint">
    <div class="wrap get">
      <div class="rv">
        <div class="ws-head" style="margin-bottom:24px"><div class="eyebrow" data-i18n>Wat je krijgt</div><h2 data-i18n>Kant-en-klaar, zonder dat jij iets hoeft te doen</h2></div>
        <ul>
          <li>{CHECK}<span data-i18n>Koppeling tussen je webshop en Klaviyo, volledig ingericht</span></li>
          <li>{CHECK}<span data-i18n>Drie mails in jouw huisstijl, met teksten in jouw toon</span></li>
          <li>{CHECK}<span data-i18n>De producten uit het mandje automatisch in de mail</span></li>
          <li>{CHECK}<span data-i18n>Getest voordat het live gaat, op computer en telefoon</span></li>
          <li>{CHECK}<span data-i18n>Uitleg zodat je ziet wat het oplevert</span></li>
        </ul>
      </div>
      <div class="plat rv" style="--d:.08s">
        <h3 data-i18n>Werkt met jouw webshop</h3>
        <div class="chips"><span>Shopify</span><span>WooCommerce</span><span>Magento</span><span>BigCommerce</span><span>Wix</span><span>PrestaShop</span></div>
        <p data-i18n>De mails draaien in Klaviyo, het mailprogramma dat de meeste webshops hiervoor gebruiken. Gebruik je het nog niet? Dan richten we het samen in.</p>
      </div>
    </div>
  </section>

  <section class="ws-sec">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow" data-i18n>Bewijs</div><h2 data-i18n>Systemen die werken, voor echte bedrijven</h2></div>
      <div class="proof2">
        <div class="pf2 main rv">
          <span class="k" data-i18n>E-commerce · Klaviyo</span>
          <b data-i18n>Recent gebouwd voor een webshop: een reeks van drie mails voor iedereen die het mandje verlaat.</b>
          <ol class="seq">
            <li><i class="d o"></i><span data-i18n>Mandje verlaten</span></li>
            <li><i class="d"></i><span data-i18n>Mail 1 · herinnering</span><em data-i18n>na 1 uur</em></li>
            <li><i class="d"></i><span data-i18n>Mail 2 · vertrouwen</span><em data-i18n>na 1 dag</em></li>
            <li><i class="d"></i><span data-i18n>Mail 3 · laatste duwtje</span><em data-i18n>na 3 dagen</em></li>
            <li><i class="d ok"></i><span data-i18n>Bestelling afgerond</span></li>
          </ol>
          <p data-i18n>Geen extra advertentiebudget, alleen meer halen uit de bezoekers die er al zijn.</p>
        </div>
        <div class="pf2-side">
          <a class="pf2 rv" style="--d:.08s" href="resultaten.html#mhl">
            <div class="top"><span class="n">90%</span><span><span class="k" data-i18n>Installatietechniek</span><b data-i18n>minder tijd per offerte</b></span></div>
            <blockquote data-i18n>Nu vul ik het formulier in en druk op één knop. De klant heeft de offerte meteen in zijn inbox.</blockquote>
            <span class="who">Mohammed, MHL Installatieservice</span><span class="go" data-i18n>Bekijk de case →</span>
          </a>
          <a class="pf2 rv" style="--d:.16s" href="resultaten.html#ftuk">
            <div class="top"><span class="n" data-i18n>8 uur</span><span><span class="k" data-i18n>E-commerce &amp; media</span><b data-i18n>per week teruggewonnen</b></span></div>
            <blockquote data-i18n>In één oogopslag zie ik hoe het bedrijf presteert. Ik heb hier zoveel tijd mee teruggewonnen.</blockquote>
            <span class="who">Forex Trading UK (FTUK)</span><span class="go" data-i18n>Bekijk de case →</span>
          </a>
        </div>
      </div>
    </div>
  </section>

  <section class="ws-sec tint">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow" data-i18n>Werkwijze</div><h2 data-i18n>Van gesprek tot draaiende mails</h2><p data-i18n>Je weet vooraf wat het kost. Je betaalt in twee delen, het laatste deel pas als alles werkt.</p></div>
      <div class="wsplit">
        <div class="wcard rv">
          <small data-i18n>Stap 1</small>
          <b data-i18n>Begin met een kennismaking</b>
          <p data-i18n>Een vrijblijvend gesprek van een half uur over je webshop en je cijfers. Je hoeft niets voor te bereiden.</p>
          <a class="btn" href="./#contact" data-i18n>Plan een gesprek</a>
          <span data-i18n>30 minuten · Vrijblijvend</span>
          <span class="wpill"><span class="pulse"></span><span data-i18n>Max. 3 nieuwe klanten per maand</span></span>
        </div>
        <ol class="wsteps rv" style="--d:.08s">
          <li><span class="n">1</span><b><span data-i18n>Kennismaking</span> <span class="tag" data-i18n>Gratis · 30 min</span></b><p data-i18n>We kijken samen naar je webshop, je cijfers en hoe je nu met verlaten mandjes omgaat.</p><small class="wget"><b data-i18n>Je weet daarna:</b> <span data-i18n>wat een mailreeks jouw webshop kan opleveren.</span></small></li>
          <li><span class="n">2</span><b><span data-i18n>Voorstel</span> <span class="tag" data-i18n>Gratis</span></b><p data-i18n>Je krijgt een concreet plan: welke mails, wanneer ze verstuurd worden en wat het kost.</p><small class="wget"><b data-i18n>Je krijgt:</b> <span data-i18n>een vaste prijs. Je zit nergens aan vast tot je akkoord geeft.</span></small></li>
          <li><span class="n">3</span><b><span data-i18n>Bouwen</span> <span class="tag" data-i18n>50% bij akkoord</span></b><p data-i18n>Insightance richt Klaviyo in en bouwt de mails in jouw huisstijl. Jij keurt ze goed voordat ze live gaan.</p></li>
          <li><span class="n">4</span><b><span data-i18n>Live</span> <span class="tag" data-i18n>50% als alles werkt</span></b><p data-i18n>Is alles getest en ben je tevreden, dan betaal je de tweede helft.</p><small class="wget"><b data-i18n>Je krijgt:</b> <span data-i18n>een reeks die vanzelf draait, en uitleg over wat hij oplevert.</span></small></li>
        </ol>
      </div>
    </div>
  </section>

  <section class="ws-sec">
    <div class="wrap">
      <div class="ws-head rv"><div class="eyebrow">FAQ</div><h2 data-i18n>Je vragen beantwoord</h2></div>
      <div class="wfaq rv">
        <details><summary><span data-i18n>Ik gebruik Klaviyo al. Wat voeg jij dan toe?</span><i>+</i></summary><p data-i18n>Klaviyo heeft een standaardreeks, maar die moet je zelf goed inrichten: de timing, teksten in jouw toon, de productblokken en het testen. Dat doe ik, zodat het vanaf dag één goed werkt.</p></details>
        <details><summary><span data-i18n>Werkt dit met mijn webshop?</span><i>+</i></summary><p data-i18n>Klaviyo koppelt met Shopify, WooCommerce, Magento, BigCommerce, Wix, PrestaShop en meer. In het kennismakingsgesprek check ik of jouw webshop erbij zit.</p></details>
        <details><summary><span data-i18n>Moet ik korting geven?</span><i>+</i></summary><p data-i18n>Nee. Vaak is een herinnering en wat extra vertrouwen al genoeg. Een kleine korting in de laatste mail is een optie, geen must.</p></details>
        <details><summary><span data-i18n>Hoe snel staat het live?</span><i>+</i></summary><p data-i18n>Meestal binnen enkele weken na akkoord. Hoe sneller ik toegang heb tot je webshop en Klaviyo, hoe sneller het live staat.</p></details>
      </div>
    </div>
  </section>

  <section class="closing">
    <div class="wrap">
      <div class="cbox rv">
        <canvas class="cflow" aria-hidden="true"></canvas>
        <div class="ctext">
          <div class="eyebrow" data-i18n>Jouw webshop</div>
          <h2 data-i18n>Benieuwd wat jouw webshop laat liggen?</h2>
          <p data-i18n>In een gesprek van 30 minuten kijken we naar je cijfers en laat ik zien hoe de mails er voor jouw shop uit zouden zien.</p>
          <div class="acts"><a class="btn" href="./#contact" data-i18n>Plan een gesprek</a><small data-i18n>30 minuten · Vrijblijvend</small></div>
        </div>
        <a class="own" href="./#contact">
          <span class="own-plus"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></span>
          <b data-i18n>Jouw webshop als volgende case</b>
          <span class="own-lines" aria-hidden="true"><i></i><i></i><i></i></span>
          <span class="own-go" data-i18n>Start hier</span>
        </a>
      </div>
    </div>
  </section>
</main>

'''

I18N = {
 "Terug naar homepage": "Back to homepage", "Terug": "Back", "Plan een gesprek": "Book a call", "Resultaten": "Results", "Privacybeleid": "Privacy policy",
 "Voor webshops": "For online stores",
 "Voor vakbedrijven": "For trades",
 "Zo’n 70% van de winkelmandjes wordt nooit afgerekend. Met een reeks automatische mails haal je een deel van die klanten alsnog binnen, zonder extra advertentiebudget.": "Around 70% of shopping carts are never checked out. A short series of automated emails brings part of those customers back, without spending more on ads.",
 "Bereken wat je laat liggen": "See what you're missing", "Plan een gesprek →": "Book a call →",
 "Gebouwd in Klaviyo · werkt met": "Built in Klaviyo · works with", "en meer": "and more",
 "Jouw webshop": "Your store", "aan: Sanne": "to: Sanne", "1 uur na bezoek": "1 hour after visit",
 "Je mandje staat nog klaar": "Your cart is still waiting", "Hoi Sanne, je was bijna klaar. We hebben je mandje voor je bewaard, zodat je in één klik verder kunt.": "Hi Sanne, you were almost done. We saved your cart, so you can pick up where you left off in one click.",
 "Linnen overhemd": "Linen shirt", "Maat M · Zandkleur": "Size M · Sand", "Bestelling afronden": "Complete your order", "Gratis verzending vanaf € 50 · 30 dagen retour": "Free shipping over €50 · 30-day returns",
 "Het probleem": "The problem", "Je betaalt voor bezoekers die vlak voor de kassa afhaken": "You pay for visitors who drop off right before checkout",
 "Advertenties, social media en tijd: daarmee krijg je mensen in je webshop. De meesten leggen iets in hun mandje en gaan dan weg. Zonder opvolging zie je ze nooit meer terug.": "Ads, social media and time: that's what it takes to get people into your store. Most of them add something to their cart and then leave. Without a follow-up, you never see them again.",
 "van de mandjes wordt verlaten": "of carts are abandoned", "Dat is het gemiddelde over tientallen onderzoeken naar webshops wereldwijd.": "That's the average across dozens of studies of online stores worldwide.",
 "op mobiel": "on mobile", "Op een telefoon haken nog meer mensen af. Vaak willen ze later verder, maar vergeten ze het.": "Even more people drop off on a phone. They often mean to finish later, then forget.",
 "extra advertentiebudget": "extra ad spend", "Je haalt meer uit bezoekers die je al hebt. Dit zijn mensen die al interesse toonden.": "You get more out of visitors you already have. These are people who already showed interest.",
 "Rekentool": "Calculator", "Wat laat jouw webshop liggen?": "What is your store leaving on the table?",
 "Vul twee getallen in. Je ziet direct hoeveel omzet er in verlaten mandjes zit, en wat een goede mailreeks daarvan terughaalt.": "Enter two numbers. You'll see right away how much revenue sits in abandoned carts, and how much a good email series wins back.",
 "Bestellingen per maand": "Orders per month", "Gemiddeld orderbedrag": "Average order value",
 "Een schatting op basis van gemiddelden: 70% van de mandjes wordt verlaten, en een goede reeks van drie mails haalt daar 5 tot 10% van terug. In een gesprek kijken we naar jouw echte cijfers.": "An estimate based on averages: 70% of carts are abandoned, and a good three-email series wins back 5 to 10% of them. On a call we look at your real numbers.",
 "Verlaten mandjes per maand": "Abandoned carts per month", "Omzet in die mandjes": "Revenue in those carts", "Terug te halen per maand": "Recoverable per month", "Bespreek jouw cijfers": "Talk through your numbers",
 "Hoe het werkt": "How it works", "Drie mails, precies op het goede moment": "Three emails, each at the right moment",
 "Iemand legt iets in zijn mandje en rekent niet af. Vanaf dat moment loopt de reeks vanzelf, tot die persoon alsnog bestelt.": "Someone adds something to their cart and doesn't check out. From that moment the series runs on its own, until that person places the order.",
 "Na 1 uur": "After 1 hour", "De herinnering": "The reminder", "Een vriendelijke mail met precies de producten uit het mandje en een knop om direct af te rekenen.": "A friendly email showing the exact products in the cart, with a button to check out right away.",
 "Na 1 dag": "After 1 day", "Het vertrouwen": "The reassurance", "Twijfel wegnemen: reviews van andere klanten, verzending en retourbeleid, en een antwoord op veelgestelde vragen.": "Taking away doubt: reviews from other customers, shipping and returns, and answers to common questions.",
 "Dit zeggen anderen over ons": "Here's what others say about us",
 "Na 3 dagen": "After 3 days", "Het laatste duwtje": "The final nudge", "Een korte laatste mail. Eventueel met een kleine korting of gratis verzending, maar dat is jouw keuze.": "A short last email. Optionally with a small discount or free shipping, but that's up to you.",
 "Nog even voor je bewaard": "Still saved for you",
 "Alles in jouw huisstijl en jouw toon, met de echte producten en prijzen uit het mandje. Bestelt iemand tussendoor, dan stopt de reeks automatisch.": "Everything in your brand style and your tone of voice, with the real products and prices from the cart. If someone orders in between, the series stops automatically.",
 "Wat je krijgt": "What you get", "Kant-en-klaar, zonder dat jij iets hoeft te doen": "Done for you, nothing for you to set up",
 "Koppeling tussen je webshop en Klaviyo, volledig ingericht": "Your store connected to Klaviyo, fully set up",
 "Drie mails in jouw huisstijl, met teksten in jouw toon": "Three emails in your brand style, written in your tone",
 "De producten uit het mandje automatisch in de mail": "The products from the cart added to each email automatically",
 "Getest voordat het live gaat, op computer en telefoon": "Tested on desktop and mobile before it goes live",
 "Uitleg zodat je ziet wat het oplevert": "A walkthrough so you can see what it brings in",
 "Werkt met jouw webshop": "Works with your store",
 "De mails draaien in Klaviyo, het mailprogramma dat de meeste webshops hiervoor gebruiken. Gebruik je het nog niet? Dan richten we het samen in.": "The emails run in Klaviyo, the email platform most online stores use for this. Not using it yet? We'll set it up together.",
 "Bewijs": "Proof", "Systemen die werken, voor echte bedrijven": "Systems that work, for real businesses",
 "E-commerce": "E-commerce", "Recent gebouwd voor een webshop: een reeks van drie mails voor iedereen die het mandje verlaat.": "Recently built for an online store: a three-email series for everyone who leaves their cart.",
 "Geen extra advertentiebudget, alleen meer halen uit de bezoekers die er al zijn.": "No extra ad spend, just more out of the visitors who are already there.",
 "Installatietechniek": "Installation services", "minder tijd per offerte": "less time per quote", "Bekijk de case →": "View the case →",
 "E-commerce & media": "E-commerce & media", "8 uur": "8 hours", "per week teruggewonnen": "saved every week",
 "Werkwijze": "How it works", "Van gesprek tot draaiende mails": "From first call to emails that run",
 "Je weet vooraf wat het kost. Je betaalt in twee delen, het laatste deel pas als alles werkt.": "You know the price up front. You pay in two parts, the second only once everything works.",
 "Kennismaking": "Intro call", "Gratis · 30 min": "Free · 30 min", "We kijken samen naar je webshop en je cijfers.": "We look at your store and your numbers together.",
 "Voorstel": "Proposal", "Gratis": "Free", "Je krijgt een concreet plan met een vaste prijs.": "You get a concrete plan with a fixed price.",
 "Bouwen": "Build", "50% bij akkoord": "50% on approval", "Insightance bouwt en test de mails. Jij keurt ze goed.": "Insightance builds and tests the emails. You approve them.",
 "Live": "Live", "50% als alles werkt": "50% once it all works", "De reeks draait. Jij ziet de bestellingen binnenkomen.": "The series is running. You see the orders come in.",
 "Vragen": "Questions", "Goed om te weten": "Good to know",
 "Ik gebruik Klaviyo al. Wat voeg jij dan toe?": "I already use Klaviyo. What do you add?",
 "Klaviyo heeft een standaardreeks, maar die moet je zelf goed inrichten: de timing, teksten in jouw toon, de productblokken en het testen. Dat doe ik, zodat het vanaf dag één goed werkt.": "Klaviyo comes with a standard flow, but you still have to set it up properly: the timing, copy in your tone, the product blocks and the testing. I take care of that, so it works well from day one.",
 "Werkt dit met mijn webshop?": "Does this work with my store?",
 "Klaviyo koppelt met Shopify, WooCommerce, Magento, BigCommerce, Wix, PrestaShop en meer. In het kennismakingsgesprek check ik of jouw webshop erbij zit.": "Klaviyo connects with Shopify, WooCommerce, Magento, BigCommerce, Wix, PrestaShop and more. On the intro call I'll check that your store is covered.",
 "Moet ik korting geven?": "Do I have to offer a discount?",
 "Nee. Vaak is een herinnering en wat extra vertrouwen al genoeg. Een kleine korting in de laatste mail is een optie, geen must.": "No. A reminder and a bit of reassurance is often enough. A small discount in the last email is an option, not a must.",
 "Hoe snel staat het live?": "How soon can it be live?",
 "Meestal binnen enkele weken na akkoord. Hoe sneller ik toegang heb tot je webshop en Klaviyo, hoe sneller het live staat.": "Usually within a few weeks of approval. The sooner I have access to your store and Klaviyo, the sooner it's live.",
 "Jouw webshop als volgende case": "Your store as the next case", "Start hier": "Start here",
 "Benieuwd wat jouw webshop laat liggen?": "Curious what your store is leaving on the table?",
 "In een gesprek van 30 minuten kijken we naar je cijfers en laat ik zien hoe de mails er voor jouw shop uit zouden zien.": "In a 30-minute call we look at your numbers and I'll show you what the emails would look like for your store.",
 "30 minuten · Vrijblijvend": "30 minutes · No obligation",
 "Je vragen beantwoord": "Your questions answered",
 "Dit zeggen anderen over het Ravi-overhemd": "Here's what others say about the Ravi shirt",
 "Nog even voor je bewaard, Lotte": "Still saved for you, Lotte",
 "E-commerce · Klaviyo": "E-commerce · Klaviyo",
 "Mandje verlaten": "Cart abandoned",
 "Mail 1 · herinnering": "Email 1 · reminder",
 "na 1 uur": "after 1 hour",
 "Mail 2 · vertrouwen": "Email 2 · reassurance",
 "na 1 dag": "after 1 day",
 "Mail 3 · laatste duwtje": "Email 3 · final nudge",
 "na 3 dagen": "after 3 days",
 "Bestelling afgerond": "Order completed",
 "Nu vul ik het formulier in en druk op één knop. De klant heeft de offerte meteen in zijn inbox.": "Now I fill in the form and press one button. The customer has the quote in their inbox right away.",
 "In één oogopslag zie ik hoe het bedrijf presteert. Ik heb hier zoveel tijd mee teruggewonnen.": "At a glance I can see how the business is performing. It has saved me so much time.",
 "Voor webshops": "For online stores",
 "Van:": "From:",
 "Lotte, je mandje staat nog klaar": "Lotte, your cart is still waiting",
 "Je bent iets vergeten": "You forgot something",
 "Hoi Lotte, je overhemd ligt nog voor je klaar. We houden je maat nog even voor je vast.": "Hi Lotte, your shirt is still waiting for you. We're holding your size for a little longer.",
 "Linnen overhemd Ravi": "Ravi linen shirt",
 "Kleur: ecru · Maat M": "Colour: ecru · Size M",
 "Aantal: 1": "Qty: 1",
 "Verzending": "Shipping",
 "Rond je bestelling af": "Complete your order",
 "Gratis verzending en retour · Vragen? Antwoord gewoon op deze mail": "Free shipping and returns · Questions? Just reply to this email",
 "Dit is een voorbeeld.": "This is an example.",
 "Jouw mails krijgen je eigen logo, kleuren, producten en toon.": "Your emails get your own logo, colours, products and tone of voice.",
 "Met een reeks automatische mails haal je een deel van die klanten alsnog binnen. Zonder extra advertentiebudget, in jouw huisstijl, en het loopt vanzelf.": "A series of automated emails brings part of those customers back. No extra ad spend, in your brand style, and it runs on its own.",
 "Onderwerp:": "Subject:",
 "JOUW LOGO": "YOUR LOGO",
 "Je vergat nog iets": "You left something behind",
 "We hebben je mandje voor je bewaard. Rond je bestelling af wanneer het jou uitkomt.": "We saved your cart for you. Complete your order whenever it suits you.",
 "Maat M · Zand · 1 stuk": "Size M · Sand · Qty 1",
 "Afrekenen": "Check out",
 "Voorbeeld. Jouw mails krijgen je eigen logo, kleuren en producten.": "Example only. Your emails get your own logo, colours and products.",
 "Stap 1": "Step 1",
 "Begin met een kennismaking": "Start with an intro call",
 "Een vrijblijvend gesprek van een half uur over je webshop en je cijfers. Je hoeft niets voor te bereiden.": "A no-obligation half-hour call about your store and your numbers. Nothing to prepare.",
 "Max. 3 nieuwe klanten per maand": "Max. 3 new clients per month",
 "We kijken samen naar je webshop, je cijfers en hoe je nu met verlaten mandjes omgaat.": "We look at your store, your numbers and how you handle abandoned carts today.",
 "Je weet daarna:": "Afterwards you know:",
 "wat een mailreeks jouw webshop kan opleveren.": "what an email series could bring your store.",
 "Je krijgt een concreet plan: welke mails, wanneer ze verstuurd worden en wat het kost.": "You get a concrete plan: which emails, when they go out and what it costs.",
 "Je krijgt:": "You get:",
 "een vaste prijs. Je zit nergens aan vast tot je akkoord geeft.": "a fixed price. You're not committed to anything until you say yes.",
 "Insightance richt Klaviyo in en bouwt de mails in jouw huisstijl. Jij keurt ze goed voordat ze live gaan.": "Insightance sets up Klaviyo and builds the emails in your brand style. You approve them before they go live.",
 "Is alles getest en ben je tevreden, dan betaal je de tweede helft.": "Once everything is tested and you're happy, you pay the second half.",
 "een reeks die vanzelf draait, en uitleg over wat hij oplevert.": "a series that runs on its own, and a walkthrough of what it brings in.",
}
I18N_HTML = {'7 van de 10 winkelmandjes worden nooit afgerekend. <em><span class="u">Haal die omzet terug.</span></em>': '7 in 10 shopping carts are never checked out. <em><span class="u">Win that revenue back.</span></em>'}

# alle vertaalde teksten moeten in de pagina voorkomen en omgekeerd
for k in I18N_HTML: assert k in MAIN, 'html-vertaling past niet: ' + k
for m in re.findall(r'data-i18n>([^<]*)<', MAIN + header + footer):
    key = m.replace('&amp;', '&')
    assert key in I18N or key in I18N_HTML, 'vertaling ontbreekt: ' + key

JS = '''<script>
  try { history.scrollRestoration = 'manual'; } catch (e) {}
  if (!location.hash) { const toTop = () => window.scrollTo(0, 0); toTop(); window.addEventListener('load', toTop); }
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const inView = el => { const r = el.getBoundingClientRect(); return r.bottom > 0 && r.top < window.innerHeight; };
  const I18N = __I18N__, I18N_HTML = __I18N_HTML__;
  let LANG = 'nl';

  // logo
  const tpl = document.getElementById('logo-svg');
  document.querySelectorAll('.logo[data-bar]').forEach(el => {
    const svg = tpl.content.firstElementChild.cloneNode(true);
    svg.querySelector('.bar').setAttribute('fill', el.dataset.bar);
    svg.querySelector('.curve').setAttribute('stroke', el.dataset.curve);
    svg.querySelectorAll('.dot').forEach(d => d.setAttribute('fill', el.dataset.curve));
    el.prepend(svg);
  });

  // rekentool: 70% van de mandjes wordt verlaten, een goede reeks haalt 5 tot 10% terug
  const $ = id => document.getElementById(id);
  const eur = n => '\u20ac\u00a0' + Math.round(n).toLocaleString(LANG === 'en' ? 'en-GB' : 'nl-NL');
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  function calc() {
    const orders = clamp(parseFloat(($('c-orders').value || '0').replace(/[^0-9]/g, '')) || 0, 0, 100000);
    const aov = clamp(parseFloat(($('c-aov').value || '0').replace(',', '.').replace(/[^0-9.]/g, '')) || 0, 0, 100000);
    const carts = orders / 0.3 * 0.7, lost = carts * aov;
    $('o-carts').textContent = Math.round(carts).toLocaleString(LANG === 'en' ? 'en-GB' : 'nl-NL');
    $('o-lost').textContent = eur(lost);
    $('o-month').textContent = eur(lost * .05) + ' \u2013 ' + eur(lost * .10);
    $('o-year').textContent = eur(lost * .05 * 12) + ' \u2013 ' + eur(lost * .10 * 12) + (LANG === 'en' ? ' per year' : ' per jaar');
  }
  [['r-orders', 'c-orders'], ['r-aov', 'c-aov']].forEach(([r, c]) => {
    $(r).addEventListener('input', () => { $(c).value = $(r).value; calc(); });
    $(c).addEventListener('input', () => { const v = parseFloat($(c).value.replace(',', '.')); if (!isNaN(v)) $(r).value = v; calc(); });
  });

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
      const l = reduce ? len : (yHead <= yStart ? 0 : (yHead >= yEnd ? len : lenAtY(yHead)));
      drawP.style.strokeDashoffset = len - l; const pt = drawP.getPointAtLength(l);
      dot.querySelectorAll('circle').forEach(c => { c.setAttribute('cx', pt.x); c.setAttribute('cy', pt.y); }); dot.style.opacity = l > 2 ? 1 : 0;
    }
    window.addEventListener('scroll', update, { passive: true }); window.addEventListener('resize', build); window.addEventListener('load', build);
    if (document.fonts) document.fonts.ready.then(build);
    let lastH = 0; setInterval(() => { const h = main.offsetHeight; if (h !== lastH) { lastH = h; build(); } }, 800);
    build();
  })();

  // nav-rand en chatknop
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

  // taal
  function setLang(l) {
    LANG = l; document.documentElement.lang = l;
    { const TT = window.__tt || (window.__tt = [document.title, (document.querySelector('meta[property="og:title"]') || {}).content || document.title]); document.title = l === 'en' ? TT[1] : TT[0]; }
    document.querySelectorAll('[data-i18n]').forEach(el => { if (el.dataset.nl === undefined) el.dataset.nl = el.textContent; el.textContent = l === 'en' ? (I18N[el.dataset.nl] || el.dataset.nl) : el.dataset.nl; });
    document.querySelectorAll('[data-i18n-html]').forEach(el => { if (el.dataset.nl === undefined) el.dataset.nl = el.innerHTML; el.innerHTML = l === 'en' ? (I18N_HTML[el.dataset.nl] || el.dataset.nl) : el.dataset.nl; });
    document.querySelectorAll('.lang span').forEach(sp => sp.classList.toggle('on', sp.dataset.l === l));
    calc();
    try { localStorage.setItem('lang', l); } catch (e) {}
  }
  document.querySelector('.lang').addEventListener('click', e => { const sp = e.target.closest('span[data-l]'); setLang(sp ? sp.dataset.l : (LANG === 'nl' ? 'en' : 'nl')); });
  { let saved = null; try { saved = localStorage.getItem('lang'); } catch (e) {}
    // geen eigen keuze: toestel met Nederlands als eerste taal krijgt NL, alle andere EN
    const browserNl = /^nl/i.test((navigator.languages && navigator.languages[0]) || navigator.language || '');
    const isBot = /bot|crawl|spider|slurp|lighthouse|facebookexternalhit|embedly|preview/i.test(navigator.userAgent);
    if (saved === 'en' || (!saved && !browserNl && !isBot)) setLang('en'); }
  calc();
</script>

'''.replace('__I18N__', json.dumps(I18N, ensure_ascii=False)).replace('__I18N_HTML__', json.dumps(I18N_HTML, ensure_ascii=False))

page = head + CSS + '</style>\n</head>\n<body>\n\n' + header + MAIN + footer + JS + cookie
(DOCS / 'webshops.html').write_text(page, encoding='utf-8', newline='')
print('ok', len(page))
