"""
LinkedIn Outreach — Kwalificatie via de Claude API

Leest de ruwe profieltekst (zie browser.py lees_batch) en laat Claude beoordelen
of dit een goede prospect is voor de gekozen niche, plus de velden naam/functie/
bedrijf/locatie eruit halen (ruwe LinkedIn-scrapetekst is rommelig, daar is een
taalmodel beter in dan stringmatching). Berichtteksten zelf komen uit berichten.py
(pure templating), niet uit dit model — Claude hoeft alleen te kwalificeren en de
velden te extraheren, zie workflows/linkedin_outreach.md.

Kosten: zelfde boekhoudpatroon als apps/content/agent.py, eigen tabel linkedin_kosten.
Waarschuwing bij $7, stop bij $10 per maand (dit is een lichte classificatietaak,
dus een veel lager plafond dan de Instagram-contentagent).
"""

import json
import sys
from datetime import date
from pathlib import Path

import anthropic

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from config import get_env  # noqa: E402,F401  (laadt .env)

MODEL = "claude-sonnet-5-5"
EFFORT = "low"
PRIJZEN = {"claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5)}  # $ per 1M tokens: in, uit, cache-lezen, cache-schrijven
LIMIET, WAARSCHUWING = 10.0, 7.0

client = anthropic.Anthropic()

NICHE_REGELS = {
    "installatiebedrijven": """Doelgroep: eigenaar, directeur, mede-eigenaar of co-owner van een klein tot
middelgroot Nederlands installatiebedrijf-achtig vakbedrijf (loodgieter, elektricien,
installatietechniek, verwarmingsmonteur/HVAC, aannemer, bouwbedrijf, zonnepanelen/
duurzame energie-installateur). Deze persoon moet zelf beslissingen kunnen nemen over
automatisering (dus eigenaar/directeur, geen gewone monteur/medewerker in loondienst
bij een groot bedrijf zoals Liander, Heijmans of Vaillant).

Verdict "ja": duidelijke eigenaar/directeur-titel, bedrijf past in de niche, redelijke
bedrijfsgrootte (niet een eenmansbedrijf met nul online aanwezigheid, niet een groot
corporate bedrijf met honderden medewerkers).
Verdict "twijfel": past grotendeels maar met een kanttekening (bv. erg klein zzp-bedrijf,
grensgeval-branche zoals badkamers/zonnepanelen, geen expliciete functietitel maar sterke
indirecte signalen).
Verdict "nee": medewerker in loondienst (geen eigenaar), student, andere sector, overleden/
ter-nagedachtenis-account, of een te grote corporate werkgever.""",
    "makelaars": """Doelgroep: makelaar (verkoop/aankoop woningen), eigenaar van een makelaardij,
hypotheekadviseur of verzekeringsadviseur in Nederland, idealiter bij een klein/zelfstandig
kantoor (niet een groot landelijk filiaalkantoor waar deze persoon waarschijnlijk niet de
beslisser is).

Verdict "ja": duidelijk makelaar/adviseur/eigenaar van een klein kantoor.
Verdict "twijfel": past grotendeels maar met een kanttekening (bv. werkt bij een grote
franchiseketen maar functietitel suggereert toch zelfstandigheid, of branche net ernaast
zoals bedrijfsmakelaardij/taxateur).
Verdict "nee": medewerker in loondienst bij een grote partij zonder beslissingsmacht,
andere sector, overleden/ter-nagedachtenis-account, student.""",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["ja", "twijfel", "nee"]},
        "naam": {"type": "string"},
        "voornaam": {"type": "string"},
        "bedrijf": {"type": "string"},
        "functie": {"type": "string"},
        "locatie": {"type": "string"},
        "reden": {"type": "string"},
    },
    "required": ["verdict", "naam", "voornaam", "bedrijf", "functie", "locatie", "reden"],
    "additionalProperties": False,
}


def _kosten_tabel(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS linkedin_kosten (
        id INTEGER PRIMARY KEY, maand TEXT, model TEXT,
        invoer INTEGER, uitvoer INTEGER, cache_lees INTEGER, cache_schrijf INTEGER, usd REAL,
        gemaakt_op TEXT DEFAULT (datetime('now')))""")
    conn.commit()


def _maand():
    return date.today().strftime("%Y-%m")


def uitgegeven(conn):
    _kosten_tabel(conn)
    return conn.execute("SELECT COALESCE(SUM(usd), 0) FROM linkedin_kosten WHERE maand = ?", (_maand(),)).fetchone()[0]


def _boek(conn, resp):
    u = resp.usage
    p = PRIJZEN[MODEL]
    lees, schrijf = getattr(u, "cache_read_input_tokens", 0) or 0, getattr(u, "cache_creation_input_tokens", 0) or 0
    usd = (u.input_tokens * p[0] + u.output_tokens * p[1] + lees * p[2] + schrijf * p[3]) / 1e6
    conn.execute("INSERT INTO linkedin_kosten (maand, model, invoer, uitvoer, cache_lees, cache_schrijf, usd) VALUES (?,?,?,?,?,?,?)",
                 (_maand(), resp.model, u.input_tokens, u.output_tokens, lees, schrijf, usd))
    conn.commit()
    return usd


def budget_over(conn):
    """True als er nog ruimte is binnen het maandplafond."""
    return uitgegeven(conn) < LIMIET


def kwalificeer(conn, niche, pagina_tekst):
    """1 Claude-aanroep: verdict + geëxtraheerde velden voor 1 profiel. Gooit RuntimeError
    als het maandplafond al bereikt is (aanroeper vangt dit op en stopt de batch)."""
    _kosten_tabel(conn)
    if not budget_over(conn):
        raise RuntimeError(f"Maandlimiet LinkedIn-kwalificatie bereikt (${LIMIET:.0f}/maand).")

    regels = NICHE_REGELS[niche]
    prompt = (
        f"Hier is de ruwe (rommelige) tekst van een LinkedIn-profiel:\n\n{pagina_tekst[:3000]}\n\n"
        f"Beoordeel dit profiel voor de volgende niche:\n{regels}\n\n"
        "Geef terug: verdict (ja/twijfel/nee), naam (volledige naam van de persoon), "
        "voornaam (alleen de voornaam, voor de aanhef van een bericht), "
        "bedrijf (korte bedrijfsnaam zonder 'B.V.'/'bv' erachter als dat net zo goed weg kan), "
        "functie (korte functietitel, bv. 'Eigenaar' of 'Directeur'), locatie (plaats + provincie "
        "als die te vinden is, anders gewoon 'Nederland'), en reden (1 kort zinnetje waarom dit "
        "verdict, nuttig voor een twijfelgeval). Als het duidelijk geen fit is (nee), mogen de "
        "overige velden leeg/kort blijven."
    )
    resp = client.beta.messages.create(
        model=MODEL, max_tokens=500, output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": prompt}], betas=["server-side-fallback-2026-07-01"], fallbacks="default",
    )
    _boek(conn, resp)
    tekst = "".join(b.text for b in resp.content if b.type == "text")
    return json.loads(tekst)
