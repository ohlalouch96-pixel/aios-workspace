# Workflow: LinkedIn Outreach

## Doel

Nieuwe MKB-installatiebedrijven (loodgieters, schilders, stukadoors, aannemers,
installatietechniek, bouwbedrijven) vinden op LinkedIn, kwalificeren, en
klaarzetten zodat Oussama zelf het connectieverzoek + openingsbericht verstuurt
— zonder dat een bot ooit zelf iets verstuurt. Derde outreach-spoor naast
webshops (`outreach`-tabel) en vakbedrijven (`ondernemers`-tabel).

**Scope van de eerste ronde:** alleen nieuwe prospects (geen overlap met de
`ondernemers`-tracker), regio **Noord-Holland** (daarna olievlek-uitbreiding
naar aangrenzende provincies — handmatig besluit, geen automatische regel).

## Architectuur in één oogopslag

```
tools/linkedin/browser.py   zoeken + profielen lezen + acceptatie-check (Playwright, persistente sessie)
tools/linkedin/limits.py    opbouwschema, daglimieten, noodstop
tools/linkedin/wachtrij.py  schrijft/leest de Google Sheet "linkedin-tracker"
apps/linkedin/cockpit.py    lokale webcockpit (127.0.0.1) — kaarten + knoppen + dashboard
scripts/collect_linkedin.py sync Sheet -> data.db (tabel `linkedin`), alleen-lezend
```

Geen Telegram voor dit kanaal (kostenoverweging, zie plan). De Instagram-
contentbot blijft ongewijzigd op Telegram draaien.

## Stappenketen

### 1. Zoeken (tool: `browser.py zoek`)

```
python tools/linkedin/browser.py zoek --titel "eigenaar OR directeur OR zaakvoerder OR oprichter" --branche "loodgieter" --regio "Noord-Holland" --aantal 20
```

Herhaal met andere branchewoorden (schilder, stukadoor, aannemer,
installatietechniek, bouwbedrijf) — dit is bewust een standaard LinkedIn
people-search op losse zoekwoorden, geen gestructureerde filter-automatisering
(geoUrn/industrie-codes), omdat dat betrouwbaarder is tegen een UI die
regelmatig wijzigt. Respecteert het dagbudget uit `limits.py` automatisch.

**Sales Navigator-proefperiode (tot ca. 2026-11-30):** gebruik in plaats
hiervan `--urls-bestand <lijst.txt>` met profiel-URL's die je zelf uit je
Sales Navigator-zoekresultaten hebt gekopieerd. Geen zoekbudget verbruikt,
wel een voorraad opbouwen voor als de proefperiode afloopt.

### 2. Lezen (tool: `browser.py lees`)

```
python tools/linkedin/browser.py lees --batch-bestand .tmp/linkedin_zoekresultaten.json
```

Levert per profiel de volledige paginatekst (naam, functie, bedrijf, locatie
én de about-paragraaf — die staat gewoon in de normale paginatekst, geen losse
sectie) in `.tmp/linkedin_profielen.json` — dit script interpreteert niets,
dat is de volgende stap.

### 3. Kwalificeren + conceptteksten schrijven (agent-werk, GEEN script)

Claude beoordeelt elk profiel uit stap 2 tegen de doelgroepcriteria:
- Functie: eigenaar, directeur, zaakvoerder of oprichter.
- Branche: installatiebedrijf-achtig (loodgieter, schilder, stukadoor,
  aannemer, installatietechniek, bouwbedrijf).
- Regio: binnen de actuele olievlek-grens (nu: Noord-Holland).

Afgekeurde profielen gaan NIET naar de sheet (zelfde filosofie als
`tools/source_prospects.py`). Voor goedgekeurde profielen schrijft Claude:
- **Connectienotitie: geen.** Op verzoek van Oussama (09-11) wordt het
  connectieverzoek altijd leeg verstuurd, geen bijgevoegde tekst. De cockpit
  toont geen notitie-blok als `connectienotitie` leeg is.
- Een openingsbericht ("Bericht 1", wordt pas na acceptatie verstuurd) — vast
  sjabloon, zie hieronder.

**Vaste sjabloon bericht 1** (vastgelegd 2026-11-09, zie ook
`outputs/outreach-ondernemers-email-strategie.md` → sectie "LinkedIn-variant"
voor de volledige geschiedenis/herzieningen):

```
Dag [voornaam],
Bedankt voor het accepteren! Ik volg wat installatiebedrijven in de regio bezighoudt.
Hoe loopt het bij [bedrijfsnaam] op dit moment, veel aanvragen binnen of relatief rustig?
```

