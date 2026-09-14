# Workflow: Prospect Sourcing & Verificatie

## Doel

Nieuwe, geverifieerde e-commerce-prospects vinden voor de outreach-campagne
(cart-abandonment-automatisering) en toevoegen aan de AIOS Outreach Tracker
Google Sheet. Vervangt het handmatig herschrijven van sourcing/verificatie-
scripts elke ronde — de pipeline zit nu vast in `tools/source_prospects.py`.

## Vereiste inputs

- **Niches/zoektermen**: bv. "sportvoeding", "supplementen", "sportkleding",
  al dan niet aangevuld met een land/regio als de vorige NL/BE-ronde verzadigd
  is (zie "Yield-verwachting" hieronder).
- **Gewenst aantal** nieuwe prospects (richtgetal, geen harde eis — zie yield-
  verwachting).

## Stappen

### 1. Kandidaten vinden (agent, geen tool)

Dit is handmatig/web-research werk van de agent — de tool sourcet niet zelf.
Zoek webshops binnen de opgegeven niche(s) via web search, en verzamel per
kandidaat: bedrijfsnaam, URL, korte niche-omschrijving, en (bij internationale
kandidaten) het land. Sla dit op als JSON-array:

```json
[
  {"name": "Voorbeeld Shop", "url": "https://voorbeeldshop.nl", "niche": "Sportvoeding", "land": "Nederland"}
]
```

`land` is optioneel — laat weg (of vul "Nederland"/"België" in) voor NL/BE-
kandidaten. Alleen bij een afwijkend land wordt dit in de Notities-kolom gezet.

Pas hier ook de **screeningcriteria** grofweg toe voordat je een kandidaat
meeneemt (zie `tools/source_prospects.py`, bovenaan het bestand, voor de
volledige lijst en voorbeelden — laag-ticket niches, borderline food-niches,
marketplace/reseller-shops, parent-company-schaal, groot-merk/volgersaantal).
Het script filtert alleen het mechanische deel (bereikbaarheid, kanaal, dedup)
— deze judgment calls blijven aan de agent. Check het Instagram-volgersaantal
in het bijzonder pas vlak vóór het versturen (niet alleen tijdens sourcing) —
dat staat niet in de HTML van de webshop en is dus makkelijk te missen
(voorbeeld: BRUNA The Label, 247k+ volgers, pas na verzending opgemerkt).

### 2. Verifiëren (dry-run, standaardgedrag)

```
python tools/source_prospects.py <candidates.json>
```

Dit draait automatisch:
1. **Dedup** tegen de huidige sheet (op exacte bedrijfsnaam, case-insensitive)
   — voordat er tijd aan verificatie wordt besteed.
2. **Bereikbaarheidscheck** per resterende kandidaat (parallel, via
   `ThreadPoolExecutor`).
3. **Popup/ESP-detectie** (Klaviyo, Mailchimp, Privy, Justuno, Omnisend,
   Sleeknote, OptinMonster, OneSignal).
4. **Contactkanaal-lookup**: eerst Instagram, anders e-mail als fallback.

Output: een resultaten-JSON (standaard `.tmp/source_prospects_results.json`)
met `qualified`, `dropped` (met reden) en `duplicates`. Er wordt in dit stadium
**niets** naar de sheet geschreven.

### 3. Handmatige screening-check (agent)

Loop de `qualified`-lijst door op de judgment-call-criteria (zie stap 1 en de
comments in `tools/source_prospects.py`). Let extra op kandidaten met
`flag_domain_mismatch: true` in de output — dat betekent dat het gevonden
e-mailadres een ander domein gebruikt dan de webshop zelf, wat kan wijzen op
een groot moederbedrijf buiten de doelgroep. Verwijder afgekeurde kandidaten
uit de lijst (of filter ze in een tussenstap) voordat je naar de sheet
schrijft.

### 4. Toevoegen aan de sheet

Herdraai met `--append` (kan met dezelfde of een handmatig opgeschoonde
candidates-file):

