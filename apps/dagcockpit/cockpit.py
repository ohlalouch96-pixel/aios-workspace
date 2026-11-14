"""
Dagcockpit — persoonlijk dagoverzicht

Draait alleen op Oussama's eigen laptop (127.0.0.1). Toont per chat de taken
van vandaag (vast weekritme uit ritme.py + eenmalige taken), om af te vinken,
met een weekstrook, de LinkedIn-content van deze week, binnenkort-lijst,
snelkoppelingen en een notitie voor vandaag. Geen aantallen uit de outreach:
die staan in de betreffende chats.

Gebruik:
    python apps/dagcockpit/cockpit.py
    (open daarna http://127.0.0.1:5070 in de browser)

Opslag: tabellen dagcockpit_* in data/data.db.
"""

import importlib
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, redirect, render_template_string, request

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import get_env  # noqa: E402
from db import get_connection  # noqa: E402
import ritme  # noqa: E402

app = Flask(__name__)

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
DAGEN_KORT = ["ma", "di", "wo", "do", "vr", "za", "zo"]
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]
MAANDEN_KORT = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


# ---------------------------------------------------------------- opslag

def _db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dagcockpit_vinkjes (
            datum TEXT NOT NULL,
            taak_id TEXT NOT NULL,
            klaar_op TEXT DEFAULT (datetime('now','localtime')),
            PRIMARY KEY (datum, taak_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dagcockpit_taken (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titel TEXT NOT NULL,
            chat TEXT NOT NULL,
            datum TEXT NOT NULL,
            klaar_op TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dagcockpit_notities (
            datum TEXT PRIMARY KEY,
            tekst TEXT NOT NULL
        )
    """)
    conn.execute("CREATE TABLE IF NOT EXISTS dagcockpit_meta (sleutel TEXT PRIMARY KEY, waarde TEXT)")
    if not conn.execute("SELECT 1 FROM dagcockpit_meta WHERE sleutel='startherinneringen'").fetchone():
        for h in ritme.STARTHERINNERINGEN:
            conn.execute("INSERT INTO dagcockpit_taken (titel, chat, datum) VALUES (?, ?, ?)",
                         (h["titel"], h["chat"], h["datum"]))
        conn.execute("INSERT INTO dagcockpit_meta VALUES ('startherinneringen', ?)", (datetime.now().isoformat(),))
    conn.commit()
    return conn


# ---------------------------------------------------------------- datums

def is_laatste_zaterdag(d):
    return d.weekday() == 5 and (d + timedelta(days=7)).month != d.month


def valt_op(taak, d):
    if taak["dagen"] == "laatste_zaterdag":
        return is_laatste_zaterdag(d)
    return d.weekday() in taak["dagen"]


def lang(d):
    return f"{DAGEN[d.weekday()]} {d.day} {MAANDEN[d.month - 1]}"


def kort(d):
    return f"{DAGEN_KORT[d.weekday()]} {d.day} {MAANDEN_KORT[d.month - 1]}"


def groet():
    uur = datetime.now().hour
    if uur < 12:
        return "Goedemorgen"
    if uur < 18:
        return "Goedemiddag"
    return "Goedenavond"


# ---------------------------------------------------------------- inhoud

def vaste_taken(d):
    return [t for t in ritme.TAKEN if valt_op(t, d)]


def taken_van_vandaag(conn, vandaag):
    """Vaste taken van vandaag + eenmalige taken van vandaag of eerder die nog open staan
    (of vandaag zijn afgevinkt). Geeft dict chat -> lijst taken."""
    iso = vandaag.isoformat()
    vinkjes = {r["taak_id"] for r in conn.execute("SELECT taak_id FROM dagcockpit_vinkjes WHERE datum=?", (iso,))}
    per_chat = {chat: [] for chat in ritme.CHATS}
    for t in vaste_taken(vandaag):
        per_chat.setdefault(t["chat"], []).append({
            "sleutel": t["id"], "titel": t["titel"], "ritme": t["ritme"],
            "klaar": t["id"] in vinkjes, "soort": "vast", "achterstand": False,
        })
    rijen = conn.execute("""
        SELECT * FROM dagcockpit_taken
        WHERE (datum <= ? AND klaar_op IS NULL) OR substr(klaar_op, 1, 10) = ?
        ORDER BY datum, id
    """, (iso, iso)).fetchall()
    for r in rijen:
        d = date.fromisoformat(r["datum"])
        if d > vandaag:
            continue
        achter = d < vandaag
        per_chat.setdefault(r["chat"], []).append({
            "sleutel": f"t{r['id']}", "id": r["id"], "titel": r["titel"],
            "ritme": f"Van {kort(d)}" if achter else "Vandaag",
            "klaar": r["klaar_op"] is not None, "soort": "eenmalig", "achterstand": achter,
        })
    return per_chat


def weekstrook(conn, vandaag):
    maandag = vandaag - timedelta(days=vandaag.weekday())
    dagen = []
    for i in range(7):
        d = maandag + timedelta(days=i)
        iso = d.isoformat()
        vast = vaste_taken(d)
        label = "Basistaken"
        for tid in ritme.WEEKSTROOK_VOORRANG:
            hit = next((t for t in vast if t["id"] == tid), None)
            if hit:
                label = hit["kort"]
                break
        eenmalig = conn.execute("SELECT klaar_op FROM dagcockpit_taken WHERE datum=?", (iso,)).fetchall()
        totaal = len(vast) + len(eenmalig)
        klaar = conn.execute("SELECT COUNT(*) FROM dagcockpit_vinkjes WHERE datum=?", (iso,)).fetchone()[0]
        klaar += sum(1 for r in eenmalig if r["klaar_op"])
        dagen.append({
            "kop": f"{DAGEN_KORT[i].upper()} {d.day}", "label": label,
            "procent": round(100 * klaar / totaal) if totaal else 0,
            "vandaag": d == vandaag, "verleden": d < vandaag,
        })
    week = vandaag.isocalendar()[1]
    zondag = maandag + timedelta(days=6)
    if maandag.month == zondag.month:
        bereik = f"{maandag.day} t/m {zondag.day} {MAANDEN[zondag.month - 1]}"
    else:
        bereik = f"{maandag.day} {MAANDEN_KORT[maandag.month - 1]} t/m {zondag.day} {MAANDEN_KORT[zondag.month - 1]}"
    return {"dagen": dagen, "titel": f"Week {week} · {bereik}"}


def linkedin_deze_week(vandaag):
    maandag = vandaag - timedelta(days=vandaag.weekday())
    zondag = maandag + timedelta(days=6)
    posts = []
    for p in ritme.LINKEDIN_WEKELIJKS:
        d = maandag + timedelta(days=p["dag"])
        posts.append((d, p["tijd"], p["pijler"]))
    for p in ritme.LINKEDIN_LOS:
        d = date.fromisoformat(p["datum"])
        if maandag <= d <= zondag:
            posts.append((d, p["tijd"], p["pijler"]))
    nu = datetime.now()
    uit = []
    for d, tijd, pijler in sorted(posts, key=lambda x: (x[0], x[1])):
        moment = datetime.combine(d, datetime.strptime(tijd, "%H:%M").time())
        uit.append({"wanneer": f"{DAGEN_KORT[d.weekday()]} {tijd.lstrip('0') if tijd.startswith('0') else tijd}",
                    "pijler": pijler, "geplaatst": moment <= nu})
    return uit


def volgende_contentdag(vandaag):
    d = vandaag
    while not is_laatste_zaterdag(d):
        d += timedelta(days=1)
    return d


def binnenkort(conn, vandaag, dagen=21):
    tot = vandaag + timedelta(days=dagen)
    items = []
    for r in conn.execute("SELECT * FROM dagcockpit_taken WHERE datum > ? AND datum <= ? AND klaar_op IS NULL",
                          (vandaag.isoformat(), tot.isoformat())):
        items.append({"datum": date.fromisoformat(r["datum"]), "titel": r["titel"], "id": r["id"], "vast": False})
    # bijzondere vaste momenten (niet de dagelijkse basistaken)
    d = vandaag + timedelta(days=1)
    while d <= tot:
        for t in vaste_taken(d):
            if t["id"] in ("linkedin_check", "content_maand"):
                items.append({"datum": d, "titel": t["titel"], "id": None, "vast": True})
        d += timedelta(days=1)
    items.sort(key=lambda x: x["datum"])
    for it in items:
        it["kop"] = f"{DAGEN_KORT[it['datum'].weekday()]} {it['datum'].day}"
        it["accent"] = "oranje" if is_laatste_zaterdag(it["datum"]) else "blauw"
    return items[:8]


def snelkoppelingen():
    uit = []
    for titel, url in ritme.SNELKOPPELINGEN:
        if titel.startswith("Outreach-tracker"):
            sid = get_env("OUTREACH_SHEET_ID")
            url = f"https://docs.google.com/spreadsheets/d/{sid}/edit" if sid else None
        elif titel == "LinkedIn-cockpit":
            url = f"http://127.0.0.1:{get_env('LINKEDIN_COCKPIT_PORT') or 5050}/"
        if url:
            uit.append({"titel": titel, "url": url})
    return uit


# ---------------------------------------------------------------- routes

@app.route("/")
def index():
    importlib.reload(ritme)
    vandaag = date.today()
    conn = _db()
    per_chat = taken_van_vandaag(conn, vandaag)
    alle = [t for lst in per_chat.values() for t in lst]
    klaar = sum(1 for t in alle if t["klaar"])
    kaarten = [{"chat": c, "kleur": ritme.CHATS.get(c, "grijs"), "taken": per_chat[c]}
               for c in per_chat if per_chat[c] and c != "Content"]
    content_taken = per_chat.get("Content", [])
    notitie = conn.execute("SELECT tekst FROM dagcockpit_notities WHERE datum=?", (vandaag.isoformat(),)).fetchone()
    vorige = conn.execute("SELECT datum, tekst FROM dagcockpit_notities WHERE datum < ? AND tekst != '' ORDER BY datum DESC LIMIT 1",
                          (vandaag.isoformat(),)).fetchone()
    html = render_template_string(
        TEMPLATE,
        groet=groet(), datum_kop=lang(vandaag).upper(),
        klaar=klaar, totaal=len(alle), procent=round(100 * klaar / len(alle)) if alle else 0,
        kaarten=kaarten, content_taken=content_taken,
        week=weekstrook(conn, vandaag), linkedin=linkedin_deze_week(vandaag),
        contentdag=kort(volgende_contentdag(vandaag)),
        binnenkort=binnenkort(conn, vandaag), links=snelkoppelingen(),
        notitie=notitie["tekst"] if notitie else "",
        vorige_notitie=(kort(date.fromisoformat(vorige["datum"])), vorige["tekst"]) if vorige else None,
        vandaag_iso=vandaag.isoformat(), chats=list(ritme.CHATS),
        ritme_taken=ritme.TAKEN, linkedin_ritme=ritme.LINKEDIN_WEKELIJKS, dagen_kort=DAGEN_KORT,
    )
    conn.close()
    return html


@app.route("/vink", methods=["POST"])
def vink():
    sleutel = request.form["sleutel"]
    aan = request.form.get("aan") == "1"
    vandaag = date.today().isoformat()
    conn = _db()
    if sleutel.startswith("t"):
        conn.execute("UPDATE dagcockpit_taken SET klaar_op=? WHERE id=?",
                     (datetime.now().isoformat(timespec="seconds") if aan else None, int(sleutel[1:])))
    elif aan:
        conn.execute("INSERT OR IGNORE INTO dagcockpit_vinkjes (datum, taak_id) VALUES (?, ?)", (vandaag, sleutel))
    else:
        conn.execute("DELETE FROM dagcockpit_vinkjes WHERE datum=? AND taak_id=?", (vandaag, sleutel))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/taak", methods=["POST"])
def taak_toevoegen():
    titel = request.form.get("titel", "").strip()
    if titel:
        conn = _db()
        conn.execute("INSERT INTO dagcockpit_taken (titel, chat, datum) VALUES (?, ?, ?)",
                     (titel, request.form.get("chat") or "Algemeen", request.form.get("datum") or date.today().isoformat()))
        conn.commit()
        conn.close()
    return redirect("/")


@app.route("/verwijder", methods=["POST"])
def verwijder():
    conn = _db()
    conn.execute("DELETE FROM dagcockpit_taken WHERE id=?", (int(request.form["id"]),))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/notitie", methods=["POST"])
def notitie_opslaan():
    conn = _db()
    conn.execute("INSERT INTO dagcockpit_notities (datum, tekst) VALUES (?, ?) ON CONFLICT(datum) DO UPDATE SET tekst=excluded.tekst",
                 (date.today().isoformat(), request.form.get("tekst", "").strip()))
    conn.commit()
    conn.close()
    return redirect("/")


# ---------------------------------------------------------------- pagina

TEMPLATE = r"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dagcockpit · Insightance</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600&display=swap" rel="stylesheet">
<style>
:root{--navy:#17345F;--navy2:#24497F;--blauw:#1D4ED8;--blauwzacht:#E8EFFD;--tekst:#10213D;--grijs:#4B5568;--lijn:#E1E6EF;--bg:#F4F6FA;--groen:#0F5A35;--groenzacht:#E3F4EA;--oranje:#8A4B08;--oranjezacht:#FDF0E1;--paars:#5B3BB0;--paarszacht:#EFEAFB;--rood:#B4231A;--roodzacht:#FCE8E6}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);font-family:Inter,system-ui,sans-serif;color:var(--tekst)}
a{color:var(--blauw)}a:hover{color:var(--navy)}
.app{display:flex;flex-wrap:wrap;min-height:100vh}
nav.menu{flex:1 1 220px;max-width:260px;background:var(--navy);color:#fff;padding:28px 20px;display:flex;flex-direction:column;gap:32px}
.merk{display:flex;align-items:center;gap:10px}
.merk b{font-weight:700;letter-spacing:.14em;font-size:13px;display:block}
.merk span{font-size:12px;color:#B9C8E4}
.menu a{display:flex;align-items:center;min-height:44px;padding:0 14px;border-radius:10px;color:#D6E0F2;text-decoration:none;font-size:14px}
.menu a.actief,.menu a:hover{background:var(--navy2);color:#fff}
.menu a.actief{font-weight:600}
.doel{margin-top:auto;background:var(--navy2);border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:6px}
.doel small{font-size:12px;color:#B9C8E4;letter-spacing:.08em}
.doel strong{font-size:15px;line-height:1.4}
main{flex:999 1 560px;min-width:0;padding:36px 40px;display:flex;flex-direction:column;gap:28px}
header.kop{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:20px}
.datum{font-size:13px;font-weight:600;letter-spacing:.12em;color:var(--blauw)}
h1{margin:6px 0 0;font-family:'Playfair Display',Georgia,serif;font-size:40px;font-weight:600}
.kaart{background:#fff;border:1px solid var(--lijn);border-radius:16px;padding:22px;display:flex;flex-direction:column;gap:16px}
.kaart h2{margin:0;font-size:16px;font-weight:700}
.kaartkop{display:flex;justify-content:space-between;align-items:center;gap:10px}
.voortgang{min-width:260px;padding:16px 20px;gap:10px}
.voortgang .rij{display:flex;justify-content:space-between;font-size:14px}
.balk{height:8px;background:#E6EBF3;border-radius:99px}
.balk div{height:8px;background:var(--blauw);border-radius:99px}
.pil{font-size:12px;font-weight:600;padding:4px 10px;border-radius:99px;white-space:nowrap}
.pil.blauw{color:var(--blauw);background:var(--blauwzacht)}
.pil.oranje{color:var(--oranje);background:var(--oranjezacht)}
.pil.paars{color:var(--paars);background:var(--paarszacht)}
.pil.grijs{color:var(--grijs);background:#EEF1F6}
.pil.rood{color:var(--rood);background:var(--roodzacht)}
.week{display:grid;grid-template-columns:repeat(7,minmax(96px,1fr));gap:10px;overflow-x:auto}
.dag{border-radius:12px;padding:12px;background:var(--bg);display:flex;flex-direction:column;gap:6px}
.dag small{font-size:12px;color:var(--grijs);font-weight:600}
.dag span{font-size:13px;font-weight:600}
.dag .mini{height:4px;background:var(--lijn);border-radius:99px}
.dag .mini div{height:4px;background:var(--blauw);border-radius:99px}
.dag.vandaag{background:var(--navy);color:#fff}
.dag.vandaag small{color:#B9C8E4}
.dag.vandaag .mini{background:var(--navy2)}
.dag.vandaag .mini div{background:#9DB8EA}
.raster{display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start}
.kaarten{flex:999 1 480px;min-width:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;align-content:start;align-items:start}
.taak{display:flex;align-items:center;gap:12px}
.taak form.vink{display:flex;align-items:center;gap:12px;flex:1;margin:0;cursor:pointer}
.taak label{display:flex;align-items:center;gap:12px;font-size:15px;cursor:pointer;flex:1;line-height:1.4}
.taak input[type=checkbox]{width:20px;height:20px;accent-color:var(--blauw);margin:0;flex-shrink:0;cursor:pointer}
.taak.klaar label{color:#6B7488;text-decoration:line-through}
.taak .ritme{font-size:12px;color:var(--grijs);white-space:nowrap}
.taak .ritme.achter{color:var(--rood);font-weight:600}
.weg{background:none;border:0;color:#8A93A6;font-size:18px;line-height:1;min-width:32px;min-height:32px;border-radius:8px;cursor:pointer}
.weg:hover{background:var(--bg);color:var(--rood)}
.uitleg{margin:0;font-size:14px;line-height:1.5;color:var(--grijs)}
.posts{display:flex;flex-direction:column;gap:8px}
.post{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:13px;color:var(--groen);background:var(--groenzacht);padding:8px 12px;border-radius:10px}
.post .wat{display:flex;gap:8px;align-items:baseline}
.post b{font-weight:700;min-width:62px}
.post.geplaatst .wat{text-decoration:line-through;opacity:.75}
.post svg{flex-shrink:0}
aside{flex:1 1 280px;display:flex;flex-direction:column;gap:20px}
.binnen{display:flex;gap:14px;align-items:flex-start}
.binnen .d{font-size:12px;font-weight:700;border-radius:8px;padding:6px 8px;min-width:44px;text-align:center}
.binnen .d.blauw{color:var(--blauw);background:var(--blauwzacht)}
.binnen .d.oranje{color:var(--oranje);background:var(--oranjezacht)}
.binnen p{margin:0;font-size:14px;line-height:1.45;flex:1}
.leeg{font-size:14px;color:var(--grijs);margin:0}
.link{display:flex;justify-content:space-between;align-items:center;min-height:44px;padding:0 14px;border-radius:10px;background:var(--bg);color:var(--tekst);text-decoration:none;font-size:14px;font-weight:500}
.link:hover{background:var(--blauwzacht);color:var(--tekst)}
.link span{color:var(--blauw)}
textarea{font-family:inherit;font-size:14px;color:var(--tekst);border:1px solid #D5DCE8;border-radius:10px;padding:12px;resize:vertical;width:100%}
.knop{font-family:inherit;font-size:15px;font-weight:600;color:#fff;background:var(--blauw);border:0;border-radius:12px;padding:12px 18px;min-height:48px;cursor:pointer}
.knop:hover{background:#1A43BA}
.knop.licht{background:var(--bg);color:var(--tekst);border:1px solid var(--lijn);min-height:44px;font-size:14px}
.vorige{font-size:13px;color:var(--grijs);margin:0;line-height:1.45}
dialog{border:0;border-radius:16px;padding:0;width:min(440px,92vw);box-shadow:0 20px 60px rgba(16,33,61,.25)}
dialog::backdrop{background:rgba(16,33,61,.45)}
dialog form{padding:26px;display:flex;flex-direction:column;gap:14px}
dialog h2{margin:0;font-size:18px}
dialog label{font-size:13px;font-weight:600;color:var(--grijs);display:flex;flex-direction:column;gap:6px}
dialog input,dialog select{font-family:inherit;font-size:15px;color:var(--tekst);border:1px solid #D5DCE8;border-radius:10px;padding:0 12px;min-height:44px}
.knoppen{display:flex;gap:10px;justify-content:flex-end;margin-top:6px}
table.ritme{width:100%;border-collapse:collapse;font-size:14px}
table.ritme th{text-align:left;font-size:12px;color:var(--grijs);font-weight:600;padding:10px 8px;border-bottom:1px solid var(--lijn)}
table.ritme td{padding:12px 8px;border-bottom:1px solid var(--lijn)}
table.ritme tr:last-child td{border-bottom:0}
.tabelbox{overflow-x:auto}
@media (max-width:700px){main{padding:24px 16px}nav.menu{max-width:none}h1{font-size:32px}}
</style>
</head>
<body>
<div class="app">

<nav class="menu" aria-label="Hoofdmenu">
  <div class="merk">
    <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><rect x="10" y="2" width="5" height="22" rx="1.5" fill="#FFFFFF"/><path d="M3 22 L22 4" stroke="#9DB8EA" stroke-width="2.5" stroke-linecap="round"/><circle cx="3" cy="22" r="2.6" fill="#9DB8EA"/><circle cx="22" cy="4" r="2.6" fill="#9DB8EA"/></svg>
    <div><b>INSIGHTANCE</b><span>Dagcockpit</span></div>
  </div>
  <div style="display:flex;flex-direction:column;gap:6px">
    <a href="#vandaag" class="actief">Vandaag</a>
    <a href="#week">Deze week</a>
    <a href="#binnenkort">Binnenkort</a>
    <a href="#ritme">Weekritme</a>
  </div>
  <div class="doel"><small>DOEL</small><strong>Eerste betalende klant</strong></div>
</nav>

<main>
  <header class="kop" id="vandaag">
    <div>
      <div class="datum">{{ datum_kop }}</div>
      <h1>{{ groet }}, Oussama</h1>
    </div>
    <div class="kaart voortgang">
      <div class="rij"><span style="color:var(--grijs)">Voortgang vandaag</span><strong>{{ klaar }} van {{ totaal }}</strong></div>
      <div class="balk"><div style="width:{{ procent }}%"></div></div>
    </div>
  </header>

  <section class="kaart" id="week" aria-label="Deze week" style="padding:18px 20px;gap:14px">
    <div class="kaartkop"><h2>Deze week</h2><span style="font-size:13px;color:var(--grijs)">{{ week.titel }}</span></div>
    <div class="week">
      {% for d in week.dagen %}
      <div class="dag{% if d.vandaag %} vandaag{% endif %}"><small>{{ d.kop }}</small><span>{{ d.label }}</span><div class="mini"><div style="width:{{ d.procent }}%"></div></div></div>
      {% endfor %}
    </div>
  </section>

  <div class="raster">
    <div class="kaarten">
      {% for k in kaarten %}
      <section class="kaart">
        <div class="kaartkop"><h2>{{ k.chat }}</h2><span class="pil {{ k.kleur }}">{{ k.taken|selectattr('klaar')|list|length }} van {{ k.taken|length }}</span></div>
        {% for t in k.taken %}
        <div class="taak{% if t.klaar %} klaar{% endif %}">
          <form class="vink" method="post" action="/vink">
            <input type="hidden" name="sleutel" value="{{ t.sleutel }}">
            <input type="hidden" name="aan" value="{{ '0' if t.klaar else '1' }}">
            <label><input type="checkbox" {% if t.klaar %}checked{% endif %} onchange="this.form.submit()">{{ t.titel }}</label>
          </form>
          <span class="ritme{% if t.achterstand and not t.klaar %} achter{% endif %}">{{ t.ritme }}</span>
          {% if t.soort == 'eenmalig' %}
          <form method="post" action="/verwijder" style="margin:0"><input type="hidden" name="id" value="{{ t.id }}"><button class="weg" type="submit" aria-label="Taak verwijderen: {{ t.titel }}">&times;</button></form>
          {% endif %}
        </div>
        {% endfor %}
      </section>
      {% endfor %}

      <section class="kaart">
        <div class="kaartkop"><h2>Content</h2><span class="pil oranje">Volgende: {{ contentdag }}</span></div>
        {% for t in content_taken %}
        <div class="taak{% if t.klaar %} klaar{% endif %}">
          <form class="vink" method="post" action="/vink">
            <input type="hidden" name="sleutel" value="{{ t.sleutel }}">
            <input type="hidden" name="aan" value="{{ '0' if t.klaar else '1' }}">
            <label><input type="checkbox" {% if t.klaar %}checked{% endif %} onchange="this.form.submit()">{{ t.titel }}</label>
          </form>
        </div>
        {% endfor %}
        <p class="uitleg">LinkedIn-posts van deze week. Ze gaan automatisch live; geplaatst = doorgestreept met vinkje.</p>
        <div class="posts">
          {% for p in linkedin %}
          <div class="post{% if p.geplaatst %} geplaatst{% endif %}">
            <span class="wat"><b>{{ p.wanneer }}</b>{{ p.pijler }}</span>
            {% if p.geplaatst %}
            <svg width="16" height="16" viewBox="0 0 16 16" role="img" aria-label="geplaatst"><path d="M3 8.5 L6.5 12 L13 4.5" fill="none" stroke="#0F5A35" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            {% else %}
            <span style="font-size:12px">gepland</span>
            {% endif %}
          </div>
          {% endfor %}
        </div>
      </section>
    </div>

    <aside>
      <section class="kaart" id="binnenkort" style="gap:14px">
        <h2>Binnenkort</h2>
        {% for b in binnenkort %}
        <div class="binnen"><span class="d {{ b.accent }}">{{ b.kop }}</span><p>{{ b.titel }}</p></div>
        {% else %}
        <p class="leeg">Niets gepland de komende drie weken.</p>
        {% endfor %}
      </section>

      <section class="kaart" style="gap:10px">
        <h2 style="margin-bottom:4px">Snelkoppelingen</h2>
        {% for l in links %}
        <a class="link" href="{{ l.url }}" target="_blank" rel="noopener">{{ l.titel }}<span aria-hidden="true">&rsaquo;</span></a>
        {% endfor %}
      </section>

      <section class="kaart" style="gap:10px">
        <form method="post" action="/notitie" style="display:flex;flex-direction:column;gap:10px;margin:0">
          <label for="notitie" style="font-size:16px;font-weight:700">Notitie voor vandaag</label>
          <textarea id="notitie" name="tekst" rows="3" placeholder="Bijvoorbeeld: Victorian Candle Co nabellen">{{ notitie }}</textarea>
          <button class="knop licht" type="submit">Notitie opslaan</button>
        </form>
        {% if vorige_notitie %}<p class="vorige"><strong>Vorige notitie ({{ vorige_notitie[0] }}):</strong> {{ vorige_notitie[1] }}</p>{% endif %}
      </section>

      <button class="knop" type="button" onclick="document.getElementById('nieuw').showModal()">Taak toevoegen</button>
    </aside>
  </div>

  <section class="kaart" id="ritme">
    <div class="kaartkop"><h2>Weekritme</h2><span style="font-size:13px;color:var(--grijs)">Aanpassen in apps/dagcockpit/ritme.py</span></div>
    <div class="tabelbox">
      <table class="ritme">
        <thead><tr><th>Taak</th><th>Chat</th><th>Wanneer</th></tr></thead>
        <tbody>
          {% for t in ritme_taken %}<tr><td>{{ t.titel }}</td><td>{{ t.chat }}</td><td>{{ t.ritme }}</td></tr>{% endfor %}
          {% for p in linkedin_ritme %}<tr><td>LinkedIn-post: {{ p.pijler }} (automatisch)</td><td>Content</td><td>{{ dagen_kort[p.dag] }} {{ p.tijd }}</td></tr>{% endfor %}
        </tbody>
      </table>
    </div>
  </section>
</main>
</div>

<dialog id="nieuw" aria-labelledby="nieuwtitel">
  <form method="post" action="/taak">
    <h2 id="nieuwtitel">Taak toevoegen</h2>
    <label>Wat moet er gebeuren?<input name="titel" required autofocus placeholder="Bijvoorbeeld: Rolla Granola opvolgen"></label>
    <label>Bij welke chat?<select name="chat">{% for c in chats %}<option{% if c == 'Algemeen' %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></label>
    <label>Wanneer?<input type="date" name="datum" value="{{ vandaag_iso }}"></label>
    <div class="knoppen">
      <button class="knop licht" type="button" onclick="this.closest('dialog').close()">Annuleren</button>
      <button class="knop" type="submit">Toevoegen</button>
    </div>
  </form>
</dialog>
</body>
</html>
"""


if __name__ == "__main__":
    poort = int(get_env("DAGCOCKPIT_PORT") or 5070)
    print(f"Dagcockpit draait op http://127.0.0.1:{poort}")
    app.run(host="127.0.0.1", port=poort, debug=False)
