"""
Outreach — Ondernemers Prospect Sourcing & Verificatie

Verifieert een lijst kandidaat-vakbedrijven (installateurs, loodgieters,
aannemers, klussenbedrijven, stukadoors, schilders, hoveniers, dakdekkers,
elektriciens e.d.), dedupliceert tegen de bestaande ondernemers-tracker sheet,
en voegt gekwalificeerde nieuwe prospects toe.

Dit script vindt GEEN kandidaten (dat doet de agent, via web-research) — het
verifieert een lijst die je aanlevert. Zie workflows/source_ondernemers.md.

Gebruik (CLI):
    python tools/source_ondernemers.py .tmp/candidates.json
    python tools/source_ondernemers.py .tmp/candidates.json --append
    python tools/source_ondernemers.py .tmp/candidates.json --workers 12 --output .tmp/results.json

Input-formaat (candidates_file, JSON-array):
    [
      {"name": "Voorbeeld Installatie", "url": "https://voorbeeldinstallatie.nl", "branche": "Installatiebedrijf"},
      ...
    ]

Zelfde curl-based fetcher als tools/source_prospects.py (Python's `requests`
wordt structureel geblokkeerd door Cloudflare TLS-fingerprinting).

Vereiste .env variabelen (zelfde als scripts/collect_outreach.py):
    GOOGLE_SERVICE_ACCOUNT_JSON — pad naar credentials/google-service-account.json
    OUTREACH_SHEET_ID           — Google Sheet ID
    (tabblad is hardcoded op "ondernemers-tracker", los van OUTREACH_SHEET_TAB)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except ImportError:
    raise ImportError("Ontbrekende packages — draai: pip install google-api-python-client google-auth")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_TAB = "ondernemers-tracker"

# ============================================================================
# Screeningcriteria (referentie — zie workflows/source_ondernemers.md)
# ============================================================================
SCREENING_REMINDER = (
    "Herinnering: dit script filtert alleen bereikbaarheid, kanaal, spoedservice-"
    "profilering en dedup. Loop de 'qualified' resultaten nog door op branche-fit "
    "(offerte-gerelateerd vakbedrijf, geen kappers/horeca/webshops) en schaal "
    "(kleine/middelgrote familiebedrijven, geen grote geprofessionaliseerde ketens) "
    "voordat je --append gebruikt."
)

# ============================================================================
# Fallback-kanaal zonder e-mail (toegevoegd 2026-10-27)
# ============================================================================
# Tot deze wijziging werd een kandidaat zonder vindbaar e-mailadres altijd
# gedropt met reason "geen e-mailadres gevonden" — ook als er wel een
# telefoonnummer of een naam+functie (eigenaar/directeur/oprichter/
# zaakvoerder, voor LinkedIn-contact) op de site stond. Dat liet bruikbare
# prospects onterecht wegvallen (66 kandidaten in de ronde van 14-10/27-10).
#
# Sinds nu: een kandidaat is ook "qualified" als er GEEN e-mailadres is maar
# er WEL een telefoonnummer (via PHONE_RE/extract_phone) of een
# persoon+functie (via extract_persoon_signaal, als LinkedIn-signaal)
# gevonden wordt. Alleen als GEEN van de drie iets opleverde, wordt gedropt
# met reason "geen e-mailadres, telefoonnummer of persoon gevonden".
# E-mail blijft de voorkeursroute: zodra een e-mailadres gevonden wordt,
# verandert er niets aan het bestaande gedrag (build_kanaal_contact/
# build_notities geven dan nog steeds hetzelfde resultaat als voorheen).

# ============================================================================
# Fetch (curl-based)
# ============================================================================
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

HEADERS_BASIC = {"User-Agent": UA}
HEADERS_FULL = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
}

CURL_ERROR_MAP = {
    3: "URL_MALFORMED", 6: "DNS_ERROR", 7: "CONN_ERROR", 28: "TIMEOUT",
    35: "SSL_ERROR", 51: "SSL_ERROR", 52: "EMPTY_RESPONSE", 56: "CONN_ERROR",
    58: "SSL_ERROR", 60: "SSL_ERROR", 97: "SSL_ERROR",
}


def fetch(url, headers, timeout=15):
    fd, body_path = tempfile.mkstemp(prefix="source_ondernemers_")
    os.close(fd)
    try:
        cmd = [
            "curl", "-sS", "-L", "--max-redirs", "5",
            "--max-time", str(timeout),
            "-o", body_path, "-w", "%{http_code}",
        ]
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
        cmd.append(url)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        except subprocess.TimeoutExpired:
            return {"ok": False, "reason": "TIMEOUT"}
        if proc.returncode != 0:
            reason = CURL_ERROR_MAP.get(proc.returncode, f"CURL_ERR_{proc.returncode}")
            return {"ok": False, "reason": reason}
        stdout = proc.stdout.strip()
        status_code = int(stdout) if stdout.isdigit() else 0
        try:
            with open(body_path, encoding="utf-8", errors="ignore") as f:
                body = f.read()
        except OSError:
            body = ""
        return {"ok": True, "status_code": status_code, "body": body}
    finally:
        try:
            os.unlink(body_path)
        except OSError:
            pass


# ============================================================================
# Spoedservice / grote-keten detectie (informatief, mede-basis voor drop)
# ============================================================================
SPOED_RE = re.compile(
    r"(24\s*/\s*7|dag\s*en\s*nacht|spoedservice|spoeddienst|no\s*cure\s*no\s*pay|"
    r"binnen\s*\d+\s*min(uten)?|storingsdienst)", re.I,
)

# ============================================================================
# E-mail-lookup
# ============================================================================
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
EMAIL_JUNK_TLDS = {"png", "jpg", "jpeg", "gif", "svg", "webp", "js", "css", "woff", "woff2", "ttf", "eot", "ico"}
HONEYPOT_EMAIL_RE = re.compile(
    r"(techaro\.lol|sentry\.io|sentry-next|wixpress\.com|example\.com|"
    r"noreply@|no-reply@|donotreply@|@sentry)", re.I,
)


def extract_email(html):
    for m in EMAIL_RE.finditer(html):
        addr = m.group(0)
        tld = addr.rsplit(".", 1)[-1].lower()
        if tld in EMAIL_JUNK_TLDS:
            continue
        if HONEYPOT_EMAIL_RE.search(addr):
            continue
        return addr
    return None


# ============================================================================
# Telefoonnummer-lookup (fallback-kanaal zonder e-mail)
# ============================================================================
# Matcht NL vaste nummers (0XX-XXXXXXX, 0XX XXX XX XX), NL mobiel (06-XXXXXXXX)
# en internationaal (+31 6 XXXXXXXX / 0031...). De regex zelf is ruim (losse
# cijferreeksen met spaties/punten/streepjes/haakjes ertussen) — de echte
# validatie zit in _normalize_nl_phone(): na het strippen van alle
# scheidingstekens moet er exact een 10-cijferig NL-nummer overblijven dat
# met 0 begint. Dat filtert ruis zoals postcodes (4 cijfers + letters, breekt
# de match al af) en KvK-nummers (8 cijfers, worden geen 10 na normalisatie).
PHONE_CHUNK_RE = re.compile(r"(?:\+?\d[\d\s().\-]{7,16}\d)")


def _normalize_nl_phone(raw):
    """Strip scheidingstekens en normaliseer naar '0XXXXXXXXX' (10 cijfers), of None."""
    digits_plus = re.sub(r"[^\d+]", "", raw)
    s = digits_plus
    if s.startswith("+31"):
        rest = s[3:]
        if rest.startswith("0"):
            rest = rest[1:]
        s = "0" + rest
    elif s.startswith("0031"):
        rest = s[4:]
        if rest.startswith("0"):
            rest = rest[1:]
        s = "0" + rest
    elif s.startswith("+"):
        return None

    if not s.isdigit() or len(s) != 10 or not s.startswith("0"):
        return None
    return s


def _format_nl_phone(s):
    """Leesbare weergave. Benadering (geen area-code-tabel) — 06 krijgt 06-XXXXXXXX,
    vaste nummers 0XX-XXXXXXX (niet altijd exact op de echte regio-codegrens)."""
    if s[1] == "6":
        return f"{s[:2]}-{s[2:]}"
    return f"{s[:3]}-{s[3:]}"


def extract_phone(html):
    text = re.sub(r"<[^>]+>", " ", html)
    for m in PHONE_CHUNK_RE.finditer(text):
        normalized = _normalize_nl_phone(m.group(0))
        if normalized:
            return _format_nl_phone(normalized)
    return None


# ============================================================================
# Personalisatie-detail extractie (heuristiek — nog handmatig te checken)
# ============================================================================
SINDS_RE = re.compile(
    r"(familiebedrijf[^.]{0,40}sinds\s*(19|20)\d{2}|sinds\s*(19|20)\d{2}[^.]{0,40}|"
    r"opgericht\s*in\s*(19|20)\d{2}|al\s*(sinds\s*)?\d{2,3}\s*jaar[^.]{0,40})",
    re.I,
)
PLAATS_RE = re.compile(r"\b\d{4}\s?[A-Z]{2}\s+([A-Za-zÀ-ÿ\s\-]{2,30})\b")


def extract_personalisatie(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    detail = None
    m = SINDS_RE.search(text)
    if m:
        detail = m.group(0).strip()
    plaats = None
    pm = PLAATS_RE.search(text)
    if pm:
        plaats = pm.group(1).strip()
    return detail, plaats


# ============================================================================
# Persoon-signaal (lichte heuristiek — geen harde LinkedIn-scrape)
# ============================================================================
PERSOON_RE = re.compile(
    r"([A-Z][a-zà-ÿ]+(?:\s+(?:van|de|der|den|van der|van den)?\s*[A-Z][a-zà-ÿ]+){1,3})"
    r"\s*[,\-]?\s*(eigenaar|eigenares|directeur|directrice|oprichter|oprichtster|zaakvoerder)",
    re.I,
)


def extract_persoon_signaal(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    m = PERSOON_RE.search(text)
    if m:
        return m.group(1).strip(), m.group(2).strip().lower()
    return None, None


CONTACT_PATHS = [
    "/contact", "/over-ons", "/over-mij", "/pages/contact", "/pages/over-ons",
    "/about", "/about-us", "/wie-zijn-wij", "/team",
]


# ============================================================================
# Verificatie per kandidaat
# ============================================================================
def check_one(candidate):
    name = candidate["name"]
    url = candidate["url"]
    branche = candidate.get("branche", "")
    result = {"name": name, "url": url, "branche": branche}

    fetched = fetch(url, HEADERS_BASIC)
    if not fetched["ok"]:
        result["status"] = "dropped"
        result["reason"] = f"onbereikbaar ({fetched['reason']})"
        return result

    status_code = fetched["status_code"]
    if status_code == 403:
        retry = fetch(url, HEADERS_FULL)
        if not retry["ok"] or retry["status_code"] == 403:
            result["status"] = "dropped"
            result["reason"] = "onbereikbaar (403 aanhoudend)"
            return result
        fetched = retry
        status_code = fetched["status_code"]
    elif status_code == 429:
        result["status"] = "dropped"
        result["reason"] = "onbereikbaar (429 rate limited)"
        return result
    elif status_code == 520:
        result["status"] = "dropped"
        result["reason"] = "onbereikbaar (520 serverfout)"
        return result
    elif status_code >= 400:
        result["status"] = "dropped"
        result["reason"] = f"onbereikbaar (HTTP {status_code})"
        return result

    html = fetched["body"]
    combined_html = html

    # Extra pagina's checken voor e-mail/persoon/detail als homepage niets oplevert.
    email = extract_email(html)
    detail, plaats = extract_personalisatie(html)
    persoon, functie = extract_persoon_signaal(html)

    if not email or not detail or not persoon:
        for path in CONTACT_PATHS:
            r = fetch(url.rstrip("/") + path, HEADERS_BASIC)
            if r["ok"] and r["status_code"] < 400:
                combined_html += r["body"]
                if not email:
                    email = extract_email(r["body"])
                if not detail:
                    d2, p2 = extract_personalisatie(r["body"])
                    if d2:
                        detail = d2
                    if p2 and not plaats:
                        plaats = p2
                if not persoon:
                    pe, pf = extract_persoon_signaal(r["body"])
                    if pe:
                        persoon, functie = pe, pf
            if email and detail and persoon:
                break

    result["spoedservice_signaal"] = bool(SPOED_RE.search(combined_html))

    if not email:
        telefoon = extract_phone(combined_html)
        if not telefoon and not persoon:
            result["status"] = "dropped"
            result["reason"] = "geen e-mailadres, telefoonnummer of persoon gevonden"
            return result
        result["status"] = "qualified"
        result["telefoon"] = telefoon
        result["detail"] = detail
        result["plaats"] = plaats
        result["persoon"] = persoon
        result["functie"] = functie
        return result

    result["status"] = "qualified"
    result["email"] = email
    result["detail"] = detail
    result["plaats"] = plaats
    result["persoon"] = persoon
    result["functie"] = functie
    return result


def verify_candidates(candidates, workers=10):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(check_one, c): c for c in candidates}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            tag = "OK" if res["status"] == "qualified" else "DROP"
            extra = res.get("email") or res.get("reason", "")
            spoed = " [SPOED]" if res.get("spoedservice_signaal") else ""
            print(f"[{tag}]{spoed} {res['name']} - {extra}")
    return results


# ============================================================================
# Dedup tegen bestaande sheet
# ============================================================================
def _get_sheet_service():
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    sheet_id = os.getenv("OUTREACH_SHEET_ID", "").strip()
    if not creds_path or not sheet_id:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON of OUTREACH_SHEET_ID ontbreekt in .env")
    full_creds_path = Path(creds_path)
    if not full_creds_path.is_absolute():
        full_creds_path = WORKSPACE_ROOT / creds_path
    creds = Credentials.from_service_account_file(str(full_creds_path), scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service, sheet_id


def normalize_domain(url):
    """Normaliseer een URL naar een vergelijkbaar domein (geen scheme/www/pad/trailing slash)."""
    if not url:
        return None
    domain = re.sub(r"^https?://", "", url.strip(), flags=re.I)
    domain = re.sub(r"^www\.", "", domain, flags=re.I)
    domain = domain.split("/")[0].lower()
    return domain or None


def get_existing_identifiers():
    """Haalt bestaande naam/domein/e-mail op uit de sheet, voor dedup op meer dan alleen de naam.

    Bug gevonden 2026-10-14: dedup matchte uitsluitend op exacte bedrijfsnaam-string.
    Dezelfde ondernemer met een net iets andere naam-extractie (bv. "Hollemandak
    Dakdekkers Loodgieters Utrecht" vs "Holleman Dakdekkers & Loodgieters", zelfde
    website) werd daardoor niet als duplicaat herkend, met dubbel verstuurde
    bericht-1-mails tot gevolg. Domein is een stabielere sleutel dan de vrij
    getypte bedrijfsnaam. E-mail wordt apart gebruikt na verificatie (zie
    dedup_qualified_by_email), omdat het e-mailadres van een kandidaat pas na
    check_one() bekend is.
    """
    service, sheet_id = _get_sheet_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{SHEET_TAB}!A:C"
    ).execute()
    values = result.get("values", [])
    names, domains, emails = set(), set(), set()
    for row in values[1:]:
        if not row:
            continue
        if row[0].strip():
            names.add(row[0].strip().lower())
        if len(row) > 1 and row[1]:
            email = extract_email(row[1])
            if email:
                emails.add(email.lower())
        if len(row) > 2 and row[2]:
            domain = normalize_domain(row[2])
            if domain:
                domains.add(domain)
    return names, domains, emails


def dedup_candidates(candidates):
    existing_names, existing_domains, _existing_emails = get_existing_identifiers()
    new, duplicates = [], []
    seen_names, seen_domains = set(), set()
    for c in candidates:
        name_key = c["name"].strip().lower()
        domain_key = normalize_domain(c.get("url", ""))
        is_dup = (
            name_key in existing_names or name_key in seen_names
            or (domain_key and (domain_key in existing_domains or domain_key in seen_domains))
        )
        if is_dup:
            duplicates.append(c)
        else:
            new.append(c)
            seen_names.add(name_key)
            if domain_key:
                seen_domains.add(domain_key)
    return new, duplicates


def dedup_qualified_by_email(qualified):
    """Tweede dedup-pas, NA verificatie: het e-mailadres is pas bekend zodra
    check_one() de website heeft gecheckt, dus dit kan niet in dedup_candidates().
    Vangt gevallen op waar naam EN domein verschillen maar het e-mailadres
    (bv. een gedeeld info@-adres, of een nieuw domein van een bestaande klant)
    al in de sheet staat. Gebruik dit altijd vlak voor --append."""
    _existing_names, _existing_domains, existing_emails = get_existing_identifiers()
    new, duplicates = [], []
    seen_emails = set()
    for c in qualified:
        email_key = c.get("email", "").strip().lower()
        if email_key and (email_key in existing_emails or email_key in seen_emails):
            c = dict(c, status="dropped", reason="e-mailadres staat al in de sheet")
            duplicates.append(c)
        else:
            new.append(c)
            if email_key:
                seen_emails.add(email_key)
    return new, duplicates


# ============================================================================
# Sheet-append
# ============================================================================
def build_notities(c):
    parts = []
    detail_bits = []
    if c.get("detail"):
        detail_bits.append(c["detail"].rstrip(".") + ".")
    if c.get("plaats"):
        detail_bits.append(c["plaats"].rstrip(".") + ".")
    if detail_bits:
        parts.append(" ".join(detail_bits))

    email = c.get("email")
    persoon = c.get("persoon")
    functie = c.get("functie", "")
    telefoon = c.get("telefoon")

    if email:
        # Bestaand gedrag (e-mail gevonden) — ongewijzigd.
        if persoon:
            parts.append(f"Kanaal: LinkedIn (persoon: {persoon}, {functie}).")
        else:
            parts.append("Kanaal: E-mail.")
        parts.append(f"E-mail: {email}.")
    elif persoon:
        # Fallback: LinkedIn-signaal zonder e-mail.
        parts.append(f"Kanaal: LinkedIn (persoon: {persoon}, {functie}) - geen e-mailadres gevonden.")
        if telefoon:
            parts.append(f"Tel: {telefoon}.")
    elif telefoon:
        # Fallback: alleen telefoonnummer.
        parts.append("Kanaal: Telefoon (geen e-mailadres of LinkedIn-persoon gevonden).")
        parts.append(f"Tel: {telefoon}.")

    return " ".join(parts)


def build_kanaal_contact(c):
    email = c.get("email")
    persoon = c.get("persoon")
    functie = c.get("functie", "")
    telefoon = c.get("telefoon")

    if email and persoon:
        return f"LinkedIn: {persoon} ({functie}) + E-mail: {email}"
    if email:
        return f"E-mail: {email}"
    if persoon and telefoon:
        return f"LinkedIn: {persoon} ({functie}) + Tel: {telefoon} (geen e-mail gevonden)"
    if persoon:
        return f"LinkedIn: {persoon} ({functie}) (geen e-mail gevonden)"
    if telefoon:
        return f"Tel: {telefoon} (geen e-mail/LinkedIn gevonden)"
    return ""


def build_sheet_row(c):
    return [
        c["name"],
        build_kanaal_contact(c),
        c["url"],
        c.get("branche", ""),
        "Te versturen",
        "", "", "",
        build_notities(c),
        "",
    ]


def append_qualified_to_sheet(qualified):
    if not qualified:
        return {"appended": 0}

    service, sheet_id = _get_sheet_service()

    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{SHEET_TAB}!A:A"
    ).execute()
    current_rows = len(result.get("values", []))
    start_row = current_rows + 1

    rows = [build_sheet_row(c) for c in qualified]
    end_row = start_row + len(rows) - 1
    range_name = f"{SHEET_TAB}!A{start_row}:J{end_row}"

    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    return {"appended": len(rows), "start_row": start_row, "end_row": end_row}


# ============================================================================
# CLI
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Verifieer en (optioneel) voeg ondernemers-prospects toe aan de Google Sheet.")
    parser.add_argument("candidates_file")
    parser.add_argument("--output", default=str(WORKSPACE_ROOT / ".tmp" / "source_ondernemers_results.json"))
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    with open(args.candidates_file, encoding="utf-8") as f:
        candidates = json.load(f)
    print(f"Kandidaten geladen: {len(candidates)}")

    new_candidates, duplicates = dedup_candidates(candidates)
    print(f"Na dedup tegen sheet: {len(new_candidates)} nieuw, {len(duplicates)} al aanwezig (overgeslagen)")

    results = verify_candidates(new_candidates, workers=args.workers)
    qualified = [r for r in results if r["status"] == "qualified"]
    dropped = [r for r in results if r["status"] == "dropped"]

    qualified, email_duplicates = dedup_qualified_by_email(qualified)
    if email_duplicates:
        print(f"Na e-mail-dedup (na verificatie): {len(email_duplicates)} extra duplicaat(en) overgeslagen (e-mailadres al in de sheet)")
        duplicates = duplicates + email_duplicates

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"qualified": qualified, "dropped": dropped, "duplicates": duplicates}, f, ensure_ascii=False, indent=2)

    print()
    print(f"Totaal: {len(results)} geverifieerd | Qualified: {len(qualified)} | Dropped: {len(dropped)}")
    print(f"Resultaten opgeslagen in: {output_path}")
    print()
    print(SCREENING_REMINDER)

    spoed = [r for r in qualified if r.get("spoedservice_signaal")]
    if spoed:
        print(f"\nSpoedservice-signaal gevonden bij {len(spoed)} kandidaten - handmatig checken/droppen:")
        for r in spoed:
            print(f"  - {r['name']} ({r['url']})")

    if args.append:
        if not qualified:
            print("\nGeen gekwalificeerde nieuwe prospects om toe te voegen.")
            return
        print(f"\n--append: {len(qualified)} prospects toevoegen aan de sheet...")
        append_result = append_qualified_to_sheet(qualified)
        print(f"Toegevoegd: {append_result['appended']} rijen (rij {append_result['start_row']} t/m {append_result['end_row']})")
    else:
        print("\n(Dry-run: geen sheet-schrijfactie uitgevoerd. Gebruik --append na de handmatige screening-check.)")


if __name__ == "__main__":
    main()
