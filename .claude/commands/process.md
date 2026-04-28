# Process

> Verwerk de GTD inbox naar nul. Loop elk item door de GTD-beslisboom — stuur naar projecten, acties, wachten-op, ooit-misschien of prullenbak.

---

## Instructies

Je helpt Oussama zijn **GTD inbox naar nul te verwerken**. Elk item krijgt een beslissing — niets blijft in de inbox.

---

## Stap 1: Inbox laden

1. Lees `gtd/inbox.md`
2. Als de inbox leeg is: "Inbox staat op nul — niets te verwerken." en stop.
3. Tel items en rapporteer: "Je hebt [N] items in de inbox. Laten we ze verwerken."

Lees ook voor context:
- `gtd/projects.md` — bestaande projecten
- `gtd/next-actions.md` — bestaande acties
- `gtd/waiting-for.md` — gedelegeerde items
- `gtd/someday-maybe.md` — backlog

---

## Stap 2: Verwerk elk item

Presenteer items **één voor één**. Doorloop voor elk item de GTD-beslisboom:

### Beslisboom

```
"Is dit uitvoerbaar?"
  |
  NEE --> Vraag:
  |   "Weggooien?" --> Verwijder uit inbox
  |   "Ooit/Misschien?" --> Verplaats naar gtd/someday-maybe.md
  |   "Referentie?" --> Noteer waar het te bewaren
  |
  JA --> Vraag:
      "Is dit een meerstappenresultaat?" --> JA: Toevoegen aan gtd/projects.md
      "Wat is de eerstvolgende fysieke actie?"
      |
      < 2 minuten? --> "Doe het nu."
      |
      Iemand anders moet het doen?
      |   JA --> Toevoegen aan gtd/waiting-for.md (wie, wat, datum)
      |
      Ik moet het doen, > 2 min
          Specifieke datum/tijd? --> Agenda-item
          Zo snel mogelijk? --> Toevoegen aan gtd/next-actions.md (kies context)
```

### Contextopties voor Volgende Acties
- **@me** — Alleen jij kunt dit (beslissingen, creatief werk, persoonlijke taken)
- **@claude** — Werk te doen met Claude Code
- **@calls** — Telefoontjes of videogesprekken
- **@errands** — Fysieke, persoonlijke taken
- **@think** — Creatief nadenken, brainstormen
- **@record** — Dingen vastleggen of opschrijven

---

## Stap 3: Routeer en verwijder

Bij elk verwerkt item:
1. Schrijf het item direct naar het bestemmingsbestand
2. Verwijder het item uit `gtd/inbox.md`
3. Als een nieuw project is aangemaakt, zorg dat het minstens één volgende actie heeft

---

## Stap 4: Afronden

Na alle items:
1. Bevestig dat `gtd/inbox.md` leeg is
2. Draai `python scripts/refresh_dashboard.py` om het dashboard bij te werken
3. Rapporteer samenvatting: verwerkte items, nieuwe projecten, nieuwe acties, wachten-op items

---

## Kritieke Regels

- **Eén item tegelijk** — Niet batch-verwerken zonder input per item
- **Bovenste item eerst** — Verwerk van boven naar beneden
- **Volgende actie moet fysiek zijn** — "Het project aanpakken" is geen actie. "Kapper Hassan bellen om afspraak te maken" wel.
- **Twee-minutenregel** — Als de actie < 2 minuten duurt, doe het nu
- **Leg het niet terug** — Elk item verlaat de inbox. Nooit "ik doe het later."
