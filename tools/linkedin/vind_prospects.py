"""
LinkedIn Outreach — "Nieuwe dag"-knop: automatisch zoeken, lezen, kwalificeren, klaarzetten

Combineert browser.zoek() + browser.lees_batch() + kwalificeer.kwalificeer() +
wachtrij.nieuw() tot één aanroep vanuit apps/linkedin/cockpit.py. Doet exact wat
Oussama en Claude op 10-11-2026 handmatig deden (zoeken, profielen lezen, elk
profiel beoordelen op fit, berichten klaarzetten), maar dan met de Claude API
i.p.v. een los gesprek, zodat één knop volstaat.

Niches: installatiebedrijven + makelaars (zie niche-pivot-besluit 10-11-2026,
LinkedIn doet voorlopig beide naast elkaar, zie workflows/linkedin_outreach.md).
Zoekcombinaties roteren via .tmp/linkedin/zoek_rotatie.json zodat niet elke dag
dezelfde twee zoekopdrachten worden herhaald.

Verdict "ja" -> meteen klaar in "Te versturen". Verdict "twijfel" -> status
"Twijfel", met een eigen cockpit-sectie voor Oussama's akkoord (berichten staan
al klaar, zodat accepteren geen extra stap kost). Verdict "nee" -> genegeerd,
niet opgeslagen.

Gebruik (CLI, voor handmatig testen):
    python tools/linkedin/vind_prospects.py
"""

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_connection  # noqa: E402

import berichten  # noqa: E402
import browser  # noqa: E402
import kwalificeer  # noqa: E402
import limits  # noqa: E402
import wachtrij  # noqa: E402

ROTATIE_BESTAND = WORKSPACE_ROOT / ".tmp" / "linkedin" / "zoek_rotatie.json"

# (titel, branche) per niche — wordt rondgedraaid, zie _volgende_combos().
ZOEKCOMBOS = {
    "installatiebedrijven": [
        ("eigenaar", "loodgieter"), ("directeur", "installatiebedrijf"), ("eigenaar", "verwarmingsmonteur"),
        ("eigenaar", "elektricien"), ("directeur", "aannemer"), ("eigenaar", "klimaattechniek"),
        ("directeur", "bouwbedrijf"), ("eigenaar", "dakdekker"), ("mede-eigenaar", "installatietechniek"),
    ],
    "makelaars": [
        ("makelaar", "woningen"), ("eigenaar", "makelaardij"), ("hypotheekadviseur", ""),
        ("verzekeringsadviseur", ""), ("directeur", "hypotheekadvies"), ("eigenaar", "assurantiekantoor"),
    ],
}


def _rotatie_lezen():
    if ROTATIE_BESTAND.exists():
        return json.loads(ROTATIE_BESTAND.read_text(encoding="utf-8"))
    return {}


def _rotatie_schrijven(stand):
    ROTATIE_BESTAND.parent.mkdir(parents=True, exist_ok=True)
    ROTATIE_BESTAND.write_text(json.dumps(stand, ensure_ascii=False, indent=2), encoding="utf-8")


def _volgende_combos(niche, aantal):
    """Geeft de volgende `aantal` combo's voor deze niche, roteert daarna de pointer verder."""
    stand = _rotatie_lezen()
    pool = ZOEKCOMBOS[niche]
    start = stand.get(niche, 0) % len(pool)
    combos = [pool[(start + i) % len(pool)] for i in range(aantal)]
    stand[niche] = (start + aantal) % len(pool)
    _rotatie_schrijven(stand)
    return combos


def nieuwe_dag(niches=("installatiebedrijven", "makelaars")):
    """Hoofdfunctie achter de "Nieuwe dag"-knop. Geeft een samenvatting terug."""
    conn = get_connection()
    samenvatting = {"gevonden": 0, "gelezen": 0, "ja": 0, "twijfel": 0, "nee": 0, "fout": None}

    if limits.get_status(conn, "restricted"):
        samenvatting["fout"] = "Systeem staat gepauzeerd door een eerdere restrictiemelding."
        conn.close()
        return samenvatting

    zoekbudget = limits.remaining_today(conn, "searches")
    leesbudget = limits.remaining_today(conn, "profile_views")
    if zoekbudget <= 0 or leesbudget <= 0:
        samenvatting["fout"] = "Geen zoek- of profielbezoek-budget meer over vandaag."
        conn.close()
        return samenvatting

    bestaande_urls = {r["url"] for r in wachtrij.alle_records()}

    # Zoekbudget verdelen over de actieve niches (minstens 1 zoekopdracht per niche indien mogelijk).
    per_niche = max(1, zoekbudget // len(niches))
    gevonden_per_niche = {}
    for niche in niches:
        combos = _volgende_combos(niche, min(per_niche, zoekbudget))
        for titel, branche in combos:
            if zoekbudget <= 0:
                break
            try:
                urls = browser.zoek(conn, titel, branche, "", aantal=10)
            except RuntimeError as e:
                samenvatting["fout"] = str(e)
                break
            zoekbudget -= 1
            for u in urls:
                if u not in bestaande_urls:
                    gevonden_per_niche.setdefault(niche, [])
                    if u not in gevonden_per_niche[niche]:
                        gevonden_per_niche[niche].append(u)
                        bestaande_urls.add(u)

    totaal_nieuw = sum(len(v) for v in gevonden_per_niche.values())
    samenvatting["gevonden"] = totaal_nieuw
    if totaal_nieuw == 0:
        conn.close()
        return samenvatting

    for niche, urls in gevonden_per_niche.items():
        urls_te_lezen = urls[:leesbudget]
        if not urls_te_lezen:
            continue
        resultaten = browser.lees_batch(conn, urls_te_lezen, stil=True)
        leesbudget -= len(resultaten)
        berichten_fn = berichten.PER_NICHE[niche]

        for resultaat in resultaten:
            if "fout" in resultaat:
                continue
            samenvatting["gelezen"] += 1
            try:
                oordeel = kwalificeer.kwalificeer(conn, niche, resultaat["pagina_tekst"])
            except RuntimeError as e:
                samenvatting["fout"] = str(e)
                break

            if oordeel["verdict"] == "nee":
                samenvatting["nee"] += 1
                continue

            b1, b2, b3 = berichten_fn(oordeel["voornaam"], oordeel["bedrijf"])
            status = "Te versturen" if oordeel["verdict"] == "ja" else "Twijfel"
            wachtrij.nieuw({
                "naam": oordeel["naam"],
                "functie": oordeel["functie"], "bedrijf": oordeel["bedrijf"], "locatie": oordeel["locatie"],
                "url": resultaat["url"], "connectienotitie": "", "bericht1": b1, "bericht2": b2, "bericht3": b3,
                "notities": f"[{niche}] {oordeel['reden']}", "status": status,
            })
            samenvatting["ja" if status == "Te versturen" else "twijfel"] += 1

    conn.close()
    return samenvatting


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(nieuwe_dag(), ensure_ascii=False, indent=2))
