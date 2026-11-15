# Bouwprompt: Instagram-contentagent met goedkeuring via Telegram

> Plak alles hieronder in een nieuwe chat met Claude Code (in een lege map op je laptop). Claude stelt je eerst vragen over je merk en bouwt daarna stap voor stap.

---

Je bent mijn bouwpartner. Samen bouwen we een **Instagram-contentagent**: een systeem dat elke dag zelf conceptposts maakt voor mijn Instagram-account (carrousels, losse afbeeldingen, reels), ze naar mij stuurt in Telegram, en pas iets doet als ik op een knop heb gedrukt. Ik ben niet technisch: leg alles in gewone taal uit voordat je het doet, en geef mij nooit lappen foutmeldingen. Schrijf tegen mij in het Nederlands, tenzij ik anders zeg.

## 1. Eerst vragen, dan bouwen

Bouw niets voordat je deze vragen hebt gesteld en mijn antwoorden hebt samengevat in een plan (`plans/instagram-contentagent.md`) dat ik goedkeur. Stel de vragen in kleine groepjes, niet allemaal tegelijk.

1. **Merk:** naam, Instagram-handle, wat doe ik, voor wie (doelgroep), wat moet een volger na het zien van mijn posts denken of doen?
2. **Taal van de posts** (Nederlands, Engels, ...) en **toon** (bijv. "eerlijk en zonder hype", "speels", "zakelijk"). Wat mag nooit (bijv. klantnamen noemen, mijn gezicht laten zien, beloftes die niet waar zijn)?
3. **Huisstijl:** logo (bestand), hoofdkleur en 4 à 6 afwisselende kleursets, lettertypen. Heb ik geen huisstijl, stel er dan een voor en laat mij kiezen.
4. **Onderwerpen:** waar haalt de agent zijn onderwerpen vandaan? (Bijv. een document met ideeën, mijn LinkedIn-posts, mijn website, een lijst diensten.) Welke vaste series of rubrieken wil ik (bijv. "Myth Check", "tips", "achter de schermen")?
5. **Contentmix:** hoeveel posts per week en welke soorten (zie hoofdstuk 3)?
6. **Draaien:** op mijn laptop of op een eigen server (VPS, ±€5 per maand, werkt ook als de laptop uit staat)? Advies: begin op de laptop, verhuis naar een server als alles werkt.
7. **Budget:** maximaal bedrag per maand voor Claude (API) en eventueel een stem (ElevenLabs).

## 2. Hoe het systeem in elkaar zit

Volg het **WAT-principe**: Workflows (instructies in Markdown), Agent (denkt en beslist), Tools (vaste Python-scripts die elke keer exact hetzelfde doen). Laat Claude alleen het denkwerk doen (teksten schrijven, kiezen, controleren); alles wat herhaalbaar is (beeld maken, video renderen, opslaan, versturen) gebeurt in scripts.

```
workflows/instagram_content.md   # ALLE spelregels (toon, tekst, kleuren, hashtags, controles); de agent leest dit altijd
tools/instagram/
  wachtrij.py          # SQLite-database: onderwerpen, posts, status, kleuren, hashtags, feedback, kosten
  bron_inlezen.py      # zet onderwerpen uit mijn bron in de wachtrij
  render_carrousel.py  # tekst -> carrousel-slides (PNG 1080x1350) via HTML + Playwright
  render_kaart.py      # losse afbeelding (bijv. handgeschreven schets op een bureau)
  render_tekst_reel.py # reel met bewegende tekst (MP4 1080x1920)
  opname_demo.py       # schermopname-reel van een fictieve demo-app (MP4 1080x1920)
  demos/*.html         # fictieve demo-apps (offerte-tool, dashboard, chat, ...), nooit echte klanten
  geluid.py            # zelfgemaakte geluidseffecten (tikjes, plop, ping), vrij te gebruiken
  telegram_review.py   # de Telegram-bot: concepten sturen, knoppen, feedback, "geplaatst"
apps/content/agent.py  # de agent: kiest, schrijft (Claude API), controleert, laat renderen, stuurt naar Telegram
.env                   # alle sleutels (NOOIT in code, NOOIT committen)
.tmp/instagram/        # concepten en tussenbestanden (wegwerp)
```

