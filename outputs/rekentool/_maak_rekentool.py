"""Voegt de algemene rekentool toe aan de homepage (versie 2: dashboard-uitstraling).
Standaard schrijft hij een VOORBEELD naar docs/_preview-index.html (index.html blijft onaangeraakt).
Met --live wordt docs/index.html zelf aangepast (alleen na akkoord van Oussama)."""
import json, pathlib, sys

DOCS = pathlib.Path(r'C:\Users\oussa\Downloads\aios-starter-kit\aios-starter-kit\docs')
LIVE = '--live' in sys.argv
s = (DOCS / 'index.html').read_text(encoding='utf-8')
assert 'id="rekentool"' not in s, 'rekentool staat er al in'

CSS = r'''
  /* ===== rekentool: hoeveel tijd kun jij terugwinnen (2026-10-13) ===== */
  #rekentool { padding-block: 72px; }
  .rt { display: grid; grid-template-columns: minmax(0, 1.08fr) minmax(0, .92fr); border-radius: 24px; overflow: hidden; border: 1px solid var(--line); background: var(--white); box-shadow: 0 50px 90px -60px rgba(23,52,95,.55); }
  .rt-in { padding: 34px 36px 30px; display: grid; gap: 26px; align-content: start; }
  .rt-step { display: grid; gap: 14px; }
  .rt-step-h { display: flex; align-items: center; gap: 12px; font-size: 15.5px; font-weight: 600; color: var(--navy); }
  .rt-step-h i { width: 26px; height: 26px; border-radius: 50%; background: var(--navy); color: #fff; font: 700 13px var(--sans); font-style: normal; display: grid; place-items: center; flex-shrink: 0; }
  .rt-step-h small { margin-left: auto; font-size: 12.5px; font-weight: 500; color: var(--faint); }
  .rt-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .rt-task { position: relative; display: grid; grid-template-columns: 38px 1fr; gap: 4px 12px; align-items: center; text-align: left; padding: 13px 14px; border-radius: 14px; border: 1.5px solid var(--line); background: var(--white); cursor: pointer; transition: border-color .2s, background .2s, box-shadow .2s; }
  .rt-task:hover { border-color: #9DBBE3; }
  .rt-task:focus-visible { outline: 2px solid var(--bright); outline-offset: 2px; }
  .rt-task .ic { grid-row: span 2; width: 38px; height: 38px; border-radius: 10px; background: var(--soft); color: var(--muted); display: grid; place-items: center; transition: background .2s, color .2s; }
  .rt-task .ic svg { width: 19px; height: 19px; }
  .rt-task b { font-size: 14px; font-weight: 600; color: var(--navy); line-height: 1.3; padding-right: 18px; }
  .rt-task .add { font-size: 12.5px; color: var(--faint); }
  .rt-task .stp { display: none; align-items: center; gap: 6px; }
  .rt-task .stp span { min-width: 52px; text-align: center; font: 600 13.5px var(--sans); color: var(--navy); font-variant-numeric: tabular-nums; }
  .rt-task .stp em { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-style: normal; font-weight: 700; font-size: 15px; line-height: 1; color: var(--bright); background: #fff; border: 1px solid #CFDDF2; user-select: none; transition: background .15s, color .15s; }
  .rt-task .stp em:hover { background: var(--bright); color: #fff; border-color: var(--bright); }
  .rt-task .tick { position: absolute; top: 9px; right: 9px; width: 18px; height: 18px; border-radius: 50%; border: 1.5px solid var(--line); background: #fff; display: grid; place-items: center; transition: background .2s, border-color .2s; }
  .rt-task .tick svg { width: 11px; height: 11px; color: #fff; opacity: 0; }
  .rt-task[aria-pressed="true"] { border-color: var(--bright); background: linear-gradient(160deg, var(--tint), #fff 80%); box-shadow: 0 10px 24px -18px rgba(31,94,255,.6); }
  .rt-task[aria-pressed="true"] .ic { background: var(--bright); color: #fff; }
  .rt-task[aria-pressed="true"] .add { display: none; }
  .rt-task[aria-pressed="true"] .stp { display: flex; }
  .rt-task[aria-pressed="true"] .tick { background: var(--bright); border-color: var(--bright); }
  .rt-task[aria-pressed="true"] .tick svg { opacity: 1; }
  .rt-task.own { grid-column: 1 / -1; border-style: dashed; }
  .rt-task.own[aria-pressed="true"] { border-style: solid; }
  .rt-task.own .own-row { display: none; align-items: center; gap: 12px; padding-right: 26px; }
  .rt-task.own[aria-pressed="true"] .own-row { display: flex; }
  .rt-task.own[aria-pressed="true"] b { display: none; }
  .rt-task.own[aria-pressed="true"] .own-row { grid-column: 2; grid-row: 1 / span 2; }
  #rekentool .rt-own { flex: 1; min-width: 0; font: 500 14px var(--sans); color: var(--navy); background: #fff; border: 1px solid #CFDDF2; border-radius: 10px; padding: 9px 12px; box-shadow: none; outline: none; }
  #rekentool .rt-own:focus { border-color: var(--bright); box-shadow: 0 0 0 3px rgba(31,94,255,.15); }
  .rt-rate { display: grid; gap: 10px; padding: 16px 18px 12px; border-radius: 14px; background: var(--soft); }
  .rt-rate-top { display: flex; justify-content: space-between; align-items: baseline; }
  .rt-rate-top span { font-size: 13.5px; color: var(--muted); }
  .rt-rate-top b { font: 600 22px var(--sans); color: var(--navy); font-variant-numeric: tabular-nums; }
  #rekentool .rt-range { -webkit-appearance: none; appearance: none; width: 100%; height: 26px; background: transparent; border: 0; border-radius: 0; padding: 0; box-shadow: none; margin: 0; cursor: pointer; --p: 20%; }
  .rt-range::-webkit-slider-runnable-track { height: 6px; border-radius: 100px; background: linear-gradient(90deg, var(--bright) var(--p), #D6E0EE var(--p)); }
  .rt-range::-moz-range-track { height: 6px; border-radius: 100px; background: linear-gradient(90deg, var(--bright) var(--p), #D6E0EE var(--p)); }
  .rt-range::-webkit-slider-thumb { -webkit-appearance: none; width: 22px; height: 22px; margin-top: -8px; border-radius: 50%; background: #fff; border: 2px solid var(--bright); box-shadow: 0 4px 12px -4px rgba(31,94,255,.6); }
  .rt-range::-moz-range-thumb { width: 18px; height: 18px; border-radius: 50%; background: #fff; border: 2px solid var(--bright); box-shadow: 0 4px 12px -4px rgba(31,94,255,.6); }
  .rt-range:focus-visible { outline: 2px solid var(--bright); outline-offset: 4px; border-radius: 6px; }
  .rt-scale { display: flex; justify-content: space-between; font-size: 12px; color: var(--faint); }
  .rt-note { font-size: 12.5px; color: var(--faint); margin: 0; line-height: 1.55; }

  .rt-out { position: relative; isolation: isolate; background: var(--navy); color: #fff; padding: 34px 34px 30px; display: grid; gap: 22px; align-content: start; }
  .rt-out::before { content: ""; position: absolute; inset: 0; z-index: -1; background: radial-gradient(70% 55% at 100% 0%, rgba(31,94,255,.5), transparent 70%), radial-gradient(60% 50% at 0% 100%, rgba(61,106,168,.35), transparent 70%); }
  .rt-out-lbl { font-size: 12px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--mid-on-dark); }
  .rt-hero { display: grid; grid-template-columns: 132px 1fr; gap: 22px; align-items: center; }
  .rt-ring { position: relative; width: 132px; height: 132px; }
  .rt-ring svg { width: 100%; height: 100%; transform: rotate(-90deg); }
  .rt-ring circle { fill: none; stroke-width: 11; }
  .rt-ring .bg { stroke: rgba(255,255,255,.12); }
  .rt-ring .hi { stroke: rgba(255,255,255,.42); stroke-linecap: round; transition: stroke-dasharray .5s var(--ease); }
  .rt-ring .lo { stroke: #4F86FF; stroke-linecap: round; transition: stroke-dasharray .5s var(--ease); }
  .rt-ring div { position: absolute; inset: 0; display: grid; place-content: center; text-align: center; }
  .rt-ring div b { font: 600 22px var(--sans); font-variant-numeric: tabular-nums; }
  .rt-ring div small { font-size: 11.5px; color: rgba(255,255,255,.7); max-width: 86px; line-height: 1.3; }
  .rt-money { display: grid; gap: 6px; }
  .rt-key { display: flex; flex-wrap: wrap; gap: 4px 14px; margin-top: 8px; font-size: 12px; color: rgba(255,255,255,.72); }
  .rt-key span { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
  .rt-key i { width: 9px; height: 9px; border-radius: 50%; background: #4F86FF; }
  .rt-key i.hi { background: rgba(255,255,255,.55); }
  .rt-key i.bg { background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.25); }
  .rt-money small { font-size: 13.5px; color: rgba(255,255,255,.75); }
  .rt-money b { font-family: var(--serif); font-size: clamp(24px, 2.2vw, 31px); font-weight: 600; line-height: 1.15; font-variant-numeric: tabular-nums; }
  .rt-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
  .rt-stat { padding: 14px 14px 12px; border-radius: 14px; background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.1); display: grid; gap: 4px; align-content: start; }
  .rt-stat b { font: 600 18px var(--sans); font-variant-numeric: tabular-nums; white-space: nowrap; }
  .rt-stat span { font-size: 12.5px; color: rgba(255,255,255,.7); line-height: 1.35; }
  .rt-cta { display: grid; gap: 14px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,.12); }
  .rt-who { display: flex; align-items: center; gap: 12px; font-size: 14px; color: rgba(255,255,255,.85); }
  .rt-who img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(255,255,255,.25); flex-shrink: 0; }
  .rt-cta .acts { display: flex; flex-wrap: wrap; align-items: center; gap: 14px; }
  .rt-cta .acts small { font-size: 13px; color: rgba(255,255,255,.6); }
  @media (max-width: 1080px) { .rt { grid-template-columns: 1fr; } }
  @media (max-width: 560px) {
    #rekentool { padding-block: 48px !important; }
    .rt-in, .rt-out { padding: 24px 18px; }
    .rt-grid { grid-template-columns: 1fr; }
    .rt-step-h small { display: none; }
    .rt-task.own .own-row { flex-wrap: wrap; }
    #rekentool .rt-own { flex-basis: 100%; }
    .rt-hero { grid-template-columns: 112px 1fr; gap: 16px; }
    .rt-ring { width: 112px; height: 112px; }
    .rt-stats { grid-template-columns: 1fr; }
    .rt-stat { grid-template-columns: auto 1fr; align-items: baseline; gap: 10px; }
  }
'''

