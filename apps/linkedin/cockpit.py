"""
LinkedIn Outreach — Lokale webcockpit

Draait alleen op Oussama's eigen laptop (127.0.0.1), geen Telegram, geen
doorlopende kosten. Toont klaarstaande kandidaten met knoppen Verstuurd /
Aanpassen / Overslaan, due follow-ups, en een dashboard met cijfers — zelfde
interactiepatroon als de Instagram-Telegram-cockpit, andere transportlaag.

Gebruik:
    python apps/linkedin/cockpit.py
    (open daarna http://127.0.0.1:5050 in de browser)
"""

import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template_string, request, url_for

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
sys.path.insert(0, str(WORKSPACE_ROOT / "tools" / "linkedin"))

from config import get_env  # noqa: E402
from db import get_connection  # noqa: E402
from generate_metrics import track_stats, rate  # noqa: E402
import collect_linkedin  # noqa: E402
import limits  # noqa: E402
import wachtrij  # noqa: E402
import browser  # noqa: E402
import vind_prospects  # noqa: E402


def _sync_vers(conn, records):
    """Schrijft de al opgehaalde sheet-records (zie wachtrij.alle_records() in index())
    door naar de lokale database, zodat het dashboard niet kan achterlopen. Doet GEEN
    eigen live Sheets-aanroep meer — collect_linkedin.write() accepteert dezelfde
    veldnamen als wachtrij.KOLOMMEN via zijn bestaande fallback-keys, dus 1 gedeelde
    fetch volstaat i.p.v. de losse collect_linkedin.collect() van hiervoor (snelheidsfix
    14-11, sheet was gegroeid naar 59 rijen en 2x volledig live ophalen werd traag)."""
    try:
        result = {"status": "success", "data": {"rows": records}}
        collect_linkedin.write(conn, result, datetime.now().strftime("%Y-%m-%d"))
    except Exception as e:
        print(f"Waarschuwing: lokale sync mislukt, toon laatst bekende data ({e})")

app = Flask(__name__)


def _ensure_feedback_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS linkedin_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            tekst TEXT NOT NULL,
            verwerkt INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def _dashboard_stats(conn):
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='linkedin'"
    ).fetchone()
    if not exists:
        return None
    rows = [dict(r) for r in conn.execute(
        "SELECT naam, status, datum_verzoek AS d1, datum_bericht1 AS d2, gereageerd FROM linkedin"
    ).fetchall()]
    st = track_stats(rows, datetime.now().date())
    st["reactieratio"] = rate(st["reacties"], st["benaderd"])

    laatste = conn.execute("SELECT MAX(collected_at) AS t FROM linkedin").fetchone()
    st["laatst_bijgewerkt"] = None
    if laatste and laatste["t"]:
        try:
            # collected_at is UTC-aware (zie collect_linkedin.py) — omzetten naar
            # lokale tijd, anders staat er standaard 1 uur "achter" (CET).
            utc_tijd = datetime.fromisoformat(laatste["t"])
            st["laatst_bijgewerkt"] = utc_tijd.astimezone().strftime("%d %b %H:%M")
        except ValueError:
            st["laatst_bijgewerkt"] = laatste["t"]
    return st


