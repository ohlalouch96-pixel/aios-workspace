# Plan: Verhaal-reels in robotkwaliteit (nieuw videosjabloon voor de contentagent)

**Created:** 2026-11-24
**Status:** Geparkeerd (24-11: Oussama kiest voor losse video's op idee, met de hand gebouwd)
**Request:** Een videosjabloon in de stijl van de robotvideo (#17), zodat de agent zelfstandig per onderwerp zulke reels maakt (beeld en muziek kiezen) met goedkeuring in Telegram.

---

## Overview

### What This Plan Accomplishes

De robotvideo is met de hand gemaakt: één HTML-bestand van 210 regels, speciaal voor dat ene verhaal. Dit plan maakt er een herbruikbaar sjabloon van ("verhaal-reel"). De agent vult het sjabloon per onderwerp met de inhoud:
- een hook in blokken;
- een ommekeer;
- drie mini-verhalen op verschillende plekken en tijden;
- een slot.

Daarnaast kiest de agent een opvallende stockclip en een muziekstuk uit een vaste bibliotheek. Het resultaat is een reel van ±15 seconden in robotkwaliteit, die via de bestaande route in Telegram ter goedkeuring komt.

### Why This Matters

Oussama noemt de robotvideo zijn beste video tot nu toe. Dat komt door vijf dingen: de hook, het beeld, de wissel tussen licht en donker, het tempo en de muziek. De automatische video's gebruiken steeds dezelfde nagebouwde schermen en voelen daardoor vlakker.

Meer reels van dit niveau zorgen voor meer bereik en profielbezoeken op @insightance.ai. Zo groeit het publiek richting de eerste betalende klant, zonder dat het Oussama tijd kost. Dat raakt de KPI's "Task Automation %" en "Away-From-Desk Autonomy".

---

## Current State

### Relevant Existing Structure

**Handgemaakte robotvideo (#17)**
- `tools/instagram/demos/robot.html` maakt de scènes met de hand:
  - de robot met hookblokken;
  - een kras plus NOPE;
  - drie mini-verhalen:
    - sc1: avond, paars/oranje, "9:04 PM. You're at dinner." met een kaart "AI answered. Job booked.";
    - sc2: strand, lichtblauw/geel;
    - sc3: ochtend, lavendel/perzik;
  - het slot.
  - De achtergronden zijn CSS-verlopen, geen video.
- `tools/instagram/demos/robot.json` bevat de tijdlijn en de geluidseffecten (klik, kras, stempel, swoosh, klok, ding, check, kassa, chime). Bij "voorbereiding" staat hoe de robotclip in losse beelden is geknipt.

**Bestaande tools**
- `tools/instagram/opname_demo.py` neemt een demopagina beeld voor beeld op en levert reel.mp4 en cover.jpg (1080x1920, 30 fps). De tool bestuurt de klok, dus elk frame is scherp.
- `tools/instagram/geluid.py` maakt de geluidseffecten.
- `tools/instagram/stem.py` en `render_stem_video.py` zijn de stemvideo's met Eric. Hier zit al een ffmpeg-mix van audio in.
- `tools/instagram/hookscore.py` en `hooks.json` scoren de hook (minimaal 60).
- `tools/instagram/diensten.py` bevat de 28 diensten, de bron voor de onderwerpen.

**Agent en wachtrij**
- `apps/content/agent.py` regelt per soort: `kies_soort`, `render()`, `opslaan()`, plus de Telegram-route via `telegram_review.py`.
- `tools/instagram/wachtrij.py` regelt de kleurregel (`echte_kleur`, `BLAUWIG`) en de wachtrij in `data/data.db`.

**Stock en muziek**
- `.tmp/instagram/stock/` bevat twee met de hand gedownloade clips: Pixabay 145864 (robot) en Pexels 8466294.
- De muziek van de robotvideo is één keer met de hand ingemixt. Er is geen muziekbibliotheek en geen inmixstap in de agent.

### Gaps or Problems Being Addressed

1. **Elke video van dit niveau is maatwerk.** De scènes, teksten, tijden en geluiden staan vast in HTML. De agent kan geen nieuwe maken.
2. **Er is geen bibliotheek met opvallend bewegend beeld.** De agent kan geen clip kiezen.
3. **Er is geen muziekbibliotheek en geen automatische inmix.** Oussama kan het muziekvolume in Instagram niet regelen (22-11), dus de muziek moet erin zitten.
4. **De automatische reels (stem- en demo-video's) ogen steeds hetzelfde.** Steeds een telefoon-, chat- of agendascherm met andere tekst (feedback van 22-11).

---

## Proposed Changes

### Summary of Changes

- Eén generiek sjabloon `verhaal.html`. Het speelt een spec af met vier delen: hook over clip, ommekeer, 3 mini-verhalen, slot. Het is ontworpen in de robotstijl.
- Een vaste set **sfeerdecors** voor de mini-verhalen. Elk decor heeft een tijd en een plek, en een kleurverloop dat bij die sfeer past:
  avond, strand, vroege ochtend, kantoor, auto, sportschool, keuken, vliegveld, regen, nacht.
- Een **clipbibliotheek** van ±15-20 opvallende stockclips:
  - van Pixabay en Pexels, gratis en commercieel bruikbaar;
  - één keer gekozen, in losse beelden geknipt en met tags beschreven.
- Een **muziekbibliotheek** van ±10 nummers:
  - met de licentie Pixabay Content License;
  - met tags voor tempo en sfeer, en een "stop"-moment voor de kras.
- Een **inmixstap**: muziek plus geluidseffecten onder de opname, met ffmpeg op de server.
- Een **nieuw soort post** in de agent, `verhaal_reel`:
  - Claude schrijft de spec;
  - hookscore en controleregels;
  - kiezen van clip, decors en muziek;
  - renderen en naar Telegram.
- De **workflow, de planning en CLAUDE.md** worden bijgewerkt.

### New Files to Create

| File Path | Purpose |
| --- | --- |
| `tools/instagram/video/verhaal.html` | Generiek sjabloon. Speelt een verhaal-spec af (hook over clip, ommekeer, 3 mini-verhalen met decor en uitkomstkaart, slot) op de klok van de opnametool |
| `tools/instagram/video/decors.css` | De sfeerdecors als kleurverlopen plus tekstkleuren, afgeleid van sc1-sc3 in robot.html |
| `tools/instagram/render_verhaal.py` | Spec naar frames (via de klok-aanpak van opname_demo), dan geluid en muziek erin mixen, dan reel.mp4 en cover.jpg, plus controleregels |
| `tools/instagram/clips.json` | Clipbibliotheek: id, bron-URL, licentie, tags (robot, stad, kantoor, telefoon, ...), knipmoment (start/duur), map met frames |
| `tools/instagram/muziek.json` | Muziekbibliotheek: bestand, bron-URL, licentie, bpm, sfeer, aanbevolen stopmoment |
| `tools/instagram/bibliotheek.py` | Eenmalig en bij aanvullen: clips en muziek downloaden, clips in beelden knippen (ffmpeg), en controleren dat alles aanwezig is |

### Files to Modify

| File Path | Changes |
| --- | --- |
| `apps/content/agent.py` | Nieuw soort `verhaal_reel`: prompt en schema voor Claude, keuze van clip, decors en muziek, `render()` tak, toevoegen aan `REEL_SOORTEN` en `kies_soort` |
| `tools/instagram/telegram_review.py` | `verhaal_reel` in `REELS` en `SOORT_LABEL` ("Reel · verhaal") |
| `tools/instagram/wachtrij.py` | `echte_kleur` voor verhaal-reels (de kleur van het slot) |
| `workflows/instagram_content.md` | Nieuwe sectie "Verhaal-reels": opbouw, regels, bibliotheken, aanvullen, wat Oussama beoordeelt |
| `CLAUDE.md` | De structuur in het Instagram-blok aanvullen (render_verhaal.py, video/verhaal.html, clips.json, muziek.json) |
| `tools/instagram/demos/robot.json` | Niet aanpassen; blijft als referentie en als origineel van #17 |

### Files to Delete (if any)

Geen.

---

## Design Decisions

### Key Decisions Made

1. **Een sjabloon met vaste opbouw, geen vrije video-AI.** De robotvideo werkt door zijn structuur: schok, ommekeer, drie herkenbare momenten, slot. Die structuur leggen we vast, en de agent varieert alleen de inhoud. Dat is betrouwbaar (WAT-principe) en kost per video bijna niets.
2. **De sfeerdecors zijn getekende kleurverlopen, geen stockvideo.** In de robotvideo zijn strand en avond ook getekend, en juist die wissel tussen licht en donker viel Oussama op. Getekende decors zijn altijd scherp, hebben de juiste kleur en vergen geen zoekwerk.
3. **Echt bewegend beeld alleen in de hook.** Daar levert het de meeste aandacht op, net als de robot. Eén clip per video uit een gecureerde bibliotheek.
4. **Vaste bibliotheken in plaats van live zoeken.** Een zoekmachine levert vaak slechte of irrelevante clips op. Een eenmalig gekozen set van ±15-20 clips en ±10 nummers garandeert de kwaliteit. Aanvullen kan later.
5. **De muziek gaat er altijd in.** Oussama kan het volume in Instagram niet regelen (22-11). De muziek stopt op de kras, net als bij de robot. Daarna zijn er alleen effecten tot het slot.
6. **Geen stem in verhaal-reels.** De robotvideo werkt zonder stem. Dat scheelt ElevenLabs-tegoed, en de stemvideo's blijven bestaan als eigen soort.
7. **Variatieregel geldt ook hier.** De kleur van het slot wordt de kleur van de post in de weekplanning, en twee reels op één dag blijven verboden.

### Alternatives Considered

- **Video-AI (Runway, Sora, Kling) voor de hele video:** afgewezen. Het kost per video, de kwaliteit wisselt, tekst in beeld lukt slecht, en de controle is lastig.
- **Live zoeken via de Pixabay-API per video:** voor nu afgewezen, omdat de kwaliteit te wisselend is. Pixabay heeft wel een gratis API voor video, dus dit kan later voor het aanvullen van de bibliotheek. Voor muziek bestaat geen officiële API.
- **Canva-sjablonen:** eerder al afgeraden (22-11). Ze draaien niet zelfstandig.
- **Elke video met de hand bouwen zoals de robot:** hoogste kwaliteit, maar het kost per video veel bouwtijd en draait dus niet zonder Claude-sessie.

### Open Questions (if any)

1. **Hoe vaak per week?** Voorstel: 2 van de 5 reels per week verhaal-reels, de rest stem- en demo-video's. Meer kan later, als de eerste goed scoren.
2. **De muziek kiezen: samen of door mij?** Voorstel: ik kies 15 kandidaten, Oussama luistert ze in één sessie (±15 min) en kiest er 10.
3. **De clips kiezen: samen of door mij?** Voorstel: ik zet ±25 kandidaten klaar als één overzichtsbeeld, en Oussama streept door wat niet past.
4. **Mag de robotclip in elke video terugkomen** als vaste "huisrobot", of juist nooit meer? Een herkenbaar karakter kan merkkracht geven, maar kan ook gaan vervelen.

---

## Step-by-Step Tasks

### Step 1: Licenties en bronnen bevestigen

Controleren (WebSearch/WebFetch) dat de licenties van Pixabay en Pexels gebruik in advertenties toestaan, zonder naamsvermelding. Pixabay-muziek kan soms een Content ID-claim krijgen op Instagram. Uitzoeken hoe dat zit en hoe het te voorkomen is, bijvoorbeeld met nummers zonder "Content ID registered".

**Actions:**
- Licentieteksten nalezen en de conclusie in de workflow zetten.
- Vastleggen: per clip en per nummer de bron-URL en de licentie in de bibliotheek.

**Files affected:**
- `workflows/instagram_content.md`

---

### Step 2: Bibliotheken samenstellen (samen met Oussama)

**Actions:**
- ±25 kandidaatclips zoeken: robot, stad bij nacht, kantoor, telefoon die rinkelt, kassa, klok, laptop, drukke straat, rustig strand, en andere clips die schokkend of opvallend zijn.
- Eén overzichtsbeeld maken, openen (Invoke-Item), en Oussama streept door wat niet past.
- 15 muziekkandidaten zoeken: uptempo, speels, ±110-130 BPM, zonder zang.
- De muziekkandidaten als één afspeelbaar bestand klaarzetten. Oussama kiest er 10.
- `bibliotheek.py` downloadt alles naar de server (`.tmp/instagram/stock/`, `.tmp/instagram/muziek/`) en knipt de clips in beelden.
- `clips.json` en `muziek.json` vullen.

**Files affected:**
- `tools/instagram/bibliotheek.py`, `tools/instagram/clips.json`, `tools/instagram/muziek.json`

---

### Step 3: Generiek sjabloon bouwen

De robotvideo omzetten naar een sjabloon dat een spec afspeelt. Robot.html is de basis voor de opbouw, het tempo en de animaties: woorden die één voor één verschijnen, de kras, de stempel, de flits, de kaarten met "✓"-uitkomst, en het slot met logo in de vaste merkkleuren.

**Actions:**
- `video/verhaal.html` laat de spec van buiten in: `window.__spec`, zoals de bestaande pagina's.
- `video/decors.css` bevat ±10 decors.
- Het tempo is gelijk aan de robot: totaal ±14-16 s, hook ±3,3 s, elk mini-verhaal ±1,5-2 s.
- Tekstlengtes worden begrensd, zodat alles in beeld past (zie de controleregels in stap 4).

**Files affected:**
- `tools/instagram/video/verhaal.html`, `tools/instagram/video/decors.css`

---

### Step 4: Renderer met inmix en controleregels

**Actions:**
- `render_verhaal.py` maakt per frame een opname op de klok van de tool, net als `opname_demo.py`. Waar mogelijk worden functies hergebruikt, niet gekopieerd.
- De geluidseffecten worden automatisch op de vaste momenten gezet via `geluid.py`.
- De muziek wordt ingemixt met ffmpeg:
  - fade-in;
  - stop op de kras;
  - volume onder de effecten.
- Controleregels:
  - geen tekst buiten beeld;
  - hook minimaal 60 (hookscore);
  - maximaal aantal woorden per regel;
  - totale duur 13-17 s;
  - het logo in de merkkleuren;
  - geen klantnamen.
- De uitvoer is gelijk aan de andere reels: `reel.mp4`, `cover.jpg` en een `controle.png` met beelden over de tijd verdeeld.

**Files affected:**
- `tools/instagram/render_verhaal.py`

---

### Step 5: Proef met de robot als spec

De robotvideo nabouwen als spec en die door het nieuwe sjabloon halen. Dat is de lat: als het naast #17 even goed oogt, werkt het sjabloon.

**Actions:**
- De robot-spec renderen en naast de originele #17 zetten, zelf vergelijken, en beide openen voor Oussama.
- Proefcontext geven: wat de proef is, waarom, dat er geluid is, en wat hij moet beoordelen (tempo, decors, muziek).

**Files affected:**
- `.tmp/instagram/` (proef, wegwerp)

---

### Step 6: Agent koppelen

**Actions:**
- Nieuw soort `verhaal_reel` in `agent.py`.
- Claude krijgt als prompt:
  - de opbouw;
  - een voorbeeld (robot);
  - een dienst uit `diensten.py`;
  - de beschikbare decors, clips (tags) en muziek (sfeer).
- Claude levert een spec, de caption (max ±35 woorden) en hashtags.
- De agent kiest of controleert de clip en de muziek: niet dezelfde als de vorige verhaal-reel.
- `render()` tak, `opslaan()`, en naar Telegram met de bestaande knoppen.
- `REELS`, `SOORT_LABEL`, `echte_kleur` en `kies_soort` bijwerken. Het aandeel volgt de afspraak uit open vraag 1.

**Files affected:**
- `apps/content/agent.py`, `tools/instagram/telegram_review.py`, `tools/instagram/wachtrij.py`

---

### Step 7: Eerste echte concepten

**Actions:**
- Op de server 2 verhaal-reels laten maken over 2 verschillende diensten.
- Eerst hier in de chat tonen (de bestanden openen), en pas na akkoord naar Telegram.
- Kosten noteren: Claude-tokens per video.

---

### Step 8: Documentatie en afronding

**Actions:**
- `workflows/instagram_content.md` krijgt een sectie "Verhaal-reels".
- `CLAUDE.md` bijwerken (Instagram-blok).
- Memory bijwerken.
- Alleen de eigen bestanden committen (expliciete `git add`) en pushen.
- Op de server pullen en de bot herstarten.

---

## Connections & Dependencies

### Files That Reference This Area

- `apps/content/agent.py` (soortkeuze, render, opslaan)
- `tools/instagram/telegram_review.py` (REELS, labels, weekplanning)
- `tools/instagram/wachtrij.py` (kleurregel)
- de servertimers `instagram-agent.timer` en `instagram-vullen.timer` (roepen de agent aan)

### Updates Needed for Consistency

- Workflow, CLAUDE.md en memory (`project_instagram_video_kwaliteit_en_concurrenten.md`).

### Impact on Existing Workflows

- Er verschijnt een nieuw soort reel in de voorraad. De verhouding beeld/reel (5/5 per week) blijft gelijk.
- De stem- en demovideo's blijven bestaan.
- De weekplanning past de variatieregel automatisch toe.
- Geen extra vaste kosten:
  - Pixabay en Pexels zijn gratis;
  - Claude-kosten per video zijn vergelijkbaar met een carrousel;
  - geen ElevenLabs.

---

## Validation Checklist

- [ ] De robot-spec door het sjabloon lijkt in tempo, decor en muziek op #17 (Oussama keurt)
- [ ] `render_verhaal.py` levert reel.mp4 (1080x1920, 30 fps), cover.jpg en controle.png zonder fouten
- [ ] De muziek stopt op de kras, en de effecten zijn hoorbaar boven de muziek
- [ ] Alle controleregels slaan aan op een bewust foute spec (te lange tekst)
- [ ] De agent maakt op de server zelfstandig 2 verschillende verhaal-reels
- [ ] De weekplanning zet geen twee reels op één dag en past de kleurregel toe
- [ ] Bronnen en licenties staan in clips.json en muziek.json
- [ ] Workflow en CLAUDE.md zijn bijgewerkt, alles is gecommit en op de server gepulld

---

## Success Criteria

1. De agent maakt zonder hulp een verhaal-reel die Oussama in kwaliteit naast de robotvideo vindt passen.
2. Twee opeenvolgende verhaal-reels gebruiken een andere clip, andere decors en andere muziek.
3. Er komen geen extra maandkosten bij.

---

## Notes

**Bouwtijd (schatting):**
- Stap 1-2, bibliotheken: ±1,5 uur, waarvan ±30 minuten van Oussama (kiezen).
- Stap 3-5, sjabloon, renderer en proef: ±3-4 uur.
- Stap 6-8, agent, eerste concepten en documentatie: ±2 uur.
- **Totaal: ±6-8 uur bouwen, verspreid over 2-3 sessies.**

**Later mogelijk:**
- automatisch aanvullen van de clipbibliotheek via de Pixabay-API;
- A/B: verhaal-reel versus stemvideo, via de wekelijkse resultaten;
- de concurrentenronde (optie C) kan aangeven welke hooks winnen.

**Wacht met bouwen tot na de advertentieresultaten van de robotvideo (week van 30-11).** Scoort de robot duidelijk beter dan de rest, dan is dat de bevestiging om dit te bouwen.
