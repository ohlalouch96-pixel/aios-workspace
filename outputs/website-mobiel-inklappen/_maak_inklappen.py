"""Homepage korter op mobiel door in te klappen (alleen schermen tot 820px; desktop blijft gelijk).
- Werkwijze: per stap alleen titel + label zichtbaar, uitleg klapt open met een tik (stap 1 staat open).
- Diensten: de 6 categorie-tegels verborgen (de knop "Bekijk alle mogelijkheden" blijft).
- Rekentool: de 3 voorgeselecteerde taken zichtbaar, de rest achter "Meer taken tonen" (knop staat in de HTML, zodat de vertaling klopt).
- Voor wie: tik brengt je naar het begin van de sectie; nog een tik op de open tegel klapt hem dicht.
- Ruimte tussen secties overal 48px (hero-onderkant en klantcases waren 56/60px).
Standaard schrijft dit een VOORBEELD naar docs/_preview-index.html; met --live wordt docs/index.html zelf aangepast (alleen na akkoord)."""
import pathlib, sys
DOCS = pathlib.Path(r'C:\Users\oussa\Downloads\aios-starter-kit\aios-starter-kit\docs')
LIVE = '--live' in sys.argv
s = (DOCS / 'index.html').read_text(encoding='utf-8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:70], s.count(a))
    s = s.replace(a, b)


CSS = '''
  @media (max-width: 560px) { .hero { padding-bottom: 48px; } #resultaten { padding-block: 48px !important; } }
  .rt-more { display: none; }
  /* mobiel: lange onderdelen inklappen, zodat de homepage korter wordt (desktop ongewijzigd) */
  @media (max-width: 820px) {
    #process li > p, #process li > .wget { display: none; }
    #process li.open > p, #process li.open > .wget { display: block; }
    #process li > b { position: relative; cursor: pointer; padding-right: 40px; -webkit-tap-highlight-color: transparent; }
    #process li > b::after { content: "+"; position: absolute; right: 0; top: 50%; width: 28px; height: 28px; margin-top: -14px; border-radius: 50%; background: var(--tint); color: var(--bright); display: grid; place-items: center; font-size: 18px; font-weight: 500; transition: transform .25s, background .25s, color .25s; }
    #process li.open > b::after { transform: rotate(45deg); background: var(--bright); color: #fff; }
    .cats { display: none; }
    #forwho .panel.shut { display: none; }
    .rt-grid.fold > .rt-task:nth-child(n+4):not([aria-pressed="true"]) { display: none; }
    .rt-more .m-c, .rt-grid:not(.fold) + .rt-more .m-o { display: none; }
    .rt-grid:not(.fold) + .rt-more .m-c { display: inline; }
    .rt-more { display: block; margin-top: 10px; width: 100%; font: 600 14.5px var(--sans); color: var(--bright); background: var(--white); border: 1px dashed #C7D6EE; border-radius: 14px; padding: 13px; cursor: pointer; }
  }
'''
rep('  /* links naar de landingspagina\'s onder "Voor wie" */', CSS + '\n  /* links naar de landingspagina\'s onder "Voor wie" */')

JS = '''
  // mobiel: werkwijze-stappen klappen open met een tik
  (function () {
    const small = () => window.innerWidth <= 820;
    const steps = [...document.querySelectorAll('#process li')];
    if (steps[0]) steps[0].classList.add('open');
    const hook = (el, head) => head && head.addEventListener('click', () => {
      if (!small()) return;
      el.classList.toggle('open');
      window.dispatchEvent(new Event('resize'));  // lijn langs de stappen en de rode draad opnieuw meten
    });
    steps.forEach(li => hook(li, li.querySelector(':scope > b')));
    // rekentool: extra taken achter een knop
    const grid = document.querySelector('.rt-grid');
    if (grid) {
      grid.classList.add('fold');
      document.querySelector('.rt-more').addEventListener('click', () => { grid.classList.toggle('fold'); window.dispatchEvent(new Event('resize')); });
    }
  })();
'''
rep('  // werkwijzelijn eindigt precies bij stap 4\n', JS + '\n  // werkwijzelijn eindigt precies bij stap 4\n')

# vertaling van de knop (homepage vertaalt tekstknopen via I18N)
rep('"Speciaal voor jouw branche": "Made for your industry",', '"Speciaal voor jouw branche": "Made for your industry", "Meer taken tonen": "Show more tasks", "Minder taken tonen": "Show fewer tasks",')

# knop "Meer taken tonen" direct na de takenlijst (twee teksten, zodat de vertaler beide kent)
END_GRID = '<path d="M20 6 9 17l-5-5"/></svg></span></div></div>\n'
i = s.index('<div class="rt-grid">'); j = s.index(END_GRID, i) + len(END_GRID)
s = s[:j] + '            <button type="button" class="rt-more"><span class="m-o">Meer taken tonen</span><span class="m-c">Minder taken tonen</span></button>\n' + s[j:]

# Voor wie (mobiel): tik brengt je naar het begin van de sectie; nog een tik op de open tegel klapt hem dicht
rep('''    tabs.forEach((t, k) => t.addEventListener('click', () => {
      auto = false; clearInterval(timer);
      const before''', '''    tabs.forEach((t, k) => t.addEventListener('click', () => {
      auto = false; clearInterval(timer);
      if (mobile()) {
        const shut = k === cur && !panel.classList.contains('shut');
        panel.classList.toggle('shut', shut);
        if (shut) tabs.forEach(x => x.setAttribute('aria-selected', 'false')); else show(k);
        const top = sec.querySelector('.sec-head').getBoundingClientRect().top + window.scrollY - document.getElementById('nav').offsetHeight - 16;
        window.scrollTo({ top, behavior: reduce ? 'auto' : 'smooth' });
        return;
      }
      const before''')
rep("    window.addEventListener('resize', place);\n    place();", "    window.addEventListener('resize', () => { if (!mobile() && panel.classList.contains('shut')) { panel.classList.remove('shut'); show(cur); } place(); });\n    place();")

out = DOCS / ('index.html' if LIVE else '_preview-index.html')
out.write_text(s, encoding='utf-8', newline='')
print('ok', out.name)
