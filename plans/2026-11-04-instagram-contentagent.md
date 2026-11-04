# Plan: Instagram-contentagent voor @insightance.ai

**Created:** 2026-11-04
**Status:** Draft (wacht op akkoord Oussama)
**Request:** Een agent die Instagram-concepten (carrousels, reels, actualiteiten, story-teksten) maakt en via Telegram ter goedkeuring stuurt. Fase 1: Oussama keurt elke post goed en plaatst zelf. Fase 2: agent plaatst na goedkeuring zelf.

---

## Overview

### What This Plan Accomplishes

Een agent die op de server draait en zelfstandig Instagram-content voor @insightance.ai voorbereidt: onderwerp kiezen, tekst schrijven, feiten checken, afbeeldingen en video's maken en het geheel naar Telegram sturen. Oussama hoeft alleen nog op ✅ te drukken (en in fase 1 zelf te plaatsen).

### Why This Matters

Doel van het account is nu volgers, exposure en bekendheid; leads komen later. Dat vraagt veel en gevarieerde content, en dat kost zonder agent te veel tijd naast de ziekenhuisbaan en de outreach. Raakt de KPI Task Automation % (contentproductie wordt vrijwel volledig geautomatiseerd) en Away-From-Desk Autonomy (goedkeuren kan vanaf de telefoon).

---

## Current State

### Relevant Existing Structure

- **Account (stap 1, klaar):** @insightance.ai, aparte merkpagina los van het persoonlijke account, creator-account, leeg. Naam "Oussama | AI Automation", profielfoto `outputs/logo-2026/profielfoto-navy.png`, bio:
  ```
  AI automation without the hype.
  Less manual work. More room to grow. ⚡
  ER nurse by day, AI builder by night.
  ```
  Link: `insightance.ai/go` (`docs/go/index.html`, UTM `utm_source=instagram&utm_medium=bio&utm_campaign=merkpagina`).
- **Beeldstijl (stap 2, goedgekeurd):** `outputs/instagram-stijl/_maak_v2.py` en `_overzicht-v2.png`.
- **Bron-content:** `outputs/linkedin-content-serie.md`, met Automation Simplified (±20 afleveringen), Myth Check (7), The Fork (10) en The Other Shift (12).
- **Demo's op de website:** `docs/demo.html` (factuur, WhatsApp), `docs/webshops.html` (rekentool), `docs/automations.html`. `docs/offerte-maker-demo.html` draagt de naam MHL en is daarom niet bruikbaar zoals hij is.
- **Server:** Hetzner VPS 91.99.172.227 (Ubuntu 22.04, 3,7 GB RAM, 61 GB vrij). CommandOS-bot draait als systemd-service `commandos-bot` onder gebruiker `commandos` in `/home/commandos/workspace`, met git pull/push-sync. ffmpeg staat er nog niet op.
- **Bestaand patroon:** afbeeldingen worden gemaakt met HTML + Playwright (Chrome), zie `outputs/logo-2026/_maak_logos.py`.

### Gaps or Problems Being Addressed

- Er is nog geen enkele post en geen proces om ze te maken.
- De oude LinkedIn-afbeeldingen (zwart-goud) passen niet meer en mogen niet terugkomen.
- Er zijn geen demo-pagina's zonder klantnamen om schermopnames van te maken.

---

## Afspraken (alles wat besloten is)

### Richting en toon
- **Taal: Engels**, definitief. Dezelfde lijn als de website en LinkedIn, gericht op de hele AI-markt.
- **Richting: "AI zonder hype".** Eerlijk over wat AI wel en niet kan, en ontkracht zowel de hype als de angst. Het oprichtersdagboek komt in de stories (The Other Shift). Actualiteiten worden altijd bekeken met de vraag "wat betekent dit echt voor jouw bedrijf?".
- **Informatief, niet formeel.** Mag schuren en uitdagen, maar altijd waar en onderbouwd.
- **Geen gezicht** (voorlopig). De naam staat alleen in de bio.
- **Nooit klantnamen** (MHL, FTUK of andere) noemen, in tekst noch beeld. Cases worden geanonimiseerd ("an installation company").

### Tekstregels (captions en slides)
1. **De eerste zin moet iemand laten stoppen met scrollen.** Dat is bij elke post het hoofddoel. Hij mag schuren en uitdagen, maar nooit onwaar of overdreven zijn.
2. **Compact.** Geen lappen tekst; korter dan de LinkedIn-versie. Richtlijn: hook + maximaal 2 korte alinea's + afsluiter.
3. **Schrijfregels uit LinkedIn gelden ook hier:** geen AI-toon (writing-style skill), geen gedachtestreepjes, geen reeks fragmentzinnen, niet elke zin op een eigen regel.
4. **Hashtags: 3 tot 5, steeds anders.** Passend bij het onderwerp van die post, geen vaste set. Nooit dezelfde hashtag in twee opeenvolgende posts. Bij actualiteiten een hashtag over dat nieuws (bijv. de naam van de tool of het bedrijf).
5. **Feitencheck:** elke claim of elk cijfer wordt online geverifieerd voordat het in een concept komt.

