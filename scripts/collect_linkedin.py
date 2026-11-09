"""
DataOS — LinkedIn Outreach Collector

Leest het tabblad "linkedin-tracker" uit dezelfde Google Sheet als de webshop-
en ondernemers-trackers en slaat de data op in de database. Alleen-lezend:
deze collector schrijft nooit naar de sheet (dat doet tools/linkedin/wachtrij.py).

Vereiste .env variabelen:
    GOOGLE_SERVICE_ACCOUNT_JSON — pad naar credentials/google-service-account.json
    OUTREACH_SHEET_ID           — Google Sheet ID
    LINKEDIN_SHEET_TAB          — Tabbladnaam (standaard: linkedin-tracker)

Tabellen: linkedin
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


def _sheet_tab():
    return os.getenv("LINKEDIN_SHEET_TAB", "linkedin-tracker").strip() or "linkedin-tracker"


def collect():
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    sheet_id = os.getenv("OUTREACH_SHEET_ID", "").strip()
    sheet_tab = _sheet_tab()

    if not creds_path:
        return {"source": "linkedin", "status": "skipped", "reason": "GOOGLE_SERVICE_ACCOUNT_JSON niet ingesteld"}
    if not sheet_id:
        return {"source": "linkedin", "status": "skipped", "reason": "OUTREACH_SHEET_ID niet ingesteld"}

    full_creds_path = Path(creds_path)
    if not full_creds_path.is_absolute():
        full_creds_path = WORKSPACE_ROOT / creds_path
    if not full_creds_path.exists():
        return {"source": "linkedin", "status": "skipped", "reason": f"Credentials bestand niet gevonden: {full_creds_path}"}

    try:
        creds = Credentials.from_service_account_file(str(full_creds_path), scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_tab}!A:R"
        ).execute()

        values = result.get("values", [])
        if len(values) < 2:
            return {
                "source": "linkedin",
                "status": "success",
                "data": {"rows": [], "headers": values[0] if values else []}
            }

        headers = [h.lower().strip() for h in values[0]]
        rows = []
        for row in values[1:]:
            while len(row) < len(headers):
                row.append("")
            record = dict(zip(headers, row))
            if not any(v.strip() for v in record.values()):
                continue
            rows.append(record)

        return {
            "source": "linkedin",
            "status": "success",
            "data": {"rows": rows, "headers": headers}
        }

    except Exception as e:
        return {"source": "linkedin", "status": "error", "reason": str(e)}


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS linkedin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            functie TEXT,
            bedrijf TEXT,
            locatie TEXT,
            url TEXT,
            status TEXT,
            connectienotitie TEXT,
            bericht1 TEXT,
            datum_verzoek TEXT,
            datum_geaccepteerd TEXT,
            datum_bericht1 TEXT,
            volgende_follow_up TEXT,
            gereageerd TEXT,
            notities TEXT,
            collected_at TEXT,
            UNIQUE(naam)
        )
    """)
    kolommen = {r[1] for r in conn.execute("PRAGMA table_info(linkedin)")}
    for nieuwe_kolom in ("bericht2", "datum_bericht2", "bericht3", "datum_bericht3"):
        if nieuwe_kolom not in kolommen:
            conn.execute(f"ALTER TABLE linkedin ADD COLUMN {nieuwe_kolom} TEXT")

    if result.get("status") != "success":
        conn.commit()
        return 0

    rows = result["data"].get("rows", [])
    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0
    namen_in_sheet = []

    for row in rows:
        naam = row.get("naam", "").strip()
        if not naam:
            continue
        namen_in_sheet.append(naam)

        conn.execute("""
            INSERT OR REPLACE INTO linkedin
            (naam, functie, bedrijf, locatie, url, status, connectienotitie, bericht1,
             datum_verzoek, datum_geaccepteerd, datum_bericht1, volgende_follow_up, gereageerd, notities, collected_at,
             bericht2, datum_bericht2, bericht3, datum_bericht3)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            naam,
            row.get("functie", ""),
            row.get("bedrijf", ""),
            row.get("locatie", ""),
            row.get("profiel-url", "") or row.get("url", ""),
            row.get("status", ""),
            row.get("connectienotitie", ""),
            row.get("bericht 1", "") or row.get("bericht1", ""),
            row.get("datum verzoek verstuurd", "") or row.get("datum_verzoek", ""),
            row.get("datum geaccepteerd", "") or row.get("datum_geaccepteerd", ""),
            row.get("datum bericht 1 verstuurd", "") or row.get("datum_bericht1", ""),
            row.get("volgende follow-up (due)", "") or row.get("volgende_follow_up", ""),
            row.get("gereageerd?", "") or row.get("gereageerd", ""),
            row.get("notities", ""),
            collected_at,
            row.get("bericht 2", "") or row.get("bericht2", ""),
            row.get("datum bericht 2 verstuurd", "") or row.get("datum_bericht2", ""),
            row.get("bericht 3", "") or row.get("bericht3", ""),
            row.get("datum bericht 3 verstuurd", "") or row.get("datum_bericht3", ""),
        ))
        records += 1

    if namen_in_sheet:
        placeholders = ",".join("?" for _ in namen_in_sheet)
        conn.execute(f"DELETE FROM linkedin WHERE naam NOT IN ({placeholders})", namen_in_sheet)

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
