"""
DataOS — Key Metrics Generator

Leest de database en genereert een leesbaar key-metrics.md bestand.
Dit bestand wordt geladen door /prime zodat je AI altijd actuele data heeft.

Gebruik:
    python scripts/generate_metrics.py
"""

import sqlite3
from datetime import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"
OUTPUT_PATH = WORKSPACE_ROOT / "context" / "key-metrics.md"


def fmt_number(value, prefix="", suffix=""):
    if value is None:
        return "Geen data"
    if isinstance(value, float):
        return f"{prefix}{value:,.0f}{suffix}"
    return f"{prefix}{value:,}{suffix}"


def fmt_currency(value, symbol="€"):
    if value is None:
        return "Geen data"
    return f"{symbol}{value:,.0f}"


def fmt_pct(value):
    if value is None:
        return "Geen data"
    return f"{value:.1f}%"


def query_one(conn, sql):
    try:
        row = conn.execute(sql).fetchone()
        return dict(row) if row else None
    except Exception:
        return None


def query_all(conn, sql):
    try:
        return [dict(r) for r in conn.execute(sql).fetchall()]
    except Exception:
        return []


def table_exists(conn, name):
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r is not None


# Reactie-uitkomsten staan als vrije tekst in de kolom "Gereageerd?", bv.
# "Ja - positief", "Ja, afgewezen (heeft al flow)". Alleen exact "Ja" tellen mist
# het grootste deel, dus classificeren op trefwoorden. Negatief eerst checken,
# anders telt "geen interesse" als positief.
NEGATIEF = ("afgewezen", "geen interesse", "nee", "al een flow", "al flow", "niet nodig", "uitschrijven")
WARM = ("positief", "voorbeeld", "bekijkt", "doorgestuurd", "interesse")


def classify_reply(gereageerd, status=""):
    """Geeft None (geen reactie), 'afgewezen', 'warm' of 'onbekend' terug."""
    g = (gereageerd or "").strip().lower()
    if status == "Afgewezen":
        return "afgewezen"
    if not g.startswith("ja"):
        return None
    if any(k in g for k in NEGATIEF):
        return "afgewezen"
    if any(k in g for k in WARM):
        return "warm"
    return "onbekend"


def parse_date(value):
    """Webshop-tracker gebruikt dd-mm-jjjj, ondernemers-tracker jjjj-mm-dd."""
    v = (value or "").strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def sent(value, today):
    """Een datum telt als verstuurd als hij vandaag of eerder is; latere datums zijn gepland."""
    d = parse_date(value)
    return d is not None and d <= today


def track_stats(rows, today):
    """rows: dicts met naam, status, d1, d2, gereageerd."""
    stats = {"totaal": len(rows), "te_versturen": 0, "benaderd": 0, "bericht2": 0,
             "afgerond": 0, "onbereikbaar": 0, "reacties": 0, "afgewezen": 0,
             "onbekend": 0, "warm": [], "vandaag": 0}
    for r in rows:
        status = r["status"]
        if status == "Te versturen":
            stats["te_versturen"] += 1
            continue
        stats["benaderd"] += 1
        if sent(r["d2"], today):
            stats["bericht2"] += 1
        if parse_date(r["d1"]) == today:
            stats["vandaag"] += 1
        if status == "Afgerond":
            stats["afgerond"] += 1
        if status == "Onbereikbaar":
            stats["onbereikbaar"] += 1
        uitkomst = classify_reply(r["gereageerd"], status)
        if uitkomst:
            stats["reacties"] += 1
            if uitkomst == "warm":
                stats["warm"].append(f"{r['naam']} ({r['gereageerd'].strip()})")
            else:
                stats[uitkomst] += 1
    return stats


def rate(part, whole):
    return f"{part / whole * 100:.1f}%" if whole else "—"


