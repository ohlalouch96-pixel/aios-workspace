# Workflow — Telefoonnummers zoeken (ondernemers-tracker)

**Status:** Actief sinds 30-10-2026.
**Tool:** `tools/find_phone_numbers.py`
**Doelgroep:** Vakbedrijven in `ondernemers-tracker` zonder telefoonnummer.

## Achtergrond

Besluit 30-10-2026: vanaf maandag 2-11 wordt de ondernemers-track vooral
telefonisch benaderd, e-mail bouwen we af (niet helemaal stoppen). Reden
(Oussama's eigen cijfers): van 318 gemailde vakbedrijven kwamen 7 reacties
terug, allemaal een kort "geen interesse". Van 20 keer bellen had hij 7 keer
iemand aan de lijn, en aan de telefoon weet hij direct waar hij staat. Van de
472 prospects hadden er maar ~40 al een telefoonnummer.

## Wat het script doet

1. Leest `ondernemers-tracker!A:J`.
2. Selecteert rijen: status `Verstuurd` / `Afgerond` / `Te versturen` (in die
   volgorde — zie prioriteit), zonder bestaand `Tel:` in kolom B, met een URL,
   en zonder harde afwijzing/opt-out in de notities (`HARD_REJECT_RE`).
   Overgeslagen: status `Afgewezen`, `Onbereikbaar`.
3. Fetcht de eigen website (homepage + contactpagina-fallback uit
   `CONTACT_PATHS`, hergebruikt van `source_ondernemers.py`) en zoekt een NL
   telefoonnummer. Bij meerdere nummers: voorkeur voor een 06-nummer (grotere
   kans op de eigenaar zelf rechtstreeks).
4. Schrijft het gevonden nummer aan kolom B toe (`{bestaande inhoud} + Tel: X`,
   overschrijft nooit). Niets gevonden → notitie in kolom I: "Tel-zoekactie
   [datum]: geen nummer gevonden op website."
5. Schrijft in batches van 20 cellen, met expliciete `ondernemers-tracker!`
   prefix (hard afgedwongen via assert) en leest na elke batch terug of de
   cellen echt gevuld zijn — zie `feedback_sheet_tabnaam_verplicht` en
   `feedback_sheet_writes_verifieren` in memory.

## Gebruik

```bash
python tools/find_phone_numbers.py                      # dry-run, print resultaten
python tools/find_phone_numbers.py --limit 20            # dry-run, eerste 20 (test)
python tools/find_phone_numbers.py --write                # schrijft naar de sheet
python tools/find_phone_numbers.py --write --workers 15
```

Draai altijd eerst een kleine `--limit`-test zonder `--write` om te controleren
of de fetchers nog werken (sites veranderen, Cloudflare-blocks komen voor)
voordat je de volledige ronde met `--write` draait.

## Na elke bel-sessie (vanaf 2-11)

Leg per gesprek kort het bezwaar vast in kolom I, bijvoorbeeld:
`Gebeld 02-11: geen tijd / al geautomatiseerd / werkt nog met papier.`
Bij een nee: altijd vragen of over drie maanden terugbellen mag, en die
uitkomst ook noteren. Na ~30 gesprekken deze notities doorlopen om het
belscript (`outputs/belscript-ondernemers-outreach.md`) scherper te maken.

## Bekende beperking

Vaste-nummer-opmaak (`0XX-XXXXXXX`) is een benadering zonder echte
regio-code-tabel — de cijfers zijn altijd correct, het streepje staat niet
altijd op de exacte regiogrens (bv. `054-6632334` i.p.v. `0546-632334`).
Zelfde beperking als in `source_ondernemers.py`.
