"""
Outreach — Prospect Sourcing & Verificatie

Verifieert een lijst kandidaat-webshops (bereikbaarheid, popup/ESP-detectie,
Instagram- of e-mail-kanaal), dedupliceert tegen de bestaande outreach-sheet,
en voegt gekwalificeerde nieuwe prospects toe aan de Google Sheet.

Dit script vindt GEEN kandidaten (dat doet de agent, via web-research op
basis van niche/zoektermen) — het verifieert een lijst die je aanlevert.
Zie workflows/source_prospects.md voor de volledige SOP.

Gebruik (CLI):
    python tools/source_prospects.py .tmp/candidates.json
    python tools/source_prospects.py .tmp/candidates.json --append
    python tools/source_prospects.py .tmp/candidates.json --workers 15 --output .tmp/results.json

Input-formaat (candidates_file, JSON-array):
    [
      {"name": "Voorbeeld Shop", "url": "https://voorbeeldshop.nl", "niche": "Sportvoeding", "land": "Nederland"},
      ...
    ]
    "land" is optioneel (default wordt behandeld als Nederland/België, dus niet vermeld in Notities).

Belangrijke les uit eerdere sourcing-rondes: Python's `requests`-library wordt
structureel geblokkeerd door Cloudflare (TLS-fingerprinting). Daarom gebruikt
dit script `curl` als onderliggende fetcher via subprocess, NIET `requests`.

Vereiste .env variabelen (zelfde als scripts/collect_outreach.py):
    GOOGLE_SERVICE_ACCOUNT_JSON — pad naar credentials/google-service-account.json
    OUTREACH_SHEET_ID           — Google Sheet ID
    OUTREACH_SHEET_TAB          — Tabbladnaam (standaard: Blad1)
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
from urllib.parse import urlparse

from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

# scripts/ heeft geen __init__.py maar is importeerbaar als namespace package
# zodra de workspace-root op sys.path staat.
sys.path.insert(0, str(WORKSPACE_ROOT))
from scripts.collect_outreach import collect as collect_outreach_sheet  # noqa: E402

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except ImportError:
    raise ImportError("Ontbrekende packages — draai: pip install google-api-python-client google-auth")

# Windows-console kan anders vastlopen op €, →, accenten in print()-output.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# ============================================================================
# Screeningcriteria (referentie — zie workflows/source_prospects.md voor SOP)
# ============================================================================
# Dit script automatiseert alleen het MECHANISCHE deel van screening:
# bereikbaarheid, kanaal-detectie (Instagram/e-mail) en dedup tegen de sheet.
#
# De onderstaande criteria zijn NIET volledig automatiseerbaar en vereisen
# dat een agent de resultaten nog doorloopt voordat ze de sheet in gaan:
#
#   - Laag-ticket niches vermijden. Voorbeeld: wenskaarten/stickers
#     (€0,75-2,50/stuk) zijn afgekeurd — orderwaarde te laag om
#     cart-abandonment-automatisering rendabel te maken voor de klant.
#   - Honing/kruiden/olijfolie-azijn: borderline. Alleen acceptabel bij
#     cadeausets/bundels met een redelijke orderwaarde, niet bij losse potjes.
#   - Parent-company schaal-check: als het gevonden contact-e-mailadres een
#     ANDER domein gebruikt dan de webshop zelf, kan dat wijzen op een groot
#     moederbedrijf buiten de doelgroep. Voorbeeld: Balkonstore.nl gaf
#     info@kooprijk.nl — bleek een webwarenhuis met ~75.000 artikelen, dus
#     afgekeurd. Dit script vlagt zo'n domein-mismatch (zie
#     "flag_domain_mismatch" in de output) als signaal, maar wijst niet
#     automatisch af — het is een aanwijzing, geen garantie.
#   - Marketplace-only / reseller-shops vermijden (geen eigen merk).
#   - Groot merk / veel volgers vermijden. Voorbeeld: BRUNA The Label (247k+
#     IG-volgers) kwam door alle mechanische checks heen (eigen merk, geen
#     domein-mismatch, geen reseller) maar is qua schaal waarschijnlijk al
#     professioneel geautomatiseerd en dus geen goede fit. Dit script checkt
#     GEEN volgersaantal (staat niet in de HTML van de webshop zelf) — dit
#     blijft een handmatige Instagram-check door de agent vlak voor het
#     versturen van het bericht, niet iets wat de verificatie-pipeline vangt.
#
# Land is GEEN afwijzingscriterium meer sinds de campagne internationaal is
# (2026-09-14). Het wordt alleen informatief in de Notities-kolom gezet.
SCREENING_REMINDER = (
    "Herinnering: dit script filtert alleen bereikbaarheid, kanaal en dedup. "
    "Loop de 'qualified' resultaten nog handmatig door op laag-ticket niches, "
    "borderline food-niches (honing/kruiden/azijn), parent-company/schaal-signalen, "
    "marketplace/reseller-shops, EN check het Instagram-volgersaantal (grote merken "
    "zoals BRUNA The Label met 247k+ volgers zijn waarschijnlijk al professioneel "
    "geautomatiseerd) voordat je --append gebruikt."
)


# ============================================================================
# Fetch (curl-based — requests wordt geblokkeerd door Cloudflare TLS-fingerprinting)
# ============================================================================
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

HEADERS_BASIC = {"User-Agent": UA}
HEADERS_FULL = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
}

# curl exit codes -> herkenbare reden. Zie `man curl` exit codes.
CURL_ERROR_MAP = {
    3: "URL_MALFORMED",
    6: "DNS_ERROR",
    7: "CONN_ERROR",
    28: "TIMEOUT",
    35: "SSL_ERROR",
    51: "SSL_ERROR",
    52: "EMPTY_RESPONSE",
    56: "CONN_ERROR",
    58: "SSL_ERROR",
    60: "SSL_ERROR",
    97: "SSL_ERROR",
}


def fetch(url, headers, timeout=15):
    """Haalt een URL op via curl (subprocess). Retourneert
    {"ok": True, "status_code": int, "body": str} of {"ok": False, "reason": str}.
    """
    fd, body_path = tempfile.mkstemp(prefix="source_prospects_")
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
# Popup/ESP-detectie
# ============================================================================
ESP_RE = re.compile(
    r"(klaviyo|mailchimp-for-woocommerce|mailchimp-for-wp|privy\.com|justuno|"
    r"omnisend|sleeknote|optinmonster|onesignal)[a-z0-9._/\-]*\.(js|com)",
    re.I,
)


# ============================================================================
# Instagram-lookup
# ============================================================================
IG_RE = re.compile(r"instagram\.com/([a-zA-Z0-9._-]+)", re.I)
# Generieke/niet-profiel paths die instagram.com/... kunnen volgen.
BAD_IG_PATHS = {"p", "reel", "reels", "o1", "explore", "accounts", "directory", "tv", "stories"}
# Placeholder-handles die thema's/CMS'en tonen bij een niet-geconfigureerde social-knop.
PLACEHOLDER_IG_HANDLES = {"shopify", "yourusername", "youraccountname", "username", "yourprofile", "youraccount"}

CONTACT_PATHS = [
    "/contact", "/over-ons", "/pages/contact", "/pages/over-ons",
    "/over-mij", "/pages/over-mij", "/about", "/about-us",
    "/pages/about-us", "/pages/contact-us", "/contact-us",
]
PRIVACY_PATHS = [
    "/privacy", "/privacy-policy", "/pages/privacy-policy",
    "/impressum", "/pages/privacy",
]


def extract_ig(html):
    for m in IG_RE.finditer(html):
        handle = m.group(1).strip("/").split("?")[0].split("/")[0]
        handle_lower = handle.lower()
        if handle_lower in BAD_IG_PATHS or handle_lower in PLACEHOLDER_IG_HANDLES:
            continue
        if len(handle) > 1:
            return handle
    return None


# ============================================================================
# E-mail-lookup (fallback als er geen Instagram is)
# ============================================================================
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# Matches op deze extensies zijn CSS/JS-bestandsnamen (bv. logo@2x.png), geen e-mail.
EMAIL_JUNK_TLDS = {"png", "jpg", "jpeg", "gif", "svg", "webp", "js", "css", "woff", "woff2", "ttf", "eot", "ico"}
# Honeypot-adressen die anti-bot-systemen (Cloudflare, Anubis e.d.) soms teruggeven aan
# scrapers, en Sentry-foutmeldingsadressen die per ongeluk in HTML terechtkomen.
HONEYPOT_EMAIL_RE = re.compile(
    r"(techaro\.lol|sentry\.io|sentry-next|wixpress\.com|example\.com|"
    r"noreply@|no-reply@|donotreply@)",
    re.I,
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


def base_domain(netloc):
    """Ruwe heuristiek: geeft de tweede-niveau-naam terug (bv. 'balkonstore' uit
    'www.balkonstore.nl'). Onbetrouwbaar voor domeinen als '.co.uk', maar dat is
    acceptabel — dit voedt alleen een informatieve vlag, geen harde filter."""
    netloc = netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    parts = netloc.split(".")
    return parts[-2] if len(parts) >= 2 else netloc


# ============================================================================
# Verificatie per kandidaat
# ============================================================================
def check_one(candidate):
    name = candidate["name"]
    url = candidate["url"]
    niche = candidate.get("niche", "")
    land = candidate.get("land", "")
    result = {"name": name, "url": url, "niche": niche, "land": land}

    fetched = fetch(url, HEADERS_BASIC)
    if not fetched["ok"]:
        result["status"] = "dropped"
        result["reason"] = f"onbereikbaar ({fetched['reason']})"
        return result

    status_code = fetched["status_code"]
    if status_code == 403:
        # False-positive bot-blocks komen voor — één retry met vollere headers.
        retry = fetch(url, HEADERS_FULL)
        if not retry["ok"] or retry["status_code"] == 403:
            result["status"] = "dropped"
            result["reason"] = "onbereikbaar (403 aanhoudend)"
            return result
        fetched = retry
        status_code = fetched["status_code"]
    elif status_code == 429:
        # Rate limiting kwam veel voor bij internationale sites — niet forceren.
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
    result["popup_variant"] = "MET-popup" if ESP_RE.search(html) else "ZONDER-popup"

    ig = extract_ig(html)
    if not ig:
        for path in CONTACT_PATHS:
            r = fetch(url.rstrip("/") + path, HEADERS_BASIC)
            if r["ok"] and r["status_code"] < 400:
                ig = extract_ig(r["body"])
                if ig:
                    break

    if ig:
        result["status"] = "qualified"
        result["channel"] = "instagram"
        result["instagram"] = ig
        return result

    # Geen Instagram gevonden -> val terug op e-mail.
    email = extract_email(html)
    if not email:
        for path in CONTACT_PATHS + PRIVACY_PATHS:
            r = fetch(url.rstrip("/") + path, HEADERS_BASIC)
            if r["ok"] and r["status_code"] < 400:
                email = extract_email(r["body"])
                if email:
                    break

    if not email:
        result["status"] = "dropped"
        result["reason"] = "geen instagram en geen e-mail gevonden"
        return result

    result["status"] = "qualified"
    result["channel"] = "email"
    result["email"] = email

    # Informatieve vlag voor de handmatige parent-company/schaal-check.
    site_base = base_domain(urlparse(url).netloc)
    email_base = base_domain("dummy." + email.split("@")[-1])
    result["flag_domain_mismatch"] = bool(site_base and email_base and site_base != email_base)

    return result


def verify_candidates(candidates, workers=10):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(check_one, c): c for c in candidates}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            tag = "OK" if res["status"] == "qualified" else "DROP"
            extra = res.get("instagram") or res.get("email") or res.get("reason", "")
            print(f"[{tag}] {res['name']} - {extra}")
    return results


# ============================================================================
# Dedup tegen bestaande sheet
# ============================================================================
def get_existing_names():
    result = collect_outreach_sheet()
    if result.get("status") != "success":
        raise RuntimeError(f"Kon sheet niet lezen voor dedup: {result.get('reason')}")
    rows = result["data"].get("rows", [])
    return {row.get("bedrijfsnaam", "").strip().lower() for row in rows if row.get("bedrijfsnaam", "").strip()}


def dedup_candidates(candidates):
    """Filtert kandidaten die op naam al in de sheet staan, VOORDAT er tijd
    aan verificatie wordt besteed."""
    existing = get_existing_names()
    new, duplicates = [], []
    for c in candidates:
        if c["name"].strip().lower() in existing:
            duplicates.append(c)
        else:
            new.append(c)
    return new, duplicates


# ============================================================================
# Sheet-append
# ============================================================================
def _get_sheet_service():
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    sheet_id = os.getenv("OUTREACH_SHEET_ID", "").strip()
    sheet_tab = os.getenv("OUTREACH_SHEET_TAB", "Blad1").strip()

    if not creds_path or not sheet_id:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON of OUTREACH_SHEET_ID ontbreekt in .env")

    full_creds_path = Path(creds_path)
    if not full_creds_path.is_absolute():
        full_creds_path = WORKSPACE_ROOT / creds_path

    creds = Credentials.from_service_account_file(str(full_creds_path), scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service, sheet_id, sheet_tab


def build_notities(c):
    parts = []
    if c["channel"] == "instagram":
        parts.append("Kanaal: Instagram.")
    else:
        parts.append("Kanaal: E-mail (geen Instagram gevonden).")

    parts.append(f"{c['popup_variant']} variant.")

    land = (c.get("land") or "").strip()
    if land and land.lower() not in {"nederland", "belgie", "belgië", "nl", "be"}:
        parts.append(f"Land: {land}.")

    if c["channel"] == "email":
        parts.append(f"E-mail: {c['email']}.")

    return " ".join(parts)


def build_sheet_row(c):
    handle = "@" + c["instagram"].lower().lstrip("@") if c["channel"] == "instagram" else ""
    return [c["name"], handle, c["url"], c["niche"], "Te versturen", "", "", "", build_notities(c), ""]


def get_banded_range_info(service, sheet_id, sheet_tab):
    """Zoekt de bandedRangeId en huidige range op via de sheet-metadata — het
    ID staat NIET vast en moet elke keer opnieuw worden opgezocht."""
    meta = service.spreadsheets().get(
        spreadsheetId=sheet_id,
        fields="sheets(properties(sheetId,title),bandedRanges)",
    ).execute()
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["title"] == sheet_tab:
            gid = sheet["properties"]["sheetId"]
            banded_ranges = sheet.get("bandedRanges", [])
            if not banded_ranges:
                return gid, None, None
            br = banded_ranges[0]
            return gid, br["bandedRangeId"], br["range"]
    raise ValueError(f"Tabblad '{sheet_tab}' niet gevonden in spreadsheet-metadata")


def extend_banding(service, sheet_id, gid, banded_range_id, existing_range, new_row_count):
    """Breidt de rijstriping (banding) uit tot het nieuwe totale rijaantal.
    Dit gebeurt NIET automatisch bij bulk-toevoegen via values().update()."""
    new_range = dict(existing_range)
    new_range["sheetId"] = gid
    new_range["endRowIndex"] = new_row_count
    body = {
        "requests": [{
            "updateBanding": {
                "bandedRange": {"bandedRangeId": banded_range_id, "range": new_range},
                "fields": "range",
            }
        }]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()


def append_qualified_to_sheet(qualified):
    """Voegt gekwalificeerde nieuwe prospects toe aan de sheet (A:J) en breidt
    de banding uit. Startrij = huidig aantal rijen + 1 (voorkomt de eerder
    opgetreden 'blanco gat'-bug bij verkeerd berekende startrijen)."""
    if not qualified:
        return {"appended": 0}

    service, sheet_id, sheet_tab = _get_sheet_service()

    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{sheet_tab}!A:A"
    ).execute()
    current_rows = len(result.get("values", []))
    start_row = current_rows + 1

    rows = [build_sheet_row(c) for c in qualified]
    end_row = start_row + len(rows) - 1
    range_name = f"{sheet_tab}!A{start_row}:J{end_row}"

    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    gid, banded_range_id, existing_range = get_banded_range_info(service, sheet_id, sheet_tab)
    banded = False
    if banded_range_id is not None:
        extend_banding(service, sheet_id, gid, banded_range_id, existing_range, end_row)
        banded = True

    return {"appended": len(rows), "start_row": start_row, "end_row": end_row, "banded_range_extended": banded}


# ============================================================================
# CLI
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Verifieer en (optioneel) voeg outreach-prospects toe aan de Google Sheet.")
    parser.add_argument("candidates_file", help='JSON-bestand: [{"name":.., "url":.., "niche":.., "land": optioneel}, ...]')
    parser.add_argument("--output", default=str(WORKSPACE_ROOT / ".tmp" / "source_prospects_results.json"))
    parser.add_argument("--append", action="store_true", help="Voeg gekwalificeerde nieuwe prospects daadwerkelijk toe aan de Google Sheet")
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

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"qualified": qualified, "dropped": dropped, "duplicates": duplicates}, f, ensure_ascii=False, indent=2)

    print()
    print(f"Totaal: {len(results)} geverifieerd | Qualified: {len(qualified)} | Dropped: {len(dropped)}")
    print(f"Resultaten opgeslagen in: {output_path}")
    print()
    print(SCREENING_REMINDER)

    mismatches = [r for r in qualified if r.get("flag_domain_mismatch")]
    if mismatches:
        print(f"\nAfwijkend e-maildomein gevonden bij {len(mismatches)} kandidaten (mogelijk groter moederbedrijf) - handmatig checken:")
        for r in mismatches:
            print(f"  - {r['name']} ({r['url']}) -> e-mail: {r.get('email')}")

    if args.append:
        if not qualified:
            print("\nGeen gekwalificeerde nieuwe prospects om toe te voegen.")
            return
        print(f"\n--append: {len(qualified)} prospects toevoegen aan de sheet...")
        append_result = append_qualified_to_sheet(qualified)
        print(f"Toegevoegd: {append_result['appended']} rijen (rij {append_result['start_row']} t/m {append_result['end_row']})")
        print(f"Banding uitgebreid: {'ja' if append_result['banded_range_extended'] else 'nee (geen bandedRange gevonden)'}")
    else:
        print("\n(Dry-run: geen sheet-schrijfactie uitgevoerd. Gebruik --append na de handmatige screening-check hierboven.)")


if __name__ == "__main__":
    main()