ICON = {
    'offertes': '<path d="M14 3H6v18h12V7z"/><path d="M14 3v4h4M9 13h6M9 17h4"/>',
    'facturen': '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
    'klant': '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 21l1.9-5.4A8 8 0 1 1 21 12z"/>',
    'plannen': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    'rapport': '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    'invoer': '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h.01M11 10h.01M15 10h.01M7 14h10"/>',
}
TASKS = [  # id, naam NL, naam EN, standaard aan, standaard uren
    ('offertes', 'Offertes maken', 'Writing quotes', True, 3),
    ('facturen', 'Facturen en herinneringen', 'Invoices and reminders', True, 2),
    ('klant', 'Klantvragen beantwoorden', 'Answering customer questions', True, 4),
    ('plannen', 'Afspraken plannen', 'Scheduling appointments', False, 2),
    ('rapport', 'Rapportages en cijfers', 'Reports and numbers', False, 2),
    ('invoer', 'Gegevens overtypen', 'Re-typing data', False, 3),
]
svg = lambda k: f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[k]}</svg>'
TICK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>'
tasks = ''.join(
    f'<div class="rt-task" role="button" tabindex="0" data-t="{t}" data-h="{h}" aria-pressed="{str(on).lower()}">'
    f'<span class="ic">{svg(t)}</span><b>{nl}</b><span class="add">+ Toevoegen</span>'
    f'<span class="stp"><em data-d="-1" aria-label="Minder uren">−</em><span>{h} uur</span><em data-d="1" aria-label="Meer uren">+</em></span>'
    f'<span class="tick" aria-hidden="true">{TICK}</span></div>'
    for t, nl, en, on, h in TASKS)

