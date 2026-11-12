"""
LinkedIn Outreach — Wachtrij en statusbeheer (Google Sheet 'linkedin-tracker')

Schrijft gekwalificeerde kandidaten naar het linkedin-tracker-tabblad en werkt
statussen/datums bij na een knopdruk in apps/linkedin/cockpit.py. Naar het
patroon van tools/source_prospects.py (append + banding-fix), maar dan voor
losse rijen i.p.v. een bulk-import.

Gebruik (CLI, vooral voor handmatig testen):
    python tools/linkedin/wachtrij.py volgende 5
    python tools/linkedin/wachtrij.py due-follow-ups
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from config import get_env  # noqa: E402
from db import get_connection  # noqa: E402

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except ImportError:
    raise ImportError("Ontbrekende packages — draai: pip install google-api-python-client google-auth")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
KOLOMMEN = [
    "naam", "functie", "bedrijf", "locatie", "url", "status",
    "connectienotitie", "bericht1", "datum_verzoek", "datum_geaccepteerd",
    "datum_bericht1", "volgende_follow_up", "gereageerd", "notities",
    "bericht2", "datum_bericht2", "bericht3", "datum_bericht3",
]
FOLLOW_UP_DAGEN = 5  # eerste follow-up-due, zie workflows/linkedin_outreach.md (nog voorlopig)


def _sheet_tab():
    return get_env("LINKEDIN_SHEET_TAB") or "linkedin-tracker"


def _service():
    creds_path = get_env("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = get_env("OUTREACH_SHEET_ID")
    if not creds_path or not sheet_id:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON of OUTREACH_SHEET_ID ontbreekt in .env")
    full_creds_path = Path(creds_path)
    if not full_creds_path.is_absolute():
        full_creds_path = WORKSPACE_ROOT / creds_path
    creds = Credentials.from_service_account_file(str(full_creds_path), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds), sheet_id


def nieuw(kandidaat):
    """kandidaat: dict met (minstens) naam, functie, bedrijf, locatie, url, connectienotitie,
    bericht1, bericht2, bericht3. Optioneel status (default 'Te versturen'; vind_prospects.py
    gebruikt 'Twijfel' voor twijfelgevallen die nog Oussama's akkoord nodig hebben)."""
    service, sheet_id = _service()
    tab = _sheet_tab()

    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A:A").execute()
    start_row = len(result.get("values", [])) + 1

    row = [
        kandidaat.get("naam", ""), kandidaat.get("functie", ""), kandidaat.get("bedrijf", ""),
        kandidaat.get("locatie", ""), kandidaat.get("url", ""), kandidaat.get("status", "Te versturen"),
        kandidaat.get("connectienotitie", ""), kandidaat.get("bericht1", ""),
        "", "", "", "", "", kandidaat.get("notities", ""),
        kandidaat.get("bericht2", ""), "",
        kandidaat.get("bericht3", ""), "",
    ]
    end_row = start_row
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=f"{tab}!A{start_row}:R{end_row}",
        valueInputOption="RAW", body={"values": [row]},
    ).execute()
    return start_row


def _rij_vinden(service, sheet_id, tab, url):
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A:R").execute()
    values = result.get("values", [])
    for i, row in enumerate(values[1:], start=2):  # rij 1 = headers
        if len(row) > 4 and row[4] == url:
            return i, row
    return None, None


def status(url, nieuwe_status, datum=None):
    """Werkt de status (+ relevante datumkolom) bij voor de rij met dit profiel-URL."""
    service, sheet_id = _service()
    tab = _sheet_tab()
    rij_nr, _ = _rij_vinden(service, sheet_id, tab, url)
    if rij_nr is None:
        raise ValueError(f"Geen rij gevonden met url={url}")

    datum = datum or datetime.now().strftime("%Y-%m-%d")
    updates = [{"range": f"{tab}!F{rij_nr}", "values": [[nieuwe_status]]}]

    datumkolom = {
        "Verzoek verstuurd": "I", "Geaccepteerd": "J", "Bericht verstuurd": "K",
        "Bericht 2 verstuurd": "P", "Afgerond": "R",
    }.get(nieuwe_status)
    if datumkolom:
        updates.append({"range": f"{tab}!{datumkolom}{rij_nr}", "values": [[datum]]})

    if nieuwe_status in ("Bericht verstuurd", "Bericht 2 verstuurd"):
        follow_up_due = (datetime.now() + timedelta(days=FOLLOW_UP_DAGEN)).strftime("%Y-%m-%d")
        updates.append({"range": f"{tab}!L{rij_nr}", "values": [[follow_up_due]]})

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id, body={"valueInputOption": "RAW", "data": updates}
    ).execute()
    return rij_nr


def herschrijf_bericht(url, veld, tekst):
    """Overschrijft bericht1/bericht2/bericht3 van een bestaande rij (bv. na een
    sjabloonwijziging, zie tools/linkedin/berichten.py). Alleen zinvol zolang dat
    bericht nog niet verstuurd is."""
    kolom = {"bericht1": "H", "bericht2": "O", "bericht3": "Q"}[veld]
    service, sheet_id = _service()
    tab = _sheet_tab()
    rij_nr, _ = _rij_vinden(service, sheet_id, tab, url)
    if rij_nr is None:
        raise ValueError(f"Geen rij gevonden met url={url}")
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=f"{tab}!{kolom}{rij_nr}",
        valueInputOption="RAW", body={"values": [[tekst]]},
    ).execute()
    return rij_nr


