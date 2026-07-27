"""
Outreach Tracker — Bulk Prospect Append

Voegt nieuwe prospects toe aan de Google Sheet outreach-tracker tab.
Dedupliceert automatisch tegen bedrijven die al in de sheet staan.

Gebruik:
    python scripts/append_outreach_prospects.py pad/naar/prospects1.csv pad/naar/prospects2.csv

Input-CSV kolommen (in deze volgorde):
    Bedrijfsnaam, Instagram handle, URL, Naam eigenaar, Product/niche,
    Platform, Heeft popup?, Geschat orderbedrag (€), Notities

Vereiste .env variabelen: GOOGLE_SERVICE_ACCOUNT_JSON, OUTREACH_SHEET_ID, OUTREACH_SHEET_TAB
"""

import csv
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
import os

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_service():
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    full_creds_path = Path(creds_path)
    if not full_creds_path.is_absolute():
        full_creds_path = WORKSPACE_ROOT / creds_path
    creds = Credentials.from_service_account_file(str(full_creds_path), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def normalize_orderbedrag(raw):
    """Zet '€45-60' / '€149 voor complete set' / 'Onbekend' om naar een enkel getal (midpoint)."""
    if not raw:
        return ""
    raw = raw.strip()
    numbers = [float(n) for n in re.findall(r"\d+(?:[.,]\d+)?", raw.replace(",", "."))]
    if not numbers:
        return ""
    if len(numbers) == 1:
        return str(round(numbers[0]))
    return str(round((numbers[0] + numbers[1]) / 2))


def dedupe_key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def load_existing_names(service, sheet_id, sheet_tab):
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{sheet_tab}!A:A"
    ).execute()
    names = [r[0] for r in result.get("values", []) if r]
    return {dedupe_key(n) for n in names}


def main(csv_paths):
    sheet_id = os.getenv("OUTREACH_SHEET_ID", "").strip()
    sheet_tab = os.getenv("OUTREACH_SHEET_TAB", "Blad1").strip()

    service = get_service()
    existing_keys = load_existing_names(service, sheet_id, sheet_tab)
    seen_keys = set(existing_keys)

    new_rows = []
    skipped = []

    for csv_path in csv_paths:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                naam = (row.get("Bedrijfsnaam") or "").strip()
                if not naam:
                    continue
                key = dedupe_key(naam)
                if key in seen_keys:
                    skipped.append(naam)
                    continue
                seen_keys.add(key)

                new_rows.append([
                    naam,
                    (row.get("Instagram handle") or "").strip(),
                    (row.get("URL") or "").strip(),
                    (row.get("Naam eigenaar") or "").strip(),
                    (row.get("Product/niche") or "").strip(),
                    (row.get("Platform") or "").strip(),
                    (row.get("Heeft popup?") or "").strip(),
                    normalize_orderbedrag(row.get("Geschat orderbedrag (€)") or ""),
                    "",  # Bedrag voor DM2 (extra/mnd)
                    "Te versturen",  # Status
                    "", "", "",  # Datum DM 1/2/3
                    (row.get("Notities") or "").strip(),
                ])

    if not new_rows:
        print("Geen nieuwe rijen om toe te voegen (alles was al duplicate).")
        return

    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{sheet_tab}!A:N",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": new_rows},
    ).execute()

    print(f"{len(new_rows)} nieuwe prospects toegevoegd aan de sheet.")
    if skipped:
        print(f"{len(skipped)} rijen overgeslagen als duplicate: {', '.join(skipped)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Gebruik: python scripts/append_outreach_prospects.py <csv1> [csv2 ...]")
        sys.exit(1)
    main(sys.argv[1:])
