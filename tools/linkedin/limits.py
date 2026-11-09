"""
LinkedIn Outreach — Opbouwschema en daglimieten

Bewaakt het week-voor-week opbouwschema (connectieverzoeken/profielbezoeken/
zoekopdrachten per dag) en de noodstop-regels uit workflows/linkedin_outreach.md.
Alle acties van tools/linkedin/browser.py en apps/linkedin/cockpit.py lopen
hier eerst langs voordat ze worden uitgevoerd.

Belangrijk: de daglimiet-telling gebeurt via het lokale linkedin_daily_log
(deze module), NIET via de Google Sheet-sync (collect_linkedin.py) — die sync
loopt achter en zou toestaan dat het daglimiet binnen één sessie overschreden
wordt. browser.py en apps/linkedin/cockpit.py loggen daarom elke actie hier
meteen, los van wanneer de sheet voor het laatst gesynchroniseerd is.

Gebruik (CLI, vooral voor handmatig testen):
    python tools/linkedin/limits.py stand
    python tools/linkedin/limits.py check
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from db import get_connection  # noqa: E402

# ============================================================================
# Opbouwschema (zie plans/2026-11-09-linkedin-outreach-agent.md)
# ============================================================================
RAMP_SCHEDULE = [
    {"week": 1, "connections": 8, "profile_views": 25, "searches": 5},
    {"week": 2, "connections": 12, "profile_views": 35, "searches": 8},
    {"week": 3, "connections": 15, "profile_views": 45, "searches": 10},
    {"week": 4, "connections": 18, "profile_views": 50, "searches": 10},
    {"week": 5, "connections": 20, "profile_views": 60, "searches": 12},  # plateau: week 5 en hoger
]
GATE_MIN_ACCEPTATIERATIO = 0.30  # voorwaarde om door te schalen naar de volgende week
NOODSTOP_MIN_ACCEPTATIERATIO = 0.15  # onder dit niveau over de laatste N verzoeken: pauzeren
NOODSTOP_WINDOW = 20  # "laatste N verzonden connectieverzoeken"
NOODSTOP_MIN_SAMPLE = 10  # pas beoordelen vanaf dit aantal afgehandelde (geaccepteerd/verlopen) verzoeken

ACCEPTED_STATUSSEN = {"Geaccepteerd", "Bericht verstuurd", "Afgerond"}
RESOLVED_NEGATIEF_STATUSSEN = {"Verlopen", "Afgewezen"}


def _ensure_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS linkedin_daily_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_date TEXT NOT NULL,
            kind TEXT NOT NULL,
            ref TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS linkedin_system_status (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        );
    """)
    conn.commit()


def _today():
    return datetime.now().strftime("%Y-%m-%d")


