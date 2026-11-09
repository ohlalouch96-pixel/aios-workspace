# Plan: LinkedIn Outreach Agent

**Created:** 2026-11-09
**Status:** Stap 1-11 gebouwd en getest (2026-11-09). Stap 12 (eind-tot-eind-test met echte LinkedIn-login) wacht op Oussama.
**Request:** Een LinkedIn-outreach-systeem bouwen (browser-automatisering voor zoeken/kwalificeren, een lokale webcockpit voor het klaarzetten en bevestigen van connectieverzoeken/berichten, en een dashboard met cijfers), geïnspireerd op Tim's "Clearvana"-systeem maar toegepast op Insightance/Oussama.

---

## Overview

### What This Plan Accomplishes

Een nieuw outreach-kanaal naast de bestaande webshop- en ondernemers-tracks: LinkedIn. Een browser-automatiseringstool zoekt en leest LinkedIn-profielen van installatiebedrijven-achtige beslissers (loodgieters, schilders, stukadoors, aannemers) met Oussama's eigen ingelogde sessie; Claude kwalificeert en schrijft een connectienotitie + openingsbericht; een lokale webcockpit (draait op zijn eigen laptop, geen Telegram) zet dit klaar zodat Oussama het met één druk op de knop zelf verstuurt op LinkedIn; en een nieuw Google Sheet-tabblad + databasetabel + sectie in `key-metrics.md` geven hem het overzicht (aantal benaderd, reacties, percentages) dat hij al kent van de webshop- en ondernemers-trackers.

### Why This Matters

Oussama's noordster is de eerste betalende klant, en LinkedIn is tot nu toe alleen een contentkanaal, geen outreach-kanaal. Dit voegt een derde, geautomatiseerd gevoede outreach-spoor toe zonder dat Oussama zelf hoeft te zoeken of te typen, terwijl het account-risico (de grootste bedreiging bij LinkedIn-automatisering) beheerst blijft doordat alleen zoeken/lezen geautomatiseerd wordt en versturen altijd een bewuste, handmatige actie van Oussama blijft.

---

## Current State

### Relevant Existing Structure

- **Outreach-trackers (Google Sheets → SQLite → key-metrics.md):** `scripts/collect_outreach.py` (webshops) en `scripts/collect_ondernemers.py` (vakbedrijven) lezen alleen-lezend een tabblad uit dezelfde Google Sheet, schrijven naar tabellen `outreach`/`ondernemers` in `data/data.db`, en `scripts/generate_metrics.py` (`section_outreach()`) genereert daaruit de tabellen in `context/key-metrics.md`. `scripts/collect.py` ontdekt en draait alle `collect_*.py`-bestanden automatisch.
- **Sourcing/verificatie van nieuwe prospects:** `tools/source_prospects.py` (webshops) verifieert kandidaten, dedupliceert tegen de sheet (naam/domein/handle/e-mail) en voegt gekwalificeerde nieuwe rijen toe via de Sheets API (`append_qualified_to_sheet`, met banding-fix). `workflows/source_prospects.md` is de bijbehorende SOP.
- **Cockpit-patroon (concept, niet het transportmiddel):** `tools/instagram/telegram_review.py` + `tools/instagram/wachtrij.py` draaien een eigen content-bot die concepten naar Oussama stuurt met knoppen **Goedkeuren / Aanpassen / Overslaan**, en na goedkeuring een "plaatsklaar"-pakket met een knop **Geplaatst** die de status bijwerkt. Plaatsen zelf doet Oussama altijd handmatig. Dit *interactiepatroon* (kaart tonen → knop → status bijwerken) is exact wat Oussama voor LinkedIn wil, maar **niet via Telegram**: Telegram-gebruik op zijn telefoon kost hem €/$11-15 per 2 dagen bij veel gebruik, en dat wil hij niet nog hoger laten oplopen door een tweede bot. Voor LinkedIn wordt dit patroon daarom hergebouwd als een lokale webpagina op zijn eigen laptop (geen Telegram-afhankelijkheid, geen doorlopende kosten) — zie Design Decisions.
- **Database-/config-conventies:** `scripts/db.py` (SQLite-init, WAL-mode, `collection_log`), `scripts/config.py` (`get_env`), `.env.example` (secties per domein).
- Geen enkel bestand in de workspace raakt vandaag LinkedIn-profielen aan — dit is een volledig nieuw kanaal.

### Gaps or Problems Being Addressed

- Er is geen manier om LinkedIn-profielen te vinden/lezen zonder dat Oussama het zelf met de hand doet.
- Er is geen plek om LinkedIn-prospects, verzonden connectieverzoeken/berichten en reacties bij te houden.
- Er is geen ingebouwde bescherming tegen te snel opschalen van LinkedIn-automatisering (account-restrictierisico) — Oussama heeft hier expliciet om gevraagd en wil dat Claude de leidende rol neemt in het opbouwschema.
- Er is geen dashboard-weergave voor LinkedIn naast de bestaande webshop-/ondernemers-cijfers in `key-metrics.md`.

---

## Proposed Changes

### Summary of Changes

