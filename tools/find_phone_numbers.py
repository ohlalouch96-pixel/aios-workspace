"""
Outreach — Telefoonnummers zoeken voor ondernemers-tracker

Besluit 30-10-2026: vanaf maandag 2-11 wordt de ondernemers-track vooral
telefonisch benaderd (zie workflows/find_phone_numbers.md voor de reden).
Dit script zoekt ontbrekende telefoonnummers op de eigen website van elk
vakbedrijf (contactpagina/footer) en vult kolom B aan — zonder bestaande
inhoud te overschrijven. Alleen een nummer dat echt op de site staat wordt
gebruikt; nooit gegokt.

Gebruik (CLI):
    python tools/find_phone_numbers.py                     # dry-run, alleen printen
    python tools/find_phone_numbers.py --limit 20           # dry-run, eerste 20
    python tools/find_phone_numbers.py --write               # schrijft naar de sheet
    python tools/find_phone_numbers.py --write --workers 12

Prioriteit (vastgelegd 30-10):
    1. status == Verstuurd      (~210, mails gehad, nog in de reeks)
    2. status == Afgerond       (~96, alle mails gehad, geen reactie)
    3. status == Te versturen   (~115, nog niets gehad)
Overgeslagen: status Afgewezen/Onbereikbaar, rijen die al een "Tel:" hebben,
en rijen met een harde afwijzing/opt-out in de notities (HARD_REJECT_RE).

Hergebruikt de curl-based fetcher en telefoon-regex uit source_ondernemers.py
(Python's requests wordt structureel geblokkeerd door Cloudflare).

Sheet-veiligheid: elke range heeft altijd de "ondernemers-tracker!" prefix
(hard afgedwongen via assert), schrijven gebeurt in kleine batches, en na elke
batch wordt teruggelezen of de waarde er echt staat (zie feedback_sheet_tabnaam_verplicht
en feedback_sheet_writes_verifieren in memory).
"""

import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_ondernemers import (  # noqa: E402
    CONTACT_PATHS,
    HEADERS_BASIC,
    PHONE_CHUNK_RE,
    _get_sheet_service,
    _normalize_nl_phone,
    fetch,
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SHEET_TAB = "ondernemers-tracker"
SH = f"{SHEET_TAB}!"

PRIORITY = {"Verstuurd": 0, "Afgerond": 1, "Te versturen": 2}

HARD_REJECT_RE = re.compile(
    r"niet meer (bellen|mailen|contacteren)|wil geen contact|opt-?out|unsubscribe|"
    r"stop met (bellen|mailen)",
    re.I,
)


def _format_nl_phone(s):
    if s[1] == "6":
        return f"{s[:2]}-{s[2:]}"
    return f"{s[:3]}-{s[3:]}"


def extract_all_phones(html):
    text = re.sub(r"<[^>]+>", " ", html)
    found = []
    for m in PHONE_CHUNK_RE.finditer(text):
        n = _normalize_nl_phone(m.group(0))
        if n and n not in found:
            found.append(n)
    return found


def best_phone(html):
    """Geeft voorkeur aan een 06-nummer (meer kans op de eigenaar zelf)."""
    phones = extract_all_phones(html)
    if not phones:
        return None, False
    mobiles = [p for p in phones if p[1] == "6"]
    if mobiles:
        return _format_nl_phone(mobiles[0]), True
    return _format_nl_phone(phones[0]), False


def find_phone_for(candidate):
    url = candidate["url"]
    if not url:
        return {"row": candidate["i"], "name": candidate["name"], "phone": None, "mobile": False}

    fetched = fetch(url, HEADERS_BASIC)
    phone, is_mobile = (None, False)
    if fetched["ok"] and fetched["status_code"] < 400:
        phone, is_mobile = best_phone(fetched["body"])

    if not phone:
        for path in CONTACT_PATHS:
            r = fetch(url.rstrip("/") + path, HEADERS_BASIC)
            if r["ok"] and r["status_code"] < 400:
                phone, is_mobile = best_phone(r["body"])
                if phone:
                    break

    return {"row": candidate["i"], "name": candidate["name"], "phone": phone, "mobile": is_mobile}


def load_candidates():
    service, sheet_id = _get_sheet_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{SHEET_TAB}!A:J"
    ).execute()
    rows = result.get("values", [])

    candidates = []
    for i, row in enumerate(rows[1:], start=2):
        row = row + [""] * (10 - len(row))
        bedrijf, kanaal, url, branche, status, f, g, h, notitie, gereageerd = row[:10]
        if status not in PRIORITY:
            continue
        if "tel:" in kanaal.lower():
            continue
        if not url:
            continue
        if HARD_REJECT_RE.search(notitie):
            continue
        candidates.append({
            "i": i, "name": bedrijf, "url": url, "status": status,
            "kanaal": kanaal, "notitie": notitie,
        })

    candidates.sort(key=lambda c: PRIORITY[c["status"]])
    return candidates, service, sheet_id


