# Workflow: LinkedIn Outreach

## Doel

Nieuwe MKB-prospects vinden op LinkedIn, kwalificeren, en klaarzetten zodat
Oussama zelf het connectieverzoek + openingsbericht verstuurt — zonder dat een
bot ooit zelf iets verstuurt. Derde outreach-spoor naast webshops
(`outreach`-tabel) en vakbedrijven (`ondernemers`-tabel).

**Twee niches naast elkaar (sinds 10-11-2026):**
- **Installatiebedrijven** (loodgieters, schilders, stukadoors, aannemers,
  installatietechniek, bouwbedrijven) — de oorspronkelijke niche.
- **Makelaars + hypotheek-/verzekeringsadviseurs** — toegevoegd na de
  niche-pivot op de `ondernemers`-tracker (zie geheugen `project_niche_pivot_
  makelaars`). Die pivot gold specifiek voor bellen/mailen (nul conversie
  daar); LinkedIn presteert anders (snelle acceptaties, eerste reacties), dus
  op verzoek van Oussama (12-11) blijft installatiebedrijven hier WEL actief,
  naast makelaars.

**Scope:** alleen nieuwe prospects (geen overlap met de `ondernemers`-tracker).
Regio **heel Nederland** (besluit Oussama, 09-11 — de olievlek-fase vanuit
Noord-Holland is overgeslagen na de eerste testronde).

## Architectuur in één oogopslag

```
tools/linkedin/browser.py       zoek()/lees_batch()/check() — Playwright, persistente sessie
tools/linkedin/limits.py        opbouwschema, daglimieten, noodstop
tools/linkedin/wachtrij.py      schrijft/leest de Google Sheet "linkedin-tracker"
tools/linkedin/berichten.py     berichtsjablonen per niche (pure templating)
tools/linkedin/kwalificeer.py   Claude API: beoordeelt 1 profiel (ja/twijfel/nee), kostenlog
tools/linkedin/vind_prospects.py  "Nieuwe dag": zoek+lees+kwalificeer+klaarzetten in 1 aanroep
apps/linkedin/cockpit.py        lokale webcockpit (127.0.0.1) — kaarten + knoppen + dashboard
scripts/collect_linkedin.py     sync Sheet -> data.db (tabel `linkedin`), alleen-lezend
```

Geen Telegram voor dit kanaal (kostenoverweging, zie plan). De Instagram-
contentbot blijft ongewijzigd op Telegram draaien.

## Stappenketen

### 1-3. Zoeken + lezen + kwalificeren (geautomatiseerd sinds 12-11: de "Nieuwe dag"-knop)

In de cockpit, bij "Te versturen": knop **"🔍 Nieuwe dag — zoek nieuwe
prospects"**. Draait `tools/linkedin/vind_prospects.py nieuwe_dag()`, duurt
1-3 minuten (echte LinkedIn-bezoeken + een Claude-aanroep per profiel):

1. **Zoeken** (`browser.zoek()`): roteert door een vaste poolt van (titel,
   branche)-combinaties per niche (zie `ZOEKCOMBOS` in `vind_prospects.py`),
   bijgehouden in `.tmp/linkedin/zoek_rotatie.json` zodat niet elke dag
   dezelfde opdracht herhaalt. Zoekbudget wordt verdeeld over de actieve
   niches. **Let op (gecalibreerd 09-11):** bewust maar twee simpele
   zoekwoorden per opdracht (titel + branche), geen "OR"-lijsten en geen
   regio in de zoekwoorden — die verdunnen de relevantie fors op LinkedIn's
   fuzzy zoekmachine. Regio wordt tijdens kwalificatie beoordeeld, niet
   vooraf gefilterd.
2. **Lezen** (`browser.lees_batch()`): leest elk nieuw gevonden profiel
   (gededupliceerd tegen de bestaande sheet) tot het daglimiet voor
   profielbezoeken.
3. **Kwalificeren** (`kwalificeer.kwalificeer()`, 1 Claude API-aanroep per
   profiel, model `claude-sonnet-5-5`, effort `low`): geeft een verdict
   (ja/twijfel/nee) + geëxtraheerde naam/functie/bedrijf/locatie terug. "ja"
   gaat direct naar "Te versturen" met berichten klaar. "Twijfel" gaat naar
   de cockpit-sectie **"Twijfelgevallen — jouw oordeel"** (berichten staan
   al klaar, 1 klik op "Toevoegen" of "Afwijzen"). "Nee" wordt genegeerd,
   niet opgeslagen. Kosten: ca. $0,007 per profiel, geboekt in
   `linkedin_kosten`, plafond $10/maand (zie `kwalificeer.LIMIET`).

**Handmatig/alternatief** (bv. voor Sales Navigator-profielen die je zelf
kopieert, of om een losse batch te draaien buiten de knop om):