def alle_records():
    """Haalt de hele sheet in ÉÉN keer op en geeft alle rijen als dicts terug
    (KOLOMMEN-gemapt). De cockpit roept dit precies 1x per paginaweergave aan
    en geeft het resultaat door aan de functies hieronder, in plaats van dat
    elke sectie zijn eigen losse Sheets-aanroep doet (dat was de reden dat
    een knopdruk traag aanvoelde — 4 losse live ophaalacties per klik)."""
    service, sheet_id = _service()
    tab = _sheet_tab()
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A:R").execute()
    values = result.get("values", [])
    records = []
    for row in values[1:]:
        while len(row) < len(KOLOMMEN):
            row.append("")
        records.append(dict(zip(KOLOMMEN, row)))
    return records


def volgende_batch(n, records=None):
    """Rijen met status 'Te versturen', beperkt tot n EN tot het resterende daglimiet.
    records: optioneel vooraf opgehaalde lijst (zie alle_records()) om een extra
    live Sheets-aanroep te vermijden; zonder opgave wordt zelf vers opgehaald."""
    import limits  # lokale import om circulaire afhankelijkheid bij CLI-gebruik te vermijden
    conn = get_connection()
    budget = limits.remaining_today(conn, "connections")
    conn.close()
    limiet = min(n, budget)
    if limiet <= 0:
        return []

    if records is None:
        records = alle_records()
    kandidaten = []
    for record in records:
        if record["status"] == "Te versturen":
            kandidaten.append(record)
        if len(kandidaten) >= limiet:
            break
    return kandidaten


def twijfelgevallen(records=None):
    """Rijen met status 'Twijfel': door vind_prospects.py (automatische zoekronde) als
    grensgeval gemarkeerd, berichten staan al klaar maar wachten op Oussama's akkoord
    (zie notities-kolom voor de reden) voordat ze naar 'Te versturen' gaan."""
    if records is None:
        records = alle_records()
    return [r for r in records if r["status"] == "Twijfel"]


def wachtend_op_acceptatie(records=None):
    """Rijen met status 'Verzoek verstuurd': connectieverzoek is weg, nog geen
    uitkomst. Bedoeld als zuiver informatieve sectie (browser.py check werkt
    dit automatisch bij; de cockpit biedt ook een handmatige override)."""
    if records is None:
        records = alle_records()
    return [r for r in records if r["status"] == "Verzoek verstuurd"]


def geaccepteerd_wachtend(records=None):
    """Rijen met status 'Geaccepteerd': connectieverzoek is geaccepteerd (via
    browser.py check), bericht 1 kan nu verstuurd worden."""
    if records is None:
        records = alle_records()
    return [r for r in records if r["status"] == "Geaccepteerd"]


# Status waaruit een follow-up kan volgen -> welk bericht er dan klaarstaat.
FOLLOW_UP_STADIA = {
    "Bericht verstuurd": "bericht2",
    "Bericht 2 verstuurd": "bericht3",
}


def onderweg(records=None):
    """Rijen met status 'Bericht verstuurd' of 'Bericht 2 verstuurd' waarvan de
    follow-up nog NIET due is: puur zichtbaarheid in de cockpit, zodat iemand
    niet 'verdwijnt' uit het dashboard tussen het versturen van een bericht en
    de volgende follow-up-datum (besluit Oussama 10-11, zie due_follow_ups()
    voor de rijen die al wel due zijn)."""
    if records is None:
        records = alle_records()
    vandaag = datetime.now().strftime("%Y-%m-%d")
    resultaat = []
    for record in records:
        if record["status"] not in FOLLOW_UP_STADIA:
            continue
        due = record["volgende_follow_up"] and record["volgende_follow_up"] <= vandaag
        if not due:
            resultaat.append(record)
    return resultaat


def due_follow_ups(records=None):
    """Rijen waarvan volgende_follow_up vandaag of eerder is, met 'volgende_actie'
    erbij (bericht2 of bericht3) zodat de cockpit weet welk bericht te tonen."""
    if records is None:
        records = alle_records()
    vandaag = datetime.now().strftime("%Y-%m-%d")
    due = []
    for record in records:
        volgende_actie = FOLLOW_UP_STADIA.get(record["status"])
        if volgende_actie and record["volgende_follow_up"] and record["volgende_follow_up"] <= vandaag:
            due.append({**record, "volgende_actie": volgende_actie})
    return due


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("volgende")
    v.add_argument("n", type=int, default=5, nargs="?")
    sub.add_parser("due-follow-ups")
    sub.add_parser("geaccepteerd")
    sub.add_parser("wachtend")
    sub.add_parser("onderweg")
    sub.add_parser("twijfel")
    args = ap.parse_args()

    if args.cmd == "volgende":
        print(json.dumps(volgende_batch(args.n), ensure_ascii=False, indent=2))
    elif args.cmd == "due-follow-ups":
        print(json.dumps(due_follow_ups(), ensure_ascii=False, indent=2))
    elif args.cmd == "geaccepteerd":
        print(json.dumps(geaccepteerd_wachtend(), ensure_ascii=False, indent=2))
    elif args.cmd == "wachtend":
        print(json.dumps(wachtend_op_acceptatie(), ensure_ascii=False, indent=2))
    elif args.cmd == "onderweg":
        print(json.dumps(onderweg(), ensure_ascii=False, indent=2))
    elif args.cmd == "twijfel":
        print(json.dumps(twijfelgevallen(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