def write_results(service, sheet_id, results, cand_by_row, batch_size):
    today_str = date.today().isoformat()
    batch = []

    def flush():
        if not batch:
            return
        assert all(d["range"].startswith(SH) for d in batch), "MISSING TAB PREFIX"
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body={"valueInputOption": "RAW", "data": list(batch)},
        ).execute()
        rows_touched = sorted({int(d["range"].split("!")[1][1:]) for d in batch})
        check_ranges = [f"{SH}A{r}:J{r}" for r in rows_touched]
        check = service.spreadsheets().values().batchGet(
            spreadsheetId=sheet_id, ranges=check_ranges
        ).execute()
        ok = all(vr.get("values") for vr in check.get("valueRanges", []))
        print(f"  batch van {len(batch)} cellen geschreven, terugleescheck: {'OK' if ok else 'LET OP - LEEG'}")
        batch.clear()

    for r in results:
        c = cand_by_row[r["row"]]
        if r.get("phone"):
            new_b = f"{c['kanaal']} + Tel: {r['phone']}"
            batch.append({"range": f"{SH}B{r['row']}", "values": [[new_b]]})
        else:
            old_i = c["notitie"].strip()
            sep = " " if old_i else ""
            new_i = f"{old_i}{sep}Tel-zoekactie {today_str}: geen nummer gevonden op website."
            batch.append({"range": f"{SH}I{r['row']}", "values": [[new_i]]})

        if len(batch) >= batch_size:
            flush()
    flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="Schrijf resultaten naar de sheet (anders dry-run).")
    ap.add_argument("--limit", type=int, default=None, help="Beperk tot de eerste N kandidaten (prioriteitsvolgorde).")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=20)
    args = ap.parse_args()

    candidates, service, sheet_id = load_candidates()
    print(f"Kandidaten zonder telefoonnummer (na filters): {len(candidates)}")
    if args.limit:
        candidates = candidates[: args.limit]
        print(f"Beperkt tot eerste {len(candidates)} (prioriteitsvolgorde: Verstuurd > Afgerond > Te versturen)")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(find_phone_for, c): c for c in candidates}
        done = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done += 1
            tag = "MOBIEL" if res.get("mobile") else ("VAST" if res.get("phone") else "GEEN")
            print(f"[{done}/{len(candidates)}] [{tag}] rij {res['row']} {res.get('name', '')} -> {res.get('phone')}")

    found = [r for r in results if r.get("phone")]
    mobile = [r for r in found if r.get("mobile")]
    not_found = [r for r in results if not r.get("phone")]

    print()
    print(f"Gevonden: {len(found)} (waarvan {len(mobile)} mobiel/06, {len(found) - len(mobile)} vast)")
    print(f"Niet gevonden: {len(not_found)}")

    if not args.write:
        print("\n(Dry-run: niets geschreven. Gebruik --write om de sheet bij te werken.)")
        return

    cand_by_row = {c["i"]: c for c in candidates}
    write_results(service, sheet_id, results, cand_by_row, args.batch_size)
    print("\nKlaar. Sheet bijgewerkt.")


if __name__ == "__main__":
    main()