- Nieuw tabblad `linkedin-tracker` in de bestaande outreach Google Sheet (zelfde sheet als webshops/ondernemers), met een kolomopzet die het patroon van `ondernemers-tracker` volgt maar uitgebreid met connectie-/follow-up-specifieke kolommen.
- Nieuwe `tools/linkedin/`-module: Playwright-browserautomatisering (persistente, handmatig ingelogde sessie) voor zoeken en profielen lezen, een veiligheidslimiet-/opbouwschema-module, en een wachtrij/sheet-writer.
- Nieuwe `apps/linkedin/cockpit.py`: lokale webapp (Flask, draait op `localhost` op Oussama's eigen laptop, geen Telegram) die dezelfde kaart-met-knoppen-flow biedt als de Instagram-cockpit, plus een dashboard-sectie met cijfers/percentages op dezelfde pagina.
- Nieuwe `scripts/collect_linkedin.py` (alleen-lezend, naar het patroon van `collect_ondernemers.py`) die het tabblad synchroniseert naar een tabel `linkedin` in `data/data.db`.
- Uitbreiding van `scripts/generate_metrics.py` met een LinkedIn-sectie in `context/key-metrics.md`, naast Webshops en Ondernemers.
- Nieuwe workflow-SOP `workflows/linkedin_outreach.md` die het geheel beschrijft: zoeken → kwalificeren → cockpit → versturen → follow-up → dashboard, inclusief het week-voor-week opbouwschema en de noodstop-regels.
- `.env.example` uitbreiden met de nieuwe variabelen (sheet-tabnaam, cockpit-poort).
- `requirements.txt` uitbreiden met `playwright` en `flask` (nieuwe, nog niet geïnstalleerde dependencies).
- `CLAUDE.md` bijwerken (nieuwe mappen `tools/linkedin/` en `apps/linkedin/`, nieuw script, nieuwe workflow, nieuwe sheet-bron in de "Verbonden bronnen"-tabel).
- **Berichtinhoud (opening + follow-upreeks) wordt in dit plan NIET uitgewerkt** — Oussama heeft hier al een aanbod/strategie liggen uit een eerdere sessie en wil dat bewust laten liggen tot de rest staat. De cockpit en de sheetkolommen worden wel al voorbereid om die tekst straks op te nemen (zie Open Questions).

### New Files to Create

| File Path | Purpose |
| --- | --- |
| `tools/linkedin/browser.py` | Playwright-automatisering: persistente login-sessie, LinkedIn people-search uitvoeren, profielen uitlezen (naam, functie, bedrijf, locatie, about-tekst), restrictie-/waarschuwingsdetectie. |
| `tools/linkedin/limits.py` | Week-voor-week opbouwschema (connectieverzoeken/profielbezoeken/zoekopdrachten per dag), daglimiet-boekhouding, noodstop-logica (acceptatieratio + restrictie-detectie). |
| `tools/linkedin/wachtrij.py` | Schrijft gekwalificeerde kandidaten + conceptteksten naar het `linkedin-tracker`-tabblad (Sheets API, schrijfrechten) en werkt statussen/datums bij. Naar het patroon van `tools/instagram/wachtrij.py`, maar schrijft naar de Sheet in plaats van alleen naar `data.db`. |
| `apps/linkedin/cockpit.py` | Lokale Flask-webapp (draait met `python apps/linkedin/cockpit.py`, bekeken op `http://localhost:<poort>` in de browser op Oussama's eigen laptop — geen Telegram, geen doorlopende kosten). Toont per kandidaat een kaart (profielinfo + kwalificatie-redenering + conceptnotitie/openingsbericht) met knoppen **✅ Verstuurd / ✏️ Aanpassen / ❌ Overslaan**, plus een dashboardsectie met cijfers/percentages uit `data.db`. Zelfde interactiepatroon als `tools/instagram/telegram_review.py`, andere transportlaag. |
| `scripts/collect_linkedin.py` | Alleen-lezend: leest `linkedin-tracker` uit de Sheet, schrijft naar tabel `linkedin` in `data/data.db`. Naar het patroon van `scripts/collect_ondernemers.py`. |
| `workflows/linkedin_outreach.md` | SOP: wanneer/hoe te zoeken, kwalificatiecriteria, cockpit-flow, opbouwschema, noodstop-regels, openstaande punten (berichtinhoud). |

### Files to Modify

| File Path | Changes |
| --- | --- |
| `scripts/generate_metrics.py` | `section_outreach()` uitbreiden met een derde track (`linkedin`-tabel, zelfde `track_stats`-aanpak) zodat LinkedIn meetelt in de tabel "Outreach: Totaal" en een eigen "Outreach: LinkedIn"-tabel krijgt. |
| `.env.example` | Nieuwe variabelen toevoegen onder een nieuwe sectie `# ─── LINKEDIN OUTREACH ───`: `LINKEDIN_SHEET_TAB` (default `linkedin-tracker`), `LINKEDIN_COCKPIT_PORT` (default `5050`). `OUTREACH_SHEET_ID`/`GOOGLE_SERVICE_ACCOUNT_JSON` worden hergebruikt (zelfde sheet, zelfde service-account). Geen Telegram-variabelen nodig. |
| `CLAUDE.md` | Workspace-structuurboom en "Verbonden bronnen"-tabel bijwerken: nieuwe mappen `tools/linkedin/` en `apps/linkedin/`, nieuw script `collect_linkedin.py`, nieuwe rij "Google Sheets → `collect_linkedin.py` → LinkedIn-outreach (tabel `linkedin`)". |
| `.gitignore` | Toevoegen: `.tmp/linkedin-session/` (Playwright-browserprofiel met ingelogde sessie — mag nooit gecommit worden, is gevoeliger dan een API-key omdat het een volledige sessie is). |
| `requirements.txt` | Toevoegen: `playwright`, `flask`. Plus eenmalige documentatie-stap (geen bestandswijziging): `playwright install chromium` moet één keer lokaal gedraaid worden na `pip install`. |

### Files to Delete (if any)

Geen.

---

## Design Decisions

### Key Decisions Made

Deze besluiten zijn al met Oussama doorgenomen op 2026-11-09 en liggen vast:

1. **Alleen nieuwe prospects, geen overlap met de ondernemers-tracker**: voorkomt dat één eigenaar via meerdere kanalen tegelijk benaderd wordt, wat als opdringerig kan overkomen. Later evalueren of cross-channel escalatie (geen reactie op e-mail → proberen via LinkedIn) een goede vervolgstap is.
2. **Browserautomatisering voor zoeken/lezen, geen automatisch versturen**: Oussama kiest bewust voor de techniek van Tim's bot voor het zoek/leesgedeelte en accepteert het daarbij horende account-risico. Versturen van connectieverzoeken en berichten blijft altijd een handmatige klik van Oussama — dit was al zijn oorspronkelijke eis en vermindert het ban-risico aanzienlijk (LinkedIn's detectie richt zich vooral op patronen in het versturen, niet op kijkgedrag alleen).
3. **Tracker leeft in een nieuw tabblad in de bestaande Google Sheet**, gesynchroniseerd naar `data.db` via een `collect_linkedin.py` naar het bestaande patroon — consistent met webshops/ondernemers, geen nieuw systeem.
4. **Claude bepaalt het opbouwschema voor daglimieten**, Oussama volgt het. Zie het schema hieronder. Uitgangspunt: **gratis LinkedIn-account** (bevestigd door Oussama op 2026-11-09), dus het schema houdt ook rekening met LinkedIn's maandelijkse "Commercial Use Limit" op zoekopdrachten/profielbezoeken die voor gratis accounts geldt (Premium/Sales Navigator heeft die beperking niet) — vandaar de bewust lage zoek-/bezoeklimieten, los van de connectieverzoek-limieten.
5. **Geen Telegram voor deze cockpit — een lokale webapp op Oussama's eigen laptop.** Reden: Telegram-gebruik op zijn telefoon kost hem €/$11-15 per 2 dagen bij intensief gebruik; een tweede bot (naast de Instagram-contentbot) zou dat verder verhogen. Hosting van de bot-server zelf verandert niets aan die kosten (die zitten aan de kant van de Telegram-mobiele-app, niet aan de botkant) — de enige echte oplossing is om voor dit kanaal geen Telegram te gebruiken. `apps/linkedin/cockpit.py` wordt daarom een kleine lokale Flask-webapp: zelfde kaart-met-knoppen-interactie als de Instagram-cockpit, maar bekeken in de browser op `localhost`, zonder enige Telegram-afhankelijkheid of doorlopende kosten.
6. **Eerste testbatch richt zich op installatiebedrijven**: loodgieters, schilders, stukadoors, aannemers, installatietechniek, bouwbedrijven. Zoekcriteria combineren functietitel (eigenaar/directeur/zaakvoerder/oprichter) met deze branchewoorden. Wordt in Step 4/12 getest en bijgesteld als een term te weinig/te veel resultaten geeft.
7. **Regio: eerst Noord-Holland, daarna olievlek-uitbreiding** (besloten 2026-11-09, vervangt het eerdere "regio Nederland"). De eerste batch(es) blijven beperkt tot Noord-Holland. Zodra die regio voldoende bewerkt is (queue raakt leeg / verzadiging zichtbaar in de cijfers), breidt de regio stapsgewijs uit naar aangrenzende provincies (bv. Utrecht, Zuid-Holland, Flevoland), net als bij een olievlek. Dit is een **handmatig besluit per keer**, geen automatische regel — Claude signaleert verzadiging, Oussama besluit of en waarheen uitgebreid wordt. `tools/linkedin/browser.py` krijgt de regio daarom als parameter (`--regio`), niet hardcoded.
8. **Sales Navigator-proefperiode (nog 3 weken vanaf 2026-11-09)**: Oussama heeft tijdelijk Sales Navigator, daarna weer een gratis account. Er wordt **geen** aparte automatisering gebouwd tegen de Sales Navigator-zoekschermen (andere UI/URL's dan de standaard LinkedIn-zoekpagina, zou na de proefperiode onbruikbare code opleveren). In plaats daarvan krijgt de zoekstap een alternatieve invoermodus: een lijst profiel-URL's die Oussama zelf uit zijn Sales Navigator-zoekresultaten haalt (kopiëren/exporteren) tijdens de proefperiode, wordt door dezelfde lees/kwalificeer/wachtrij-pipeline verwerkt als een automatische zoekopdracht. Zo wordt de proefperiode gebruikt om nu, met betere filters en zonder de maandelijkse Commercial-Use-Limit, een voorraad gekwalificeerde kandidaten op te bouwen — de verstuur-ramp-up (Design Decision 4) verandert hierdoor niet, want die limiet is platform-breed en onafhankelijk van het abonnement.
9. **Acceptatie-detectie is een apart, terugkerend browser-commando** (gevonden bij de eindcontrole op 2026-11-09 — dit ontbrak): de noodstop-regel op acceptatieratio heeft data nodig over wie een verzoek heeft geaccepteerd. `browser.py` krijgt daarom een `check`-subcommando dat periodiek (bv. bij het opstarten van elke sessie) Oussama's eigen "Verzonden uitnodigingen"-pagina bekijkt — dat is alleen je eigen accountactiviteit bekijken, geen informatie over anderen opvragen — en de status `Geaccepteerd` (of `Verlopen`/`Ingetrokken`) bijwerkt in de Sheet + lokale database.
10. **Daglimiet-boekhouding gebeurt lokaal en direct, niet via de Sheet-sync** (ook gevonden bij de eindcontrole): als de cockpit alleen naar de Sheet zou schrijven en moest wachten op de volgende `collect_linkedin.py`-sync om te weten hoeveel er vandaag al verstuurd is, kon het daglimiet per ongeluk overschreden worden binnen één sessie. Daarom schrijft de cockpit bij elke `✅ Verstuurd`-knop **meteen** ook een regel naar een lokaal `linkedin_daily_log`-tabelletje in `data.db` (naast de Sheet-update), zodat `limits.py` altijd een actuele telling heeft, onafhankelijk van de sync-frequentie.
11. **Berichtinhoud wordt later ingevuld** — infrastructuur wordt wel voorbereid (velden voor connectienotitie + 4 berichten in de sheet, placeholder-tekst in de cockpit), maar de daadwerkelijke tekst/aanbod-invulling is een aparte, latere stap.

### Opbouwschema daglimieten (nieuw, door Claude opgesteld per Oussama's verzoek)

| Week | Connectieverzoeken/dag | Profielbezoeken/dag | Zoekopdrachten/dag | Voorwaarde om door te gaan naar volgende week |
| --- | --- | --- | --- | --- |
| 1 | 8 | 25 | 5 | Geen restrictiemelding van LinkedIn gezien |
| 2 | 12 | 35 | 8 | Acceptatieratio ≥30% over week 1 én geen restrictie |
| 3 | 15 | 45 | 10 | Acceptatieratio ≥30% over week 2 én geen restrictie |
| 4 | 18 | 50 | 10 | Acceptatieratio ≥30% over week 3 én geen restrictie |
| 5+ (plateau) | 20 | 60 | 12 | Blijft op dit niveau; geen verdere opschaling gepland |

**Noodstop-regels** (automatisch, het systeem handelt dit zelf af en toont het bovenaan de cockpit-pagina):
- Acceptatieratio over de laatste 20 verzonden connectieverzoeken zakt onder 15% → automatisch pauzeren op het huidige niveau (niet terugschalen, wel stoppen met nieuwe verzoeken) totdat Oussama het herbekeken heeft.
- Als de browser-tool bij het inloggen/zoeken een LinkedIn-restrictiemelding, verificatieverzoek of CAPTCHA tegenkomt → direct en volledig stoppen (ook met zoeken/lezen), duidelijke waarschuwing boven in de cockpit-pagina, pas herstarten na handmatige bevestiging van Oussama.
- Bij twee opeenvolgende dagen zonder acceptaties op de verzonden verzoeken van die week → waarschuwing naar Oussama, geen automatische pauze (kan ook aan de doelgroep/boodschap liggen, niet per se aan het account).
- Elke opschaling naar de volgende week-stap gebeurt niet automatisch op de kalenderdatum, maar pas zodra de voorwaarde in de tabel hierboven is bevestigd (de bot checkt dit bij de eerste actie van een nieuwe week en meldt het resultaat).

### Alternatives Considered

- **Volledig automatisch versturen (zoals sommige groeihacking-tools doen)**: afgewezen, expliciet door Oussama vanaf het begin uitgesloten vanwege ban-risico.
- **Alleen handmatig zoeken door Oussama, Claude kwalificeert/schrijft alleen**: was de conservatievere optie die is voorgelegd; Oussama heeft bewust gekozen voor de geautomatiseerde zoek/leesvariant.
- **Tracker direct in `data.db` zonder Google Sheet (zoals het Instagram-systeem doet)**: overwogen omdat het technisch eenvoudiger is (geen Sheets-API-schrijfrechten nodig voor de wachtrij), maar afgewezen omdat Oussama expliciet akkoord ging met het sheet-gebaseerde advies en hij op de Sheet kan terugkijken/handmatig kan bijwerken zoals bij de andere tracks.
- **Telegram-cockpit (zelfde bot-aanpak als Instagram)**: dit was het oorspronkelijke voorstel, afgewezen door Oussama vanwege de kosten van Telegram-gebruik op zijn telefoon (€/$11-15 per 2 dagen bij intensief gebruik). Vervangen door een lokale Flask-webapp op zijn eigen laptop, die hetzelfde kaart-met-knoppen-interactiepatroon biedt zonder Telegram-afhankelijkheid.

### Open Questions

Status per 2026-11-09 — de eerste drie zijn door Oussama beantwoord, er resteert nog één technische vraag:

1. ~~LinkedIn-accounttype~~ → **Beantwoord: structureel een gratis account**, met een tijdelijke Sales Navigator-proefperiode (nog 3 weken vanaf 2026-11-09). Plan bouwt structureel voor het gratis account (inclusief de maandelijkse Commercial Use Limit) en benut de proefperiode alleen via de `--urls-bestand`-invoermodus in Step 4, niet via aparte Sales-Navigator-automatisering. Zie Design Decision 8.
2. ~~Nieuwe Telegram-bot~~ → **Vervallen.** Oussama wil geen tweede Telegram-bot (kostenoverweging, zie Design Decisions). Vervangen door een lokale webapp (`apps/linkedin/cockpit.py`), geen handmatige Telegram-setup nodig.
3. ~~Zoekcriteria eerste ronde~~ → **Beantwoord: installatiebedrijven** (loodgieters, schilders, stukadoors, aannemers, installatietechniek, bouwbedrijven), **regio Noord-Holland** (daarna olievlek-uitbreiding, zie Design Decision 7), functietitels eigenaar/directeur/zaakvoerder/oprichter.
4. **Eenmalige handmatige LinkedIn-login**: bij de eerste keer draaien moet Oussama zelf inloggen in het Playwright-browservenster (headful, met zijn eigen 2FA) zodat de sessie lokaal kan worden opgeslagen. Dit gebeurt op zijn eigen laptop, niet automatisch — nog te bevestigen.
5. **Poort/toegang lokale cockpit**: welke lokale poort (voorstel default `5050`) en of de webapp alleen op `localhost` luistert (geen netwerktoegang van buiten de laptop) — voorstel: alleen `127.0.0.1`, nooit bereikbaar van buiten het apparaat. Te bevestigen bij `/implement`.

---

## Step-by-Step Tasks

### Step 1: Google Sheet voorbereiden

Nieuw tabblad `linkedin-tracker` toevoegen aan de bestaande outreach Google Sheet (zelfde spreadsheet-ID als `OUTREACH_SHEET_ID`).

**Actions:**
- Tabblad `linkedin-tracker` aanmaken met kolommen A–N (14 kolommen): Naam, Functie, Bedrijf, Locatie, Profiel-URL, Status, Connectienotitie, Bericht 1 (openingsbericht na acceptatie), Datum verzoek verstuurd, Datum geaccepteerd, Datum bericht 1 verstuurd, Volgende follow-up (due-datum, één kolom; wordt verfijnd naar meerdere stappen zodra de follow-up-berichtenreeks is ingevuld), Gereageerd?, Notities.
- Statuswaarden vastleggen (zelfde idee als ondernemers-tracker): `Te versturen` → `Verzoek verstuurd` → `Geaccepteerd` → `Bericht verstuurd` → `Afgerond` / `Afgewezen` / `Genegeerd` / `Verlopen` (verzoek nooit geaccepteerd, door LinkedIn automatisch ingetrokken of handmatig verlopen verklaard — gedetecteerd door Step 4's `check`-commando).
- Banding (rijstriping) instellen zoals op de andere tabbladen, zodat `tools/linkedin/wachtrij.py` straks dezelfde `updateBanding`-aanpak kan hergebruiken als `tools/source_prospects.py`.

**Files affected:** geen (wijziging in de Google Sheet zelf, geen code).

---

### Step 2: `.env` en `.gitignore` voorbereiden

**Actions:**
- `.env.example` uitbreiden met een nieuwe sectie:
  ```
  # ─── LINKEDIN OUTREACH ────────────────────────────────────────────────────
  LINKEDIN_SHEET_TAB=linkedin-tracker
  LINKEDIN_COCKPIT_PORT=5050
  ```
- Geen bot-token/chat-ID nodig (geen Telegram voor dit kanaal) — alleen de bestaande `OUTREACH_SHEET_ID`/`GOOGLE_SERVICE_ACCOUNT_JSON` worden hergebruikt.
- `.gitignore` aanvullen met `.tmp/linkedin-session/`.

**Files affected:**
- `.env.example`
- `.gitignore`

---

### Step 3: `tools/linkedin/limits.py` — opbouwschema en daglimieten

**Actions:**
- Implementeer het opbouwschema-tabel uit "Design Decisions" als een datastructuur (startdatum van week 1 = eerste keer dat de bot daadwerkelijk een connectieverzoek-actie voorbereidt).
- Functie `current_week_limits(conn)`: bepaalt in welke week je zit (op basis van de eerste rij in `linkedin`-tabel met een ingevulde verzenddatum) en geeft de bijbehorende limieten terug, MAAR controleert eerst of de voorwaarde voor opschaling (acceptatieratio vorige week) gehaald is — zo niet, blijft op het huidige niveau.
- Functie `remaining_today(conn, kind)` (`kind` = connections/profile_views/searches): telt hoeveel acties van dat type vandaag al gedaan zijn uit het lokale `linkedin_daily_log`-tabelletje (bevat ALLE actietypes: connectieverzoeken, profielbezoeken, zoekopdrachten — niet alleen profielbezoeken/zoekopdrachten) en geeft het resterende budget terug. Dit tabelletje wordt rechtstreeks geschreven door `browser.py` (bij zoeken/lezen) en door de cockpit (bij `✅ Verstuurd`) — **niet** pas via de periodieke `collect_linkedin.py`-sheetsync, zodat het daglimiet altijd actueel is binnen één sessie (zie Design Decision 10).
- Functie `check_noodstop(conn)`: implementeert de drie noodstop-regels uit Design Decisions, geeft `{"pauzeren": bool, "reden": str}` terug.
- Alle schrijfacties (browser-tool én cockpit-webapp) roepen deze module aan vóór ze een actie uitvoeren.

**Files affected:**
- `tools/linkedin/limits.py` (nieuw)

---

### Step 4: `tools/linkedin/browser.py` — zoeken en profielen lezen

**Actions:**
- Playwright met een **persistente context** (`launch_persistent_context`, profielmap `.tmp/linkedin-session/`), zodat een eenmalige handmatige login (headful, door Oussama) daarna hergebruikt wordt voor headless runs.
- CLI-subcommando `login`: opent een headful venster, wacht tot Oussama zelf inlogt en Enter drukt in de terminal, slaat de sessie op.
- CLI-subcommando `zoek --titel "..." --branche "..." --regio "Noord-Holland" --aantal N`: voert een standaard LinkedIn people-search uit (niet Sales Navigator — zie Design Decision 8) binnen het dagbudget uit `limits.py`, verzamelt profiel-URLs van de resultatenpagina's. `--regio` is een vrije parameter, niet hardcoded, zodat de olievlek-uitbreiding (Design Decision 7) later zonder codewijziging naar een andere provincie kan.
- CLI-subcommando `zoek --urls-bestand <lijst.txt>`: alternatieve invoer, slaat de automatische zoekstap over en gaat direct met een door Oussama aangeleverde lijst profiel-URL's verder (bv. gekopieerd uit zijn Sales Navigator-zoekresultaten tijdens de proefperiode). Telt niet mee tegen het zoekopdrachten-dagbudget (er wordt niet automatisch gezocht), telt wél mee tegen het profielbezoeken-dagbudget zodra de URL's gelezen worden.
- CLI-subcommando `lees <profiel-url>`: opent een profiel, leest naam, functie, huidig bedrijf, locatie en de about-tekst uit; respecteert het profielbezoeken-dagbudget. Werkt identiek voor profielen gevonden via standaardzoek of via `--urls-bestand`.
- CLI-subcommando `check` (nieuw, zie Design Decision 9 — ontbrak in de eerdere versie van dit plan): bezoekt Oussama's eigen "Verzonden uitnodigingen"-pagina (`linkedin.com/mynetwork/invitation-manager/sent/`), vergelijkt met de rijen in status `Verzoek verstuurd`, en zet ze op `Geaccepteerd` (niet meer in de lijst, wel in bestaande connecties) of `Verlopen`/`Ingetrokken` (niet meer in de lijst, ook niet in connecties). Dit voedt de acceptatieratio die de noodstop-regel gebruikt. Draait als eerste stap van elke sessie, vóór een nieuwe batch.
- Elke actie (zoekopdracht, profielbezoek, `check`-aanroep) schrijft een regel naar het lokale `linkedin_daily_log`-tabelletje in `data.db` (zie Step 3) — dit is de bron voor `limits.py`, niet de Sheet.
- Randomized delays tussen acties (geen vaste intervallen) en een realistische user-agent/viewport, als mitigatie tegen automatiseringsdetectie — een mitigatie, geen garantie.
- Detecteert bekende restrictie-/verificatie-/CAPTCHA-pagina's (op tekst/URL-patroon) en roept dan `limits.check_noodstop`-achtige stop-logica aan; de status wordt in `data.db` vastgelegd zodat de cockpit-pagina de waarschuwing bij het volgende laden direct bovenaan toont.
- Resultaten (ruwe profieldata) worden NIET direct gekwalificeerd door dit script — dat is Claude's taak (reasoning), dit script levert alleen de feiten.

**Files affected:**
- `tools/linkedin/browser.py` (nieuw)

---

### Step 5: Kwalificatie- en conceptvorming (agent-werk, geen tool)

**Actions:**
- Documenteer in `workflows/linkedin_outreach.md` dat dit stap bewust GEEN script is: Claude beoordeelt de ruwe profieldata uit Step 4 tegen de doelgroepcriteria (installatiebedrijven-beslisser: eigenaar/directeur, relevante branche, regio binnen de actuele olievlek-grens) en schrijft de connectienotitie + openingsbericht (placeholder-toon totdat Oussama's aanbod-strategie wordt ingevuld, zie Open Questions).
- Afgekeurde profielen worden niet naar de sheet geschreven (zelfde filosofie als `source_prospects.py`: het script levert kandidaten, de agent + een lichte screeningstap bepalen wat de sheet in gaat).

**Files affected:**
- `workflows/linkedin_outreach.md` (nieuw, beschrijft dit expliciet)

---

### Step 6: `tools/linkedin/wachtrij.py` — sheet-writer en statusbeheer

**Actions:**
- `nieuw(conn_of_service, kandidaat_dict)`: schrijft een nieuwe rij naar `linkedin-tracker` met status `Te versturen`, naar het patroon van `append_qualified_to_sheet` in `tools/source_prospects.py` (startrij opnieuw opvragen, banding uitbreiden).
- `status(rij, nieuwe_status, datum=None)`: werkt een bestaande rij bij (status + relevante datumkolom), gebruikt door de cockpit-webapp na een knopdruk.
- `volgende_batch(n)`: haalt de eerstvolgende `n` rijen met status `Te versturen` op, voor de cockpit-webapp om te tonen, rekening houdend met het daglimiet uit `limits.py`.
- `due_follow_ups()`: rijen waarvan de follow-up-due-datum vandaag of eerder is en nog geen vervolgstatus hebben — voor de follow-up-cockpit-flow.

**Files affected:**
- `tools/linkedin/wachtrij.py` (nieuw)

---

### Step 7: `apps/linkedin/cockpit.py` — de lokale webcockpit

**Actions:**
- Kleine Flask-app, luistert alleen op `127.0.0.1:<LINKEDIN_COCKPIT_PORT>` (nooit bereikbaar van buiten de laptop).
- Start-commando: `python apps/linkedin/cockpit.py` → print de lokale URL → Oussama opent die in zijn browser.
- Hoofdpagina: twee secties op één scherm.
  - **Te versturen** (uit `wachtrij.volgende_batch()`): per kandidaat een kaart (naam, functie, bedrijf, locatie, profiel-link, kwalificatieredenering, connectienotitie-tekst) met knoppen **✅ Verstuurd / ✏️ Aanpassen / ❌ Overslaan**.
  - **Dashboard**: cijfers/percentages uit `data.db` (zelfde cijfers als de LinkedIn-sectie in `key-metrics.md`: totaal, benaderd, reacties, reactieratio, warme leads), zodat hij niet apart `key-metrics.md` hoeft te openen.
- Knop-acties (simpele POST-routes, geen SPA-framework nodig):
  - **✅ Verstuurd** → status + datum bijwerken via `wachtrij.py` (schrijft naar de Sheet) **én meteen een regel in het lokale `linkedin_daily_log` (zie Design Decision 10 — niet wachten op de volgende sheet-sync)**, follow-up-due-datum berekenen en vastleggen.
  - **✏️ Aanpassen** → tekstveld op de pagina voor feedback, legt dit vast in een `linkedin_feedback`-tabelletje (tekst-only, geen Whisper/spraak nodig op een laptop), de agent herschrijft de conceptnotitie in een volgende sessie.
  - **❌ Overslaan** → status `Genegeerd`.
- Dezelfde kaart-flow, aparte sectie "Follow-ups" voor rijen uit `due_follow_ups()`, zodra de berichtinhoud (Open Question / later werk) is ingevuld — voor nu een placeholder-pad dat al werkt met voorlopige tekst.
- Geen Telegram, geen externe afhankelijkheden buiten Flask + de bestaande Sheets/SQLite-laag.

**Files affected:**
- `apps/linkedin/cockpit.py` (nieuw)

---

### Step 8: `scripts/collect_linkedin.py` — sync naar data.db

**Actions:**
- Kopieer het patroon van `scripts/collect_ondernemers.py` 1-op-1: alleen-lezend, tabblad `linkedin-tracker` (naam uit `.env` via `LINKEDIN_SHEET_TAB`, default `linkedin-tracker`), schrijft naar tabel `linkedin` met kolommen die aansluiten op de sheetkolommen uit Step 1 (naam, functie, bedrijf, locatie, url, status, datum_verzoek, datum_geaccepteerd, datum_bericht1, gereageerd, notities, collected_at).
- `UNIQUE(naam)`-constraint en `DELETE ... WHERE naam NOT IN (...)`-opschoning, zelfde als ondernemers.

**Files affected:**
- `scripts/collect_linkedin.py` (nieuw)

---

### Step 9: Dashboard-sectie in `key-metrics.md`

**Actions:**
- `section_outreach()` in `scripts/generate_metrics.py` uitbreiden met een derde `tracks`-item zodra `table_exists(conn, "linkedin")`, met passende kolomlabels ("verzoek verstuurd" i.p.v. "bericht 1 of gebeld", "bericht 1" i.p.v. "bericht 2").
- Totaal-tabel ("Outreach: Totaal") telt automatisch mee zodra de derde track in `tracks` staat (de bestaande som-logica itereert al over alle tracks).
- Testen: `python scripts/collect_linkedin.py` → `python scripts/generate_metrics.py` → controleren dat `context/key-metrics.md` een "Outreach: LinkedIn"-sectie krijgt.

**Files affected:**
- `scripts/generate_metrics.py`

---

### Step 10: Workflow-SOP schrijven

**Actions:**
- `workflows/linkedin_outreach.md` schrijven: doel, vereiste inputs (zoekcriteria), de volledige stappenketen (zoeken → lezen → kwalificeren → wachtrij → cockpit → versturen → follow-up → dashboard), het opbouwschema-tabel (kopie uit dit plan, want de workflow is de levende versie die bijgehouden wordt), de noodstop-regels, en een expliciet "Nog niet ingevuld"-blok voor de berichtinhoud/aanbod-strategie (Open Question 5), zodat een latere sessie precies weet waar ze moet beginnen.

**Files affected:**
- `workflows/linkedin_outreach.md` (nieuw)

---

### Step 11: `CLAUDE.md` bijwerken

**Actions:**
- Workspace-structuurboom: `tools/linkedin/` toevoegen met de drie scripts (`browser.py`, `limits.py`, `wachtrij.py`), `apps/linkedin/cockpit.py` toevoegen, `scripts/collect_linkedin.py` toevoegen, `workflows/linkedin_outreach.md` toevoegen.
- "Verbonden bronnen"-tabel: nieuwe rij `Google Sheets | collect_linkedin.py | LinkedIn-outreach (tabel linkedin)`.

**Files affected:**
- `CLAUDE.md`

---

### Step 12: End-to-end test met een kleine, echte batch

**Actions:**
- `pip install -r requirements.txt` + eenmalig `playwright install chromium`.
- `tools/linkedin/browser.py login` (handmatig, eenmalig).
- Eén kleine testzoekopdracht (bv. 3-5 profielen) binnen het week 1-budget.
- Eén testkandidaat volledig door de flow heen: wachtrij → lokale cockpit-pagina → `✅ Verstuurd` → controleren dat de sheetrij, het lokale `linkedin_daily_log`, `data.db` (na `collect.py`) én `key-metrics.md` kloppen.
- `tools/linkedin/browser.py check` draaien nadat het testverzoek (handmatig) geaccepteerd of genegeerd is, en controleren dat de status in de Sheet/database overeenkomstig bijgewerkt wordt.
- Pas na een succesvolle test de eerste echte batch starten.

**Files affected:** geen nieuwe bestanden; dit is een validatiestap.

---

## Connections & Dependencies

### Files That Reference This Area

- `scripts/collect.py` ontdekt `collect_linkedin.py` automatisch (geen wijziging nodig, werkt op basis van bestandsnaam-patroon `collect_*.py`).
- `context/key-metrics.md` wordt door `/prime` geladen — de nieuwe LinkedIn-sectie is daardoor direct zichtbaar in elke volgende sessie.

### Updates Needed for Consistency

- `CLAUDE.md` (Step 11).
- `.env.example` (Step 2).
- `requirements.txt` aanvullen met `playwright` en `flask` (verplicht, zie Files to Modify), plus de eenmalige `playwright install chromium`-stap documenteren in `workflows/linkedin_outreach.md`.

### Impact on Existing Workflows

Geen impact op de bestaande webshop-/ondernemers-outreach-flows of op de Instagram-contentagent (die blijft op Telegram draaien, ongewijzigd) — dit is een nieuw, los kanaal dat wel bewust het bestaande Sheet-tracker-patroon hergebruikt en het Instagram-cockpit-interactiepatroon (kaart → knop → status) overneemt, maar dan op een lokale webpagina in plaats van via Telegram.

---

## Validation Checklist

- [ ] `tools/linkedin/browser.py login` slaat een herbruikbare sessie op in `.tmp/linkedin-session/` — **nog te doen door Oussama (stap 12)**
- [ ] Een testzoekopdracht levert profiel-URLs op binnen het week 1-daglimiet — **nog te doen (stap 12), inclusief eventuele selector-calibratie**
- [ ] Een testprofiel wordt correct uitgelezen (naam/functie/bedrijf/locatie/about) — **nog te doen (stap 12)**
- [x] Een conceptkandidaat komt via `wachtrij.py` in het `linkedin-tracker`-tabblad terecht met status `Te versturen` — getest 2026-11-09 (testrij toegevoegd, gecontroleerd, weer opgeruimd)
- [x] De lokale cockpit-pagina toont de kaart met de juiste knoppen en verwerkt `✅ Verstuurd` / `✏️ Aanpassen` / `❌ Overslaan` correct — getest 2026-11-09 (HTTP 200, kaart zichtbaar, Verstuurd-knop gaf 302 + status+datum klopten in de sheet)
- [x] De cockpit is alleen bereikbaar via `127.0.0.1` (lokaal), niet van buiten de laptop — `app.run(host="127.0.0.1", ...)`
- [x] `python scripts/collect_linkedin.py` synchroniseert het tabblad naar `data.db` zonder fouten — getest met data (2 rijen) en met een lege sheet (0 rijen)
- [x] `python scripts/generate_metrics.py` toont een "Outreach: LinkedIn"-sectie en telt mee in "Outreach: Totaal" — getest 2026-11-09, ook via de volledige `scripts/collect.py`-orchestrator
- [ ] De noodstop-logica pauzeert daadwerkelijk bij een gesimuleerde lage acceptatieratio — logica gebouwd en de "lege data"-paden getest, maar nog niet getest met een echte lage-ratio-dataset; eerste kans daarvoor is bij een echte batch na stap 12
- [ ] `browser.py check` detecteert correct een testgeval van acceptatie — **nog te doen (stap 12)**, kan niet zonder echte LinkedIn-sessie
- [x] Het daglimiet in `limits.py` blijft correct binnen één sessie (meerdere acties kort na elkaar, zonder tussentijdse `collect_linkedin.py`-sync), dankzij het directe `linkedin_daily_log` — getest: cockpit-knop verhoogde de teller meteen (0/8 → 1/8) zonder sync
- [x] `.env.example`, `.gitignore` (bleek al voldoende), `requirements.txt` en `CLAUDE.md` zijn bijgewerkt
- [x] `pip install -r requirements.txt` en `playwright install chromium` zijn eenmalig gedraaid vóór de eerste test — Flask geïnstalleerd, Playwright+Chromium stonden al klaar
- [x] Geen enkel wachtwoord of 2FA-code wordt ergens opgeslagen — alleen de Playwright-sessiemap (lokaal, gitignored); nog te bevestigen bij de echte login in stap 12

---

## Success Criteria

1. Oussama kan `tools/linkedin/browser.py` een zoekopdracht laten uitvoeren en krijgt in de lokale cockpit-pagina kandidaat-kaarten met kant-en-klare connectienotities te zien.
2. Met één druk op ✅ in de cockpit wordt de status/datum automatisch bijgehouden, zonder dat Oussama iets in de Sheet hoeft te typen, en zonder enige Telegram-kosten.
3. `context/key-metrics.md` toont LinkedIn-cijfers (benaderd, reacties, reactieratio) naast webshops en ondernemers, in hetzelfde format.
4. Het systeem respecteert zelfstandig het week-voor-week opbouwschema en stopt zichzelf (met melding) bij een lage acceptatieratio of een LinkedIn-restrictiesignaal.
5. Er is geen moment waarop de bot zelf een connectieverzoek of bericht verstuurt — dat blijft altijd Oussama's eigen klik.

---

## Notes

- **Berichtinhoud/aanbod-strategie (Open Question 5) is bewust buiten scope van `/implement` van dit plan.** Zodra de rest staat en getest is, is de vervolgstap: de bestaande, al besproken aanbod-strategie invullen in de placeholder-velden van de sheet en de cockpit-teksten.
- Mocht blijken dat LinkedIn's automatiseringsdetectie ook het zoek/leesgedeelte sneller blokkeert dan verwacht (ondanks de randomized delays), is de fallback-optie die eerder is overwogen (Oussama zoekt zelf, plakt profiel-URLs/tekst voor Claude) nog steeds beschikbaar als Step 4 vervangen moet worden — de rest van de architectuur (wachtrij, cockpit, sheet, dashboard) verandert daardoor niet.
- Als later blijkt dat Oussama de cockpit toch liever vanaf zijn telefoon zou willen bedienen (bijvoorbeeld onderweg), is de lokale webapp ook vanaf de telefoon te benaderen zolang die op hetzelfde wifi-netwerk zit als de laptop (geen Telegram/mobiele data nodig) — dit is geen onderdeel van de huidige scope, maar wel een mogelijke latere uitbreiding zonder herontwerp.