SECTION = f'''
  <!-- REKENTOOL -->
  <section id="rekentool">
    <div class="wrap">
      <div class="sec-head rv">
        <div class="eyebrow">Rekentool</div>
        <h2>Hoeveel tijd kun jij terugwinnen?</h2>
        <p>Kies de taken die bij jou elke week terugkomen en schat hoeveel uur ze kosten. Je ziet direct wat dat handwerk per jaar kost, en wat automatiseren kan opleveren.</p>
      </div>
      <div class="rt rv">
        <div class="rt-in">
          <div class="rt-step">
            <div class="rt-step-h"><i>1</i><span>Welke taken kosten je elke week tijd?</span><small>Uren per week</small></div>
            <div class="rt-grid">{tasks}<div class="rt-task own" role="button" tabindex="0" data-t="eigen" data-h="2" aria-pressed="false"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg></span><b>Eigen taak</b><span class="add">Staat jouw taak er niet bij? Voeg hem toe</span><span class="own-row"><input class="rt-own" type="text" maxlength="40" placeholder="Bijvoorbeeld: voorraad bijhouden" aria-label="Naam van je eigen taak"><span class="stp"><em data-d="-1" aria-label="Minder uren">−</em><span>2 uur</span><em data-d="1" aria-label="Meer uren">+</em></span></span><span class="tick" aria-hidden="true">{TICK}</span></div></div>
          </div>
          <div class="rt-step">
            <div class="rt-step-h"><i>2</i><span>Wat is een uur van jou waard?</span></div>
            <div class="rt-rate">
              <div class="rt-rate-top"><span>Jouw uurwaarde</span><b id="rt-rate-o">€ 50</b></div>
              <input class="rt-range" type="range" id="rt-rate" min="25" max="150" step="5" value="50" aria-label="Uurwaarde in euro">
              <div class="rt-scale"><span>€ 25</span><span>€ 150</span></div>
            </div>
          </div>
          <p class="rt-note">Een schatting: we gaan ervan uit dat 50 tot 70% van deze taken te automatiseren is, over 46 werkweken per jaar. In een gesprek kijken we wat er bij jou echt kan.</p>
        </div>
        <div class="rt-out" aria-live="polite">
          <div class="rt-out-lbl">Jouw resultaat</div>
          <div class="rt-hero">
            <div class="rt-ring"><svg viewBox="0 0 120 120" aria-hidden="true"><circle class="bg" cx="60" cy="60" r="50"/><circle class="hi" id="rt-ring-hi" cx="60" cy="60" r="50"/><circle class="lo" id="rt-ring-lo" cx="60" cy="60" r="50"/></svg><div><b id="rt-win">± 5</b><small id="rt-win-u">uur per week terug</small></div></div>
            <div class="rt-money"><small>Terug te winnen per jaar</small><b id="rt-year">€ 10.350 – € 14.490</b><div class="rt-key"><span><i class="lo"></i>Zeker te automatiseren</span><span><i class="hi"></i>Waarschijnlijk ook</span><span><i class="bg"></i>Blijft handwerk</span></div></div>
          </div>
          <div class="rt-stats">
            <div class="rt-stat"><b id="rt-h">9 uur</b><span>handwerk per week</span></div>
            <div class="rt-stat"><b id="rt-cost">€ 20.700</b><span>kost dat nu per jaar</span></div>
            <div class="rt-stat"><b id="rt-days">26 – 36</b><span>werkdagen per jaar terug</span></div>
          </div>
          <div class="rt-cta">
            <div class="rt-who"><img src="images/oussama.png" alt="" loading="lazy"><span>Oussama rekent het in 30 minuten met je door</span></div>
            <div class="acts"><a class="btn" href="#contact">Bespreek jouw situatie</a><small>Vrijblijvend</small></div>
          </div>
        </div>
      </div>
    </div>
  </section>
'''