### Actualiteiten: dubbele controle
1. **Zoeken:** nieuws vinden dat relevant is voor ondernemers.
2. **Controle 1:** de oorspronkelijke bron lezen (niet alleen een samenvatting) en de kern vaststellen.
3. **Controle 2:** een tweede, onafhankelijke bron zoeken die hetzelfde bevestigt, en datum, cijfers en namen nalopen.
4. Faalt een van de twee controles, dan gaat het onderwerp niet door; er gaat dan geen concept naar Oussama.
5. **In Telegram altijd de bronlinks meesturen** (beide bronnen), zodat Oussama zelf nog kan controleren voordat hij goedkeurt.

### Beeldstijl
- Cover met grote, vette Inter-letters en een gekleurd kernwoord. Binnenslides licht, met een label-pil en een markering onder de kernzin. Cijferslide met een groot Playfair-cijfer. Myth Check met een groot aanhalingsteken en het citaat in Playfair.
- Vast op elke slide: bovenbalk met serienaam en teller, logo + @insightance.ai onderaan. Formaat 1080×1350 (4:5).
- **Kleurregel:** navy is de basis, ongeveer 2 op de 3 posts. Af en toe een andere kleurenset om te verrassen (zwart/rood, blauw/geel, groen/limoen, crème/oranje, rood, paars). Geen kleurenfestijn, geen voorspelbaar patroon, nooit twee keer dezelfde niet-navy kleur achter elkaar.
- **Nooit de oude zwart-gouden afbeeldingen.** Elke post krijgt een nieuwe afbeelding vanuit de tekst.

### Contentmix (±5 posts per week, geen vaste dagen of tijden)

| Soort | Inhoud | Hoe vaak |
|---|---|---|
| Carrousel | Automation Simplified, Myth Check, geanonimiseerde cases | 2 à 3 per week |
| Reel: bewegende tekst | Een onderwerp als korte video, 10 à 15 seconden | Afwisselend met demo-reels, samen ±2 per week |
| Reel: schermopname-demo | Fictieve demo die laat zien wat mogelijk is | |
| Actualiteit | AI-nieuws met de vraag "wat betekent dit voor jouw bedrijf?" | ±1 per week |
| Losse afbeelding | The Fork | Af en toe |
| Story-tekst | The Other Shift, achter de schermen | Voorstel; Oussama zet het op een eigen foto |

### Schermopname-demo's
- **Fictief, maar binnen wat echt kan.** Fictieve bedrijfsnamen en gegevens, maar alleen functionaliteit die we echt kunnen bouwen. Niets beloven wat niet bestaat.
- **Onderwerpen:** offerte-maker (gegevens intikken, versturen), dashboard (klikken, filteren, cijfers bekijken), binnenkomende factuur, WhatsApp-bericht, klantenservice-chat, rekentool, calculaties.
- **Zonder n8n.** De opnames worden gemaakt van eigen demo-pagina's, opgenomen in een echte browser die automatisch klikt en typt.
- 1080×1920 (9:16), geen muziek (die voegt Oussama zelf toe als hij wil).

### Goedkeuren via Telegram
- Elk concept komt in Telegram binnen met: de slides of de video, de caption, de hashtags en bij actualiteiten de bronlinks.
- Knoppen: **✅ Goedkeuren**, **✏️ Aanpassen**, **❌ Overslaan**.
- Bij ✏️: Oussama typt of spreekt in wat er anders moet, de agent past het aan en stuurt het opnieuw.
- Bij ✅ (fase 1): de agent stuurt de bestanden in originele kwaliteit plus de caption in een kopieerbaar blok. Oussama plaatst zelf en drukt daarna op **📤 Geplaatst**, zodat de agent bijhoudt wat er online staat.
- Niets wordt ooit geplaatst zonder ✅.

### Wat bij Oussama blijft
Goedkeuren, in fase 1 zelf plaatsen, muziek, polls en stickers (kan alleen in de app), eigen sfeerbeelden en story-foto's.

---

## Proposed Changes

### Summary of Changes

- Agent (Claude Agent SDK) die dagelijks op de server draait en concepten klaarzet.
- Deterministische tools voor renderen (carrousel, tekst-reel, demo-opname), wachtrij/administratie en Telegram.
- Fictieve demo-pagina's voor schermopnames (niet op de live site).
- Workflow-SOP met alle bovenstaande afspraken als vaste instructie voor de agent.
- Eigen Telegram-bot voor content, los van CommandOS.

