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


def section_outreach(conn):
    """Outreach-tracker — kappers en andere prospects."""
    if not table_exists(conn, "outreach"):
        return []
    lines = ["## Outreach Status"]
    row = query_one(conn, "SELECT * FROM outreach ORDER BY date DESC LIMIT 1")
    totals = query_one(conn, """
        SELECT
            COUNT(*) as totaal,
            SUM(CASE WHEN status = 'benaderd' THEN 1 ELSE 0 END) as benaderd,
            SUM(CASE WHEN status = 'gereageerd' THEN 1 ELSE 0 END) as gereageerd,
            SUM(CASE WHEN status = 'deal' THEN 1 ELSE 0 END) as deals,
            SUM(CASE WHEN status = 'afgewezen' THEN 1 ELSE 0 END) as afgewezen
        FROM outreach
    """)
    if totals:
        lines.append("| Metric | Waarde |")
        lines.append("|--------|--------|")
        lines.append(f"| Totaal benaderd | {totals['totaal'] or 0} |")
        lines.append(f"| Gereageerd | {totals['gereageerd'] or 0} |")
        lines.append(f"| Deals gesloten | {totals['deals'] or 0} |")
        lines.append(f"| Afgewezen | {totals['afgewezen'] or 0} |")
        if totals['totaal'] and totals['totaal'] > 0:
            conv = (totals['deals'] or 0) / totals['totaal'] * 100
            lines.append(f"| Conversieratio | {conv:.1f}% |")
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
