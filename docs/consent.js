// cookiemelding + Google Analytics 4, gedeeld door alle pagina's in docs/
// GA4 laadt pas na "Akkoord". Keuze staat in localStorage "cookie_consent": 'all' of 'functional'.
// Oude waarde 'accepted' (alleen functioneel gevraagd) telt niet als akkoord, die bezoekers zien de melding opnieuw.
(function () {
  const GA_ID = 'G-K1EFV00ZCN'; // Measurement ID uit GA4: Beheer > Gegevensstromen > webstream
  const KEY = 'cookie_consent';

  const get = () => { try { return localStorage.getItem(KEY); } catch (e) { return null; } };
  const set = (v) => { try { localStorage.setItem(KEY, v); } catch (e) {} };

  // herkenbare bots (linkcheckers van Meta/LinkedIn, headless browsers) niet meetellen
  const isBot = navigator.webdriver || /bot|crawl|spider|slurp|headless|preview|externalhit|meta-external|lighthouse|pingdom|monitor/i.test(navigator.userAgent);

  let gaLoaded = false;
  function loadGA() {
    if (gaLoaded || isBot || !/^G-[A-Z0-9]+$/.test(GA_ID) || GA_ID === 'G-XXXXXXXXXX') return;
    gaLoaded = true;
    const s = document.createElement('script');
    s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag('js', new Date());
    gtag('config', GA_ID);
  }

  // intrekken: GA-cookies weghalen en pagina herladen zodat gtag niet meer actief is
  function dropGA() {
    document.cookie.split(';').map((c) => c.split('=')[0].trim()).filter((n) => /^_ga/.test(n)).forEach((n) => {
      ['', '; domain=' + location.hostname, '; domain=.' + location.hostname.replace(/^www\./, '')].forEach((d) => {
        document.cookie = n + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + d;
      });
    });
  }

  const T = {
    nl: ['Insightance gebruikt functionele cookies om de website goed te laten werken. Ga je akkoord, dan gebruiken we ook Google Analytics om te zien hoe bezoekers de website gebruiken. <a href="/privacybeleid.html#p8">Meer informatie</a>', 'Alleen functioneel', 'Akkoord'],
    en: ['Insightance uses functional cookies to make the website work properly. If you accept, we also use Google Analytics to see how visitors use the website. <a href="/privacybeleid.html#p8">More information</a>', 'Functional only', 'Accept'],
  };

  const CSS = '.ck{position:fixed;z-index:60;left:20px;bottom:max(20px,env(safe-area-inset-bottom,0px));max-width:440px;display:grid;gap:12px;padding:18px 20px;background:#fff;color:#17345F;border:1px solid #C9D5E4;border-radius:16px;box-shadow:0 24px 48px -20px rgba(23,52,95,.35);font:14px/1.55 "Inter",system-ui,sans-serif;text-align:left}'
    + '.ck[hidden]{display:none}.ck p{margin:0;color:#465369}.ck p a{color:#1F5EFF}.ck-b{display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap}'
    + '.ck-b button{font:600 14px/1 "Inter",system-ui,sans-serif;border-radius:100px;padding:10px 18px;cursor:pointer;border:1px solid #C9D5E4;background:#fff;color:#17345F}'
    + '.ck-b button.ok{background:#1F5EFF;border-color:#1F5EFF;color:#fff}@media (max-width:560px){.ck{left:12px;right:12px;max-width:none}}';

  function box() {
    let b = document.getElementById('ck');
    if (b) return b;
    // pagina's zonder eigen cookiemelding: zelf opbouwen
    const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    b = document.createElement('div');
    b.className = 'ck'; b.id = 'ck'; b.setAttribute('role', 'dialog'); b.setAttribute('aria-live', 'polite'); b.hidden = true;
    b.innerHTML = '<p id="ck-t"></p><div class="ck-b"><button type="button" id="ck-no"></button><button type="button" class="ok" id="ck-ok"></button></div>';
    document.body.appendChild(b);
    return b;
  }

  let ready = false;
  function open(delay) {
    const b = box();
    const fill = () => { const t = T[document.documentElement.lang === 'en' ? 'en' : 'nl']; document.getElementById('ck-t').innerHTML = t[0]; document.getElementById('ck-no').textContent = t[1]; document.getElementById('ck-ok').textContent = t[2]; };
    if (!ready) {
      ready = true;
      new MutationObserver(fill).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
      const close = (v) => {
        const was = get(); set(v);
        b.hidden = true; document.body.classList.remove('ck-open');
        if (v === 'all') loadGA();
        else if (was === 'all') { dropGA(); location.reload(); }
      };
      document.getElementById('ck-ok').addEventListener('click', () => close('all'));
      document.getElementById('ck-no').addEventListener('click', () => close('functional'));
    }
    fill();
    setTimeout(() => { b.hidden = false; document.body.classList.add('ck-open'); }, delay);
  }

  // acties meten (alleen als GA na akkoord geladen is). Sleutelgebeurtenissen in GA4 aanvinken:
  // gesprek_ingepland, contactformulier_verstuurd, whatsapp_klik, email_klik
  function track(name, params) { if (gaLoaded && window.gtag) gtag('event', name, params || {}); }
  window.insTrack = track;

  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('a'); if (!a) return;
    const h = a.getAttribute('href') || '';
    if (/calendly\.com/.test(h) || a.classList.contains('bk-open')) track('agenda_geopend');
    else if (/wa\.me|whatsapp\.com/.test(h)) track('whatsapp_klik');
    else if (/^mailto:/.test(h)) track('email_klik');
    else if (/#contact$/.test(h)) track('contact_knop_klik');
  }, true);

  // Calendly meldt een geboekte afspraak via postMessage
  window.addEventListener('message', (e) => {
    if (/calendly\.com$/.test((e.origin || '').replace(/^https?:\/\//, '')) && e.data && e.data.event === 'calendly.event_scheduled') track('gesprek_ingepland');
  });

  let calcDone = false;
  const onCalc = (e) => { if (!calcDone && e.target.closest && e.target.closest('#rekentool')) { calcDone = true; track('rekentool_gebruikt'); } };
  document.addEventListener('input', onCalc, true);
  document.addEventListener('change', onCalc, true);
  document.addEventListener('submit', (e) => { if (e.target.id === 'tform') track('offertetool_demo_gebruikt'); }, true);

  // keuze later wijzigen, bv. via de link in het privacybeleid
  window.insightanceCookies = () => open(0);

  const c = get();
  if (c === 'all') loadGA();
  else if (c !== 'functional') {
    if (document.body) open(800); else document.addEventListener('DOMContentLoaded', () => open(800));
  }
})();