### New Files to Create

| File Path | Purpose |
|---|---|
| `workflows/instagram_content.md` | SOP: alle afspraken hierboven (toon, tekstregels, hashtags, kleurregel, dubbele feitencheck, geen klantnamen, contentmix) |
| `tools/instagram/bron_inlezen.py` | Leest `outputs/linkedin-content-serie.md` in en zet onderwerpen als items in de wachtrij |
| `tools/instagram/wachtrij.py` | Administratie in SQLite (tabel `instagram_posts`): onderwerp, soort, kleurenset, gebruikte hashtags, status (concept / goedgekeurd / geplaatst / overgeslagen), bronnen |
| `tools/instagram/render_carrousel.py` | Carrousel-slides in de goedgekeurde stijl (voortbouwend op `_maak_v2.py`), kiest de kleurenset volgens de kleurregel |
| `tools/instagram/render_tekst_reel.py` | Reel met bewegende tekst: HTML-animatie, opgenomen met Playwright, omgezet naar mp4 (ffmpeg) |
| `tools/instagram/opname_demo.py` | Schermopname-reel: Playwright opent een demo-pagina, klikt en typt volgens een script, neemt op en levert een mp4 van 1080×1920 |
| `tools/instagram/demos/*.html` | Fictieve demo's: offerte-maker, dashboard, factuur, WhatsApp, klantenservice, rekentool, calculatie (huisstijl, fictieve namen) |
| `tools/instagram/telegram_review.py` | Content-bot: concepten versturen met knoppen, reacties (✅/✏️/❌/📤) verwerken |
| `apps/content/agent.py` | De agent zelf: kiest wat er gemaakt moet worden, schrijft teksten, doet feitenchecks (webzoeken), roept de tools aan, verwerkt aanpassingen |
| `apps/content/README.md` | Hoe het draait, hoe te herstarten |
| server: `instagram-content.service` + `.timer` | systemd: bot altijd aan, agent dagelijks |

### Files to Modify

| File Path | Changes |
|---|---|
| `CLAUDE.md` | Workspace-structuur (tools/instagram, apps/content, workflow) en korte uitleg |
| `todo/README.md` | Item "Contentagent voor Instagram" bijwerken naar "in bouw" / weghalen na oplevering |
| `reference/utm-links.md` | Al bijgewerkt met `/go` |
| `.env` (server) | `CONTENT_BOT_TOKEN`, `CONTENT_CHAT_ID` |

### Files to Delete

Geen.

---

## Design Decisions

### Key Decisions Made

1. **Draait op de eigen server**, net als CommandOS. Werkt ook als de laptop uit staat. (Besluit Oussama.)
2. **Aparte Telegram-bot voor content.** Twee programma's kunnen niet tegelijk berichten van dezelfde bot ophalen. Een aparte bot voorkomt dat de contentagent en CommandOS elkaar in de weg zitten, en houdt goedkeuringen overzichtelijk gescheiden van gewone chats.
3. **Tekst door Claude, beeld door vaste scripts.** Het schrijven en feitenchecken vraagt denkwerk, het renderen moet elke keer identiek zijn (WAT-principe).
4. **Demo's als eigen HTML-pagina's, niet op de live site.** Zo kunnen ze fictieve namen dragen zonder dat ze per ongeluk als echte klantpagina gevonden worden, en n8n blijft erbuiten.
5. **Wachtrij in SQLite op de server.** Voorkomt dubbele onderwerpen, bewaakt de kleurregel en hashtag-afwisseling.
6. **Buffer in plaats van vaste planning.** De agent zorgt dat er steeds ±3 goedgekeurde of klaarstaande concepten zijn, en stuurt er maximaal 2 per dag, zodat Telegram niet volloopt.

### Alternatives Considered

- **Integreren in de CommandOS-bot:** afgewezen, omdat het risico geeft dat de twee functies elkaar storen en de berichten door elkaar gaan lopen.
- **Schermopnames van n8n:** afgewezen door Oussama, n8n blijft erbuiten.
- **Vaste post-tijden zoals op LinkedIn:** afgewezen, Instagram moet levendig en onvoorspelbaar aanvoelen.

### Open Questions

1. **Nieuwe bot aanmaken:** Oussama maakt in Telegram via @BotFather een bot aan (±1 minuut, ik loop het mee door) en geeft de token. Naamvoorstel: "Insightance Content".
2. **Kosten Claude-gebruik:** wordt tijdens de bouw gemeten op de eerste concepten en gerapporteerd voordat de agent dagelijks gaat draaien.

---

## Step-by-Step Tasks

### Step 1: Workflow-SOP schrijven
Alle afspraken uit dit plan vastleggen als instructie voor de agent.
**Files affected:** `workflows/instagram_content.md`