# ============================================================================
# Loggen van acties (aangeroepen door browser.py en apps/linkedin/cockpit.py)
# ============================================================================
def log_action(conn, kind, ref=None, date=None):
    """kind: 'connection' | 'profile_view' | 'search'. ref: profiel-URL of zoekomschrijving."""
    _ensure_tables(conn)
    conn.execute(
        "INSERT INTO linkedin_daily_log (action_date, kind, ref, created_at) VALUES (?, ?, ?, ?)",
        (date or _today(), kind, ref, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def count_today(conn, kind, date=None):
    _ensure_tables(conn)
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM linkedin_daily_log WHERE kind = ? AND action_date = ?",
        (kind, date or _today()),
    ).fetchone()
    return row["n"] if row else 0


# ============================================================================
# Systeemstatus (restrictie-vlag, gezet door browser.py bij een waarschuwing)
# ============================================================================
def set_status(conn, key, value):
    _ensure_tables(conn)
    conn.execute(
        "INSERT INTO linkedin_system_status (key, value, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        (key, value, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def get_status(conn, key, default=None):
    _ensure_tables(conn)
    row = conn.execute("SELECT value FROM linkedin_system_status WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def clear_restriction(conn):
    """Handmatige bevestiging door Oussama na een restrictiemelding — vereist voor herstart."""
    set_status(conn, "restricted", "")
    set_status(conn, "restricted_reason", "")


# ============================================================================
# Opbouwschema: in welke week zitten we, en mag er doorgeschaald worden
# ============================================================================
def _week_start_date(conn):
    """Datum van het eerste ooit gelogde connectieverzoek. None = nog geen enkele verzonden."""
    _ensure_tables(conn)
    row = conn.execute(
        "SELECT MIN(action_date) AS d FROM linkedin_daily_log WHERE kind = 'connection'"
    ).fetchone()
    return row["d"] if row and row["d"] else None


def _acceptatieratio_voor_periode(conn, start_date, end_date):
    """Ratio geaccepteerd / (geaccepteerd + verlopen/afgewezen) van connectieverzoeken
    verzonden in [start_date, end_date]. None als er nog niets afgehandeld is."""
    if not _table_exists(conn, "linkedin"):
        return None
    refs = [r["ref"] for r in conn.execute(
        "SELECT ref FROM linkedin_daily_log WHERE kind = 'connection' AND action_date >= ? AND action_date <= ? AND ref IS NOT NULL",
        (start_date, end_date),
    ).fetchall()]
    if not refs:
        return None
    geaccepteerd, negatief = 0, 0
    for ref in refs:
        row = conn.execute("SELECT status FROM linkedin WHERE url = ?", (ref,)).fetchone()
        if not row:
            continue
        if row["status"] in ACCEPTED_STATUSSEN:
            geaccepteerd += 1
        elif row["status"] in RESOLVED_NEGATIEF_STATUSSEN:
            negatief += 1
    resolved = geaccepteerd + negatief
    return (geaccepteerd / resolved) if resolved else None


def _table_exists(conn, name):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def current_week_limits(conn):
    """Bepaalt de daglimieten die NU gelden. Schaalt alleen door naar de volgende
    week als de acceptatieratio van de voorgaande week >= GATE_MIN_ACCEPTATIERATIO was.
    Zonder eerder verzonden connectieverzoek: week 1 (startpunt)."""
    start = _week_start_date(conn)
    if start is None:
        limieten = dict(RAMP_SCHEDULE[0])
        limieten["effectieve_week"] = 1
        limieten["kalenderweek"] = 1
        return limieten

    start_dt = datetime.strptime(start, "%Y-%m-%d").date()
    vandaag = datetime.now().date()
    kalenderweek = min((vandaag - start_dt).days // 7 + 1, len(RAMP_SCHEDULE))

    effectieve_week = 1
    for w in range(2, kalenderweek + 1):
        vorige_start = start_dt.fromordinal(start_dt.toordinal() + (w - 2) * 7)
        vorige_eind = start_dt.fromordinal(vorige_start.toordinal() + 6)
        ratio = _acceptatieratio_voor_periode(conn, vorige_start.isoformat(), vorige_eind.isoformat())
        if ratio is not None and ratio >= GATE_MIN_ACCEPTATIERATIO:
            effectieve_week = w
        else:
            break  # blijft op het huidige niveau tot de voorwaarde gehaald is

    idx = min(effectieve_week, len(RAMP_SCHEDULE)) - 1
    limieten = dict(RAMP_SCHEDULE[idx])
    limieten["effectieve_week"] = effectieve_week
    limieten["kalenderweek"] = kalenderweek
    return limieten


def remaining_today(conn, kind):
    """kind: 'connections' | 'profile_views' | 'searches' (let op: meervoud, zoals in RAMP_SCHEDULE)."""
    limieten = current_week_limits(conn)
    log_kind = {"connections": "connection", "profile_views": "profile_view", "searches": "search"}[kind]
    gedaan = count_today(conn, log_kind)
    return max(0, limieten[kind] - gedaan)


# ============================================================================
# Noodstop
# ============================================================================
def check_noodstop(conn):
    """Geeft {"pauzeren": bool, "reden": str|None, "waarschuwing": str|None} terug."""
    restricted = get_status(conn, "restricted")
    if restricted:
        return {
            "pauzeren": True,
            "reden": f"LinkedIn-restrictiemelding gedetecteerd: {get_status(conn, 'restricted_reason') or 'onbekende reden'}. "
                     "Handmatig bevestigen vereist (limits.clear_restriction) voordat het systeem verder gaat.",
            "waarschuwing": None,
        }

    if not _table_exists(conn, "linkedin"):
        return {"pauzeren": False, "reden": None, "waarschuwing": None}

    laatste_refs = [r["ref"] for r in conn.execute(
        "SELECT ref FROM linkedin_daily_log WHERE kind = 'connection' AND ref IS NOT NULL "
        "ORDER BY id DESC LIMIT ?", (NOODSTOP_WINDOW,)
    ).fetchall()]
    geaccepteerd, negatief = 0, 0
    for ref in laatste_refs:
        row = conn.execute("SELECT status FROM linkedin WHERE url = ?", (ref,)).fetchone()
        if not row:
            continue
        if row["status"] in ACCEPTED_STATUSSEN:
            geaccepteerd += 1
        elif row["status"] in RESOLVED_NEGATIEF_STATUSSEN:
            negatief += 1
    resolved = geaccepteerd + negatief

    if resolved >= NOODSTOP_MIN_SAMPLE:
        ratio = geaccepteerd / resolved
        if ratio < NOODSTOP_MIN_ACCEPTATIERATIO:
            return {
                "pauzeren": True,
                "reden": f"Acceptatieratio over de laatste {resolved} afgehandelde connectieverzoeken is {ratio:.0%}, "
                         f"onder de noodstop-grens van {NOODSTOP_MIN_ACCEPTATIERATIO:.0%}. Nieuwe connectieverzoeken gepauzeerd.",
                "waarschuwing": None,
            }

    # Zwakke waarschuwing: twee opeenvolgende dagen zonder acceptaties deze week (geen harde pauze)
    vandaag = datetime.now().date()
    gisteren = vandaag.fromordinal(vandaag.toordinal() - 1)
    recent = [r["ref"] for r in conn.execute(
        "SELECT ref FROM linkedin_daily_log WHERE kind = 'connection' AND ref IS NOT NULL "
        "AND action_date IN (?, ?)", (vandaag.isoformat(), gisteren.isoformat())
    ).fetchall()]
    if recent:
        any_accepted = any(
            (conn.execute("SELECT status FROM linkedin WHERE url = ?", (r,)).fetchone() or {"status": ""})["status"] in ACCEPTED_STATUSSEN
            for r in recent
        )
        if not any_accepted:
            return {
                "pauzeren": False,
                "reden": None,
                "waarschuwing": "Geen acceptaties in de laatste 2 dagen — kan aan het account liggen, maar ook aan de doelgroep/boodschap. Even checken.",
            }

    return {"pauzeren": False, "reden": None, "waarschuwing": None}


def can_act(conn, kind):
    """Combineert noodstop + daglimiet. Geeft (toegestaan: bool, reden: str|None) terug."""
    noodstop = check_noodstop(conn)
    if noodstop["pauzeren"]:
        return False, noodstop["reden"]
    if kind == "connections" and remaining_today(conn, "connections") <= 0:
        return False, "Daglimiet voor connectieverzoeken is bereikt."
    if kind == "profile_views" and remaining_today(conn, "profile_views") <= 0:
        return False, "Daglimiet voor profielbezoeken is bereikt."
    if kind == "searches" and remaining_today(conn, "searches") <= 0:
        return False, "Daglimiet voor zoekopdrachten is bereikt."
    return True, None


# ============================================================================
# CLI
# ============================================================================
def main():
    conn = get_connection()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stand"

    if cmd == "stand":
        limieten = current_week_limits(conn)
        print(f"Effectieve week: {limieten['effectieve_week']} (kalenderweek {limieten.get('kalenderweek', 1)})")
        print(f"Connectieverzoeken: {count_today(conn, 'connection')}/{limieten['connections']} vandaag")
        print(f"Profielbezoeken:    {count_today(conn, 'profile_view')}/{limieten['profile_views']} vandaag")
        print(f"Zoekopdrachten:     {count_today(conn, 'search')}/{limieten['searches']} vandaag")
    elif cmd == "check":
        print(check_noodstop(conn))
    else:
        print("Gebruik: python tools/linkedin/limits.py [stand|check]")

    conn.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