```
python tools/linkedin/browser.py zoek --titel "eigenaar" --branche "loodgieter" --aantal 20
python tools/linkedin/browser.py zoek --urls-bestand <lijst.txt>   # Sales Navigator-proefperiode, geen zoekbudget
python tools/linkedin/browser.py lees --batch-bestand .tmp/linkedin_zoekresultaten.json
```

Kwalificatiecriteria (zelfde regels als `kwalificeer.NICHE_REGELS`):
- **Installatiebedrijven:** eigenaar/directeur/mede-eigenaar van een klein
  tot middelgroot installatiebedrijf-achtig vakbedrijf (loodgieter,
  elektricien, installatietechniek, HVAC, aannemer, bouwbedrijf, zonnepanelen).
  Geen gewone medewerker bij een groot bedrijf (Liander, Heijmans, Vaillant).
- **Makelaars:** makelaar/eigenaar van een makelaardij, hypotheek- of
  verzekeringsadviseur, idealiter bij een klein/zelfstandig kantoor (geen
  medewerker bij een groot filiaalkantoor zonder beslissingsmacht).

Voor goedgekeurde profielen geldt:
- **Connectienotitie: geen.** Op verzoek van Oussama (09-11) wordt het
  connectieverzoek altijd leeg verstuurd, geen bijgevoegde tekst. De cockpit
  toont geen notitie-blok als `connectienotitie` leeg is.
- Een openingsbericht ("Bericht 1", wordt pas na acceptatie verstuurd) — vast
  sjabloon per niche, zie `tools/linkedin/berichten.py` en hieronder.

**Vaste sjabloon bericht 1 — installatiebedrijven** (vastgelegd 2026-11-09,
zie ook `outputs/outreach-ondernemers-email-strategie.md` → sectie
"LinkedIn-variant" voor de volledige geschiedenis/herzieningen):

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

**Vaste sjabloon bericht 2** (follow-up als bericht 1 geen reactie krijgt,
vastgelegd 2026-11-09):

```
Dag [voornaam],
Ik help installatiebedrijven met het automatiseren van tijdrovende klusjes, zoals het opstellen van offertes, calculaties maken of de facturatie bijhouden. Ik vroeg me af hoe dit bij [bedrijfsnaam] gaat.
Zou je het interessant vinden om vrijblijvend te kijken wat er mogelijk is voor [bedrijfsnaam]?
Hier alvast een voorbeeld van zo'n offertetool: insightance.ai/offerte
Ik hoor graag van je.
```

Voorbeelden beperkt tot offertes/calculaties/facturatie (geen klantenservice
e.d.) — alleen voor offerte-gerelateerde pijnpunten bestaat een bewezen demo
(MHL), zelfde regel als in `outputs/outreach-ondernemers-email-strategie.md`.

**Link: `insightance.ai/offerte`** (herzien 09-11, was eerst de volledige
URL met UTM-parameters zichtbaar in het bericht). LinkedIn-chats tonen altijd
de letterlijke getypte tekst, geen verborgen hyperlinks met afwijkende
weergavetekst — dus een korte, eigen redirect-link (zelfde patroon als
`insightance.ai/li`, `/wa`, `/ig`, `/go`) stuurt door naar
`insightance.ai/vakbedrijven?utm_source=linkedin&utm_medium=outreach&utm_campaign=li2`.
Bestand: `docs/offerte/index.html`.

**Vaste sjabloon bericht 3** (laatste follow-up als bericht 2 ook geen reactie
krijgt, vastgelegd 2026-11-09 — sluit de reeks af):

```
Dag [voornaam],
Ik laat het hierbij, geen verdere berichten van mijn kant. Mocht het ooit relevant worden, dan weet je me te vinden.
Succes met [bedrijfsnaam]!
```

Status wordt na het versturen direct `Afgerond` (geen nieuwe follow-up-datum
— dit is de laatste stap).

**Vaste sjabloon berichten 1-3 — makelaars/adviseurs** (vastgelegd
2026-11-12, gebaseerd op het pijnpunt uit `outputs/belscript-makelaars.md`:
verkoopadviezen/aanvragen die blijven liggen zonder systematische opvolging):

```
Dag [voornaam],
Bedankt voor het accepteren! Ik volg wat er speelt bij makelaars en adviseurs in de regio rond opvolging van lopende aanvragen.
Hoe gaat dat bij [bedrijfsnaam], blijft een aanvraag of advies weleens even liggen voordat er opvolging is, of hebben jullie dat goed op orde?
```

```
Dag [voornaam],
Ik help makelaars en adviseurs met het automatiseren van tijdrovende taken, zoals het bijhouden en herinneren van openstaande aanvragen of de opvolging na een eerste contact. Ik vroeg me af hoe dit bij [bedrijfsnaam] gaat.
Zou je het interessant vinden om vrijblijvend te kijken wat er mogelijk is voor [bedrijfsnaam]?
Ondernemers die dit automatiseren winnen doorgaans 10 tot 15 uur per week terug.
Ik hoor graag van je.
```