**Database (SQLite), minimaal:** `instagram_bron` (onderwerpen + of ze gebruikt zijn), `instagram_posts` (id, soort, onderwerp, kleurenset, hashtags, caption, bronnen, map, muziekadvies, status: concept / goedgekeurd / geplaatst / overgeslagen), `instagram_feedback` (post_id, tekst, verwerkt), `instagram_kosten` (maand, stap, kosten in $).

## 3. Soorten posts

| Soort | Wat | Hoe gemaakt |
|---|---|---|
| Carrousel | 4 à 8 slides: cover met hook, uitleg, eventueel cijferslide, slot met call to action | HTML-sjabloon in huisstijl, Playwright maakt PNG's |
| Losse afbeelding | Bijv. een handgeschreven schets (Venn-diagram, splitsing, lijstje, voor/na) op wisselende ondergronden (bureau, whiteboard, servet) | HTML/SVG met handschriftlettertype |
| Reel met bewegende tekst | 4 à 6 korte zinnen die woord voor woord verschijnen, 12 à 18 sec | HTML-animatie, frame voor frame opgenomen, ffmpeg naar MP4 |
| Demo-reel | Een fictieve app op een beeldscherm/laptop/telefoon; muis beweegt, er wordt getypt en geklikt, camera zoomt in | Eigen demo-pagina's + Playwright volgens een klikscript |
| Actualiteit | Nieuws uit mijn vakgebied met de vraag "wat betekent dit voor jou?" | Carrousel, met dubbele feitencheck (zie 5) |
| Story-idee | Korte tekst die ik zelf op een eigen foto zet | Alleen tekst |
| (Optioneel) video met stem | Voice-over met een AI-stem, scènes verschijnen op het gesproken woord | ElevenLabs (zie 7) |

**Belangrijk bij alle beeld:** render frame voor frame met een klok die het script bestuurt (animaties stilzetten en per frame verzetten), niet "in het echt opnemen". Dan is elk frame scherp en het tempo altijd gelijk. Gebruik fonts lokaal (woff2-bestanden meeleveren), niet van internet.

## 4. Telegram: zo keur ik goed

1. Ik maak via **@BotFather** een eigen bot aan (loop mij er stap voor stap doorheen) en geef jou de token. Zet hem in `.env`. Gebruik een **aparte bot** voor content: twee programma's die dezelfde bot uitlezen, botsen.
2. Elk concept komt binnen met: de beelden of video, de caption + hashtags in een kopieerbaar blok, een muziekadvies, en bij actualiteiten de bronlinks.
3. Knoppen: **✅ Goedkeuren**, **✏️ Aanpassen**, **❌ Overslaan**.
4. Bij ✏️ typ of spreek ik in wat er anders moet (spraak wordt uitgeschreven, bijv. met Whisper). De agent past alleen dat aan en stuurt een nieuwe versie.
5. Bij ✅ krijg ik de bestanden in originele kwaliteit en de caption om te kopiëren. Ik plaats zelf en druk daarna op **📤 Geplaatst**.
6. **Fase 1: er wordt nooit iets automatisch geplaatst.** (Fase 2, later en apart: automatisch plaatsen via de officiële Instagram API.)

## 5. Spelregels voor de inhoud (zet ze allemaal in de workflow)

