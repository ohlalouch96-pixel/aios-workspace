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
import random
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dagcockpit_content (
            datum TEXT NOT NULL,
            kanaal TEXT NOT NULL,
            aantal INTEGER,
            klaar INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (datum, kanaal)
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
    if taak.get("vanaf") and d.isoformat() < taak["vanaf"]:
        return False
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
    for t in [t for t in ritme.TAKEN if valt_op(t, vandaag) or t.get("toon_altijd")]:
        uit = not valt_op(t, vandaag)
        label = t["ritme"]
        if uit:
            d = vandaag + timedelta(days=1)
            while not valt_op(t, d):
                d += timedelta(days=1)
            label = f"weer op {DAGEN_KORT[d.weekday()]}"
        per_chat.setdefault(t["chat"], []).append({
            "sleutel": t["id"], "titel": t["titel"], "ritme": label,
            "klaar": t["id"] in vinkjes and not uit, "soort": "vast", "achterstand": False, "uit": uit,
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


def content_week(conn, vandaag):
    """LinkedIn- en Instagram-posts van deze week (ma-zo) per dag, met handmatig vinkje en aantal."""
    maandag = vandaag - timedelta(days=vandaag.weekday())
    zondag = maandag + timedelta(days=6)
    opgeslagen = {(r["datum"], r["kanaal"]): r for r in conn.execute(
        "SELECT * FROM dagcockpit_content WHERE datum BETWEEN ? AND ?", (maandag.isoformat(), zondag.isoformat()))}
    li_posts = {}
    for p in ritme.LINKEDIN_WEKELIJKS:
        d = maandag + timedelta(days=p["dag"])
        li_posts.setdefault(d, []).append((p["tijd"], p["pijler"]))
    for p in ritme.LINKEDIN_LOS:
        d = date.fromisoformat(p["datum"])
        if maandag <= d <= zondag:
            li_posts.setdefault(d, []).append((p["tijd"], p["pijler"]))
    dagen, linkedin, instagram = [], [], []
    for i in range(7):
        d = maandag + timedelta(days=i)
        iso = d.isoformat()
        dagen.append({"kop": DAGEN_KORT[i], "dag": d.day, "vandaag": d == vandaag})
        posts = [{"tijd": t[1:] if t.startswith("0") else t, "kort": ritme.PIJLER_KORT.get(pl, pl), "pijler": pl}
                 for t, pl in sorted(li_posts.get(d, []))]
        li = opgeslagen.get((iso, "linkedin"))
        linkedin.append({"iso": iso, "posts": posts, "aantal": len(posts), "klaar": bool(li and li["klaar"])})
        ig = opgeslagen.get((iso, "instagram"))
        aantal = ig["aantal"] if ig and ig["aantal"] is not None else ritme.INSTAGRAM_STANDAARD_AANTAL
        instagram.append({"iso": iso, "aantal": aantal, "klaar": bool(ig and ig["klaar"])})
    return {"dagen": dagen, "linkedin": linkedin, "instagram": instagram}


def volgende_zaterdag(vandaag):
    return vandaag + timedelta(days=(5 - vandaag.weekday()) % 7)


def volgende_contentdag(vandaag):
    d = vandaag
    while not is_laatste_zaterdag(d):
        d += timedelta(days=1)
    return d


def agenda_groepen(items, vandaag):
    """Binnenkort-items gegroepeerd per week: Deze week / Volgende week / Week erna."""
    maandag = vandaag - timedelta(days=vandaag.weekday())
    namen = ["Deze week", "Volgende week", "Week erna"]
    groepen = []
    for it in items:
        idx = min((it["datum"] - maandag).days // 7, 2)
        if not groepen or groepen[-1]["naam"] != namen[idx]:
            groepen.append({"naam": namen[idx], "regels": []})
        groepen[-1]["regels"].append(it)
    return groepen


def binnenkort(conn, vandaag):
    """Twee weken vooruit: t/m de zondag van de week waarin (morgen + 7 dagen) valt.
    Op zondag 15-11 dus t/m zondag 29-11; vanaf zondag 22-11 t/m 6-12."""
    verder = vandaag + timedelta(days=8)
    tot = verder + timedelta(days=6 - verder.weekday())
    items = []
    for r in conn.execute("SELECT * FROM dagcockpit_taken WHERE datum > ? AND datum <= ? AND klaar_op IS NULL",
                          (vandaag.isoformat(), tot.isoformat())):
        items.append({"datum": date.fromisoformat(r["datum"]), "titel": r["titel"], "id": r["id"], "vast": False})
    # bijzondere vaste momenten (niet de dagelijkse basistaken)
    d = vandaag + timedelta(days=1)
    while d <= tot:
        for t in vaste_taken(d):
            if t["id"] in ritme.BINNENKORT_VAST:
                items.append({"datum": d, "titel": t.get("agenda", t["titel"]), "id": None, "vast": True})
        d += timedelta(days=1)
    items.sort(key=lambda x: x["datum"])
    for it in items:
        it["kop"] = f"{DAGEN_KORT[it['datum'].weekday()]} {it['datum'].day}"
        it["wd"], it["dag"] = DAGEN_KORT[it["datum"].weekday()], it["datum"].day
        it["accent"] = "oranje" if is_laatste_zaterdag(it["datum"]) else "blauw"
    return items


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


def _quote_ronde(nr):
    """Gehusselde volgorde van alle quotes voor ronde nr; begint nooit met de laatste van de vorige ronde."""
    q = list(ritme.QUOTES)
    random.Random(nr).shuffle(q)
    if nr > 0 and len(q) > 1:
        vorige = list(ritme.QUOTES)
        random.Random(nr - 1).shuffle(vorige)
        if q[0] == vorige[-1]:
            q[0], q[1] = q[1], q[0]
    return q


def dagquote(dag):
    """Elke dag een andere quote: alle quotes komen in willekeurige volgorde aan de beurt voordat er een terugkomt."""
    n = len(ritme.QUOTES)
    ronde, plek = divmod(dag.toordinal(), n)
    return _quote_ronde(ronde)[plek]


def todo_lijst():
    """Open punten uit todo/README.md: elke ## kop die niet doorgestreept is, met een kort statuslabel."""
    pad = WORKSPACE_ROOT / "todo" / "README.md"
    if not pad.exists():
        return []
    items, huidig = [], None
    for regel in pad.read_text(encoding="utf-8").splitlines():
        if regel.startswith("## "):
            titel = regel[3:].strip()
            huidig = None if titel.startswith("~~") else {"titel": titel, "status": ""}
            if huidig:
                items.append(huidig)
        elif huidig and regel.startswith("**Status:**") and not huidig["status"]:
            huidig["status"] = regel.replace("**Status:**", "").strip()
    for it in items:
        st = it["status"].lower()
        if "gepland" in st:
            it["label"], it["kleur"] = "Gepland", "blauw"
        elif any(w in st for w in ("opgepakt", "ingeschreven", "loopt", "bezig")):
            it["label"], it["kleur"] = "Loopt", "groen"
        else:
            it["label"], it["kleur"] = "Geparkeerd", "grijs"
        kop = it["titel"].split(" (")[0]
        voor = kop.split(":")[0]
        it["titel"] = voor if len(voor) > 6 else kop
    volgorde = {"Loopt": 0, "Gepland": 1, "Geparkeerd": 2}
    return sorted(items, key=lambda x: volgorde[x["label"]])


def todo_cirkel(items):
    """Segmenten voor het cirkeldiagram: (label, aantal, kleur, dasharray, offset) op omtrek 100."""
    kleuren = {"Loopt": "#5FD39A", "Gepland": "#8FB2F7", "Geparkeerd": "#4F6690"}
    totaal = len(items) or 1
    segs, start = [], 0.0
    for label in ("Loopt", "Gepland", "Geparkeerd"):
        n = sum(1 for i in items if i["label"] == label)
        lengte = 100 * n / totaal
        segs.append({"label": label, "aantal": n, "kleur": kleuren[label],
                     "dash": f"{max(lengte - 1.5, 0):.2f} {100 - max(lengte - 1.5, 0):.2f}", "offset": f"{25 - start:.2f}"})
        start += lengte
    return segs


ICONEN = {
    "LinkedIn": '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M8 10v6M8 7.5v.01M12 16v-4a2 2 0 0 1 4 0v4M12 10v6"/>',
    "Webshops": '<path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    "Installatiebedrijven en makelaars": '<path d="M6 3h3l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 4 5a2 2 0 0 1 2-2z"/>',
    "Accountants en administratiekantoren": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M12 11h2M8 15h2M12 15h2M16 11v4"/>',
    "Instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5v.01"/>',
    "Website": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "Content": '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M13 7l4 4"/>',
    "Agenda": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "_": '<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>',
}


# ---------------------------------------------------------------- routes

@app.route("/")
def index():
    importlib.reload(ritme)
    try:
        vandaag = date.fromisoformat(request.args["datum"]) if request.args.get("datum") else date.today()
    except ValueError:
        vandaag = date.today()
    conn = _db()
    per_chat = taken_van_vandaag(conn, vandaag)
    alle = [t for lst in per_chat.values() for t in lst if not t.get("uit")]
    klaar = sum(1 for t in alle if t["klaar"])
    kaarten = [{"chat": c, "kleur": ritme.CHATS.get(c, "grijs"), "taken": per_chat[c]}
               for c in per_chat if per_chat[c] and c not in ("Content", "Algemeen", "Instagram-content")]
    algemeen = [{"chat": "Algemeen", "kleur": ritme.CHATS.get("Algemeen", "grijs"), "taken": per_chat.get("Algemeen", [])}]
    algemeen = [k for k in algemeen if k["taken"]]
    content_taken = per_chat.get("Content", [])
    notitie = conn.execute("SELECT tekst FROM dagcockpit_notities WHERE datum=?", (vandaag.isoformat(),)).fetchone()
    vorige = conn.execute("SELECT datum, tekst FROM dagcockpit_notities WHERE datum < ? AND tekst != '' ORDER BY datum DESC LIMIT 1",
                          (vandaag.isoformat(),)).fetchone()
    html = render_template_string(
        TEMPLATE,
        groet=groet(), datum_kop=lang(vandaag).upper(),
        klaar=klaar, totaal=len(alle), procent=round(100 * klaar / len(alle)) if alle else 0,
        kaarten=kaarten, algemeen=algemeen, content_taken=content_taken,
        week=weekstrook(conn, vandaag), cw=content_week(conn, vandaag),
        contentdag=kort(volgende_contentdag(vandaag)),
        insta_taken=per_chat.get("Instagram-content", []),
        instadag=kort(volgende_zaterdag(vandaag)),
        agenda=agenda_groepen(binnenkort(conn, vandaag), vandaag), quote=dagquote(vandaag), links=snelkoppelingen(), todo=todo_lijst(), todo_cirkel=todo_cirkel(todo_lijst()),
        notitie=notitie["tekst"] if notitie else "",
        vorige_notitie=(kort(date.fromisoformat(vorige["datum"])), vorige["tekst"]) if vorige else None,
        vandaag_iso=vandaag.isoformat(), chats=list(ritme.CHATS),
        iconen=ICONEN, ritme_taken=ritme.TAKEN, linkedin_ritme=ritme.LINKEDIN_WEKELIJKS, dagen_kort=DAGEN_KORT,
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


@app.route("/content", methods=["POST"])
def content():
    kanaal = request.form["kanaal"]
    datum = date.fromisoformat(request.form["datum"]).isoformat()
    conn = _db()
    conn.execute("INSERT OR IGNORE INTO dagcockpit_content (datum, kanaal) VALUES (?, ?)", (datum, kanaal))
    if "aantal" in request.form:
        conn.execute("UPDATE dagcockpit_content SET aantal=? WHERE datum=? AND kanaal=?",
                     (max(0, min(9, int(request.form["aantal"]))), datum, kanaal))
    else:
        conn.execute("UPDATE dagcockpit_content SET klaar=? WHERE datum=? AND kanaal=?",
                     (1 if request.form.get("aan") == "1" else 0, datum, kanaal))
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,500&display=swap" rel="stylesheet">
<style>
:root{--navy:#0E1E38;--navy2:#1C3358;--blauw:#A8823F;--blauwzacht:#F4ECDD;--goud:#C9A961;--tekst:#141B2B;--grijs:#4B5568;--lijn:#E6DFD2;--bg:#F6F3ED;--groen:#0F5A35;--groenzacht:#E3F4EA;--oranje:#8A4B08;--oranjezacht:#FDF0E1;--paars:#5B3BB0;--paarszacht:#EFEAFB;--rood:#B4231A;--roodzacht:#FCE8E6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);font-family:Inter,system-ui,sans-serif;color:var(--tekst)}
a{color:var(--blauw)}a:hover{color:var(--navy)}
.app{display:flex;flex-wrap:wrap;min-height:100vh}
nav.menu{flex:1 1 210px;max-width:240px;background:var(--navy);color:#fff;padding:20px 16px;display:flex;flex-direction:column;gap:18px}
.merk{display:flex;align-items:center;gap:10px;padding:0 4px}
.merk b{font-weight:700;letter-spacing:.14em;font-size:13px;display:block}
.merk span{font-size:12px;color:#B9C8E4}
.menukop{font-size:11px;letter-spacing:.12em;color:#9FB2D6;font-weight:600;padding:0 6px;margin-bottom:6px}
.menu .link{display:flex;justify-content:space-between;align-items:center;min-height:32px;padding:0 10px;border-radius:9px;color:#E3EAF6;text-decoration:none;font-size:13px}
.menu .link:hover{background:var(--navy2);color:#fff}
.menu .link span{color:#9DB8EA}
.menuknop{font-family:inherit;width:100%;text-align:left;display:flex;justify-content:space-between;align-items:center;min-height:38px;padding:0 10px;border-radius:9px;color:#E3EAF6;background:transparent;border:0;font-size:13px;cursor:pointer}
.menuknop:hover{background:var(--navy2);color:#fff}
.doel{margin-top:auto;background:linear-gradient(150deg,#2B5596,#1B3D70);border:1px solid #F2C14E;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:5px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.doel small{font-size:11px;color:#F2C14E;letter-spacing:.14em;font-weight:700;margin-top:4px}
.doel strong{font-family:'Playfair Display',Georgia,serif;font-size:18px;line-height:1.25;font-weight:600;color:#fff}
.quote{flex:1 1 280px;margin:0;text-align:center;font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:19px;line-height:1.4;color:var(--navy2);padding:0 12px}
.dag small{display:flex;justify-content:space-between;align-items:center}
.voorbij{width:16px;height:16px;border-radius:50%;background:#1F8A55;display:inline-flex;align-items:center;justify-content:center}
main{flex:999 1 560px;min-width:0;padding:24px 28px;display:flex;flex-direction:column;gap:18px}
header.kop{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px}
.datum{font-size:12px;font-weight:600;letter-spacing:.12em;color:var(--blauw)}
h1{margin:4px 0 0;font-family:'Playfair Display',Georgia,serif;font-size:32px;font-weight:600}
.rechts{display:flex;align-items:center;gap:14px}
.ring{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid var(--lijn);border-radius:14px;padding:8px 16px 8px 8px}
.ring div{display:flex;flex-direction:column}
.ring small{font-size:12px;color:var(--grijs)}
.ring strong{font-size:15px}
.kaart{background:#fff;border:1px solid var(--lijn);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column;gap:10px}
.kaart h2{margin:0;font-size:15px;font-weight:700}
.kaartkop{display:flex;justify-content:space-between;align-items:center;gap:10px}
.pil{font-size:11px;font-weight:600;padding:3px 9px;border-radius:99px;white-space:nowrap}
.pil.blauw{color:var(--blauw);background:var(--blauwzacht)}
.pil.oranje{color:var(--oranje);background:var(--oranjezacht)}
.pil.paars{color:var(--paars);background:var(--paarszacht)}
.pil.grijs{color:var(--grijs);background:#EEF1F6}
.week{display:grid;grid-template-columns:repeat(7,minmax(86px,1fr));gap:8px;overflow-x:auto}
.dag{border-radius:10px;padding:8px 10px;background:var(--bg);display:flex;flex-direction:column;gap:4px}
.dag small{font-size:11px;color:var(--grijs);font-weight:600}
.dag span{font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dag .mini{height:3px;background:var(--lijn);border-radius:99px}
.dag .mini div{height:3px;background:var(--blauw);border-radius:99px}
.dag.vandaag{background:var(--navy);color:#fff}
.dag.vandaag small{color:#B9C8E4}
.dag.vandaag .mini{background:var(--navy2)}
.dag.vandaag .mini div{background:#9DB8EA}
.raster{display:grid;grid-template-columns:minmax(0,2.4fr) minmax(300px,1fr);gap:18px;align-items:start}
.kaarten{display:flex;flex-direction:column;gap:14px}
.takenrij{display:grid;gap:14px;align-items:stretch}
.takenrij.vol .kaartkop .ico{display:none}
.pillen{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.cweek{display:grid;grid-template-columns:72px repeat(7,minmax(0,1fr));column-gap:4px;row-gap:8px;align-items:start}
.ckop{font-size:11px;font-weight:600;color:var(--grijs);text-align:center;padding:3px 0;border-radius:99px}
.ckop.nu{background:var(--navy);color:#fff}
.klabel{font-size:12px;font-weight:700;padding-top:8px}
.cel{display:flex;flex-direction:column;align-items:center;gap:2px;text-align:center;min-width:0}
.cel form{margin:0}
.bol{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:inherit;font-size:13px;font-weight:700;border:2px solid var(--groen);color:var(--groen);background:var(--groenzacht);cursor:pointer;padding:0;margin-bottom:2px}
.bol:hover{background:#CDEBDA}
.cel.klaar .bol{background:var(--groen);border-color:var(--groen)}
.bol.leeg{border:2px dashed #C9D1DE;background:transparent;color:#9AA3B5;cursor:default}
.tijd{font-size:11px;font-weight:700;color:var(--tekst)}
.pijl{font-size:10px;color:var(--grijs);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.aantal{font-size:11px;font-weight:600;color:var(--grijs)}
.cel.klaar .tijd,.cel.klaar .pijl,.cel.klaar .aantal{text-decoration:line-through;color:#6B8A78}
select.aantal{font-family:inherit;border:0;background:transparent;cursor:pointer;padding:2px 0;color:var(--grijs)}
select.aantal:hover{color:var(--blauw)}
.menutodo{display:flex;flex-direction:column;gap:8px}
.menutodo .menukop{display:flex;justify-content:space-between;margin-bottom:0}
.todorij{display:flex;align-items:center;gap:12px;padding:0 6px}
.todorij .leg{display:flex;flex-direction:column;gap:3px;font-size:12px;color:#E3EAF6;flex:1}
.todorij .leg span{display:flex;align-items:center;gap:7px}
.todorij .leg i{width:8px;height:8px;border-radius:2px}
.todorij .leg b{margin-left:auto}
.menutodo ul{list-style:none;margin:0;padding:0 6px;display:flex;flex-direction:column;gap:5px;font-size:12px;color:#E3EAF6}
.menutodo li{display:flex;align-items:center;gap:7px}
.menutodo li i{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.taak{display:flex;align-items:center;gap:10px}
.taak form.vink{display:flex;align-items:center;flex:1;margin:0}
.taak label{display:flex;align-items:center;gap:10px;font-size:14px;cursor:pointer;flex:1;line-height:1.35}
.taak input[type=checkbox]{width:18px;height:18px;accent-color:var(--blauw);margin:0;flex-shrink:0;cursor:pointer}
.taak.klaar label{color:#6B7488;text-decoration:line-through}
.taak .ritme{font-size:11px;color:var(--grijs);white-space:nowrap}
.taak .ritme.achter{color:var(--rood);font-weight:600}
.weg{background:none;border:0;color:#8A93A6;font-size:16px;line-height:1;min-width:28px;min-height:28px;border-radius:7px;cursor:pointer}
.weg:hover{background:var(--bg);color:var(--rood)}
table.posts{width:100%;border-collapse:collapse;font-size:13px}
table.posts td{padding:6px 4px;border-top:1px solid var(--lijn)}
table.posts tr:first-child td{border-top:0}
table.posts .wanneer{font-weight:700;color:var(--groen);white-space:nowrap;width:70px}
table.posts .status{text-align:right;width:70px}
table.posts tr.geplaatst .wanneer,table.posts tr.geplaatst .wat{text-decoration:line-through;color:#6B8A78}
.gepland{font-size:11px;font-weight:600;color:var(--groen);background:var(--groenzacht);padding:2px 8px;border-radius:99px}
.zijkant{display:flex;flex-direction:column;gap:14px}
table.todo{width:100%;border-collapse:collapse;font-size:13px}
table.todo td{padding:6px 0;border-top:1px solid var(--lijn);vertical-align:middle}
table.todo tr:first-child td{border-top:0}
table.todo td.l{text-align:right;width:90px}
.pil.groen{color:var(--groen);background:var(--groenzacht)}
details.geparkeerd summary{font-size:13px;font-weight:600;color:var(--blauw);cursor:pointer;min-height:32px;display:flex;align-items:center}
details.geparkeerd[open] summary{margin-bottom:4px}
table.binnen{width:100%;border-collapse:collapse;font-size:13px}
table.binnen td{padding:4px 0;vertical-align:top;border-top:1px solid var(--lijn);line-height:1.35}
table.binnen tr:first-child td{border-top:0}
table.binnen .d{width:52px;font-weight:700;white-space:nowrap}
table.binnen .d.blauw{color:var(--blauw)}
table.binnen .d.oranje{color:var(--oranje)}
.leeg{font-size:13px;color:var(--grijs);margin:0}
textarea{font-family:inherit;font-size:13px;color:var(--tekst);border:1px solid #D5DCE8;border-radius:10px;padding:10px;resize:vertical;width:100%}
.notitierij{display:flex;justify-content:space-between;align-items:center;gap:8px}
.knop{font-family:inherit;font-size:14px;font-weight:600;color:#fff;background:var(--blauw);border:0;border-radius:11px;padding:0 16px;min-height:44px;cursor:pointer}
.knop:hover{background:#1A43BA}
.knop.licht{background:var(--bg);color:var(--tekst);border:1px solid var(--lijn)}
.knop.klein{min-height:34px;font-size:13px;padding:0 12px;border-radius:9px}
.vorige{font-size:12px;color:var(--grijs);margin:0;line-height:1.4}
dialog{border:0;border-radius:16px;padding:0;width:min(560px,92vw);box-shadow:0 20px 60px rgba(16,33,61,.25)}
dialog::backdrop{background:rgba(16,33,61,.45)}
dialog .binnenin{padding:24px;display:flex;flex-direction:column;gap:14px}
dialog h2{margin:0;font-size:18px}
dialog label{font-size:13px;font-weight:600;color:var(--grijs);display:flex;flex-direction:column;gap:6px}
dialog input,dialog select{font-family:inherit;font-size:15px;color:var(--tekst);border:1px solid #D5DCE8;border-radius:10px;padding:0 12px;min-height:44px}
.knoppen{display:flex;gap:10px;justify-content:flex-end;margin-top:4px}
table.ritme{width:100%;border-collapse:collapse;font-size:13px}
table.ritme th{text-align:left;font-size:12px;color:var(--grijs);font-weight:600;padding:8px 6px;border-bottom:1px solid var(--lijn)}
table.ritme td{padding:8px 6px;border-bottom:1px solid var(--lijn)}
@media (max-width:900px){.raster,.kaarten{grid-template-columns:minmax(0,1fr)}.kaart.content{grid-column:auto}nav.menu{max-width:none}main{padding:20px 16px}}
/* Tegelstijl B: navy koppen (gekozen 15-11) */
section.kaart.nk{padding:0;overflow:hidden;gap:0;border-radius:14px}
section.kaart.nk > .kaartkop{background:var(--navy);padding:8px 12px;min-height:48px}
section.kaart.nk > .kaartkop h2{color:#fff;display:flex;align-items:center;gap:10px;font-size:14px;line-height:1.25}
section.kaart.nk > :not(.kaartkop):not(.balk){margin-left:12px;margin-right:12px}
section.kaart.nk > :last-child{margin-bottom:12px}
section.kaart.nk > .balk + *,section.kaart.nk > .kaartkop + :not(.balk){margin-top:10px}
.balk.klaar{height:22px;background:#1F8A55;color:#fff;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;gap:6px;letter-spacing:.04em}
.takenlijst .taak label{font-size:13px}
.post{display:block;font-size:10px;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.post .tijd{font-size:11px}
.ico{width:28px;height:28px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;background:rgba(201,169,97,.14);border:1px solid rgba(201,169,97,.5)}
.teller{font-size:12px;font-weight:700;color:var(--goud);flex-shrink:0}
section.kaart.nk > .kaartkop h2{min-width:0}
.klaar-tag{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;color:#fff;background:#1F8A55;padding:4px 10px;border-radius:99px;flex-shrink:0}
.balk{height:3px;background:#1C3358}
.balk div{height:3px;background:var(--goud)}
.takenrij section.kaart.nk{display:flex;flex-direction:column}
.takenrij .takenlijst{flex:1}
.takenlijst{display:flex;flex-direction:column;gap:6px}
.takenlijst .taak{flex:1;background:#FAF7F1;border:1px solid #EFE8DA;border-radius:9px;padding:5px 9px;min-height:34px}
.takenlijst .taak.klaar{background:#F6F3EC}
.taak.uit{background:#EFECE6 !important;border-style:dashed !important;opacity:.75}
.taak.uit label,.taak.uit input{cursor:not-allowed;color:#8B8577}
.taak.uit .ritme{color:#8B8577;font-style:italic}
.kaart.content .kaartkop .pil.oranje,.kaart.content .kaartkop .pil.paars{background:rgba(255,255,255,.1);color:#E8E2D4}
.agenda{gap:0}
.groep{font-size:10px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:var(--blauw);margin-top:8px;margin-bottom:5px}
ul.kal{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1px}
ul.kal li{display:flex;align-items:center;gap:10px;font-size:12.5px;line-height:1.25}
.cal{width:50px;height:18px;flex-shrink:0;border-radius:5px;overflow:hidden;border:1px solid var(--lijn);display:flex}
.cal small{width:22px;display:flex;align-items:center;justify-content:center;background:var(--navy);color:var(--goud);font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.cal b{flex:1;display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--tekst)}
/* Kleurstelling A: navy & goud (gekozen 15-11) */
.knop{background:var(--navy)}.knop:hover{background:var(--navy2)}
.menukop,.merk span{color:var(--goud)}
.menu .link,.menuknop,.menutodo ul,.todorij .leg{color:#E8E2D4}
.menu .link span,.menuknop span{color:var(--goud)}
.ring svg circle + circle{stroke:var(--goud)}
.dag.vandaag small{color:var(--goud)}.dag.vandaag .mini div{background:var(--goud)}
h1{color:var(--tekst)}.quote{color:var(--blauw)}
.doel{background:#0A1628;border:1px solid var(--goud);border-radius:6px;box-shadow:0 12px 30px rgba(0,0,0,.4)}
.doel small{color:var(--goud)}.doel svg circle{stroke:var(--goud)}.doel svg circle:last-child{fill:var(--goud)}
/* Compacter bij 5+ tegels (19-11) */
.takenrij.vol .takenlijst .taak label{font-size:12px;line-height:1.25}.takenrij.vol .takenlijst .taak{min-height:28px;padding:4px 8px}.takenrij.vol .takenlijst{gap:5px}
.takenrij.vol section.kaart.nk > .kaartkop h2{font-size:13px;line-height:1.15}.takenrij.vol section.kaart.nk > .kaartkop{min-height:44px;padding:6px 10px}
</style>
</head>
<body>
{% macro icoon(naam) %}<span class="ico" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A961" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{{ (iconen.get(naam) or iconen['_'])|safe }}</svg></span>{% endmacro %}
{% macro taakregel(t) %}
        <div class="taak{% if t.klaar %} klaar{% endif %}{% if t.uit %} uit{% endif %}">
          <form class="vink" method="post" action="/vink">
            <input type="hidden" name="sleutel" value="{{ t.sleutel }}">
            <input type="hidden" name="aan" value="{{ '0' if t.klaar else '1' }}">
            <label><input type="checkbox" {% if t.klaar %}checked{% endif %}{% if t.uit %} disabled{% endif %} onchange="this.form.submit()">{{ t.titel }}</label>
          </form>
          {% if t.uit or t.soort == 'eenmalig' %}<span class="ritme{% if t.achterstand and not t.klaar %} achter{% endif %}">{{ t.ritme }}</span>{% endif %}
          {% if t.soort == 'eenmalig' %}
          <form method="post" action="/verwijder" style="margin:0"><input type="hidden" name="id" value="{{ t.id }}"><button class="weg" type="submit" aria-label="Taak verwijderen: {{ t.titel }}">&times;</button></form>
          {% endif %}
        </div>
{% endmacro %}
{% macro takenkaart(k) %}
      {% set actief = k.taken|rejectattr('uit')|list %}{% set af = actief|selectattr('klaar')|list|length %}
      <section class="kaart nk">
        <div class="kaartkop"><h2>{{ icoon(k.chat) }}<span>{{ k.chat|replace('administratiekantoren', 'administratie&shy;kantoren')|replace('Installatiebedrijven', 'Installatie&shy;bedrijven')|safe }}</span></h2>
          {% if not (actief and af == actief|length) %}<span class="teller">{{ af }}/{{ actief|length }}</span>{% endif %}
        </div>
        {% if actief and af == actief|length %}<div class="balk klaar"><svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5 L6.5 12 L13 4.5" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>Klaar</div>
        {% else %}<div class="balk"><div style="width:{{ (100 * af / (actief|length)) if actief else 0 }}%"></div></div>{% endif %}
        <div class="takenlijst">{% for t in k.taken %}{{ taakregel(t) }}{% endfor %}</div>
      </section>
{% endmacro %}
<div class="app">

<nav class="menu" aria-label="Zijmenu">
  <div class="merk">
    <svg width="24" height="24" viewBox="0 0 26 26" aria-hidden="true"><rect x="10" y="2" width="5" height="22" rx="1.5" fill="#FFFFFF"/><path d="M3 22 L22 4" stroke="#9DB8EA" stroke-width="2.5" stroke-linecap="round"/><circle cx="3" cy="22" r="2.6" fill="#9DB8EA"/><circle cx="22" cy="4" r="2.6" fill="#9DB8EA"/></svg>
    <div><b>INSIGHTANCE</b><span>Dagcockpit</span></div>
  </div>
  <div>
    <div class="menukop">SNELKOPPELINGEN</div>
    {% for l in links %}
    <a class="link" href="{{ l.url }}" target="_blank" rel="noopener">{{ l.titel }}<span aria-hidden="true">&rsaquo;</span></a>
    {% endfor %}
  </div>
  <div>
    <div class="menukop">INSTELLINGEN</div>
    <button class="menuknop" type="button" onclick="document.getElementById('ritme').showModal()">Weekritme bekijken<span aria-hidden="true">&rsaquo;</span></button>
  </div>
  <div class="menutodo">
    <div class="menukop"><span>TO-DO</span><span>{{ todo|length }} open</span></div>
    <div class="todorij">
      <svg width="48" height="48" viewBox="0 0 42 42" role="img" aria-label="{% for c in todo_cirkel %}{{ c.aantal }} {{ c.label|lower }}{% if not loop.last %}, {% endif %}{% endfor %}">
        <circle cx="21" cy="21" r="15.915" fill="none" stroke="#24497F" stroke-width="6"/>
        {% for c in todo_cirkel %}{% if c.aantal %}<circle cx="21" cy="21" r="15.915" fill="none" stroke="{{ c.kleur }}" stroke-width="6" stroke-dasharray="{{ c.dash }}" stroke-dashoffset="{{ c.offset }}"/>{% endif %}{% endfor %}
        <text x="21" y="24.5" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">{{ todo|length }}</text>
      </svg>
      <div class="leg">{% for c in todo_cirkel %}<span><i style="background:{{ c.kleur }}"></i>{{ c.label }}<b>{{ c.aantal }}</b></span>{% endfor %}</div>
    </div>
    <ul>{% for t in todo if t.label != 'Geparkeerd' %}<li><i style="background:{{ '#5FD39A' if t.label == 'Loopt' else '#8FB2F7' }}"></i>{{ t.titel }}</li>{% endfor %}</ul>
    <button class="menuknop" type="button" onclick="document.getElementById('geparkeerd').showModal()">Geparkeerd bekijken<span aria-hidden="true">&rsaquo;</span></button>
  </div>
  <div class="doel">
    <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="13" fill="none" stroke="#F2C14E" stroke-width="2.5"/><circle cx="16" cy="16" r="8" fill="none" stroke="#F2C14E" stroke-width="2.5"/><circle cx="16" cy="16" r="3.2" fill="#F2C14E"/></svg>
    <small>MIJN DOEL</small><strong>Eerste betalende klant</strong>
  </div>
</nav>

<main>
  <header class="kop">
    <div>
      <div class="datum">{{ datum_kop }}</div>
      <h1>{{ groet }}, Oussama Hlalouch</h1>
    </div>
    <p class="quote">&ldquo;{{ quote }}&rdquo;</p>
    <div class="rechts">
      <div class="ring">
        <svg width="52" height="52" viewBox="0 0 52 52" role="img" aria-label="{{ klaar }} van {{ totaal }} klaar">
          <circle cx="26" cy="26" r="21" fill="none" stroke="#E6EBF3" stroke-width="6"/>
          {% if procent > 0 %}<circle cx="26" cy="26" r="21" fill="none" stroke="#1D4ED8" stroke-width="6" stroke-linecap="round" stroke-dasharray="{{ (procent * 1.3195)|round(1) }} 132" transform="rotate(-90 26 26)"/>{% endif %}
          <text x="26" y="30" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#10213D">{{ procent }}%</text>
        </svg>
        <div><small>Voortgang vandaag</small><strong>{{ klaar }} van {{ totaal }}</strong></div>
      </div>
      <button class="knop" type="button" onclick="document.getElementById('nieuw').showModal()">Taak toevoegen</button>
    </div>
  </header>

  <section class="kaart" aria-label="Deze week" style="padding:12px 14px;gap:8px">
    <div class="kaartkop"><h2 style="font-size:14px">Deze week</h2><span style="font-size:12px;color:var(--grijs)">{{ week.titel }}</span></div>
    <div class="week">
      {% for d in week.dagen %}
      <div class="dag{% if d.vandaag %} vandaag{% endif %}"><small>{{ d.kop }}{% if d.verleden %}<span class="voorbij" role="img" aria-label="voorbij"><svg width="10" height="10" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5 L6.5 12 L13 4.5" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>{% endif %}</small><span>{{ d.label }}</span><div class="mini"><div style="width:{{ d.procent }}%"></div></div></div>
      {% endfor %}
    </div>
  </section>

  <div class="raster">
    <div class="kaarten">
      <div class="takenrij{% if kaarten|length > 4 %} vol{% endif %}" style="grid-template-columns:repeat({{ kaarten|length }},minmax(0,1fr))">{% for k in kaarten %}{{ takenkaart(k) }}{% endfor %}</div>

      <section class="kaart content nk">
        <div class="kaartkop"><h2>{{ icoon('Content') }}<span>Content deze week</span></h2></div>
        {% if content_taken or insta_taken %}<div class="takenlijst">{% for t in content_taken + insta_taken %}{{ taakregel(t) }}{% endfor %}</div>{% endif %}
        <div class="cweek">
          <div></div>
          {% for d in cw.dagen %}<div class="ckop{% if d.vandaag %} nu{% endif %}">{{ d.kop }} {{ d.dag }}</div>{% endfor %}
          <div class="klabel">LinkedIn</div>
          {% for c in cw.linkedin %}
          <div class="cel{% if c.klaar %} klaar{% endif %}">
            {% if c.aantal %}
            <form method="post" action="/content"><input type="hidden" name="kanaal" value="linkedin"><input type="hidden" name="datum" value="{{ c.iso }}"><input type="hidden" name="aan" value="{{ '0' if c.klaar else '1' }}">
              <button class="bol" type="submit" aria-pressed="{{ 'true' if c.klaar else 'false' }}" title="{% for p in c.posts %}{{ p.tijd }} {{ p.pijler }}{% if not loop.last %} · {% endif %}{% endfor %}">{% if c.klaar %}<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5 L6.5 12 L13 4.5" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>{% else %}{{ c.aantal }}{% endif %}</button></form>
            {% for p in c.posts %}<span class="post"><span class="tijd">{{ p.tijd }}</span> <span class="pijl" title="{{ p.pijler }}">{{ p.kort }}</span></span>{% endfor %}
            {% else %}<span class="bol leeg" aria-label="geen post">&ndash;</span><span class="aantal">geen post</span>{% endif %}
          </div>
          {% endfor %}
          <div class="klabel">Instagram</div>
          {% for c in cw.instagram %}
          <div class="cel{% if c.klaar %} klaar{% endif %}">
            {% if c.aantal %}
            <form method="post" action="/content"><input type="hidden" name="kanaal" value="instagram"><input type="hidden" name="datum" value="{{ c.iso }}"><input type="hidden" name="aan" value="{{ '0' if c.klaar else '1' }}">
              <button class="bol" type="submit" aria-pressed="{{ 'true' if c.klaar else 'false' }}">{% if c.klaar %}<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5 L6.5 12 L13 4.5" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>{% else %}{{ c.aantal }}{% endif %}</button></form>
            {% else %}<span class="bol leeg" aria-label="geen post">&ndash;</span>{% endif %}
            {% if c.klaar %}<span class="aantal">{{ c.aantal }} post{{ '' if c.aantal == 1 else 's' }}</span>
            {% else %}<form method="post" action="/content"><input type="hidden" name="kanaal" value="instagram"><input type="hidden" name="datum" value="{{ c.iso }}">
              <select class="aantal" name="aantal" aria-label="Aantal Instagram-posts op {{ c.iso }}" onchange="this.form.submit()">{% for n in range(0, 6) %}<option value="{{ n }}"{% if n == c.aantal %} selected{% endif %}>{{ n }} post{{ '' if n == 1 else 's' }}</option>{% endfor %}</select></form>{% endif %}
          </div>
          {% endfor %}
        </div>
      </section>

    </div>

    <div class="zijkant">
      <section class="kaart nk agenda">
        <div class="kaartkop"><h2>{{ icoon('Agenda') }}<span>Agenda</span></h2></div>
        {% for k in algemeen %}<div class="groep">Vandaag</div><div class="takenlijst">{% for t in k.taken %}{{ taakregel(t) }}{% endfor %}</div>{% endfor %}
        {% for g in agenda %}
        <div class="groep">{{ g.naam }}</div>
        <ul class="kal">{% for b in g.regels %}<li><span class="cal"><small>{{ b.wd }}</small><b>{{ b.dag }}</b></span><span>{{ b.titel }}</span></li>{% endfor %}</ul>
        {% else %}{% if not algemeen %}<p class="leeg">Niets gepland de komende twee weken.</p>{% endif %}{% endfor %}
      </section>

    </div>
  </div>
</main>
</div>

<dialog id="nieuw" aria-labelledby="nieuwtitel">
  <form method="post" action="/taak" class="binnenin">
    <h2 id="nieuwtitel">Taak toevoegen</h2>
    <label>Wat moet er gebeuren?<input name="titel" required placeholder="Bijvoorbeeld: Rolla Granola opvolgen"></label>
    <label>Bij welke chat?<select name="chat">{% for c in chats %}<option{% if c == 'Algemeen' %} selected{% endif %}>{{ c }}</option>{% endfor %}</select></label>
    <label>Wanneer?<input type="date" name="datum" value="{{ vandaag_iso }}"></label>
    <div class="knoppen">
      <button class="knop licht" type="button" onclick="this.closest('dialog').close()">Annuleren</button>
      <button class="knop" type="submit">Toevoegen</button>
    </div>
  </form>
</dialog>

<dialog id="geparkeerd" aria-labelledby="geparkeerdtitel">
  <div class="binnenin">
    <h2 id="geparkeerdtitel">Geparkeerd</h2>
    <table class="ritme"><tbody>{% for t in todo if t.label == 'Geparkeerd' %}<tr><td>{{ t.titel }}</td></tr>{% endfor %}</tbody></table>
    <div class="knoppen"><button class="knop" type="button" onclick="this.closest('dialog').close()">Sluiten</button></div>
  </div>
</dialog>

<dialog id="ritme" aria-labelledby="ritmetitel">
  <div class="binnenin">
    <h2 id="ritmetitel">Weekritme</h2>
    <p class="leeg">Deze taken komen vanzelf terug op de dagen hieronder. Iets aanpassen? Vraag het in de chat Algemeen.</p>
    <table class="ritme">
      <thead><tr><th>Taak</th><th>Chat</th><th>Wanneer</th></tr></thead>
      <tbody>
        {% for t in ritme_taken %}<tr><td>{{ t.titel }}</td><td>{{ t.chat }}</td><td>{{ t.ritme }}</td></tr>{% endfor %}
        {% for p in linkedin_ritme %}<tr><td>LinkedIn-post: {{ p.pijler }}</td><td>automatisch</td><td>{{ dagen_kort[p.dag] }} {{ p.tijd }}</td></tr>{% endfor %}
      </tbody>
    </table>
    <div class="knoppen"><button class="knop" type="button" onclick="this.closest('dialog').close()">Sluiten</button></div>
  </div>
</dialog>
</body>
</html>
"""


if __name__ == "__main__":
    poort = int(get_env("DAGCOCKPIT_PORT") or 5070)
    print(f"Dagcockpit draait op http://127.0.0.1:{poort}")
    app.run(host="127.0.0.1", port=poort, debug=False)
