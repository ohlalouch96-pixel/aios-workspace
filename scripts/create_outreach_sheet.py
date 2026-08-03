"""
Maakt een nieuwe Google Sheet aan voor de e-commerce DM outreach tracker.
Vult hem met alle kolommen en bekende prospects.
Deelt de sheet met ohlalouch96@gmail.com zodat je er direct bij kunt.

Gebruik:
    python scripts/create_outreach_sheet.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except ImportError:
    raise ImportError("Draai eerst: pip install google-api-python-client google-auth")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

USER_EMAIL = "ohlalouch96@gmail.com"

KOLOMMEN = [
    "Bedrijfsnaam",
    "Instagram handle",
    "URL",
    "Naam eigenaar",
    "Product / niche",
    "Platform",
    "Heeft popup?",
    "Geschat orderbedrag (€)",
    "Status",
    "Datum DM 1",
    "Datum volgende actie",
    "Notities",
]

STATUSSEN = [
    "Te versturen",
    "DM 1 verstuurd",
    "DM 2 verstuurd",
    "DM 3 verstuurd",
    "Reageert",
    "Call ingepland",
    "Klant",
    "Gesloten",
]

PROSPECTS = [
    ["Teddah.nl",           "@teddah.nl",            "https://www.teddah.nl",            "", "Supplementen / lifestyle", "Shopify",    "Ja",       "", "Te versturen", "", "", ""],
    ["Lichaam-in-balans.nl","",                       "https://lichaam-in-balans.nl",     "", "Gezondheid / supplementen","WooCommerce","Ja",       "", "Te versturen", "", "", ""],
    ["Dakistoresports.com", "@dakistoresports",       "https://dakistoresports.com",      "", "Sport",                    "Shopify",    "Ja",       "", "Te versturen", "", "", ""],
    ["Vitafit.nu",          "@vitafit_labs_",         "https://vitafit.nu",               "", "Supplementen",             "WooCommerce","Onbekend", "", "Te versturen", "", "", ""],
    ["MuscleMuse.nl",       "@musclemuse_official",   "https://musclemuse.nl",            "", "Sportkleding",             "Shopify",    "Ja",       "", "Te versturen", "", "", ""],
    ["JumboGym.nl",         "@jumbogym.nl",           "https://jumbogym.nl",              "", "Gymkleding",               "Shopify",    "Ja",       "", "Te versturen", "", "", ""],
    ["Peakout.shop",        "@peakout.shop",          "https://peakout.shop",             "", "Sport / fitness",          "WooCommerce","Onbekend", "", "Te versturen", "", "", ""],
    ["LifeGoesOn.nl",       "@lifegoesonfpp",         "https://lifegoeson.nl",            "", "Christelijke sportkleding","Shopify",    "Onbekend", "", "Te versturen", "", "", ""],
    ["Padellewear.nl",      "@padelle.wear",          "https://www.padellewear.nl",       "", "Padelkleding",             "JouwWeb",    "Nee",      "", "Te versturen", "", "", ""],
    ["GymEvo.nl",           "@gymevo_nl",             "https://gymevo.nl",                "", "Gymkleding",               "WooCommerce","Ja",       "", "Te versturen", "", "", ""],
    ["KluppSportswear.nl",  "@kluppsportswear",       "https://kluppsportswear.nl",       "", "Sportkleding",             "WooCommerce","Ja",       "", "Te versturen", "", "", ""],
    ["AthleticClarity.nl",  "@athleticclarity",       "https://www.athleticclarity.nl",   "", "Sport",                    "Shopify",    "Onbekend", "", "Te versturen", "", "", ""],
    ["Keanto.com",          "@keanto.official",       "https://keanto.com",               "", "Lifestyle (Amsterdam)",    "Shopify",    "Onbekend", "", "Te versturen", "", "", ""],
]


def main():
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not creds_path:
        print("FOUT: GOOGLE_SERVICE_ACCOUNT_JSON niet ingesteld in .env")
        return

    full_path = Path(creds_path)
    if not full_path.is_absolute():
        full_path = WORKSPACE_ROOT / creds_path
    if not full_path.exists():
        print(f"FOUT: Credentials bestand niet gevonden: {full_path}")
        return

    creds = Credentials.from_service_account_file(str(full_path), scopes=SCOPES)
    sheets = build("sheets", "v4", credentials=creds)
    drive  = build("drive",  "v3", credentials=creds)

    # Sheet aanmaken
    sheet_body = {
        "properties": {"title": "Outreach Tracker — E-commerce DM"},
        "sheets": [{"properties": {"title": "Prospects"}}],
    }
    spreadsheet = sheets.spreadsheets().create(body=sheet_body).execute()
    sheet_id  = spreadsheet["spreadsheetId"]
    tab_id    = spreadsheet["sheets"][0]["properties"]["sheetId"]
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    print(f"Sheet aangemaakt: {sheet_url}")

    # Kolomkoppen + prospects invullen
    rows = [KOLOMMEN] + PROSPECTS
    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Prospects!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    # Opmaak: koprij vetgedrukt + bevroren
    requests = [
        {
            "repeatCell": {
                "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        },
        {
            "updateSheetProperties": {
                "properties": {"sheetId": tab_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {"sheetId": tab_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": len(KOLOMMEN)}
            }
        },
    ]
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": requests}
    ).execute()

    # Delen met jouw Google account
    drive.permissions().create(
        fileId=sheet_id,
        body={"type": "user", "role": "writer", "emailAddress": USER_EMAIL},
        sendNotificationEmail=False,
    ).execute()
    print(f"Sheet gedeeld met {USER_EMAIL}")
    print(f"\nOpen je sheet hier:\n{sheet_url}")


if __name__ == "__main__":
    main()
