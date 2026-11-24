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

# Hoeveel van het dagbudget elke niche krijgt (besluit Oussama 16-11: iets meer focus
# op makelaars dan op installatiebedrijven). Verhouding, geen harde aantallen — werkt
# dus ook door als het dagbudget later verder opschaalt.
NICHE_GEWICHT = {"installatiebedrijven": 2, "makelaars": 3}

# (titel, branche) per niche — wordt rondgedraaid, zie _volgende_combos().
ZOEKCOMBOS = {
    "installatiebedrijven": [
        ("eigenaar", "loodgieter"), ("directeur", "installatiebedrijf"), ("eigenaar", "verwarmingsmonteur"),
        ("eigenaar", "elektricien"), ("directeur", "aannemer"), ("eigenaar", "klimaattechniek"),
        ("directeur", "bouwbedrijf"), ("eigenaar", "dakdekker"), ("mede-eigenaar", "installatietechniek"),
    ],
    # Meer makelaar- dan adviseur-combo's (besluit Oussama 17-11): verzekeringsadviseurs
    # hebben weinig te maken met opvolging van lopende aanvragen, dus die passen minder
    # goed bij het aanbod. Adviseurs blijven aanwezig (zie niche-besluit 10-11), maar
    # krijgen een kleiner deel van de rotatie dan makelaars.
    "makelaars": [
        ("makelaar", "woningen"), ("eigenaar", "makelaardij"), ("verkoopmakelaar", "woningen"),
        ("aankoopmakelaar", "woningen"), ("directeur", "makelaardij"), ("hypotheekadviseur", ""),
        ("verzekeringsadviseur", ""),
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


def _verdeel_zoekbudget(zoekbudget, niches):
    """Verdeelt het zoekbudget over de niches volgens NICHE_GEWICHT, met minstens 1
    zoekopdracht per niche (zolang het budget dat toelaat). De laatste niche krijgt
    wat er daarna nog over is, zodat er door afronding nooit budget blijft liggen."""
    gewichten = [NICHE_GEWICHT.get(n, 1) for n in niches]
    totaal_gewicht = sum(gewichten)
    verdeling = {}
    rest = zoekbudget
    for i, niche in enumerate(niches):
        resterende_niches = len(niches) - i
        if i == len(niches) - 1:
            aandeel = rest
        else:
            aandeel = max(1, round(zoekbudget * gewichten[i] / totaal_gewicht))
            aandeel = min(aandeel, rest - (resterende_niches - 1))  # laat minstens 1 over per niche hierna
        verdeling[niche] = max(0, aandeel)
        rest -= verdeling[niche]
    return verdeling


def nieuwe_dag(niches=("installatiebedrijven", "makelaars"), zoekbudget_override=None, leesbudget_override=None):
    """Hoofdfunctie achter de "Nieuwe dag"-knop. Geeft een samenvatting terug.

    zoekbudget_override/leesbudget_override: alleen invullen na expliciete, bewuste
    goedkeuring van Oussama om het dagbudget vandaag te overschrijden (bv. een kleine
    extra ronde na een slechte eerste ronde). Negeert dan het normale daglimiet, maar
    logt de acties gewoon (zie browser.py negeer_limiet), zodat latere dagen/ratio's
    kloppen. Zonder deze parameters verandert er niets aan het normale gedrag."""
    conn = get_connection()
    samenvatting = {"gevonden": 0, "gelezen": 0, "ja": 0, "twijfel": 0, "nee": 0, "fout": None}
    negeer_limiet = zoekbudget_override is not None or leesbudget_override is not None

    if limits.get_status(conn, "restricted"):
        samenvatting["fout"] = "Systeem staat gepauzeerd door een eerdere restrictiemelding."
        conn.close()
        return samenvatting

    if negeer_limiet:
        noodstop = limits.check_noodstop(conn)
        if noodstop["pauzeren"]:
            samenvatting["fout"] = noodstop["reden"]
            conn.close()
            return samenvatting
        zoekbudget = zoekbudget_override if zoekbudget_override is not None else limits.remaining_today(conn, "searches")
        leesbudget = leesbudget_override if leesbudget_override is not None else limits.remaining_today(conn, "profile_views")
    else:
        zoekbudget = limits.remaining_today(conn, "searches")
        leesbudget = limits.remaining_today(conn, "profile_views")
        if zoekbudget <= 0 or leesbudget <= 0:
            samenvatting["fout"] = "Geen zoek- of profielbezoek-budget meer over vandaag."
            conn.close()
            return samenvatting

    bestaande_urls = {r["url"] for r in wachtrij.alle_records()}

    # Zoekbudget verdelen over de actieve niches, gewogen via NICHE_GEWICHT.
    budget_per_niche = _verdeel_zoekbudget(zoekbudget, niches)
    gevonden_per_niche = {}
    for niche in niches:
        combos = _volgende_combos(niche, min(budget_per_niche[niche], zoekbudget))
        for titel, branche in combos:
            if zoekbudget <= 0:
                break
            try:
                urls = browser.zoek(conn, titel, branche, "", aantal=10, negeer_limiet=negeer_limiet)
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
        resultaten = browser.lees_batch(conn, urls_te_lezen, stil=True, negeer_limiet=negeer_limiet)
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