PAGINA = """
<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LinkedIn Outreach — Insightance</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --navy:#17345F; --mid:#3D6AA8; --bright:#1F5EFF; --bright-hover:#1449D6;
    --mid-on-dark:#9DBBE3; --tint:#EAF1FB; --soft:#F5F8FC; --white:#FFFFFF;
    --ink:#1B2638; --muted:#465369; --faint:#5E6C84; --line:#C9D5E4;
    --green:#1a8a5e; --green-bg:#e9f7ef; --red:#c0392b; --red-bg:#fdecea;
    --amber:#946c00; --amber-bg:#fef6e0;
  }
  * { box-sizing: border-box; }
  body {
    font-family: 'Inter', -apple-system, 'Segoe UI', Arial, sans-serif;
    margin: 0; background: var(--soft); color: var(--ink);
  }
  .shell { max-width: 980px; margin: 0 auto; padding: 28px 24px 60px; }

  /* Header */
  .topbar { display: flex; align-items: flex-end; justify-content: space-between; flex-wrap: wrap; gap: 14px; margin-bottom: 22px; }
  .brand-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--mid); margin: 0 0 4px; }
  .topbar h1 { font-size: 23px; font-weight: 800; color: var(--navy); margin: 0; }
  .pillrow { display: flex; gap: 8px; flex-wrap: wrap; }
  .pill { background: var(--white); border: 1px solid var(--line); border-radius: 999px; padding: 7px 14px; font-size: 12.5px; font-weight: 600; color: var(--muted); display: flex; align-items: center; gap: 6px; }
  .pill b { color: var(--navy); font-weight: 700; }
  .pill .bar { width: 44px; height: 5px; border-radius: 3px; background: var(--line); overflow: hidden; display: inline-block; }
  .pill .bar span { display: block; height: 100%; background: var(--bright); }
  .pill.week { background: var(--navy); color: var(--white); border-color: var(--navy); }
  .pill.week b { color: var(--white); }

  /* Banners */
  .banner { display: flex; gap: 10px; align-items: flex-start; border-radius: 10px; padding: 13px 16px; margin-bottom: 18px; font-size: 13.5px; line-height: 1.5; }
  .banner.stop { background: var(--red-bg); color: var(--red); border: 1px solid #f3c6c0; }
  .banner.warn { background: var(--amber-bg); color: var(--amber); border: 1px solid #f0ddab; }
  .banner.ok { background: var(--green-bg); color: var(--green); border: 1px solid #bfe3d1; }
  .banner b { font-weight: 700; }

  /* Section headers */
  .sectie { margin-top: 36px; }
  .sectie-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
  .sectie-head h2 { font-size: 14px; font-weight: 700; color: var(--navy); text-transform: uppercase; letter-spacing: .04em; margin: 0; }
  .count-badge { background: var(--tint); color: var(--mid); font-weight: 700; font-size: 12px; border-radius: 999px; padding: 2px 10px; }
  .freshness { font-size: 11.5px; color: var(--faint); font-weight: 500; }

  /* Empty state */
  .leeg { color: var(--faint); font-size: 13.5px; background: var(--white); border: 1px dashed var(--line); border-radius: 10px; padding: 18px; text-align: center; }

  /* Dashboard tiles */
  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 12px; }
  .tile { background: var(--white); border: 1px solid var(--line); border-radius: 12px; padding: 16px 16px 14px; }
  .tile .num { font-size: 24px; font-weight: 800; color: var(--navy); line-height: 1.1; }
  .tile .lbl { font-size: 12px; color: var(--faint); margin-top: 4px; font-weight: 500; }
  .tile.accent .num { color: var(--bright); }
  .tile.warm .num { color: var(--green); }

  /* Candidate card */
  .card { background: var(--white); border: 1px solid var(--line); border-radius: 14px; padding: 20px 22px; margin-bottom: 14px; box-shadow: 0 1px 2px rgba(23,52,95,0.04); }
  .persoon { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
  .avatar { width: 42px; height: 42px; border-radius: 50%; background: var(--navy); color: var(--white); font-weight: 700; font-size: 15px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .persoon-naam { font-size: 15.5px; font-weight: 700; color: var(--ink); }
  .persoon-sub { font-size: 12.5px; color: var(--faint); margin-top: 1px; }

  .bericht-blok { background: var(--tint); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
  .bericht-blok.preview { background: var(--soft); border: 1px dashed var(--line); }
  .bericht-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: var(--mid); margin-bottom: 5px; }
  .preview-tag { text-transform: none; font-weight: 500; color: var(--faint); letter-spacing: 0; }
  .bericht-tekst { font-size: 13.5px; line-height: 1.5; color: var(--ink); white-space: pre-wrap; }
  .bericht-acties { margin-top: 8px; }

  .btn { border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 6px; transition: background .15s, opacity .15s; }
  .btn-primary { background: var(--bright); color: var(--white); }
  .btn-primary:hover { background: var(--bright-hover); }
  .btn-outline { background: var(--white); color: var(--navy); border: 1px solid var(--line); }
  .btn-outline:hover { background: var(--tint); }
  .btn-ghost { background: transparent; color: var(--faint); border: 1px solid var(--line); }
  .btn-ghost:hover { background: var(--soft); }
  .btn-sm { padding: 5px 10px; font-size: 12px; }
  .btn-danger-ghost { background: transparent; color: var(--red); border: 1px solid #f0c7c2; }
  .btn-danger-ghost:hover { background: var(--red-bg); }

  .knoppenrij { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px; align-items: center; }
  .knoppenrij form { display: inline; }
  a.btn { text-decoration: none; }

  details.aanpassen summary { list-style: none; }
  details.aanpassen summary::-webkit-details-marker { display: none; }
  details.aanpassen[open] .btn-ghost { background: var(--soft); }
  .aanpassen-paneel { margin-top: 10px; }
  textarea { width: 100%; min-height: 56px; border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; font-family: inherit; font-size: 13px; resize: vertical; }
  textarea:focus { outline: 2px solid var(--bright); outline-offset: -1px; }

  /* Follow-up card (lichter, nog niet actionable) */
  .card.muted { background: var(--soft); box-shadow: none; }
  .due-badge { background: var(--amber-bg); color: var(--amber); font-size: 11px; font-weight: 700; border-radius: 999px; padding: 2px 10px; }

  /* Compacte chips (bv. "Wachten op acceptatie") — alleen naam + 2 kleine acties */
  .chip-wrap { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { display: flex; align-items: center; gap: 4px; background: var(--white); border: 1px solid var(--line); border-radius: 999px; padding: 6px 8px 6px 14px; }
  .chip-naam { font-size: 13px; font-weight: 600; color: var(--ink); margin-right: 2px; }
  .chip-icon { background: transparent; border: none; color: var(--mid); cursor: pointer; font-size: 13px; line-height: 1; width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; text-decoration: none; font-family: inherit; }
  .chip-icon:hover { background: var(--tint); color: var(--navy); }
  .chip form { display: inline; }
</style>
<script>
function kopieerUitElement(id, btn) {
  const tekst = document.getElementById(id).textContent;
  navigator.clipboard.writeText(tekst).then(() => {
    const origineel = btn.innerHTML;
    btn.innerHTML = "✅ Gekopieerd";
    setTimeout(() => { btn.innerHTML = origineel; }, 1500);
  });
}
function initialen(naam) {
  return naam.split(" ").filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join("");
}
</script>
</head>
<body>
<div class="shell">

  <div class="topbar">
    <div>
      <p class="brand-eyebrow">Insightance · Automatisering</p>
      <h1>LinkedIn Outreach Cockpit</h1>
    </div>
    <div class="pillrow">
      <span class="pill week">Week {{ limieten.effectieve_week }}</span>
      <span class="pill">Connecties <b>{{ vandaag.connections }}/{{ limieten.connections }}</b>
        <span class="bar"><span style="width:{{ (vandaag.connections / limieten.connections * 100) if limieten.connections else 0 }}%"></span></span>
      </span>
      <span class="pill">Profielen <b>{{ vandaag.profile_views }}/{{ limieten.profile_views }}</b>
        <span class="bar"><span style="width:{{ (vandaag.profile_views / limieten.profile_views * 100) if limieten.profile_views else 0 }}%"></span></span>
      </span>
      <span class="pill">Zoekopdrachten <b>{{ vandaag.searches }}/{{ limieten.searches }}</b>
        <span class="bar"><span style="width:{{ (vandaag.searches / limieten.searches * 100) if limieten.searches else 0 }}%"></span></span>
      </span>
    </div>
  </div>

  {% if noodstop.pauzeren %}
  <div class="banner stop">⛔ <div><b>Gepauzeerd.</b> {{ noodstop.reden }}</div></div>
  {% endif %}
  {% if noodstop.waarschuwing %}
  <div class="banner warn">⚠️ <div>{{ noodstop.waarschuwing }}</div></div>
  {% endif %}
  {% if check_fout %}
  <div class="banner stop">⛔ <div><b>Check mislukt.</b> {{ check_fout }}</div></div>
  {% endif %}
  {% if check_geaccepteerd is not none %}
  <div class="banner ok">✅ <div>Check op LinkedIn voltooid: <b>{{ check_geaccepteerd }}</b> geaccepteerd, <b>{{ check_verlopen }}</b> verlopen/ingetrokken.</div></div>
  {% endif %}
  {% if nieuwe_dag_fout %}
  <div class="banner stop">⛔ <div><b>Nieuwe dag mislukt.</b> {{ nieuwe_dag_fout }}</div></div>
  {% endif %}
  {% if nieuwe_dag_ja is not none %}
  <div class="banner ok">✅ <div>Nieuwe zoekronde klaar: {{ nieuwe_dag_gelezen }} profielen gelezen, <b>{{ nieuwe_dag_ja }}</b> klaargezet in "Te versturen", <b>{{ nieuwe_dag_twijfel }}</b> twijfelgeval(len) voor jouw oordeel.</div></div>
  {% endif %}

  <div class="sectie" style="margin-top: 22px;">
    <div class="sectie-head">
      <h2>Dashboard</h2>
      {% if stats and stats.laatst_bijgewerkt %}<span class="freshness">Laatst bijgewerkt: {{ stats.laatst_bijgewerkt }}</span>{% endif %}
    </div>
    {% if stats is none %}
    <div class="leeg">Nog geen data. Draai <code>scripts/collect_linkedin.py</code> zodra de eerste kandidaten in de sheet staan.</div>
    {% else %}
    <div class="tiles">
      <div class="tile"><div class="num">{{ stats.totaal }}</div><div class="lbl">Totaal prospects</div></div>
      <div class="tile"><div class="num">{{ stats.te_versturen }}</div><div class="lbl">Nog te versturen</div></div>
      <div class="tile accent"><div class="num">{{ stats.benaderd }}</div><div class="lbl">Benaderd</div></div>
      <div class="tile"><div class="num">{{ stats.vandaag }}</div><div class="lbl">Vandaag benaderd</div></div>
      <div class="tile accent"><div class="num">{{ stats.reacties }}</div><div class="lbl">Reacties</div></div>
      <div class="tile"><div class="num">{{ stats.reactieratio }}</div><div class="lbl">Reactieratio</div></div>
      <div class="tile"><div class="num">{{ stats.afgewezen }}</div><div class="lbl">Afgewezen</div></div>
      <div class="tile warm"><div class="num">{{ stats.warm|length }}</div><div class="lbl">Warme leads</div></div>
    </div>
    {% endif %}
  </div>

  <div class="sectie">
    <div class="sectie-head">
      <h2>Te versturen</h2>
      <div style="display:flex; gap:10px; align-items:center;">
        <span class="count-badge">{{ kandidaten|length }}</span>
        <form method="post" action="{{ url_for('nieuwe_dag') }}"><button class="btn btn-outline btn-sm">🔍 Nieuwe dag — zoek nieuwe prospects (1-3 min)</button></form>
      </div>
    </div>
    {% if not kandidaten %}
    <div class="leeg">Niets klaarstaand. Klik boven op "Nieuwe dag" om automatisch te zoeken, of zet handmatig iets klaar via <code>wachtrij.nieuw()</code>.</div>
    {% endif %}
    {% for k in kandidaten %}
    <div class="card">
      <div class="persoon">
        <div class="avatar">{{ k.naam[:1] }}{{ (k.naam.split(' ')|length > 1 and k.naam.split(' ')[1][:1]) or '' }}</div>
        <div>
          <div class="persoon-naam">{{ k.naam }} — {{ k.functie }}</div>
          <div class="persoon-sub">{{ k.bedrijf }} · {{ k.locatie }}</div>
        </div>
      </div>

      <div class="knoppenrij">
        <a class="btn btn-outline" href="{{ k.url }}" target="_blank">💬 Open op LinkedIn</a>
        <form method="post" action="{{ url_for('verstuurd') }}"><input type="hidden" name="url" value="{{ k.url }}"><button class="btn btn-primary">✅ Connectie verstuurd</button></form>
        <form method="post" action="{{ url_for('overslaan') }}"><input type="hidden" name="url" value="{{ k.url }}"><button class="btn btn-danger-ghost">❌ Overslaan</button></form>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="sectie">
    <div class="sectie-head">
      <h2>Twijfelgevallen — jouw oordeel</h2>
      <span class="count-badge">{{ twijfel|length }}</span>
    </div>
    {% if not twijfel %}
    <div class="leeg">Geen twijfelgevallen.</div>
    {% endif %}
    {% for t in twijfel %}
    <div class="card muted">
      <div class="persoon">
        <div class="avatar">{{ t.naam[:1] }}</div>
        <div>
          <div class="persoon-naam">{{ t.naam }} — {{ t.functie }}</div>
          <div class="persoon-sub">{{ t.bedrijf }} · {{ t.locatie }}</div>
        </div>
      </div>
      <p class="persoon-sub" style="margin-bottom: 10px;">{{ t.notities }}</p>
      <div class="knoppenrij">
        <a class="btn btn-outline" href="{{ t.url }}" target="_blank">💬 Bekijk op LinkedIn</a>
        <form method="post" action="{{ url_for('twijfel_accepteren') }}"><input type="hidden" name="url" value="{{ t.url }}"><button class="btn btn-primary">✅ Toevoegen aan Te versturen</button></form>
        <form method="post" action="{{ url_for('twijfel_afwijzen') }}"><input type="hidden" name="url" value="{{ t.url }}"><button class="btn btn-danger-ghost">❌ Afwijzen</button></form>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="sectie">
    <div class="sectie-head">
      <h2>Wachten op acceptatie</h2>
      <div style="display:flex; gap:10px; align-items:center;">
        <span class="count-badge">{{ wachtend|length }}</span>
        <form method="post" action="{{ url_for('check_linkedin') }}"><button class="btn btn-outline btn-sm">🔄 Check op LinkedIn (±15 sec)</button></form>
      </div>
    </div>
    {% if not wachtend %}
    <div class="leeg">Niemand aan het wachten.</div>
    {% else %}
    <div class="chip-wrap">
      {% for w in wachtend %}
      <div class="chip" title="{{ w.bedrijf }} · {{ w.locatie }} · verzoek verstuurd {{ w.datum_verzoek }}">
        <span class="chip-naam">{{ w.naam }}</span>
        <a class="chip-icon" href="{{ w.url }}" target="_blank" title="Open op LinkedIn">↗</a>
        <form method="post" action="{{ url_for('geaccepteerd_handmatig') }}"><input type="hidden" name="url" value="{{ w.url }}"><button type="submit" class="chip-icon" title="Zelf gezien dat dit geaccepteerd is">✓</button></form>
      </div>
      {% endfor %}
    </div>
    {% endif %}
  </div>

  <div class="sectie">
    <div class="sectie-head">
      <h2>Geaccepteerd — bericht 1 klaarzetten</h2>
      <span class="count-badge">{{ geaccepteerd|length }}</span>
    </div>
    {% if not geaccepteerd %}
    <div class="leeg">Niemand heeft nog geaccepteerd (of <code>browser.py check</code> is nog niet gedraaid).</div>
    {% endif %}
    {% for g in geaccepteerd %}
    <div class="card">
      <div class="persoon">
        <div class="avatar">{{ g.naam[:1] }}</div>
        <div>
          <div class="persoon-naam">{{ g.naam }} — {{ g.functie }}</div>
          <div class="persoon-sub">{{ g.bedrijf }} · {{ g.locatie }}</div>
        </div>
      </div>
      {% if g.bericht1 %}
      <div class="bericht-blok">
        <div class="bericht-label">Bericht 1</div>
        <div class="bericht-tekst" id="acc-bericht1-{{ loop.index }}">{{ g.bericht1 }}</div>
        <div class="bericht-acties"><button type="button" class="btn btn-outline btn-sm" onclick="kopieerUitElement('acc-bericht1-{{ loop.index }}', this)">📋 Kopieer</button></div>
      </div>
      {% else %}
      <p class="persoon-sub" style="margin-bottom: 10px;">Bericht 1 is nog niet ingevuld voor deze kandidaat.</p>
      {% endif %}
      <details class="aanpassen">
        <summary><span class="btn btn-ghost btn-sm">▸ Bericht 2 en 3 bekijken <span class="preview-tag">nog niet relevant</span></span></summary>
        <div class="aanpassen-paneel">
          {% if g.bericht2 %}
          <div class="bericht-blok preview">
            <div class="bericht-label">Bericht 2 — follow-up</div>
            <div class="bericht-tekst" id="acc-bericht2-{{ loop.index }}">{{ g.bericht2 }}</div>
            <div class="bericht-acties"><button type="button" class="btn btn-outline btn-sm" onclick="kopieerUitElement('acc-bericht2-{{ loop.index }}', this)">📋 Kopieer</button></div>
          </div>
          {% endif %}
          {% if g.bericht3 %}
          <div class="bericht-blok preview">
            <div class="bericht-label">Bericht 3 — laatste follow-up</div>
            <div class="bericht-tekst" id="acc-bericht3-{{ loop.index }}">{{ g.bericht3 }}</div>
            <div class="bericht-acties"><button type="button" class="btn btn-outline btn-sm" onclick="kopieerUitElement('acc-bericht3-{{ loop.index }}', this)">📋 Kopieer</button></div>
          </div>
          {% endif %}
        </div>
      </details>
      <div class="knoppenrij">
        <a class="btn btn-outline" href="{{ g.url }}" target="_blank">💬 Open op LinkedIn</a>
        <form method="post" action="{{ url_for('bericht1_verstuurd') }}"><input type="hidden" name="url" value="{{ g.url }}"><button class="btn btn-primary">✅ Verstuurd</button></form>
        <details class="aanpassen">
          <summary><span class="btn btn-ghost">✏️ Aanpassen</span></summary>
          <div class="aanpassen-paneel">
            <form method="post" action="{{ url_for('aanpassen') }}">
              <input type="hidden" name="url" value="{{ g.url }}">
              <textarea name="feedback" placeholder="Wat moet er anders aan bericht 1?"></textarea>
              <div style="margin-top:8px;"><button class="btn btn-primary btn-sm" type="submit">Opslaan</button></div>
            </form>
          </div>
        </details>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="sectie">
    <div class="sectie-head">
      <h2>Verstuurd — wachten op reactie</h2>
      <span class="count-badge">{{ onderweg|length }}</span>
    </div>
    {% if not onderweg %}
    <div class="leeg">Niemand onderweg.</div>
    {% endif %}
    {% for o in onderweg %}
    <div class="card muted">
      <div class="persoon">
        <div class="avatar">{{ o.naam[:1] }}</div>
        <div>
          <div class="persoon-naam">{{ o.naam }} — {{ o.functie }}</div>
          <div class="persoon-sub">{{ o.bedrijf }} · {{ o.locatie }}</div>
        </div>
      </div>
      {% if o.status == 'Bericht verstuurd' %}
      <p class="persoon-sub" style="margin-bottom: 10px;">Bericht 1 verstuurd op {{ o.datum_bericht1 }}. Volgende follow-up (bericht 2) staat gepland op {{ o.volgende_follow_up }}.</p>
      {% else %}
      <p class="persoon-sub" style="margin-bottom: 10px;">Bericht 2 verstuurd op {{ o.datum_bericht2 }}. Volgende follow-up (bericht 3) staat gepland op {{ o.volgende_follow_up }}.</p>
      {% endif %}
      <div class="knoppenrij">
        <a class="btn btn-outline" href="{{ o.url }}" target="_blank">💬 Open op LinkedIn</a>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="sectie">
    <div class="sectie-head">
      <h2>Follow-ups due</h2>
      <span class="count-badge">{{ follow_ups|length }}</span>
    </div>
    {% if not follow_ups %}
    <div class="leeg">Niets due.</div>
    {% endif %}
    {% for f in follow_ups %}
    <div class="card muted">
      <div class="persoon">
        <div class="avatar">{{ f.naam[:1] }}</div>
        <div>
          <div class="persoon-naam">{{ f.naam }} — {{ f.bedrijf }}</div>
          <div class="persoon-sub"><span class="due-badge">Due {{ f.volgende_follow_up }}</span></div>
        </div>
      </div>
      {% set fu_tekst = f.bericht3 if f.volgende_actie == 'bericht3' else f.bericht2 %}
      {% set fu_label = 'Bericht 3 — laatste follow-up' if f.volgende_actie == 'bericht3' else 'Bericht 2 — follow-up' %}
      {% set fu_route = 'bericht3_verstuurd' if f.volgende_actie == 'bericht3' else 'bericht2_verstuurd' %}
      {% if fu_tekst %}
      <div class="bericht-blok">
        <div class="bericht-label">{{ fu_label }}</div>
        <div class="bericht-tekst" id="fu-bericht-{{ loop.index }}">{{ fu_tekst }}</div>
        <div class="bericht-acties"><button type="button" class="btn btn-outline btn-sm" onclick="kopieerUitElement('fu-bericht-{{ loop.index }}', this)">📋 Kopieer</button></div>
      </div>
      {% else %}
      <p class="persoon-sub" style="margin-bottom: 10px;">{{ fu_label }} is nog niet ingevuld voor deze kandidaat.</p>
      {% endif %}
      <div class="knoppenrij">
        <a class="btn btn-outline" href="{{ f.url }}" target="_blank">💬 Open op LinkedIn</a>
        <form method="post" action="{{ url_for(fu_route) }}"><input type="hidden" name="url" value="{{ f.url }}"><button class="btn btn-primary">✅ Verstuurd</button></form>
      </div>
    </div>
    {% endfor %}
  </div>

</div>
</body>
</html>
"""