def section_outreach(conn):
    """Outreach — webshops (outreach-tabel) en ondernemers/vakbedrijven (ondernemers-tabel).

    Status is een pipeline-stage (waar een prospect NU staat), geen log. Daarom:
    benaderd = alles behalve 'Te versturen'; bericht 2 = datum ingevuld en niet in
    de toekomst (de webshop-e-mailreeks heeft eigen statussen als 'Email 2 verstuurd').
    Bij ondernemers telt een afwijzing aan de telefoon (status 'Afgewezen', geen
    'Ja' in Gereageerd?) ook als reactie.
    """
    today = datetime.now().date()
    tracks = []
    if table_exists(conn, "outreach"):
        rows = query_all(conn, "SELECT naam, status, datum_dm1 AS d1, datum_dm2 AS d2, gereageerd FROM outreach")
        tracks.append(("Webshops", "DM1/mail 1", "DM2/mail 2", track_stats(rows, today)))
    if table_exists(conn, "ondernemers"):
        rows = query_all(conn, "SELECT naam, status, datum_bericht1 AS d1, datum_bericht2 AS d2, gereageerd FROM ondernemers")
        tracks.append(("Ondernemers (vakbedrijven)", "bericht 1 of gebeld", "bericht 2", track_stats(rows, today)))
    if not tracks:
        return []

    lines = []
    for titel, b1, b2, st in tracks:
        lines.append(f"## Outreach: {titel}")
        lines.append("| Metric | Waarde |")
        lines.append("|--------|--------|")
        lines.append(f"| Totaal prospects | {st['totaal']} |")
        lines.append(f"| Nog te benaderen | {st['te_versturen']} |")
        lines.append(f"| Benaderd ({b1}, cumulatief) | {st['benaderd']} |")
        lines.append(f"| Vandaag voor het eerst benaderd | {st['vandaag']} |")
        lines.append(f"| {b2[0].upper() + b2[1:]} ontvangen (cumulatief) | {st['bericht2']} |")
        lines.append(f"| Volledige reeks doorlopen (Afgerond) | {st['afgerond']} |")
        if st["onbereikbaar"]:
            lines.append(f"| Onbereikbaar (bounce) | {st['onbereikbaar']} |")
        lines.append(f"| Reacties (alle uitkomsten) | {st['reacties']} |")
        lines.append(f"| Reactieratio (van benaderd) | {rate(st['reacties'], st['benaderd'])} |")
        lines.append(f"| Afgewezen | {st['afgewezen']} |")
        lines.append(f"| Warme leads | {len(st['warm'])} |")
        lines.append(f"| Reactie zonder vastgelegde uitkomst | {st['onbekend']} |")
        lines.append("")
        if st["warm"]:
            lines.append("**Warme leads:** " + "; ".join(st["warm"]))
            lines.append("")

    if len(tracks) > 1:
        lines.append("## Outreach: Totaal")
        lines.append("| Metric | Waarde |")
        lines.append("|--------|--------|")
        for key, label in [("totaal", "Totaal prospects"), ("benaderd", "Benaderd"),
                           ("te_versturen", "Nog te benaderen"), ("reacties", "Reacties"),
                           ("afgewezen", "Afgewezen")]:
            lines.append(f"| {label} | {sum(t[3][key] for t in tracks)} |")
        lines.append(f"| Warme leads | {sum(len(t[3]['warm']) for t in tracks)} |")
        lines.append("")
    return lines


def section_fx_rates(conn):
    """Wisselkoersen — gratis test-collector."""
    if not table_exists(conn, "fx_rates"):
        return []
    lines = ["## Wisselkoersen (EUR basis)"]
    lines.append("| Valuta | Koers | Datum |")
    lines.append("|--------|-------|-------|")
    rows = query_all(conn, """
        SELECT date, currency, rate FROM fx_rates
        WHERE date = (SELECT MAX(date) FROM fx_rates)
        ORDER BY currency
    """)
    for r in rows:
        lines.append(f"| {r['currency']} | {r['rate']:.4f} | {r['date']} |")
    lines.append("")
    return lines


# Voeg hier toekomstige sectie-functies toe:
# def section_stripe(conn): ...
# def section_youtube(conn): ...
# def section_google_analytics(conn): ...

SECTIONS = [
    section_outreach,
    section_fx_rates,
]


def generate(conn):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# Key Metrics",
        "",
        f"> Auto-gegenereerd vanuit database. Laatste update: {today}",
        f"> Bron: `data/data.db` | Vernieuwen: `python scripts/generate_metrics.py`",
        "",
    ]

    for section_fn in SECTIONS:
        try:
            section_lines = section_fn(conn)
            if section_lines:
                lines.extend(section_lines)
        except Exception as e:
            lines.append(f"<!-- Fout in {section_fn.__name__}: {e} -->")
            lines.append("")

    lines.append("## Data Versheid")
    lines.append("| Bron | Laatste Record | Status |")
    lines.append("|------|----------------|--------|")

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name != 'collection_log' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()

    for t in tables:
        name = t["name"]
        latest = None
        for date_col in ["date", "datum", "created_at", "collected_at"]:
            try:
                row = conn.execute(f"SELECT MAX({date_col}) as d FROM {name}").fetchone()
                if row and row["d"]:
                    latest = str(row["d"])[:10]
                    break
            except Exception:
                continue
        if latest:
            lines.append(f"| {name} | {latest} | Verbonden |")
        else:
            lines.append(f"| {name} | — | Leeg |")

    lines.append("")
    return "\n".join(lines)


def main():
    if not DB_PATH.exists():
        print(f"Database niet gevonden: {DB_PATH}")
        print("Draai eerst: python scripts/collect.py")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    content = generate(conn)
    conn.close()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Key metrics geschreven naar: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