- **De eerste zin moet laten stoppen met scrollen.** Mag schuren, nooit onwaar of overdreven.
- **Kort:** hook + hooguit 2 korte alinea's + afsluiter. Geen AI-toon (geen gedachtestreepjes, geen reeksen fragmentzinnen, niet elke zin op een eigen regel, geen woorden als "game-changer").
- **Vaste afsluiter** onder elke caption (die bepaal ik), automatisch toegevoegd, en nooit dubbel als de schrijver hem al zelf in de tekst zette.
- **Hashtags:** 3 tot 6, per post passend en steeds anders; nooit dezelfde hashtag in twee opeenvolgende posts.
- **Feitencheck:** elke claim of elk cijfer online controleren. Actualiteiten **dubbel**: originele bron lezen + een tweede onafhankelijke bron; faalt er één, dan geen concept. Stuur beide links mee. Oud nieuws mag als terugblik met datum ("On October 26, ...").
- **Nooit klantnamen** in tekst of beeld (ook niet op een schermopname van je eigen website: verberg ze alleen in de opname). Cases geanonimiseerd.
- **Demo's: fictief maar echt bouwbaar.** Fictieve bedrijven en namen, e-mailadressen op `.example`, alleen functionaliteit die echt kan.
- **Kleurregel:** hoofdkleur ongeveer 2 op de 3 posts, verder afwisselend een andere set; nooit twee keer dezelfde niet-hoofdkleur achter elkaar; geen vast patroon. Leg dit vast in `wachtrij.py`, niet in de prompt.
- **Afwisseling:** wissel soort, serie, toestel in demo's (beeldscherm, laptop, telefoon, tablet) en ondergrond bij schetsen. Niet steeds hetzelfde onderwerp.
- **Muziek** zit niet in de video; ik kies die zelf in de app. Geef per concept een kort muziekadvies (sfeer + zoekterm). Let op: wil ik een post later **promoten (betaalde advertentie)**, dan mag alleen muziek uit de **Meta Sound Collection**; gewone muziek uit de bibliotheek wordt dan gedempt of geweigerd.

## 6. De agent zelf

- **Dagelijks** (timer) houdt de agent een **voorraad van ±3** klaarstaande concepten bij (status concept of goedgekeurd), en maakt er **maximaal 2 per dag**. Zo loopt Telegram niet vol. Pas na 📤 Geplaatst komt er ruimte.
- Kiest de soort volgens de mix (gewogen, niet twee keer dezelfde soort achter elkaar), haalt het volgende onderwerp uit de wachtrij, laat Claude schrijven met een **vast JSON-schema per soort**, controleert de uitkomst met code (lengte, hashtags, verboden tekens, verplichte velden) en vraagt bij een fout één keer opnieuw.
- Verwerkt feedback uit Telegram, past alleen aan wat gevraagd is, en stuurt opnieuw.
- **Kostenbewaking:** elke Claude-aanroep in `instagram_kosten`; bij 75% van mijn maandbudget een melding in Telegram, bij 100% stoppen.
- Gebruik een recent, goed schrijvend Claude-model via de Anthropic API (sleutel in `.env`).

## 7. Optioneel: video met een AI-stem (ElevenLabs)

Alleen als ik dat wil. Wat wij geleerd hebben (scheelt veel tijd en tegoed):
- **Gratis plan = geen commercieel gebruik.** Voor een bedrijfsaccount minstens het Starter-plan (±$6/mnd, 30.000 tekens). Een video kost ±150-450 tekens per opname.
- **Hele script in één opname** inspreken, nooit per zin (anders klinkt elke zin als een herstart). Knip daarna op het echte geluid (stiltes meten), want de woordtijden van het nieuwste model lopen uit.
- **Pauzes gelijk maken** door alleen echte stilte korter/langer te maken (±1 sec rust na elke zin). Nooit kunstmatig een ademhaling toevoegen, nooit de toonhoogte verschuiven (klinkt als een andere stem).
- Regie-tags spaarzaam (zoals `[confident]`, `[curious]`, `[warm]`); tags als `[softly]` laten de stem wegzakken. Zet altijd `[long pause]` achter de laatste zin, anders wordt het laatste woord afgekapt.
- **Controle na elke opname:** volume per zin gelijktrekken; toonhoogte per zin meten (zakt een zin weg: andere opname); en **de opname laten uitschrijven en vergelijken met het script**, want de stem slaat soms woorden over terwijl de woordtijden kloppen. "wanna" = "want to".
- Geluidsspoor even lang maken als het beeld (anders hapert het einde op telefoons).
- **Eerst gratis proefvideo zonder stem** (geschatte timing) om script en beeld te beoordelen; pas daarna tegoed uitgeven. Cache elke opname, zodat opnieuw renderen niets kost.
- Let op: de API geeft het **verbruikte** aantal tekens terug, niet wat er over is.
- Onze ervaring: bij tekst- en demo-reels voegde een stem weinig toe (de tekst vertelt het al, veel mensen kijken zonder geluid). Een stem werkt het best bij video's die om de stem heen gebouwd zijn.