JS = '''
<script>
  // rekentool: uren per taak x uurwaarde, 50 tot 70% te automatiseren, 46 werkweken per jaar
  (function () {
    const box = document.getElementById('rekentool'); if (!box) return;
    const $ = id => document.getElementById(id), en = () => (window.LANG || document.documentElement.lang) === 'en';
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const num = n => Math.round(n).toLocaleString(en() ? 'en-GB' : 'nl-NL'), eur = n => '\\u20ac\\u00a0' + num(n);
    const hrs = n => num(n) + (en() ? (Math.round(n) === 1 ? ' hour' : ' hours') : ' uur');
    const WEEKS = 46, LO = .5, HI = .7, C = 2 * Math.PI * 50;
    // getallen tellen soepel naar de nieuwe waarde
    const shown = {};
    function tween(id, vals, fmt) {
      const el = $(id), from = shown[id] || vals.map(() => 0); shown[id] = vals;
      if (reduce) { el.textContent = fmt(vals); return; }
      const t0 = performance.now();
      (function step(t) { const k = Math.min(1, (t - t0) / 420), e = 1 - Math.pow(1 - k, 3); el.textContent = fmt(vals.map((v, i) => from[i] + (v - from[i]) * e)); if (k < 1) requestAnimationFrame(step); })(t0);
    }
    function calc() {
      let h = 0;
      box.querySelectorAll('.rt-task').forEach(t => { t.querySelector('.stp span').textContent = hrs(+t.dataset.h); if (t.getAttribute('aria-pressed') === 'true') h += +t.dataset.h; });
      const r = $('rt-rate'), rate = +r.value; $('rt-rate-o').textContent = eur(rate);
      r.style.setProperty('--p', ((rate - r.min) / (r.max - r.min) * 100) + '%');
      const cost = h * rate * WEEKS;
      tween('rt-win', [h * (LO + HI) / 2], v => '\\u00b1\\u00a0' + num(v[0]));
      $('rt-win-u').textContent = en() ? 'hours a week back' : 'uur per week terug';
      tween('rt-year', [cost * LO, cost * HI], v => eur(v[0]) + ' \\u2013 ' + eur(v[1]));
      tween('rt-h', [h], v => hrs(v[0]));
      tween('rt-cost', [cost], v => eur(v[0]));
      tween('rt-days', [h * LO * WEEKS / 8, h * HI * WEEKS / 8], v => Math.round(v[0]) === Math.round(v[1]) ? '\\u00b1\\u00a0' + num(v[0]) : num(v[0]) + ' \\u2013 ' + num(v[1]));
      $('rt-ring-lo').style.strokeDasharray = (h ? C * LO : 0) + ' ' + C;
      $('rt-ring-hi').style.strokeDasharray = (h ? C * HI : 0) + ' ' + C;
    }
    box.querySelectorAll('.rt-task').forEach(t => {
      const toggle = () => { const on = t.getAttribute('aria-pressed') !== 'true'; t.setAttribute('aria-pressed', on); calc(); const f = t.querySelector('.rt-own'); if (on && f && !f.value) setTimeout(() => f.focus({ preventScroll: true }), 30); };
      t.addEventListener('click', e => {
        if (e.target.closest('.rt-own')) return;
        const b = e.target.closest('em[data-d]');
        if (b) { e.stopPropagation(); t.dataset.h = Math.max(1, Math.min(20, +t.dataset.h + +b.dataset.d)); calc(); return; }
        toggle();
      });
      t.addEventListener('keydown', e => { if (e.target.closest('.rt-own')) return; if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    });
    $('rt-rate').addEventListener('input', calc);
    // na een taalwissel opnieuw invullen (de vertaling van de pagina loopt eerst)
    new MutationObserver(calc).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
    // pas gaan tellen als de rekentool in beeld komt
    if ('IntersectionObserver' in window && !reduce) {
      calc.done = false;
      const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); calc(); } }, { threshold: .3 });
      io.observe(box.querySelector('.rt-out'));
    } else calc();
  })();
</script>
'''