### Step 2: Wachtrij en bron
- `bron_inlezen.py` haalt alle onderwerpen uit de LinkedIn-serie.
- `wachtrij.py` met tabel `instagram_posts`, inclusief logica voor kleurregel en hashtag-afwisseling.
**Files affected:** `tools/instagram/bron_inlezen.py`, `tools/instagram/wachtrij.py`

### Step 3: Carrousel-renderer
Van `_maak_v2.py` een herbruikbare tool maken die tekst + soort + kleurenset omzet naar slides. Testen met 3 onderwerpen.
**Files affected:** `tools/instagram/render_carrousel.py`

### Step 4: Reels met bewegende tekst
HTML-animatie + Playwright-opname + ffmpeg naar mp4 (1080×1920). Eén testreel maken en ter beoordeling voorleggen.
**Files affected:** `tools/instagram/render_tekst_reel.py`

### Step 5: Fictieve demo's + schermopnames
- Demo-pagina's bouwen (beginnen met offerte-maker en dashboard, daarna factuur, WhatsApp, klantenservice, rekentool, calculatie).
- `opname_demo.py` met per demo een klik- en typscript, realistisch tempo (zichtbaar typen, muisbewegingen).
- Eerste twee demo-reels ter beoordeling voorleggen.
**Files affected:** `tools/instagram/demos/*.html`, `tools/instagram/opname_demo.py`

### Step 6: Telegram-content-bot
- Oussama maakt de bot aan via @BotFather.
- `telegram_review.py`: versturen met knoppen, ✏️-feedback (tekst en spraak) terugsturen naar de agent, ✅ levert het plaatsklare pakket, 📤 markeert als geplaatst.
**Files affected:** `tools/instagram/telegram_review.py`, `.env`

### Step 7: De agent
- `apps/content/agent.py`: buffer bewaken, onderwerp kiezen, tekst schrijven volgens de SOP, feitencheck (dubbel bij actualiteiten), tools aanroepen, naar Telegram sturen, aanpassingen verwerken.
- Testrun lokaal: 5 concepten (2 carrousels, 1 tekst-reel, 1 demo-reel, 1 actualiteit).
**Files affected:** `apps/content/agent.py`, `apps/content/README.md`

### Step 8: Naar de server
- ffmpeg en Playwright/Chrome installeren, fonts meenemen.
- systemd-service (bot altijd aan) en timer (agent dagelijks), draaiend onder gebruiker `commandos`.
- End-to-end test vanaf de telefoon.
**Files affected:** server-configuratie

### Step 9: Documentatie
CLAUDE.md, todo/README.md en geheugen bijwerken; committen en pushen.
**Files affected:** `CLAUDE.md`, `todo/README.md`

### Fase 2 (later, apart plan)
Automatisch plaatsen na ✅ via de officiële "Instagram API with Instagram Login" (geen Facebook-pagina nodig, wel het creator-account dat er al is). Carrousels en reels kunnen zo geplaatst worden; muziek, polls en stickers niet.

---

## Connections & Dependencies

### Files That Reference This Area
- `outputs/linkedin-content-serie.md` (bron, wordt alleen gelezen)
- `docs/go/index.html` en `reference/utm-links.md` (bio-link)

### Updates Needed for Consistency
- CLAUDE.md workspace-structuur
- Geheugen: `project_instagram_contentagent.md`

### Impact on Existing Workflows
- CommandOS blijft ongewijzigd (aparte bot en service).
- LinkedIn-ritme blijft ongewijzigd; nieuwe LinkedIn-posts worden automatisch ook bron voor Instagram.

---

## Validation Checklist

- [ ] SOP bevat alle afspraken uit dit plan
- [ ] Carrousel volgt de goedgekeurde stijl en de kleurregel
- [ ] Geen enkele klantnaam in tekst of beeld (automatische check op "MHL", "FTUK" en bekende klantnamen)
- [ ] Hashtags verschillen per post, nooit dezelfde in twee opeenvolgende posts
- [ ] Actualiteit komt alleen door na twee controles en bevat twee bronlinks in Telegram
- [ ] Tekst-reel en demo-reel zijn 1080×1920 mp4 en zien er echt uit
- [ ] ✅ / ✏️ / ❌ / 📤 werken vanaf de telefoon
- [ ] Er wordt niets geplaatst zonder ✅
- [ ] Draait op de server terwijl de laptop uit staat
- [ ] CLAUDE.md bijgewerkt

---

## Success Criteria

1. Oussama krijgt elke week ±5 concepten in Telegram die hij met één tik kan goedkeuren.
2. Minimaal 4 van de 5 eerste concepten zijn zonder of met één aanpassing goed genoeg om te plaatsen.
3. Nul feitelijke fouten in geplaatste posts.