@app.route("/")
def index():
    conn = get_connection()
    _ensure_feedback_table(conn)
    records = wachtrij.alle_records()  # DE ENIGE live Sheets-aanroep van deze paginaweergave
    _sync_vers(conn, records)
    kandidaten = wachtrij.volgende_batch(10, records=records)
    wachtend = wachtrij.wachtend_op_acceptatie(records=records)
    geaccepteerd = wachtrij.geaccepteerd_wachtend(records=records)
    onderweg = wachtrij.onderweg(records=records)
    twijfel = wachtrij.twijfelgevallen(records=records)
    follow_ups = wachtrij.due_follow_ups(records=records)
    noodstop = limits.check_noodstop(conn)
    limieten = limits.current_week_limits(conn)
    vandaag = {
        "connections": limits.count_today(conn, "connection"),
        "profile_views": limits.count_today(conn, "profile_view"),
        "searches": limits.count_today(conn, "search"),
    }
    stats = _dashboard_stats(conn)
    conn.close()
    return render_template_string(
        PAGINA, kandidaten=kandidaten, wachtend=wachtend, geaccepteerd=geaccepteerd, onderweg=onderweg,
        twijfel=twijfel, follow_ups=follow_ups, noodstop=noodstop, limieten=limieten, vandaag=vandaag, stats=stats,
        check_fout=request.args.get("check_fout"),
        check_geaccepteerd=request.args.get("check_geaccepteerd"),
        check_verlopen=request.args.get("check_verlopen"),
        nieuwe_dag_fout=request.args.get("nieuwe_dag_fout"),
        nieuwe_dag_ja=request.args.get("nieuwe_dag_ja"),
        nieuwe_dag_twijfel=request.args.get("nieuwe_dag_twijfel"),
        nieuwe_dag_gelezen=request.args.get("nieuwe_dag_gelezen"),
    )


