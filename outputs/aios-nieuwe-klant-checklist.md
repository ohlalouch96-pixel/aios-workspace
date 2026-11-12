# Checklist: AIOS bouwen voor een nieuwe klant

**Status:** Klaar om te gebruiken zodra een klant ja zegt (eerste kandidaat: de fysiotherapeut, vervolgafspraak rond 25-11-2026).
**Belangrijk:** dit wordt ALTIJD in een nieuwe, losse map gebouwd, nooit binnen `aios-starter-kit\aios-starter-kit` (jouw eigen workspace). Zo blijft jouw eigen AIOS volledig gescheiden, ook qua geheugen van Claude.

---

## Stap 1: Nieuwe map aanmaken

Maak een lege map op je laptop, bijvoorbeeld op het Bureaublad: `aios-[klantnaam]` (bijv. `aios-fysio`).

## Stap 2: Het lege sjabloon uitpakken

Pak dit bestand uit in die nieuwe map:
```
C:\Users\oussa\Downloads\aios-starter-kit.zip
```
Dit is het oorspronkelijke, nog ongebruikte sjabloon (lege context-bestanden, lege CLAUDE.md).

## Stap 3: De modules erbij kopiëren

Kopieer de map `module-installs` van je eigen workspace naar de nieuwe map (overschrijft het lege mapje uit het zip-bestand):
```
Van:  C:\Users\oussa\Downloads\aios-starter-kit\aios-starter-kit\module-installs
Naar: [jouw nieuwe map]\aios-starter-kit\module-installs
```

## Stap 4: Claude Code openen in de NIEUWE map

Dit is de stap waar je vaak over twijfelt: open Claude Code niet in je eigen workspace, maar wijs hem specifiek naar de nieuwe map die je net gemaakt hebt. In VS Code: open die map als project (File → Open Folder), en start daar een nieuwe Claude Code-sessie. Alles wat je daarna doet, inclusief mijn geheugen, blijft dan vanzelf gescheiden van je eigen AIOS.

## Stap 5: De lagen installeren, in deze volgorde

Zeg in die nieuwe sessie steeds:
1. `/install module-installs/context-os-v1` — het interview over de praktijk/het bedrijf van de klant (wie ze zijn, wat ze doen, hun doelen). Dit is de belangrijkste stap.
2. `/install module-installs/infra-os-v1` — zet versiebeheer (git) op zodat niets kwijtraakt.
3. Daarna op basis van wat de klant nodig heeft: `data-os-v1` (cijfers/koppelingen), `intel-os-v1` + `daily-brief-v1` (overzicht/samenvattingen), `productivity-os-v1`, `command-os-v1`.

Je hoeft niet alles te installeren, alleen de lagen die voor deze klant waarde toevoegen.

## Stap 6: Testen

Draai `/prime` en controleer of Claude de praktijk/het bedrijf van de klant goed samenvat.

## Stap 7: Koppelingen (als dat nodig is)

Modules die externe accounts gebruiken (Google Sheets, etc.) hebben de EIGEN account/sleutels van de klant nodig, nooit die van jou.

## Stap 8: Overdragen aan de klant

Zip de volledige nieuwe map en stuur die via WeTransfer of Google Drive, met de instructie: "Open dit in Claude Code en zeg: lees INSTALL.md en zet dit op." (Zelfde patroon als het bestaande `/share`-commando.)

---

**Wanneer je hier echt mee aan de slag gaat:** open een nieuwe chat (niet de "random vragen"-chat) en vraag om deze stappen samen te doorlopen.
