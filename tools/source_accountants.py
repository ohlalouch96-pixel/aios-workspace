"""
Outreach: Accountants- en administratiekantoren, prospect sourcing & verificatie

Nieuwe doelgroep sinds 18-11-2026. Doel is
eerst valideren met informatieve belgesprekken: herkennen kleine kantoren het
najagen van ontbrekende stukken bij klanten als pijnpunt?

Verifieert een lijst kandidaat-kantoren (die de agent aanlevert, bv. uit de
NOAB-ledenzoeker of webzoekopdrachten), haalt per kantoor telefoon (voorkeur
06), e-mail, eigenaar en een grootte-schatting van de eigen website,
dedupliceert tegen het tabblad accountants-tracker (naam + domein + e-mail) en
voegt nieuwe prospects toe.

Hergebruikt fetcher, e-mail-, telefoon- en sheet-helpers uit
tools/source_makelaars.py (curl-based, want Python's requests wordt door
Cloudflare geblokkeerd).

Gebruik:
    python tools/source_accountants.py .tmp/acc_candidates.json            # dry-run
    python tools/source_accountants.py .tmp/acc_candidates.json --append   # schrijft naar sheet

Input (JSON-array):
    [{"name": "Mintaxx", "url": "https://www.mintaxx.nl", "city": "Amsterdam", "bron": "NOAB"}, ...]

Sheet-veiligheid: elke range heeft de prefix "accountants-tracker!" (assert).
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_makelaars import (  # noqa: E402
    HEADERS_BASIC,
    HEADERS_FULL,
    WORKSPACE_ROOT,
    _format_nl_phone,
    _get_sheet_service,
    extract_all_phones,
    extract_email,
    fetch,
    normalize_domain,
)

SHEET_TAB = "accountants-tracker"
SH = f"{SHEET_TAB}!"

HEADER = [
    "Kantoor", "Plaats", "Website", "Eigenaar", "Telefoon", "E-mail", "Grootte",
    "Gebeld op", "Resultaat", "Uren per week kwijt", "Toestemming terugbellen", "Notities",
]

CONTACT_PATHS = [
    "/contact", "/over-ons", "/over-mij", "/team", "/ons-team", "/het-team",
    "/wie-zijn-wij", "/medewerkers", "/about", "/about-us", "/over",
]

FUNCTIE_WOORDEN = (
    r"eigenaar|eigenaresse|eigenares|directeur|directrice|oprichter|oprichtster|"
    r"vennoot|managing partner|register\s?accountant|accountant[\s\-]administratieconsulent|"
    r"belastingadviseur|fiscalist|fiscaal jurist|"
    r"\bAA\b|\bRA\b|\bFB\b"
)
NAAM = r"([A-Z][a-zà-ÿ]+(?:\s+(?:van|de|der|den|van der|van den|ten|ter)?\s*[A-Z][a-zà-ÿ'\-]+){1,3})"
# Naam gevolgd door functie ("Jan Jansen, eigenaar") of functie gevolgd door
# naam ("Eigenaar: Jan Jansen"). Functiewoord hoofdletterongevoelig, naam niet.
PERSOON_RE = re.compile(NAAM + r"\s*[,\-|(–:]?\s*((?i:" + FUNCTIE_WOORDEN + r"))")
PERSOON_OMGEKEERD_RE = re.compile(
    r"\b((?i:eigenaar|eigenaresse|eigenares|directeur|directrice|oprichter|oprichtster))"
    r"\s*(?:en\s+\w+\s*)?[:\-–]?\s*" + NAAM
)
IK_BEN_RE = re.compile(r"(?i:mijn naam is|ik ben|my name is)\s+" + NAAM)
PLACEHOLDER_RE = re.compile(
    r"john@doe|jouw@|your@|naam@|voorbeeld@|email@email|info@domein|123456|(\d)\1{5}", re.I
)
EIGENAAR_RE = re.compile(r"eigena|directeur|directrice|oprichte|vennoot|managing partner", re.I)
EMAIL_HASH_RE = re.compile(r"^[0-9a-f]{20,}@")  # versleuteld/anti-spam adres, onbruikbaar
NAAM_STOPWOORDEN = {
    "zoek", "goede", "jij", "bij", "op", "een", "uw", "over", "en", "met", "voor",
    "naar", "ons", "onze", "team", "meer", "wij", "als", "de", "het", "uw", "contact",
    "home", "lees", "neem", "bel", "onze", "diensten", "welkom", "administratie",
    "google", "maps", "jaarrekeningen", "aangifte", "inkomstenbelasting", "boekhouder",
    "besloten", "grondlegger", "directie", "algemeen", "accountant", "advies",
}
AANTAL_RE = re.compile(
    r"(?:team\s+van|met)\s+(\d{1,3})\s+(?:medewerkers|collega'?s|professionals|mensen|specialisten)|"
    r"(\d{1,3})\s+(?:medewerkers|collega'?s|professionals)\b",
    re.I,
)


def _tekst(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def extract_personen(html):
    out, seen = [], set()
    tekst = _tekst(html)
    hits = [(m.group(1), m.group(2)) for m in PERSOON_RE.finditer(tekst)]
    hits += [(m.group(2), m.group(1)) for m in PERSOON_OMGEKEERD_RE.finditer(tekst)]
    # Kleine kantoren (eenmanszaak) stellen zich vaak voor met "Mijn naam is ...".
    hits += [(m.group(1), "eigenaar?") for m in IK_BEN_RE.finditer(tekst)]
    for naam, functie in hits:
        naam = naam.strip()
        if any(w.lower() in NAAM_STOPWOORDEN for w in naam.split()):
            continue
        if naam.lower() not in seen:
            seen.add(naam.lower())
            out.append((naam, functie.strip().lower()))
    return out


def extract_aantal(html):
    for m in AANTAL_RE.finditer(_tekst(html)):
        n = int(m.group(1) or m.group(2))
        if 1 <= n <= 500:
            return n
    return None


def schat_grootte(personen, aantal):
    if aantal:
        return f"{aantal} (volgens site)"
    n = len(personen)
    if n == 0:
        return "onbekend"
    if n <= 2:
        return "1-3 (schatting)"
    if n <= 6:
        return "3-10 (schatting)"
    return "10+ (schatting)"


def check_one(c):
    res = {"name": c["name"], "url": c["url"], "city": c.get("city", ""), "bron": c.get("bron", "")}
    f = fetch(c["url"], HEADERS_BASIC)
    if f["ok"] and f["status_code"] == 403:
        f = fetch(c["url"], HEADERS_FULL)
    if not f["ok"] or f["status_code"] >= 400:
        res.update(status="dropped", reason=f"onbereikbaar ({f.get('reason') or f.get('status_code')})")
        return res

    pages = [f["body"]]
    for path in CONTACT_PATHS:
        r = fetch(c["url"].rstrip("/") + path, HEADERS_BASIC, timeout=10)
        if r["ok"] and r["status_code"] < 400 and len(r["body"]) > 500:
            pages.append(r["body"])
    combined = "\n".join(pages)

    email = extract_email(PLACEHOLDER_RE.sub(" ", combined))
    if email and (PLACEHOLDER_RE.search(email) or EMAIL_HASH_RE.search(email)):
        email = None
    telefoon, mobiel = None, False
    for p in pages:
        nums = [n for n in extract_all_phones(p) if not PLACEHOLDER_RE.search(n)]
        mob = [n for n in nums if n[1] == "6"]
        if mob:
            telefoon, mobiel = _format_nl_phone(mob[0]), True
            break
        if nums and not telefoon:
            telefoon = _format_nl_phone(nums[0])
    personen = []
    for p in pages:
        for x in extract_personen(p):
            if x[0].lower() not in {y[0].lower() for y in personen}:
                personen.append(x)
    eigenaar = next((f"{n} ({fn})" for n, fn in personen if EIGENAAR_RE.search(fn)), "")
    if not eigenaar and personen:
        eigenaar = f"{personen[0][0]} ({personen[0][1]}, check)"
    aantal = extract_aantal(combined)
    grootte = schat_grootte(personen, aantal)

    if not telefoon and not email:
        res.update(status="dropped", reason="geen telefoon of e-mail gevonden")
        return res

    groot = (aantal and aantal > 10) or len(personen) > 6
    res.update(
        status="qualified", email=email or "", telefoon=telefoon or "", mobiel=mobiel,
        eigenaar=eigenaar, grootte=grootte, groot=bool(groot),
    )
    return res


def ensure_tab(service, sheet_id):
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    tabs = [s["properties"]["title"] for s in meta["sheets"]]
    if SHEET_TAB not in tabs:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": SHEET_TAB}}}]},
        ).execute()
        rng = f"{SH}A1:L1"
        assert rng.startswith(SH)
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=rng, valueInputOption="RAW", body={"values": [HEADER]}
        ).execute()
        print(f"Tabblad '{SHEET_TAB}' aangemaakt met kopregel.")


def get_existing(service, sheet_id):
    rng = f"{SH}A:F"
    assert rng.startswith(SH)
    rows = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=rng).execute().get("values", [])
    names, domains, emails = set(), set(), set()
    for row in rows[1:]:
        row = row + [""] * (6 - len(row))
        if row[0].strip():
            names.add(row[0].strip().lower())
        d = normalize_domain(row[2])
        if d:
            domains.add(d)
        if row[5].strip():
            emails.add(row[5].strip().lower())
    return names, domains, emails, len(rows)


def build_row(r):
    notities = []
    if r.get("bron"):
        notities.append(f"Bron: {r['bron']}.")
    if r.get("mobiel"):
        notities.append("Telefoon is mobiel (06).")
    if r.get("groot"):
        notities.append("Let op: mogelijk groter kantoor, check vóór bellen.")
    return [
        r["name"], r["city"], r["url"], r.get("eigenaar", ""), r.get("telefoon", ""),
        r.get("email", ""), r.get("grootte", ""), "", "", "", "", " ".join(notities),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates_file")
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--output", default=str(WORKSPACE_ROOT / ".tmp" / "source_accountants_results.json"))
    args = ap.parse_args()

    cands = json.load(open(args.candidates_file, encoding="utf-8"))
    service, sheet_id = _get_sheet_service()
    if args.append:
        ensure_tab(service, sheet_id)
    try:
        names, domains, emails, n_rows = get_existing(service, sheet_id)
    except Exception:
        names, domains, emails, n_rows = set(), set(), set(), 0  # tab bestaat nog niet (dry-run)

    nieuw, dubbel = [], []
    seen_n, seen_d = set(), set()
    for c in cands:
        n, d = c["name"].strip().lower(), normalize_domain(c.get("url", ""))
        if n in names or n in seen_n or (d and (d in domains or d in seen_d)):
            dubbel.append(c)
            continue
        seen_n.add(n)
        if d:
            seen_d.add(d)
        nieuw.append(c)
    print(f"Kandidaten: {len(cands)} | nieuw: {len(nieuw)} | al in sheet of dubbel: {len(dubbel)}")

    results = []
    with ThreadPoolExecutor(args.workers) as ex:
        for fut in as_completed([ex.submit(check_one, c) for c in nieuw]):
            results.append(fut.result())

    qualified, seen_e = [], set()
    for r in results:
        if r["status"] != "qualified":
            continue
        e = r["email"].lower()
        if e and (e in emails or e in seen_e):
            r.update(status="dropped", reason="e-mailadres staat al in de sheet")
            continue
        if e:
            seen_e.add(e)
        qualified.append(r)
    dropped = [r for r in results if r["status"] == "dropped"]

    for r in sorted(qualified, key=lambda x: x["name"].lower()):
        flag = (" [06]" if r["mobiel"] else "") + (" [GROOT?]" if r["groot"] else "")
        print(f"[OK]{flag} {r['name']} | {r['city']} | {r['eigenaar'] or '-'} | {r['telefoon'] or '-'} | {r['email'] or '-'} | {r['grootte']}")
    for r in dropped:
        print(f"[DROP] {r['name']}: {r['reason']}")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    json.dump({"qualified": qualified, "dropped": dropped, "duplicates": dubbel},
              open(args.output, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nQualified: {len(qualified)} | Dropped: {len(dropped)} | Resultaten: {args.output}")

    if not args.append:
        print("(Dry-run: niets naar de sheet geschreven. Gebruik --append na screening.)")
        return
    if not qualified:
        return
    start = max(n_rows, 1) + 1
    rows = [build_row(r) for r in sorted(qualified, key=lambda x: x["name"].lower())]
    rng = f"{SH}A{start}:L{start + len(rows) - 1}"
    assert rng.startswith(SH)
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=rng, valueInputOption="RAW", body={"values": rows}
    ).execute()
    print(f"Toegevoegd: {len(rows)} rijen ({rng})")


if __name__ == "__main__":
    main()