Regels: "Dag [voornaam]," als aanhef (geen "Hoi", geen Goedemorgen/middag/avond
— een LinkedIn-bericht wordt vaak uren/dagen later gelezen). Geen gedachtestreepjes.
Enters zonder lege regel ertussen. De middelste zin ("Ik volg wat
installatiebedrijven in de regio bezighoudt") is vast voor ALLE kandidaten,
niet aanpassen. De slotvraag mag per branche lichtjes variëren zolang hij
specifiek-maar-open blijft (geen "Hoe gaat het?" — te vaag, geen duidelijk
onderwerp).

Bericht 2/3 en de follow-upreeks staan nog open, zie "Nog niet ingevuld".

### 4. In de wachtrij zetten (tool: `wachtrij.py`, aangeroepen door de agent)

```python
import sys; sys.path.insert(0, "tools/linkedin")
import wachtrij
wachtrij.nieuw({"naam": ..., "functie": ..., "bedrijf": ..., "locatie": ...,
                 "url": ..., "connectienotitie": ..., "bericht1": ...})
```

Status wordt automatisch `Te versturen`.

### 5. Versturen (cockpit, mens-in-de-lus)

```
python apps/linkedin/cockpit.py
```

Open `http://127.0.0.1:5050`. Oussama bekijkt elke kaart, stuurt het
connectieverzoek + notitie ZELF op LinkedIn, en bevestigt met **✅ Verstuurd**.
Dat werkt de Sheet bij én logt de actie meteen lokaal (daglimiet blijft
actueel binnen de sessie, zie Design Decision 10 in het plan).

### 6. Acceptatie-check (tool: `browser.py check`)

```
python tools/linkedin/browser.py check
```

Draait als eerste stap van elke sessie, vóór een nieuwe batch. Bekijkt alleen
Oussama's eigen "Verzonden uitnodigingen" en connecties-pagina (geen
informatie over anderen) en zet statussen op `Geaccepteerd` of `Verlopen`.
**Let op:** werkt alleen de lokale database bij — zet dezelfde statussen ook
via `wachtrij.status()` in de Sheet, anders overschrijft de volgende
`collect_linkedin.py`-sync het weer.

### 7. Na acceptatie: openingsbericht versturen

Zodra een rij op `Geaccepteerd` staat, verschijnt die niet automatisch opnieuw
in de cockpit als "te versturen" — dit is nog een open punt (zie "Nog niet
ingevuld"): een aparte sectie "Geaccepteerd — bericht 1 klaarzetten" moet nog
aan de cockpit toegevoegd worden zodra de berichtinhoud is vastgesteld.

### 8. Follow-ups

`wachtrij.due_follow_ups()` + de cockpit-sectie "Follow-ups due" tonen wie aan
de beurt is. Inhoud van de follow-upberichten: zie "Nog niet ingevuld".

### 9. Dashboard

`scripts/collect.py` (draait `collect_linkedin.py` automatisch mee) +
`scripts/generate_metrics.py` houden `context/key-metrics.md` actueel. De
cockpit toont dezelfde cijfers direct op de hoofdpagina.

## Opbouwschema daglimieten

| Week | Connectieverzoeken/dag | Profielbezoeken/dag | Zoekopdrachten/dag | Voorwaarde om door te gaan |
| --- | --- | --- | --- | --- |
| 1 | 8 | 25 | 5 | Geen restrictiemelding gezien |
| 2 | 12 | 35 | 8 | Acceptatieratio ≥30% over week 1, geen restrictie |
| 3 | 15 | 45 | 10 | Acceptatieratio ≥30% over week 2, geen restrictie |
| 4 | 18 | 50 | 10 | Acceptatieratio ≥30% over week 3, geen restrictie |
| 5+ (plateau) | 20 | 60 | 12 | Blijft op dit niveau |

`tools/linkedin/limits.py` berekent dit automatisch (`current_week_limits`) en
schaalt NIET door als de voorwaarde niet gehaald is.

## Noodstop-regels

- Acceptatieratio over de laatste 20 verzonden connectieverzoeken <15% →
  automatisch pauzeren (nieuwe connectieverzoeken), zichtbaar in de cockpit.
- LinkedIn-restrictiemelding/CAPTCHA/verificatieverzoek gedetecteerd → direct
  en volledig stoppen (ook zoeken/lezen). Herstarten pas na handmatige
  bevestiging: `limits.clear_restriction(conn)`.
- Twee opeenvolgende dagen zonder acceptaties → waarschuwing, geen harde pauze.

## Nog niet ingevuld (bewust uitgesteld, zie het implementatieplan)

- **Berichtinhoud/aanbod-strategie**: de definitieve tekst/toon voor de
  connectienotitie, het openingsbericht en de follow-upreeks. Moet aansluiten
  bij de bestaande `/vakbedrijven`-positionering (offertetijd, administratie,
  klantcontact), niet bij cart-recovery-taal.
- **"Geaccepteerd" → "Bericht 1 klaarzetten"-sectie** in de cockpit (stap 7
  hierboven) — wachtte op de berichtinhoud om zinvol te kunnen bouwen.
- **Volledige follow-upreeks (meerdere stappen)**: de sheet heeft nu één
  "Volgende follow-up (due)"-kolom; wordt uitgebreid zodra het aantal/timing
  van follow-upstappen vastligt.

## Bekende valkuilen / eerlijke beperkingen

- De CSS-selectors in `browser.py` zijn gebaseerd op LinkedIn's bekende
  paginastructuur maar NIET getest tegen de live site (geen netwerktoegang
  vanuit de bouwomgeving). De eerste echte run is ook een calibratieronde —
  als `zoek`/`lees`/`check` niets of onzin opleveren, eerst de selectors in
  `browser.py` controleren tegen de daadwerkelijke pagina (rechtermuisknop →
  Inspecteren) voordat er iets anders aan de architectuur verandert.
- Gratis LinkedIn-account: let op de maandelijkse "Commercial Use Limit" op
  zoekopdrachten/profielbezoeken. Als zoeken plotseling niets meer oplevert
  zonder duidelijke reden, kan dit de oorzaak zijn — dan pauzeren tot de
  volgende maand, niet proberen te omzeilen.
- `browser.py check` leunt op het verdwijnen van een naam uit de "Verzonden
  uitnodigingen"-lijst. Als LinkedIn die pagina herontwerpt, moet de selector
  bijgewerkt worden.
