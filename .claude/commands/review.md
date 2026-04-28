# Review

> Begeleide wekelijkse review via de GTD-methodologie. Verwerkt inbox, doorloopt alle project- en actielijsten, scant gebieden en ooit-misschien, herbouwt het dashboard. Wekelijks draaien (zondag aanbevolen). Doel: 30-60 minuten.

---

## Instructies

Je voert een **GTD wekelijkse review** uit voor Oussama. Dit is de belangrijkste gewoonte in het systeem — het houdt de GTD-bestanden betrouwbaar en volledig. Volg de fasen hieronder interactief.

---

## Fase 1: Context laden

Lees alle GTD-bestanden:
1. `gtd/dashboard.md`
2. `gtd/inbox.md`
3. `gtd/projects.md`
4. `gtd/next-actions.md`
5. `gtd/waiting-for.md`
6. `gtd/someday-maybe.md`
7. `gtd/areas.md`
8. `gtd/review-checklist.md`

---

## Fase 2: HELDER WORDEN

**Doel:** Leeg alle inboxen en leg alles vast wat in je hoofd zweeft.

### 2.1 Verwerk Inbox
1. Lees `gtd/inbox.md`
2. Als items bestaan, doorloop elk via de GTD-beslisboom
3. Stuur elk item naar het juiste GTD-bestand
4. Leeg inbox naar nul

### 2.2 Geestelijke Opruiming
1. Presenteer triggerlijst categorieën uit `gtd/review-checklist.md`
2. Loop door elke categorie — vraag "Nog open lussen hier?"
3. Leg alles nieuws vast in inbox, verwerk het dan

**STOP na HELDER WORDEN en bevestig voordat je doorgaat.**

---

## Fase 3: ACTUEEL WORDEN

**Doel:** Zorg dat alle lijsten de realiteit weerspiegelen. Elk project heeft een volgende actie.

### 3.1 Review Agenda
- Vraag over de afgelopen week: gemiste follow-ups?
- Vraag over de komende 2 weken: voorbereiding nodig?

### 3.2 Loop Volgende Acties door
- Presenteer elke contextsectie uit `gtd/next-actions.md`
- Per actie: "Klaar? Nog relevant? Aanpassen?"

### 3.3 Loop Wachten-Op door
- Presenteer elk item uit `gtd/waiting-for.md`
- Markeer overdue items — stel follow-up voor

### 3.4 Loop Projecten door
- Presenteer elk project uit `gtd/projects.md`
- Per project: "Nog actief? Voortgang? Statuswijziging?"
- **Vastgelopen-project-test:** Heeft elk actief project minstens één volgende actie?

**STOP na ACTUEEL WORDEN en bevestig voordat je doorgaat.**

---

## Fase 4: CREATIEF WORDEN

**Doel:** Kijk omhoog en naar buiten.

### 4.1 Scan Ooit/Misschien
- Presenteer categorieën uit `gtd/someday-maybe.md`
- "Iets klaar om te activeren? Iets te verwijderen? Nieuwe ideeën?"

### 4.2 Scan Gebieden
- Presenteer `gtd/areas.md` met huidige gezondheidsnoten
- "Enig gebied verwaarloosd? Ontbrekend project?"

### 4.3 Open Brainstorm
- "Grote ideeën of strategische gedachten van deze review?"

---

## Fase 5: HERBOUWEN

**Doel:** Dashboard bijwerken met verse data.

1. Draai `python scripts/refresh_dashboard.py`
2. Update "Laatste Review" naar vandaag
3. Zet "Volgende Review" op volgende week
4. Rapporteer samenvatting

---

## Kritieke Regels

- **Interactief** — Dit is een gesprek, geen monoloog
- **Sla geen fasen over** — Elke fase heeft een doel
- **Specifieke acties** — "Nadenken over pricing" is geen actie. "Drie prijsopties uitwerken in een document" wel.
- **Elk project heeft een volgende actie nodig**
- **Update bestanden direct** — Niet alleen bespreken, ook schrijven
