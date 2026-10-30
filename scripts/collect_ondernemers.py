"""
DataOS — Ondernemers Tracker Collector

Leest het tabblad "ondernemers-tracker" (vakbedrijven: installateurs, loodgieters,
hoveniers e.d.) uit dezelfde Google Sheet als de webshop-tracker en slaat de data
op in de database. Alleen-lezen: deze collector schrijft nooit naar de sheet.

Vereiste .env variabelen:
    GOOGLE_SERVICE_ACCOUNT_JSON — pad naar credentials/google-service-account.json
    OUTREACH_SHEET_ID           — Google Sheet ID
    (tabblad is hardcoded op "ondernemers-tracker", net als in tools/source_ondernemers.py)

Tabellen: ondernemers
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
SHEET_TAB = "ondernemers-tracker"


def collect():
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    sheet_id = os.getenv("OUTREACH_SHEET_ID", "").strip()

    if not creds_path:
        return {"source": "ondernemers", "status": "skipped", "reason": "GOOGLE_SERVICE_ACCOUNT_JSON niet ingesteld"}
    if not sheet_id:
        return {"source": "ondernemers", "status": "skipped", "reason": "OUTREACH_SHEET_ID niet ingesteld"}

    full_creds_path = Path(creds_path)
    if not full_creds_path.is_absolute():
        full_creds_path = WORKSPACE_ROOT / creds_path
    if not full_creds_path.exists():
        return {"source": "ondernemers", "status": "skipped", "reason": f"Credentials bestand niet gevonden: {full_creds_path}"}

    try:
        creds = Credentials.from_service_account_file(str(full_creds_path), scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{SHEET_TAB}!A:J"
        ).execute()

        values = result.get("values", [])
        if len(values) < 2:
            return {
                "source": "ondernemers",
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
            if not any(v.strip() for v in record.values()):
                continue
            rows.append(record)

        return {
            "source": "ondernemers",
            "status": "success",
            "data": {"rows": rows, "headers": headers}
        }

    except Exception as e:
        return {"source": "ondernemers", "status": "error", "reason": str(e)}


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ondernemers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            kanaal_contact TEXT,
            url TEXT,
            branche TEXT,
            status TEXT,
            datum_bericht1 TEXT,
            datum_bericht2 TEXT,
            datum_bericht3 TEXT,
            notities TEXT,
            gereageerd TEXT,
            collected_at TEXT,
            UNIQUE(naam)
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    rows = result["data"].get("rows", [])
    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0
    namen_in_sheet = []

    for row in rows:
        naam = row.get("bedrijfsnaam", "").strip()
        if not naam:
            continue
        namen_in_sheet.append(naam)

        conn.execute("""
            INSERT OR REPLACE INTO ondernemers
            (naam, kanaal_contact, url, branche, status, datum_bericht1, datum_bericht2, datum_bericht3, notities, gereageerd, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            naam,
            row.get("kanaal + contact", ""),
            row.get("url", ""),
            row.get("branche / pijnpunt", ""),
            row.get("status", ""),
            row.get("datum bericht 1", ""),
            row.get("datum bericht 2 (+5 dagen)", ""),
            row.get("datum bericht 3 (+11 dagen)", ""),
            row.get("notities", ""),
            row.get("gereageerd?", ""),
            collected_at
        ))
        records += 1

    # Verwijder prospects die niet meer in de sheet staan (voorkomt spook-rijen)
    if namen_in_sheet:
        placeholders = ",".join("?" for _ in namen_in_sheet)
        conn.execute(f"DELETE FROM ondernemers WHERE naam NOT IN ({placeholders})", namen_in_sheet)

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        rows = result["data"].get("rows", [])
        print(f"Sheet gelezen: {len(rows)} rijen gevonden")
        db_path = WORKSPACE_ROOT / "data" / "data.db"
        conn = sqlite3.connect(str(db_path))
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        written = write(conn, result, today)
        conn.close()
        print(f"{written} prospects opgeslagen in database")
    elif result["status"] == "skipped":
        print(f"Overgeslagen: {result.get('reason')}")
    else:
        print(f"Fout: {result.get('reason')}")