```
python tools/source_prospects.py <candidates.json> --append
```

Dit schrijft de gekwalificeerde nieuwe rijen naar kolommen A:J (startrij =
huidig aantal rijen + 1) en breidt daarna automatisch de rijstriping
(banding) uit tot het nieuwe totale rijaantal.

**Let op:** gebruik `--append` alleen na stap 3. Er is geen ingebouwde
tussenstap die afgekeurde kandidaten er automatisch uitfiltert.

## Kolommen (A:J)

| Kolom | Inhoud |
|---|---|
| A | Bedrijfsnaam |
| B | Instagram handle (leeg bij e-mail-kanaal) |
| C | URL |
| D | Product/niche |
| E | Status ("Te versturen") |
| F/G/H | Datum DM1/2/3 (leeg) |
| I | Notities — zie format hieronder |
| J | Gereageerd? (leeg) |

**Notities-format**: `Kanaal: Instagram.` of `Kanaal: E-mail (geen Instagram
gevonden).`, gevolgd door `MET-popup variant.` of `ZONDER-popup variant.`,
gevolgd door `Land: [land].` (alleen als land afwijkt van Nederland/België),
en bij e-mail-kanaal ook `E-mail: [adres].`

## Bekende valkuilen / edge cases

- **Cloudflare TLS-fingerprinting**: Python's `requests`-library wordt
  structureel geblokkeerd. Het script gebruikt daarom `curl` via subprocess
  als fetcher — niet aanpassen naar `requests`.
- **HTTP 403**: kan een false-positive bot-block zijn. Het script doet één
  retry met vollere `Accept`/`Accept-Language`-headers. Blijft het 403, dan
  wordt de kandidaat laten vallen (niet geforceerd).
- **HTTP 429 (rate limiting)**: kwam veel voor bij internationale sites.
  Geen retry — kandidaat wordt direct laten vallen.
- **DNS-fouten, SSL-fouten, 520-serverfouten**: kandidaat wordt laten vallen,
  niet geforceerd.
- **Placeholder-Instagram-links**: sommige thema's tonen `instagram.com/shopify`
  (of vergelijkbaar) als een social-knop niet geconfigureerd is. Dit wordt
  gefilterd, samen met generieke paths zoals `/p/`, `/reel/`.
- **Honeypot-e-mailadressen**: anti-bot-systemen (Cloudflare, Anubis e.d.)
  geven soms een lokaas-adres terug aan scrapers (bv. `*@techaro.lol`), en
  Sentry-foutmeldingsadressen kunnen per ongeluk in HTML terechtkomen. Beide
  worden uitgefilterd bij de e-mail-fallback.
- **Banding-verlenging**: rijstriping breidt NIET automatisch mee uit bij
  bulk-toevoegen via de Sheets API. Het script zoekt de huidige
  `bandedRangeId` op via `spreadsheets().get()` (dit ID kan wijzigen — nooit
  hardcoden) en breidt die daarna uit via `updateBanding`.
- **Startrij-bug**: eerdere rondes hadden een verkeerd berekende startrij,
  wat een blanco gat in de sheet veroorzaakte. Het script berekent de
  startrij altijd als `huidig_aantal_rijen + 1`, opnieuw opgevraagd vlak
  vóór het schrijven.

## Yield-verwachting

De opbrengst daalt naarmate een niche/regio verzadigd raakt — dit is een
verwacht patroon, geen bug. Voorbeeld: een NL/BE-only ronde had een doel van
250 nieuwe prospects maar leverde er 39 op omdat de markt verzadigd was.
Nadat de campagne internationaal + e-mail-only-kanaal ging toestaan, leverde
eenzelfde doel van 250 er 252 op. Meld een lage yield transparant in plaats
van de screeningcriteria te verlagen om een quotum te halen.

Land is sinds 2026-09-14 geen afwijzingscriterium meer (de campagne is
internationaal) — alleen nog een informatief veld in de Notities-kolom.
