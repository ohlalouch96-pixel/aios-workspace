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
    """kandidaat: dict met (minstens) naam, functie, bedrijf, locatie, url, connectienotitie, bericht1, bericht2, bericht3."""
    service, sheet_id = _service()
    tab = _sheet_tab()

    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A:A").execute()
    start_row = len(result.get("values", [])) + 1

    row = [
        kandidaat.get("naam", ""), kandidaat.get("functie", ""), kandidaat.get("bedrijf", ""),
        kandidaat.get("locatie", ""), kandidaat.get("url", ""), "Te versturen",
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


def volgende_batch(n):
    """Rijen met status 'Te versturen', beperkt tot n EN tot het resterende daglimiet."""
    import limits  # lokale import om circulaire afhankelijkheid bij CLI-gebruik te vermijden
    conn = get_connection()
    budget = limits.remaining_today(conn, "connections")
    conn.close()
    limiet = min(n, budget)
    if limiet <= 0:
        return []

    service, sheet_id = _service()
    tab = _sheet_tab()
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A:R").execute()
    values = result.get("values", [])
    kandidaten = []
    for row in values[1:]:
        while len(row) < len(KOLOMMEN):
            row.append("")
        record = dict(zip(KOLOMMEN, row))
        if record["status"] == "Te versturen":
            kandidaten.append(record)
        if len(kandidaten) >= limiet:
            break
    return kandidaten


def wachtend_op_acceptatie():
    """Rijen met status 'Verzoek verstuurd': connectieverzoek is weg, nog geen
    uitkomst. Bedoeld als zuiver informatieve sectie (browser.py check werkt
    dit automatisch bij; de cockpit biedt ook een handmatige override)."""
    service, sheet_id = _service()
    tab = _sheet_tab()
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A:R").execute()
    values = result.get("values", [])
    wachtend = []
    for row in values[1:]:
        while len(row) < len(KOLOMMEN):
            row.append("")
        record = dict(zip(KOLOMMEN, row))
        if record["status"] == "Verzoek verstuurd":
            wachtend.append(record)
    return wachtend


def geaccepteerd_wachtend():
    """Rijen met status 'Geaccepteerd': connectieverzoek is geaccepteerd (via
    browser.py check), bericht 1 kan nu verstuurd worden."""
    service, sheet_id = _service()
    tab = _sheet_tab()
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A:R").execute()
    values = result.get("values", [])
    wachtend = []
    for row in values[1:]:
        while len(row) < len(KOLOMMEN):
            row.append("")
        record = dict(zip(KOLOMMEN, row))
        if record["status"] == "Geaccepteerd":
            wachtend.append(record)
    return wachtend


# Status waaruit een follow-up kan volgen -> welk bericht er dan klaarstaat.
FOLLOW_UP_STADIA = {
    "Bericht verstuurd": "bericht2",
    "Bericht 2 verstuurd": "bericht3",
}


def due_follow_ups():
    """Rijen waarvan volgende_follow_up vandaag of eerder is, met 'volgende_actie'
    erbij (bericht2 of bericht3) zodat de cockpit weet welk bericht te tonen."""
    service, sheet_id = _service()
    tab = _sheet_tab()
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{tab}!A:R").execute()
    values = result.get("values", [])
    vandaag = datetime.now().strftime("%Y-%m-%d")
    due = []
    for row in values[1:]:
        while len(row) < len(KOLOMMEN):
            row.append("")
        record = dict(zip(KOLOMMEN, row))
        volgende_actie = FOLLOW_UP_STADIA.get(record["status"])
        if volgende_actie and record["volgende_follow_up"] and record["volgende_follow_up"] <= vandaag:
            record["volgende_actie"] = volgende_actie
            due.append(record)
    return due


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("volgende")
    v.add_argument("n", type=int, default=5, nargs="?")
    sub.add_parser("due-follow-ups")
    sub.add_parser("geaccepteerd")
    sub.add_parser("wachtend")
    args = ap.parse_args()

    if args.cmd == "volgende":
        print(json.dumps(volgende_batch(args.n), ensure_ascii=False, indent=2))
    elif args.cmd == "due-follow-ups":
        print(json.dumps(due_follow_ups(), ensure_ascii=False, indent=2))
    elif args.cmd == "geaccepteerd":
        print(json.dumps(geaccepteerd_wachtend(), ensure_ascii=False, indent=2))
    elif args.cmd == "wachtend":
        print(json.dumps(wachtend_op_acceptatie(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