```
Dag [voornaam],
Ik laat het hierbij, geen verdere berichten van mijn kant. Mocht het ooit relevant worden, dan weet je me te vinden.
Succes met [bedrijfsnaam]!
```

Geen link in bericht 2 (nog geen makelaars-specifieke demo/landingspagina
zoals de offertetool voor installatiebedrijven) — in plaats daarvan het
algemene 10-15 uur/week-cijfer, zelfde bron als
`outputs/outreach-ondernemers-email-strategie.md`. Bericht 3 is identiek aan
de installatiebedrijven-versie (al generiek genoeg voor beide niches).

**Gespreksregels na een reactie (geen vast script, maar wel een vaste regel):**
Als iemand op bericht 1, 2 of 3 reageert, is er bewust GEEN vast vervolgscript —
Oussama meldt dat aan Claude en het gesprek gaat ad-hoc verder. Wel een
standing regel: **niet te lang blijven hangen.** Niet meerdere rondes open
vragen stellen — na een reactie relatief snel richting een vrijblijvende call
sturen, bijvoorbeeld: *"Vind je het goed als ik je vrijblijvend kan laten
zien wat mogelijk is voor jouw bedrijf?"* Doel is een call, niet een lang
LinkedIn-gesprek.

### 4. In de wachtrij zetten (automatisch via de "Nieuwe dag"-knop, of handmatig)

De "Nieuwe dag"-knop doet dit al automatisch (stap 1-3 hierboven). Voor een
losse handmatige toevoeging:

```python
import sys; sys.path.insert(0, "tools/linkedin")
import wachtrij
wachtrij.nieuw({"naam": ..., "functie": ..., "bedrijf": ..., "locatie": ...,
                 "url": ..., "connectienotitie": ..., "bericht1": ...,
                 "bericht2": ..., "bericht3": ...})
```

Status wordt standaard `Te versturen`; geef `"status": "Twijfel"` mee om in
de cockpit-sectie "Twijfelgevallen" te komen i.p.v. direct in "Te versturen".

### 5. Versturen (cockpit, mens-in-de-lus)

```
python apps/linkedin/cockpit.py
```

Open `http://127.0.0.1:5050`. De cockpit-kaart in **"Te versturen"** toont
bewust ALLEEN naam/functie/bedrijf/locatie (geen berichttekst, want er gaat
geen notitie mee — zie hierboven) — gehouden zo simpel mogelijk, besluit
Oussama 09-11. Oussama stuurt het (lege) connectieverzoek ZELF op LinkedIn,
en bevestigt met **✅ Connectie verstuurd**. Dat werkt de Sheet bij én logt de
actie meteen lokaal (daglimiet blijft actueel binnen de sessie, zie Design
Decision 10 in het plan). De kandidaat verschijnt daarna in **"Wachten op
acceptatie"** — puur informatief, geen berichttekst nodig, met een handmatige
"✅ Geaccepteerd"-knop als noodgreep (zie stap 6 voor de automatische route).

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

Cockpit-sectie **"Geaccepteerd — bericht 1 klaarzetten"** toont alle rijen met
status `Geaccepteerd` (via `wachtrij.geaccepteerd_wachtend()`), met bericht 1
direct zichtbaar + kopieerknop. Bericht 2 en 3 staan bewust ingeklapt achter
een "▸ Bericht 2 en 3 bekijken"-toggle (besluit Oussama 09-11: alleen het nu
relevante bericht meteen tonen, de rest desgewenst opklappen). Na
**✅ Verstuurd** (route `/bericht1_verstuurd`) wordt de status `Bericht
verstuurd` en plant `wachtrij.status()` automatisch de follow-up-due-datum
voor bericht 2 (vandaag + `FOLLOW_UP_DAGEN`).

### 8. Follow-ups

`wachtrij.due_follow_ups()` + de cockpit-sectie "Follow-ups due" tonen wie aan
de beurt is, met een `volgende_actie`-veld (`bericht2` of `bericht3`) dat
bepaalt welk bericht en welke knop-route (`/bericht2_verstuurd` of
`/bericht3_verstuurd`) getoond wordt. Na bericht 3 wordt de status `Afgerond`
— geen nieuwe follow-up gepland, de reeks is dan compleet.

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

## Status berichtenreeks

Volledige reeks (connectieverzoek → bericht 1 → bericht 2 → bericht 3) is
vastgelegd voor beide niches (installatiebedrijven 09-11, makelaars 12-11) en
volledig gebouwd, inclusief de geautomatiseerde "Nieuwe dag"-knop (12-11).
Toekomstige aanpassingen aan de teksten: pas `tools/linkedin/berichten.py`
aan (niet alleen dit document — dat is de bron die de agent écht gebruikt),
werk bestaande sheetrijen bij via `wachtrij.py`, en houd
`outputs/outreach-ondernemers-email-strategie.md` in sync.

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