@app.route("/nieuwe_dag", methods=["POST"])
def nieuwe_dag():
    """Zoekt, leest en kwalificeert automatisch nieuwe prospects (installatiebedrijven +
    makelaars), zie tools/linkedin/vind_prospects.py. Duurt 1-3 minuten (echte LinkedIn-
    bezoeken + Claude-kwalificatie per profiel)."""
    resultaat = vind_prospects.nieuwe_dag()
    return redirect(url_for(
        "index", nieuwe_dag_fout=resultaat["fout"], nieuwe_dag_ja=resultaat["ja"],
        nieuwe_dag_twijfel=resultaat["twijfel"], nieuwe_dag_gelezen=resultaat["gelezen"],
    ))


@app.route("/twijfel_accepteren", methods=["POST"])
def twijfel_accepteren():
    url = request.form["url"]
    wachtrij.status(url, "Te versturen")
    return redirect(url_for("index"))


@app.route("/twijfel_afwijzen", methods=["POST"])
def twijfel_afwijzen():
    url = request.form["url"]
    wachtrij.status(url, "Genegeerd")
    return redirect(url_for("index"))


@app.route("/check_linkedin", methods=["POST"])
def check_linkedin():
    """Opent echt een browser naar LinkedIn (verzonden uitnodigingen + connecties),
    en schrijft wijzigingen direct door naar de Sheet — zie tools/linkedin/browser.py check()."""
    conn = get_connection()
    resultaat = browser.check(conn)
    conn.close()
    if "fout" in resultaat:
        return redirect(url_for("index", check_fout=resultaat["fout"]))
    for url in resultaat["geaccepteerd"]:
        wachtrij.status(url, "Geaccepteerd")
    for url in resultaat["verlopen"]:
        wachtrij.status(url, "Verlopen")
    return redirect(url_for(
        "index", check_geaccepteerd=len(resultaat["geaccepteerd"]), check_verlopen=len(resultaat["verlopen"]),
    ))