## 8. Controleren vóórdat ik iets zie

Ik wil niets zien dat jij niet zelf hebt gecontroleerd. Maak bij elke video een **controleblad** (per scène een paar stilstaande beelden naast elkaar) en bekijk dat zelf. Check minimaal:
1. Tekst in beeld volgt wat er gebeurt/gezegd wordt, niets valt buiten beeld of overlapt; alles binnen de veilige zone van Reels (niet onder de knoppen rechts of de caption onderin).
2. Rustig tempo: elke scène minstens ±3 seconden, na elke zin ±1 seconde rust; de slottekst blijft ±3,5 seconden staan. **Liever iets te rustig dan te snel** (te snel = niet te volgen).
3. **Het eerste beeld is niet leeg**: de hook staat er vanaf frame 1 (dat ziet iemand in de feed).
4. Bedragen en cijfers kloppen onderling; geen klantnamen; kleuren volgens de kleurregel.
5. Bij een nieuwe versie: vergelijk met de vorige en meld wat er veranderd is. Verander alleen wat ik vraag.

## 9. Bouwvolgorde (laat na elke stap het resultaat zien)

Toon vóór elke stap het hele lijstje, met afgeronde stappen doorgestreept. Na elke stap: laat mij het resultaat zien (open het bestand) en wacht op mijn akkoord.

1. Plan + workflow met alle spelregels (na mijn antwoorden uit hoofdstuk 1).
2. Wachtrij (SQLite) + onderwerpen inlezen + kleurregel + hashtag-afwisseling.
3. Carrousel-renderer in mijn huisstijl; 2 voorbeelden ter beoordeling.
4. Losse afbeelding (schets); 1 voorbeeld.
5. Reel met bewegende tekst; 1 voorbeeld.
6. Fictieve demo-pagina's + opname-tool; 2 voorbeelden.
7. Telegram-bot (ik maak de bot aan, jij begeleidt); test alle knoppen vanaf mijn telefoon.
8. De agent (schrijven, controleren, renderen, versturen, feedback verwerken, kosten); proefronde met 5 concepten.
9. (Optioneel) stemvideo's en geluidseffecten.
10. Naar de server (als ik dat wil) en de dagelijkse timer aanzetten op een tijd die ik kies.
11. Documentatie: een korte `README.md` en `CLAUDE.md` met hoe alles werkt en hoe ik het herstart.

## 10. Server (als ik daarvoor kies)

- Ubuntu-VPS, eigen gebruiker (niet root), firewall aan, fail2ban, inloggen met SSH-sleutel.
- Installeren: Python, Playwright + Chromium, ffmpeg, lettertypen **inclusief een emoji-font** (anders worden emoji's in beeld lege vakjes).
- `systemd`: de bot als service die altijd draait, de agent als timer (dagelijks, in mijn tijdzone, bijv. `OnCalendar=*-*-* 08:15:00 Europe/Amsterdam`).
- Database en concepten staan vanaf dan op de server; **draai de bot niet ook nog op de laptop** (twee luisteraars botsen).
- Maak een back-up van de database vóór grote wijzigingen.

## 11. Werkafspraken

- Leg uit wat je gaat doen voordat je het doet, in gewone taal. Noem beperkingen vooraf, niet pas als het misgaat.
- **Vraag toestemming voordat je iets doet dat geld kost** (betaalde API-aanroepen buiten de afgesproken runs, abonnementen). Test eerst gratis waar het kan.
- Sleutels alleen in `.env`, nooit in code of berichten; `.env` in `.gitignore`.
- Gebruik git: na elke afgeronde stap opslaan (commit) met een duidelijke beschrijving.
- Als iets mislukt: zoek de oorzaak, los het op, test opnieuw, en schrijf de les op in de workflow zodat het niet nog eens gebeurt.
- Doe alleen wat ik vraag; stel verbeteringen voor, maar voer ze pas uit na mijn akkoord.

Begin nu met de vragen uit hoofdstuk 1.
