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
import limits  # noqa: E402
import wachtrij  # noqa: E402

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
    return st


PAGINA = """
<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>LinkedIn Outreach — Cockpit</title>
<style>
  body { font-family: -apple-system, 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 30px auto; padding: 0 16px; color: #1B2638; background: #F5F8FC; }
  h1 { font-size: 20px; }
  h2 { font-size: 15px; color: #465369; margin-top: 32px; }
  .banner { background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; }
  .warning { background: #fef3c7; border: 1px solid #fcd34d; color: #92400e; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; }
  .card { background: white; border: 1px solid #C9D5E4; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; }
  .card h3 { margin: 0 0 4px; font-size: 15px; }
  .meta { color: #5E6C84; font-size: 13px; margin-bottom: 8px; }
  .tekst { background: #EAF1FB; border-radius: 6px; padding: 8px 10px; font-size: 13px; margin-bottom: 8px; white-space: pre-wrap; }
  .knoppen form { display: inline; }
  button { border: none; border-radius: 5px; padding: 6px 12px; font-size: 13px; cursor: pointer; margin-right: 6px; }
  .ok { background: #1F5EFF; color: white; }
  .edit { background: #eee; }
  .skip { background: #fff; border: 1px solid #ddd; }
  table.dash { border-collapse: collapse; width: 100%; font-size: 13px; }
  table.dash td, table.dash th { border-bottom: 1px solid #C9D5E4; padding: 4px 8px; text-align: left; }
  .leeg { color: #5E6C84; font-size: 13px; }
  textarea { width: 100%; height: 50px; }
</style>
</head>
<body>
<h1>LinkedIn Outreach — Cockpit</h1>

{% if noodstop.pauzeren %}
<div class="banner"><b>Gepauzeerd:</b> {{ noodstop.reden }}</div>
{% endif %}
{% if noodstop.waarschuwing %}
<div class="warning">{{ noodstop.waarschuwing }}</div>
{% endif %}

<p class="meta">
  Week {{ limieten.effectieve_week }} — connectieverzoeken {{ vandaag.connections }}/{{ limieten.connections }},
  profielbezoeken {{ vandaag.profile_views }}/{{ limieten.profile_views }},
  zoekopdrachten {{ vandaag.searches }}/{{ limieten.searches }} (vandaag)
</p>

<h2>Te versturen ({{ kandidaten|length }})</h2>
{% if not kandidaten %}<p class="leeg">Niets klaarstaand. Draai eerst tools/linkedin/browser.py zoek + lees, en laat Claude de conceptnotities schrijven via wachtrij.nieuw().</p>{% endif %}
{% for k in kandidaten %}
<div class="card">
  <h3>{{ k.naam }} — {{ k.functie }}</h3>
  <div class="meta">{{ k.bedrijf }} · {{ k.locatie }} · <a href="{{ k.url }}" target="_blank">profiel</a></div>
  <div class="tekst"><b>Connectienotitie:</b> {{ k.connectienotitie }}</div>
  {% if k.bericht1 %}<div class="tekst"><b>Bericht 1 (na acceptatie):</b> {{ k.bericht1 }}</div>{% endif %}
  <div class="knoppen">
    <form method="post" action="{{ url_for('verstuurd') }}"><input type="hidden" name="url" value="{{ k.url }}"><button class="ok">✅ Verstuurd</button></form>
    <form method="post" action="{{ url_for('overslaan') }}"><input type="hidden" name="url" value="{{ k.url }}"><button class="skip">❌ Overslaan</button></form>
    <details style="display:inline-block; vertical-align: top;">
      <summary class="edit" style="display:inline; padding: 6px 12px; border-radius:5px; background:#eee; cursor:pointer;">✏️ Aanpassen</summary>
      <form method="post" action="{{ url_for('aanpassen') }}">
        <input type="hidden" name="url" value="{{ k.url }}">
        <textarea name="feedback" placeholder="Wat moet er anders aan deze notitie/bericht?"></textarea>
        <button class="edit" type="submit">Opslaan</button>
      </form>
    </details>
  </div>
</div>
{% endfor %}

<h2>Follow-ups due ({{ follow_ups|length }})</h2>
{% if not follow_ups %}<p class="leeg">Niets due.</p>{% endif %}
{% for f in follow_ups %}
<div class="card">
  <h3>{{ f.naam }} — {{ f.bedrijf }}</h3>
  <div class="meta">Due: {{ f.volgende_follow_up }} · <a href="{{ f.url }}" target="_blank">profiel</a></div>
  <p class="leeg">Berichtinhoud voor follow-ups is nog niet ingevuld (zie workflows/linkedin_outreach.md).</p>
</div>
{% endfor %}

<h2>Dashboard</h2>
{% if stats is none %}
<p class="leeg">Nog geen data (draai scripts/collect_linkedin.py nadat de eerste kandidaten in de sheet staan).</p>
{% else %}
<table class="dash">
  <tr><td>Totaal prospects</td><td>{{ stats.totaal }}</td></tr>
  <tr><td>Nog te versturen</td><td>{{ stats.te_versturen }}</td></tr>
  <tr><td>Benaderd (cumulatief)</td><td>{{ stats.benaderd }}</td></tr>
  <tr><td>Vandaag voor het eerst benaderd</td><td>{{ stats.vandaag }}</td></tr>
  <tr><td>Reacties</td><td>{{ stats.reacties }}</td></tr>
  <tr><td>Reactieratio</td><td>{{ stats.reactieratio }}</td></tr>
  <tr><td>Afgewezen</td><td>{{ stats.afgewezen }}</td></tr>
  <tr><td>Warme leads</td><td>{{ stats.warm|length }}</td></tr>
</table>
{% endif %}

</body>
</html>
"""


@app.route("/")
def index():
    conn = get_connection()
    _ensure_feedback_table(conn)
    kandidaten = wachtrij.volgende_batch(10)
    follow_ups = wachtrij.due_follow_ups()
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
        PAGINA, kandidaten=kandidaten, follow_ups=follow_ups, noodstop=noodstop,
        limieten=limieten, vandaag=vandaag, stats=stats,
    )


@app.route("/verstuurd", methods=["POST"])
def verstuurd():
    url = request.form["url"]
    conn = get_connection()
    wachtrij.status(url, "Verzoek verstuurd")
    limits.log_action(conn, "connection", ref=url)
    conn.close()
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