I18N = {
    'Rekentool': 'Calculator', 'Hoeveel tijd kun jij terugwinnen?': 'How much time could you win back?',
    'Kies de taken die bij jou elke week terugkomen en schat hoeveel uur ze kosten. Je ziet direct wat dat handwerk per jaar kost, en wat automatiseren kan opleveren.':
        'Pick the tasks that come back every week and estimate how many hours they take. You will see right away what that manual work costs you a year, and what automating it could bring.',
    'Welke taken kosten je elke week tijd?': 'Which tasks take up your time every week?', 'Uren per week': 'Hours per week',
    '+ Toevoegen': '+ Add', 'Eigen taak': 'Your own task', 'Staat jouw taak er niet bij? Voeg hem toe': 'Task not listed? Add your own',
    'Zeker te automatiseren': 'Can be automated', 'Waarschijnlijk ook': 'Likely too', 'Blijft handwerk': 'Stays manual', 'Wat is een uur van jou waard?': 'What is an hour of your time worth?', 'Jouw uurwaarde': 'Your hourly value',
    'Een schatting: we gaan ervan uit dat 50 tot 70% van deze taken te automatiseren is, over 46 werkweken per jaar. In een gesprek kijken we wat er bij jou echt kan.':
        'An estimate: we assume 50 to 70% of these tasks can be automated, over 46 working weeks a year. On a call we look at what is really possible for you.',
    'Jouw resultaat': 'Your result', 'Terug te winnen per jaar': 'You could win back each year',
    'handwerk per week': 'of manual work a week', 'kost dat nu per jaar': 'what it costs you now each year', 'werkdagen per jaar terug': 'working days back each year',
    'Oussama rekent het in 30 minuten met je door': 'Oussama will go through the numbers with you in 30 minutes',
    'Bespreek jouw situatie': 'Talk through your situation', 'Vrijblijvend': 'No obligation',
}
for t, nl, en, on, h in TASKS:
    I18N[nl] = en
