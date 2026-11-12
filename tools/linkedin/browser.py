"""
LinkedIn Outreach — Browserautomatisering (zoeken, lezen, acceptatie-check)

Gebruikt Playwright met een PERSISTENTE, handmatig ingelogde sessie (Oussama's
eigen LinkedIn-account). Dit script verstuurt NOOIT een connectieverzoek of
bericht — dat blijft altijd een handmatige klik via apps/linkedin/cockpit.py.
Het levert alleen ruwe feiten; kwalificeren en tekst schrijven is agent-werk
(zie workflows/linkedin_outreach.md, stap "Kwalificatie").

Elke actie respecteert het daglimiet uit tools/linkedin/limits.py en wordt daar
meteen gelogd. Bij een restrictiemelding/CAPTCHA van LinkedIn stopt het script
direct en zet een vlag die apps/linkedin/cockpit.py bovenaan toont.

LET OP (eerlijke beperking): de CSS-selectors hieronder zijn gebaseerd op
LinkedIn's bekende paginastructuur, maar LinkedIn wijzigt die regelmatig. Dit
script is nog niet getest tegen de live site (geen netwerktoegang vanuit deze
omgeving) — de eerste echte run (stap 12 van het implementatieplan) dient ook
als calibratieronde. Zie workflows/linkedin_outreach.md voor wat te doen als
een selector niets oplevert.

Gebruik (CLI):
    python tools/linkedin/browser.py login
    python tools/linkedin/browser.py zoek --titel "eigenaar OR directeur" --branche "loodgieter" --regio "Noord-Holland" --aantal 20
    python tools/linkedin/browser.py zoek --urls-bestand .tmp/linkedin_urls.txt
    python tools/linkedin/browser.py lees <profiel-url>
    python tools/linkedin/browser.py lees --batch-bestand .tmp/linkedin_zoekresultaten.json
    python tools/linkedin/browser.py check
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_DIR = WORKSPACE_ROOT / ".tmp" / "linkedin-session"
DEFAULT_ZOEK_OUTPUT = WORKSPACE_ROOT / ".tmp" / "linkedin_zoekresultaten.json"

sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_connection  # noqa: E402
import limits  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise ImportError("Ontbrekend package — draai: pip install playwright && playwright install chromium")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
VIEWPORT = {"width": 1440, "height": 900}

# Tekstpatronen die wijzen op een restrictie-/verificatiepagina van LinkedIn.
RESTRICTIE_PATRONEN = [
    "we've restricted", "we have restricted", "temporarily restricted",
    "unusual activity", "please verify", "security verification",
    "quick security check", "let's do a quick security check",
    "checkpoint/challenge",
]


def _delay(a=2.0, b=5.0):
    time.sleep(random.uniform(a, b))


def _detect_restriction(page):
    try:
        url = page.url.lower()
        tekst = page.inner_text("body").lower()
    except Exception:
        return None
    for patroon in RESTRICTIE_PATRONEN:
        if patroon in url or patroon in tekst:
            return patroon
    return None


def _stop_op_restrictie(conn, patroon):
    limits.set_status(conn, "restricted", "1")
    limits.set_status(conn, "restricted_reason", f"Gedetecteerd patroon: '{patroon}'")
    print(f"\n[RESTRICTIE GEDETECTEERD] '{patroon}' — script stopt direct.")
    print("Handmatig bevestigen vereist: python tools/linkedin/limits.py check (en los het op in de browser), "
          "daarna python -c \"import tools.linkedin.limits as l, scripts.db as db; l.clear_restriction(db.get_connection())\"")


def _context(headless=True):
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    p = sync_playwright().start()
    ctx = p.chromium.launch_persistent_context(
        str(SESSION_DIR),
        headless=headless,
        viewport=VIEWPORT,
        user_agent=USER_AGENT,
    )
    return p, ctx


# ============================================================================
# login — eenmalige handmatige login, sessie wordt lokaal opgeslagen
# ============================================================================
def cmd_login(timeout_sec=600):
    """Wacht automatisch tot de login gelukt is (geen input() — werkt ook als dit script
    zonder aangesloten terminal-stdin draait, bv. als achtergrondproces)."""
    print("Er opent een browservenster. Log zelf in op LinkedIn (incl. je eigen 2FA).")
    print(f"Dit script wacht automatisch tot je bent ingelogd (max {timeout_sec // 60} minuten).")
    p, ctx = _context(headless=False)
    page = ctx.new_page()
    page.goto("https://www.linkedin.com/login")

    gestart = time.time()
    while time.time() - gestart < timeout_sec:
        try:
            if "linkedin.com/feed" in page.url or "linkedin.com/mynetwork" in page.url:
                print("Login gedetecteerd (doorgestuurd naar feed/mynetwork).")
                break
            cookies = ctx.cookies("https://www.linkedin.com")
            if any(c["name"] == "li_at" for c in cookies):
                print("Login gedetecteerd (sessie-cookie aanwezig).")
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        print(f"Nog niet ingelogd na {timeout_sec // 60} minuten — sessie wordt alsnog opgeslagen zoals die nu is.")

    ctx.close()
    p.stop()
    print("Sessie opgeslagen in .tmp/linkedin-session/. Volgende keer kan dit script headless draaien.")


# ============================================================================
# zoek — standaard LinkedIn people-search (geen Sales Navigator, zie plan)
# ============================================================================
def _zoek_url(titel, branche, regio, page_nr=1):
    # Gecalibreerd op 2026-11-09 tegen de live site: simpele combinaties (bv. "eigenaar
    # loodgieter") geven relevante resultaten, maar een letterlijk "OR" of de regio
    # meeplakken in de keywords verdunt de relevantie fors (LinkedIn's keyword-zoek is
    # fuzzy, geen echte boolean search). Regio wordt daarom NIET in de zoekopdracht
    # gestopt — dat wordt gecontroleerd tijdens het kwalificeren (stap 5), met de
    # daadwerkelijke locatie uit het gelezen profiel.
    keywords = " ".join(x for x in [titel, branche] if x)
    from urllib.parse import quote
    return f"https://www.linkedin.com/search/results/people/?keywords={quote(keywords)}&origin=GLOBAL_SEARCH_HEADER&page={page_nr}"


def zoek(conn, titel, branche, regio="", aantal=20):
    """Zoekt op LinkedIn's standaard people-search en geeft gevonden profiel-urls terug
    (zonder duplicaten). Logt 1 'search'-actie bij limits, ongeacht hoeveel pagina's er
    intern doorlopen worden. Gooit RuntimeError als het daglimiet al bereikt is."""
    toegestaan, reden = limits.can_act(conn, "searches")
    if not toegestaan:
        raise RuntimeError(reden)

    p, ctx = _context(headless=True)
    page = ctx.new_page()
    gevonden = []
    try:
        for page_nr in range(1, 11):  # LinkedIn's eigen paginalimiet; stopt eerder zodra aantal gehaald is
            url = _zoek_url(titel, branche, regio, page_nr)
            page.goto(url)
            _delay()

            patroon = _detect_restriction(page)
            if patroon:
                _stop_op_restrictie(conn, patroon)
                break

            # LinkedIn's zoekresultatenpagina bevat ook /in/-links buiten de eigenlijke
            # resultatenlijst (bv. "andere suggesties"-zijbalk). Die links hebben alleen
            # de naam als tekst (kort), de echte resultaatkaarten bevatten ook functie +
            # bedrijf (tekstlengte >180 in de praktijk) — gecalibreerd op 2026-11-09 tegen
            # de live site. Drempel van 50 laat ruim marge over naar de korte suggesties.
            links = page.eval_on_selector_all(
                "a[href*='/in/']",
                "els => els.map(e => ({href: e.href, lengte: (e.textContent || '').trim().length}))",
            )
            beste = {}
            for l in links:
                href = l["href"].split("?")[0]
                if l["lengte"] > beste.get(href, -1):
                    beste[href] = l["lengte"]
            nieuw = [href for href, lengte in beste.items() if lengte > 50]
            for l in nieuw:
                if l not in gevonden:
                    gevonden.append(l)

            if len(gevonden) >= aantal or not nieuw:
                break
            _delay()
    finally:
        ctx.close()
        p.stop()

    gevonden = gevonden[:aantal]
    limits.log_action(conn, "search", ref=f"{titel} | {branche} | {regio}")
    return gevonden


def cmd_zoek(args):
    conn = get_connection()

    if args.urls_bestand:
        urls = [u.strip() for u in Path(args.urls_bestand).read_text(encoding="utf-8").splitlines() if u.strip()]
        urls = list(dict.fromkeys(urls))  # dedup, volgorde behouden
        output = {"bron": "urls_bestand", "bestand": args.urls_bestand, "urls": urls, "gevonden_op": datetime.now(timezone.utc).isoformat()}
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{len(urls)} profiel-URL's uit {args.urls_bestand} overgenomen (geen zoekbudget gebruikt) -> {args.output}")
        conn.close()
        return

    try:
        gevonden = zoek(conn, args.titel, args.branche, args.regio, args.aantal)
    except RuntimeError as e:
        print(f"Geblokkeerd: {e}")
        conn.close()
        sys.exit(1)

    output = {
        "bron": "zoeken", "titel": args.titel, "branche": args.branche, "regio": args.regio,
        "urls": gevonden, "gevonden_op": datetime.now(timezone.utc).isoformat(),
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(gevonden)} profiel-URL's gevonden -> {args.output}")
    conn.close()


# ============================================================================
# lees — profiel openen, ruwe tekst teruggeven (Claude kwalificeert, niet dit script)
# ============================================================================
def _lees_profiel(page, conn, url):
    toegestaan, reden = limits.can_act(conn, "profile_views")
    if not toegestaan:
        return {"url": url, "fout": reden}

    page.goto(url)
    _delay()

    patroon = _detect_restriction(page)
    if patroon:
        _stop_op_restrictie(conn, patroon)
        return {"url": url, "fout": f"restrictie gedetecteerd: {patroon}"}

    try:
        # Bevat naam, functie, bedrijf, locatie EN de about-tekst (geen apart #about-element
        # gevonden bij calibratie op 2026-11-09 — de about-paragraaf staat gewoon in de
        # normale paginatekst van <main>, dus geen losse selector nodig).
        top_card = page.inner_text("main")
    except Exception:
        top_card = ""

    limits.log_action(conn, "profile_view", ref=url)
    return {
        "url": url,
        "pagina_tekst": top_card[:4000],
        "gelezen_op": datetime.now(timezone.utc).isoformat(),
    }


def lees_batch(conn, urls, stil=False):
    """Leest een lijst profiel-urls uit, stopt bij een restrictie of een leeg daglimiet.
    Geeft de ruwe resultatenlijst terug (zie _lees_profiel: url/pagina_tekst of url/fout)."""
    p, ctx = _context(headless=True)
    page = ctx.new_page()
    resultaten = []
    try:
        for url in urls:
            resultaat = _lees_profiel(page, conn, url)
            resultaten.append(resultaat)
            if not stil:
                print(f"[{'OK' if 'fout' not in resultaat else 'FOUT'}] {url}")
            if "fout" in resultaat:
                if not stil:
                    print(f"  gestopt: {resultaat['fout']}")
                break
            _delay()
    finally:
        ctx.close()
        p.stop()
    return resultaten


def cmd_lees(args):
    conn = get_connection()
    urls = [args.url] if args.url else json.loads(Path(args.batch_bestand).read_text(encoding="utf-8"))["urls"]

    resultaten = lees_batch(conn, urls)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(resultaten, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(resultaten)} profielen verwerkt -> {args.output}")
    conn.close()


# ============================================================================
# check — eigen "verzonden uitnodigingen" + connecties bekijken (acceptatie-detectie)
# ============================================================================
def check(conn=None):
    """Checkt LinkedIn's eigen 'verzonden uitnodigingen' + connecties-pagina en
    werkt de lokale database bij. Geeft de urls terug die van status veranderd
    zijn, zodat een aanroeper (bv. apps/linkedin/cockpit.py) dat ook meteen naar
    de Google Sheet kan doorschrijven i.p.v. alleen de lokale db."""
    eigen_conn = conn is None
    if eigen_conn:
        conn = get_connection()
    try:
        if limits.get_status(conn, "restricted"):
            return {"fout": "Systeem staat gepauzeerd door een eerdere restrictiemelding (zie limits.check_noodstop)."}

        p, ctx = _context(headless=True)
        page = ctx.new_page()
        try:
            page.goto("https://www.linkedin.com/mynetwork/invitation-manager/sent/")
            _delay()
            patroon = _detect_restriction(page)
            if patroon:
                _stop_op_restrictie(conn, patroon)
                return {"fout": f"restrictie gedetecteerd: {patroon}"}
            try:
                verzonden_namen = page.eval_on_selector_all(
                    "a[href*='/in/']", "els => els.map(e => e.href.split('?')[0])"
                )
            except Exception:
                verzonden_namen = []
            verzonden_set = set(verzonden_namen)

            page.goto("https://www.linkedin.com/mynetwork/invite-connect/connections/")
            _delay()
            try:
                connectie_urls = page.eval_on_selector_all(
                    "a[href*='/in/']", "els => els.map(e => e.href.split('?')[0])"
                )
            except Exception:
                connectie_urls = []
            connectie_set = set(connectie_urls)
        finally:
            ctx.close()
            p.stop()

        if not _row_table_exists(conn):
            return {"fout": "Tabel 'linkedin' bestaat nog niet (draai eerst scripts/collect_linkedin.py)."}

        rijen = conn.execute("SELECT naam, url FROM linkedin WHERE status = 'Verzoek verstuurd'").fetchall()
        geaccepteerd_urls, verlopen_urls = [], []
        for rij in rijen:
            if rij["url"] in verzonden_set:
                continue
            if rij["url"] in connectie_set:
                conn.execute("UPDATE linkedin SET status = 'Geaccepteerd' WHERE url = ?", (rij["url"],))
                geaccepteerd_urls.append(rij["url"])
            else:
                conn.execute("UPDATE linkedin SET status = 'Verlopen' WHERE url = ?", (rij["url"],))
                verlopen_urls.append(rij["url"])
        conn.commit()
        return {
            "geaccepteerd": geaccepteerd_urls,
            "verlopen": verlopen_urls,
            "nog_in_afwachting": len(rijen) - len(geaccepteerd_urls) - len(verlopen_urls),
        }
    finally:
        if eigen_conn:
            conn.close()


def cmd_check():
    resultaat = check()
    if "fout" in resultaat:
        print(resultaat["fout"])
        return
    print(f"Check voltooid: {len(resultaat['geaccepteerd'])} geaccepteerd, {len(resultaat['verlopen'])} verlopen/ingetrokken, "
          f"{resultaat['nog_in_afwachting']} nog in afwachting.")
    print("Let op: dit werkt alleen de lokale database bij. Zet dezelfde statussen ook in de Google Sheet via "
          "tools/linkedin/wachtrij.py zodat ze niet weer overschreven worden door de volgende collect_linkedin.py-sync.")


def _row_table_exists(conn):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='linkedin'"
    ).fetchone() is not None


# ============================================================================
# CLI
# ============================================================================
def main():
    ap = argparse.ArgumentParser(description="LinkedIn-browserautomatisering: zoeken, lezen, acceptatie-check.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("login")

    z = sub.add_parser("zoek")
    z.add_argument("--titel", default="")
    z.add_argument("--branche", default="")
    z.add_argument("--regio", default="")
    z.add_argument("--aantal", type=int, default=20)
    z.add_argument("--urls-bestand", default=None)
    z.add_argument("--output", default=str(DEFAULT_ZOEK_OUTPUT))

    l = sub.add_parser("lees")
    l.add_argument("url", nargs="?", default=None)
    l.add_argument("--batch-bestand", default=None)
    l.add_argument("--output", default=str(WORKSPACE_ROOT / ".tmp" / "linkedin_profielen.json"))

    sub.add_parser("check")

    args = ap.parse_args()

    if args.cmd == "login":
        cmd_login()
    elif args.cmd == "zoek":
        cmd_zoek(args)
    elif args.cmd == "lees":
        if not args.url and not args.batch_bestand:
            sys.exit("Geef een profiel-URL of --batch-bestand op.")
        cmd_lees(args)
    elif args.cmd == "check":
        cmd_check()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