@app.route("/verstuurd", methods=["POST"])
def verstuurd():
    url = request.form["url"]
    conn = get_connection()
    wachtrij.status(url, "Verzoek verstuurd")
    limits.log_action(conn, "connection", ref=url)
    conn.close()
    return redirect(url_for("index"))


@app.route("/geaccepteerd_handmatig", methods=["POST"])
def geaccepteerd_handmatig():
    url = request.form["url"]
    wachtrij.status(url, "Geaccepteerd")
    return redirect(url_for("index"))


@app.route("/bericht1_verstuurd", methods=["POST"])
def bericht1_verstuurd():
    url = request.form["url"]
    wachtrij.status(url, "Bericht verstuurd")  # plant ook meteen de bericht2-due-datum
    return redirect(url_for("index"))


@app.route("/bericht2_verstuurd", methods=["POST"])
def bericht2_verstuurd():
    url = request.form["url"]
    wachtrij.status(url, "Bericht 2 verstuurd")
    return redirect(url_for("index"))


@app.route("/bericht3_verstuurd", methods=["POST"])
def bericht3_verstuurd():
    url = request.form["url"]
    wachtrij.status(url, "Afgerond")  # bericht 3 is de laatste stap, reeks is daarmee compleet
    return redirect(url_for("index"))


@app.route("/overslaan", methods=["POST"])
def overslaan():
    url = request.form["url"]
    wachtrij.status(url, "Genegeerd")
    return redirect(url_for("index"))


@app.route("/aanpassen", methods=["POST"])
def aanpassen():
    url = request.form["url"]
    feedback = request.form.get("feedback", "").strip()
    if feedback:
        conn = get_connection()
        _ensure_feedback_table(conn)
        conn.execute("INSERT INTO linkedin_feedback (url, tekst) VALUES (?, ?)", (url, feedback))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    poort = int(get_env("LINKEDIN_COCKPIT_PORT") or 5050)
    print(f"Cockpit draait op http://127.0.0.1:{poort}")
    app.run(host="127.0.0.1", port=poort, debug=False)
