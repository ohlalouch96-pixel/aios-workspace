"""
DataOS — Outreach Tracker Collector

Leest de AIOS Outreach Tracker Google Sheet en slaat de data op in de database.
Houdt bij hoeveel prospects benaderd zijn, hoeveel hebben gereageerd en hoeveel deals gesloten zijn.

Vereiste .env variabelen:
    GOOGLE_SERVICE_ACCOUNT_JSON — pad naar credentials/google-service-account.json
    OUTREACH_SHEET_ID           — Google Sheet ID
    OUTREACH_SHEET_TAB          — Tabbladnaam (standaard: Blad1)

Tabellen: outreach
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except ImportError:
    raise ImportError("Ontbrekende packages — draai: pip install google-api-python-client google-auth")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def collect():
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    sheet_id = os.getenv("OUTREACH_SHEET_ID", "").strip()
    sheet_tab = os.getenv("OUTREACH_SHEET_TAB", "Blad1").strip()

    if not creds_path:
        return {"source": "outreach", "status": "skipped", "reason": "GOOGLE_SERVICE_ACCOUNT_JSON niet ingesteld"}
    if not sheet_id:
        return {"source": "outreach", "status": "skipped", "reason": "OUTREACH_SHEET_ID niet ingesteld"}

    full_creds_path = Path(creds_path)
    if not full_creds_path.is_absolute():
        full_creds_path = WORKSPACE_ROOT / creds_path
    if not full_creds_path.exists():
        return {"source": "outreach", "status": "skipped", "reason": f"Credentials bestand niet gevonden: {full_creds_path}"}

    try:
        creds = Credentials.from_service_account_file(str(full_creds_path), scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)

        range_name = f"{sheet_tab}!A:H"
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()

        values = result.get("values", [])
        if len(values) < 2:
            return {
                "source": "outreach",
                "status": "success",
                "data": {"rows": [], "headers": values[0] if values else []}
            }

        headers = [h.lower().strip() for h in values[0]]
        rows = []
        for row in values[1:]:
            # Vul ontbrekende kolommen aan met lege strings
            while len(row) < len(headers):
                row.append("")
            record = dict(zip(headers, row))
            # Sla lege rijen over
            if not any(record.values()):
                continue
            rows.append(record)

        return {
            "source": "outreach",
            "status": "success",
            "data": {"rows": rows, "headers": headers}
        }

    except Exception as e:
        return {"source": "outreach", "status": "error", "reason": str(e)}


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outreach (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT,
            naam TEXT NOT NULL,
            type TEXT,
            contactpersoon TEXT,
            kanaal TEXT,
            status TEXT,
            omzet_potentieel REAL,
            notities TEXT,
            collected_at TEXT,
            UNIQUE(naam, datum)
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    rows = result["data"].get("rows", [])
    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0

    for row in rows:
        naam = row.get("naam", "").strip()
        if not naam:
            continue

        omzet_raw = row.get("omzet_potentieel", "").strip().replace("€", "").replace(",", ".")
        try:
            omzet = float(omzet_raw) if omzet_raw else None
        except ValueError:
            omzet = None

        conn.execute("""
            INSERT OR REPLACE INTO outreach
            (datum, naam, type, contactpersoon, kanaal, status, omzet_potentieel, notities, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("datum", date),
            naam,
            row.get("type", ""),
            row.get("contactpersoon", ""),
            row.get("kanaal", ""),
            row.get("status", "benaderd"),
            omzet,
            row.get("notities", ""),
            collected_at
        ))
        records += 1

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        rows = result["data"].get("rows", [])
        print(f"Sheet gelezen: {len(rows)} rijen gevonden")
        for row in rows[:3]:
            print(f"  - {row.get('naam', '?')} | {row.get('status', '?')} | {row.get('type', '?')}")
    elif result["status"] == "skipped":
        print(f"Overgeslagen: {result.get('reason')}")
    else:
        print(f"Fout: {result.get('reason')}")
