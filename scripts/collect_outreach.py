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

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


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

        range_name = f"{sheet_tab}!A:N"
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


def update_sheet(bedrijfsnaam, kolom, waarde):
    """Update een specifieke cel in de sheet op basis van bedrijfsnaam."""
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    sheet_id = os.getenv("OUTREACH_SHEET_ID", "").strip()
    sheet_tab = os.getenv("OUTREACH_SHEET_TAB", "Blad1").strip()

    full_creds_path = Path(creds_path)
    if not full_creds_path.is_absolute():
        full_creds_path = WORKSPACE_ROOT / creds_path

    creds = Credentials.from_service_account_file(str(full_creds_path), scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)

    # Kolomnamen → kolomletter
    KOLOM_MAP = {
        "bedrijfsnaam": "A", "instagram handle": "B", "url": "C",
        "naam eigenaar": "D", "product / niche": "E", "platform": "F",
        "heeft popup?": "G", "geschat orderbedrag": "H", "bedrag voor dm2": "I",
        "status": "J", "datum dm 1": "K", "datum dm 2": "L", "datum dm 3": "M", "notities": "N"
    }

    kolom_letter = KOLOM_MAP.get(kolom.lower())
    if not kolom_letter:
        return f"Onbekende kolom: {kolom}"

    # Vind rijnummer van het bedrijf
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{sheet_tab}!A:A"
    ).execute()
    namen = [r[0] if r else "" for r in result.get("values", [])]
    try:
        rij = namen.index(bedrijfsnaam) + 1  # 1-indexed
    except ValueError:
        return f"Bedrijf niet gevonden: {bedrijfsnaam}"

    cel = f"{sheet_tab}!{kolom_letter}{rij}"
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=cel,
        valueInputOption="RAW",
        body={"values": [[waarde]]}
    ).execute()
    return f"Bijgewerkt: {bedrijfsnaam} → {kolom} = {waarde} (cel {cel})"


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outreach (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            instagram_handle TEXT,
            url TEXT,
            contactpersoon TEXT,
            niche TEXT,
            platform TEXT,
            heeft_popup TEXT,
            omzet_potentieel REAL,
            bedrag_dm2 TEXT,
            status TEXT,
            datum_dm1 TEXT,
            datum_dm2 TEXT,
            datum_dm3 TEXT,
            notities TEXT,
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

    for row in rows:
        naam = row.get("bedrijfsnaam", "").strip()
        if not naam:
            continue

        omzet_raw = row.get("geschat orderbedrag (€)", "").strip().replace("€", "").replace(",", ".")
        try:
            omzet = float(omzet_raw) if omzet_raw else None
        except ValueError:
            omzet = None

        conn.execute("""
            INSERT OR REPLACE INTO outreach
            (naam, instagram_handle, url, contactpersoon, niche, platform, heeft_popup,
             omzet_potentieel, bedrag_dm2, status, datum_dm1, datum_dm2, datum_dm3, notities, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            naam,
            row.get("instagram handle", ""),
            row.get("url", ""),
            row.get("naam eigenaar", ""),
            row.get("product / niche", ""),
            row.get("platform", ""),
            row.get("heeft popup?", ""),
            omzet,
            row.get("bedrag voor dm2 (extra/mnd)", ""),
            row.get("status", ""),
            row.get("datum dm 1", ""),
            row.get("datum dm 2 (+5 dagen)", ""),
            row.get("datum dm 3 (+11 dagen)", ""),
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
            print(f"  - {row.get('bedrijfsnaam', '?')} | {row.get('status', '?')} | {row.get('datum dm 1', '-')}")

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
