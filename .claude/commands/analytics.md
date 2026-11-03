# Analytics

> Haal de websitecijfers van insightance.ai op uit Google Analytics 4 en vat ze samen in gewone taal.

## Variables

periode: $ARGUMENTS (optioneel: leeg = 7 dagen t/m gisteren; of een einddatum JJJJ-MM-DD; of "vorige week")

## Read

- `workflows/ga4_weekly_report.md` — hoe de samenvatting eruitziet, valkuilen (bots, cookie-akkoord, vertraging)
- `reference/utm-links.md` — welke UTM-code bij welk bericht/kanaal hoort

## Run

1. Bepaal de einddatum:
   - leeg → standaard (gisteren)
   - datum → `--end <datum>`
   - "vorige week" → de zondag van de week vóór de afgelopen week
2. Draai `python tools/ga4_weekly_report.py` (met `--end` indien nodig).
3. Geeft het script een fout, leg die in één zin uit en los hem op (zie "Toegang" in de workflow).

## Summary

Geef een korte samenvatting in het Nederlands, gewone taal, geen gedachtestreepjes, geen tabellen dumpen:

1. **Bezoekers** — hoeveel, en meer of minder dan de week ervoor (in één zin)
2. **Waar ze vandaan komen** — top 3 bronnen, en welke link (mail2, dm2, bio, profiel, ...) het meeste opleverde
3. **Wat ze bekijken** — populairste pagina's en waar mensen het langst bleven
4. **Wat ze doen** — acties (gesprek ingepland, WhatsApp, rekentool, offertetool-demo) en via welke bron
5. **Eén concrete tip** — precies één, gebaseerd op de cijfers
6. Kort noemen: alleen bezoekers die "Akkoord" klikten tellen mee, en hoeveel bot-bezoeken zijn weggefilterd

Vraag daarna of Oussama iets wil aanpassen.
