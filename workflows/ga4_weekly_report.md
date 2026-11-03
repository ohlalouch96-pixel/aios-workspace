# Workflow — Wekelijkse GA4-samenvatting (insightance.ai)

**Status:** Actief sinds 03-11-2026. Eerste review: maandag 09-11-2026 (korter dan een week, prima).
**Tool:** `tools/ga4_weekly_report.py`
**Wanneer:** vaste review elke **maandag**, over de 7 dagen t/m gisteren (ma t/m zo). Oussama start de sessie zelf en vraagt om de stand; bij /prime hoeft het niet naar voren te komen.

## Doel

Oussama wil elke week zien waar bezoekers vandaan komen (welk kanaal, welke
outreach- of profiellink), wat ze bekijken, hoe lang ze blijven en welke
acties ze doen, met toe- of afname ten opzichte van de week ervoor.

## Stappen

1. `python tools/ga4_weekly_report.py` (of `--end JJJJ-MM-DD` voor een andere week).
   Schrijft ook `.tmp/ga4/weekrapport_<datum>.md` + `.json`.
2. Maak daarvan een korte samenvatting in gewone taal (Nederlands, geen jargon, geen gedachtestreepjes):
   - aantal bezoekers en verschil met vorige week (in één zin)
   - top 3 bronnen, en welke UTM-link (`mail2`, `dm2`, `bio`, ...) het meeste opleverde
   - welke pagina's het meest bekeken werden en waar mensen het langst bleven
   - acties (gesprek ingepland, WhatsApp, rekentool, offertetool-demo) en via welke bron
   - precies één concrete tip (bv. "DM2 levert bezoekers op maar niemand gebruikt de rekentool")
3. Geen tabellen dumpen tenzij Oussama erom vraagt.
4. Daarna eventueel samen aanpassingen doen (links, pagina's, berichten).

## Om rekening mee te houden

- Alleen bezoekers die "Akkoord" klikten worden geteld: cijfers zijn een ondergrens. Altijd kort noemen.
- Oussama's eigen apparaten staan op "Alleen functioneel" en tellen niet mee.
- Bots: consent.js laadt GA niet voor herkenbare bots; het script filtert daarnaast datacentersteden
  (`BOT_CITIES`) en toont hoeveel. 03-11: na het wijzigen van de IG-bio kwamen 9 "bezoekers" uit
  Prineville/Luleå (Meta), Ashburn (Amazon) en Springfield, allemaal first_visit zonder engagement.
  Zie je nieuwe verdachte steden, voeg ze toe aan `BOT_CITIES`.
- Standaardrapporten lopen 24-48 uur achter; de huidige dag is nooit compleet.
- "Betrokken bezoek" = langer dan 10 seconden, of 2+ pagina's, of een sleutelgebeurtenis. Beste maat voor echte interesse.
- UTM-afspraken: `reference/utm-links.md`. Kale links (zonder label) tellen als direct of als referral.

## Toegang

- Property-ID in `.env` (`GA4_PROPERTY_ID=562176820`), service account `GOOGLE_SERVICE_ACCOUNT_JSON`.
- Service account `dataos-reader@aios-workspace-494503.iam.gserviceaccount.com` heeft rol Kijker op de property.
- Google Analytics Data API staat aan in Cloud-project aios-workspace-494503 (Gmail-account van Oussama).
  GA4 zelf staat op oussama@insightance.ai.
- Fout "User does not have sufficient permissions" = Kijker-rol weg of verkeerd Property-ID.