I18N_ATTR = {'Uurwaarde in euro': 'Hourly value in euros', 'Minder uren': 'Fewer hours', 'Meer uren': 'More hours', 'Bijvoorbeeld: voorraad bijhouden': 'For example: keeping track of stock', 'Naam van je eigen taak': 'Name of your own task'}

# ---- invoegen ----
k = s.rindex('</style>', 0, s.index('<header class="nav"'))
s = s[:k] + CSS + s[k:]
a = '\n  <!-- WERKWIJZE -->'
assert s.count(a) == 1
s = s.replace(a, SECTION + a)
for name, d in (('const I18N = {', I18N), ('const I18N_ATTR = {', I18N_ATTR)):
    assert s.count(name) == 1, name
    s = s.replace(name, name + ''.join(f'{json.dumps(kk, ensure_ascii=False)}: {json.dumps(vv, ensure_ascii=False)}, ' for kk, vv in d.items() if f'{json.dumps(kk, ensure_ascii=False)}:' not in s))
b = s.rindex('</body>')
s = s[:b] + JS + s[b:]

# ---- menu-item en twee verwijzingen naar de rekentool ----
def once(old, new):
    global s
    assert s.count(old) == 1, (old[:60], s.count(old))
    s = s.replace(old, new)
once('      <li><a href="resultaten.html">Resultaten</a></li>\n', '      <li><a href="resultaten.html">Resultaten</a></li>\n      <li><a href="#rekentool">Rekentool</a></li>\n')
once('  <a href="resultaten.html">Resultaten</a>\n  <a href="#howwework">', '  <a href="resultaten.html">Resultaten</a>\n  <a href="#rekentool">Rekentool</a>\n  <a href="#howwework">')
once('\n      </div>\n      <div class="week rv"', '\n        <a class="link rt-promo" href="#rekentool">Bereken het voor jouw bedrijf →</a>\n      </div>\n      <div class="week rv"')
i = s.index('<div class="bens">'); j = s.index('\n        </div>', i) + len('\n        </div>')
s = s[:j] + '\n        <a class="link rt-promo in-panel" href="#rekentool">Bereken wat het jou oplevert →</a>' + s[j:]
k2 = s.rindex('</style>', 0, s.index('<header class="nav"'))
s = s[:k2] + '  .rt-promo { display: inline-block; margin-top: 26px; font-size: 14.5px; }\n  .rt-promo.in-panel { justify-self: start; margin-top: 14px; }\n' + s[k2:]
EXTRA = {'Bereken het voor jouw bedrijf →': 'Work it out for your business →', 'Bereken wat het jou oplevert →': 'See what it could save you →'}
s = s.replace('const I18N = {', 'const I18N = {' + ''.join(f'{json.dumps(kk, ensure_ascii=False)}: {json.dumps(vv, ensure_ascii=False)}, ' for kk, vv in EXTRA.items()), 1)

out = DOCS / ('index.html' if LIVE else '_preview-index.html')
out.write_text(s, encoding='utf-8', newline='')
print('ok', out.name, len(s))
