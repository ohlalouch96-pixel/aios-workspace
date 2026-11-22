# Plan: wekelijkse concurrentenronde Instagram (optie C, officiële API)

**Datum:** 22-11-2026 · **Status:** in uitvoering · **Besluit:** Oussama, optie C

## Doel
Elke vrijdag automatisch zien welke reels en posts bij vergelijkbare AI-automatiseringsaccounts uitschieten. De winnende hooks en formats gaan naar Telegram (kort overzicht) en naar de hookstap van de contentagent, zodat de concepten van zaterdag 07:00 er meteen van leren.

## Accounts (start, 22-11)
@theaiagents, @lvl_aiautomations, @aiautomation.cc, @selr__ai, @automatedbusiness.ai, @nessalazne, @the_ai_dude, @dapta.ai

Afgevallen: @digital20ltd en @patternautomation (niet interessant), @ash_automates. Aanvullen tot 10 à 12 accounts met minimaal ±20.000 volgers, gecontroleerd via de API.

## Hoe
- **API:** Meta Instagram Graph API, *Business Discovery* (`business_discovery.username(x){followers_count,media{caption,media_type,media_product_type,timestamp,like_count,comments_count,view_count,permalink}}`). Officieel en gratis, geen scrapen. Alleen zakelijke accounts en creator-accounts; verborgen aantallen komen niet mee.
- **Uitschieter:** views (reels) of likes + reacties (overig), gedeeld door de mediaan van dat account over de laatste ±25 posts. ≥3x is een signaal, <1,5x is ruis (methode uit de ig-viral-skill).
- **Analyse:** Claude benoemt per uitschieter de hookformule (`hooks.json`), het format en de lengte. Regel: de formule overnemen, nooit de video of de tekst.

## Stappen
1. **Instellen met Oussama** (eenmalig, ±20-30 min):
   - Instagram is professioneel en gekoppeld aan een Facebook-pagina.
   - Meta-ontwikkelaarsapp aanmaken met de rechten `instagram_basic`, `pages_show_list`, `pages_read_engagement`.
   - In `.env`: `META_APP_ID`, `META_APP_SECRET` en een token.
   - Daarna levert de tool zelf een pagina-token zonder vervaldatum en het IG-gebruikers-ID.
2. **Tool `tools/instagram/concurrenten.py`:** ophalen, opslaan in `data/data.db` (tabellen `ig_concurrent_*`), uitschieters berekenen. CLI: `ophalen`, `rapport`.
3. **Analyse plus overzicht:**
   - Claude-aanroep (kostenlog `instagram_kosten`).
   - Weekoverzicht naar Telegram.
   - Het lijstje "werkt nu" naar `data/instagram_swipe.json`.
4. **Koppeling met de agent:** `kies_hook` krijgt de recente winnende formules als voorkeur mee.
5. **Server:** `instagram-concurrenten.timer` elke vrijdag 18:00 (Europe/Amsterdam).
6. **Documentatie:** `workflows/instagram_concurrenten.md`, CLAUDE.md en de memory bijwerken.

## Kosten
- **API:** gratis.
- **Claude-analyse:** ±$0,10-0,20 per week, binnen de $20-limiet van de agent.
