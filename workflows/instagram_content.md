# Workflow — Instagram-content @insightance.ai

**Status:** In bouw sinds 04-11-2026. Plan: `plans/2026-11-04-instagram-contentagent.md`.
**Tools:** `tools/instagram/` (bron_inlezen, wachtrij, render_carrousel, render_kaart, render_tekst_reel, opname_demo; later Telegram)
**Fase 1:** de agent maakt concepten, Oussama keurt elke post goed via Telegram en plaatst zelf. Niets gaat online zonder ✅.

## Doel

Volgers, exposure en bekendheid voor Insightance opbouwen op een aparte merkpagina. Leads komen later.
Geen nieuwe onderwerpen verzinnen: bron is `outputs/linkedin-content-serie.md`, aangevuld met actualiteiten.

## Harde regels

- **Engels.** Natuurlijk, idiomatisch, nooit letterlijk vertaald.
- **Nooit klantnamen** (MHL, FTUK of andere echte klanten), niet in tekst en niet in beeld. Cases anoniem ("an installation company").
- **Niets aan de live website (`docs/`) veranderen.** Demo's leven in `tools/instagram/demos/`.
- **Elke claim klopt en is herleidbaar.** Cijfers altijd online verifiëren voordat ze in een concept komen. Bij twijfel: weglaten.
- **Geen gezicht.** Naam alleen in de bio.

## Richting en toon

"AI without the hype." Eerlijk over wat AI wel en niet kan; prikt door hype én angst. Informatief, niet formeel.
**Mix van informatie én bewijs (04-11):** niet alleen uitleg, ook laten zien wat AI concreet oplevert en wat er mogelijk is (demo's van offertes, dashboards, rekentool, klantenservice, resultaten). Bewijs is wat mensen willen zien. Reken op ongeveer de helft informatief, de helft bewijs/mogelijkheden.
Mag schuren en uitdagen, maar altijd vanuit deskundigheid: nooit klinken als iemand die maar wat roept.
Oprichtersdagboek (The Other Shift) alleen in stories. Actualiteiten altijd vanuit "wat betekent dit echt voor jouw bedrijf?".

## Tekst (caption en slides)

1. **Eerste zin = scroll-stopper.** Dat is bij elke post het hoofddoel. Schurend, verrassend of herkenbaar. Test: zou deze zin alleen iemand laten stoppen? Zo niet, herschrijven.
2. **Compact, korter dan LinkedIn.** Hook + maximaal 2 korte alinea's + afsluiter. Geen lappen tekst.
3. **Geen AI-toon** (writing-style skill): geen gedachtestreepjes, geen "Not X. Not Y."-reeksen, geen woorden als simply/seamless/leverage/robust, geen "That's it."-afsluiters, zinslengte afwisselen, niet elke zin op een eigen regel.
4. **Slides:** één gedachte per slide, kort. Cover = de hook. Laatste slide = afsluiter of zachte uitnodiging ("Follow for AI without the hype ⚡" of een variant, niet elke keer dezelfde).
5. **Hashtags: 3 tot 6, steeds anders.** Ook het aantal wisselt: nooit twee posts achter elkaar met hetzelfde aantal (dus niet steeds 3). Passend bij het onderwerp, geen vaste set, nooit dezelfde hashtag als in de vorige post (`wachtrij.py hashtags` geeft de recente). Actualiteit: een hashtag over dat nieuws (tool, bedrijf, onderwerp). The Fork: geen hashtags.
7. **Vaste afsluiter** onder de vraag, boven de hashtags, op bijna elke post (niet bij The Fork). Volgorde: tekst → vraag → afsluiter → hashtags. Tekst: zie "Afsluiter" hieronder.
6. Bron-teksten van LinkedIn zijn het vertrekpunt, niet de eindtekst: herschrijven voor een informeler, scrollend publiek.

## Afsluiter

Geïnspireerd op een LinkedIn-voorbeeld dat Oussama aandroeg (wat hij bouwt + aanbod van een gesprek). Tekst (vastgesteld 04-11): geen witregel tussen de twee zinnen, geen "Curious?" en geen belgesprek noemen (Oussama peilt eerst via DM of iemand echt interesse heeft), altijd eindigen op ⚡ als herkenningsteken (zelfde als in de bio).

```
I build AI systems for business owners, so you and your team can focus on the work that actually matters.
Send me a DM and I'll show you what's possible for your business ⚡
```

## Actualiteiten: één controle (sinds 06-11, was dubbel; dubbel kostte te veel tijd)

1. Zoek nieuws dat relevant is voor ondernemers (niet puur voor techneuten), alleen uit officiële bronnen of gevestigde nieuwssites, geen blogs of samenvattingen.
2. **Controle:** lees de bron zelf en check namen, cijfers en datums. Alleen gecheckte feiten gaan de post in, geen "voorbeelden" die je niet kon nagaan.
3. Klopt het niet: onderwerp vervalt, geen concept naar Oussama.
4. In Telegram altijd de **bronlink(s)** meesturen, zodat Oussama zelf kan controleren voordat hij goedkeurt.

## Beeld

- Carrousel 1080×1350 via `tools/instagram/render_carrousel.py` (stijl goedgekeurd 04-11, zie `outputs/instagram-stijl/_overzicht-v2.png`).
  Cover: groot vet Inter, kernwoord in accentkleur. Binnenslides licht met label-pil en markering. Cijferslide: groot Playfair-cijfer. Myth Check: aanhalingsteken + Playfair-citaat.
- **Kleurregel:** navy is de basis, ongeveer 2 op de 3 posts. Af en toe een andere set (zwart, blauw, groen, creme, rood, paars) om te verrassen. Geen kleurenfestijn, geen vast patroon, nooit twee keer dezelfde niet-navy set achter elkaar. `wachtrij.py kleur` kiest volgens deze regel.
- **Out of the box mag ook.** Niet alles hoeft een carrousel. Af en toe een losse afbeelding in een heel andere stijl, bijvoorbeeld de handgeschreven notitiekaart op een bureau (`tools/instagram/render_kaart.py`: Venn-diagram of splitsing). The Fork gebruikt deze kaart. Wissel ook de ondergrond af: bureau, kantoor, ipad, scherm, krant (zwart-wit), whiteboard, servet (café). En wissel de schets zelf af: venn, fork, lijst (afvinken), voor_na, stappen, grafiek, loop (kringloop). Nooit twee keer achter elkaar dezelfde ondergrond of schets; nieuwe ondergronden mogen erbij (alle kanten op).
- Nooit de oude zwart-gouden LinkedIn-afbeeldingen. Elke post krijgt nieuw beeld.
- Reels 1080×1920, geen muziek (Oussama voegt die zelf toe als hij wil). Tekst-reel: `tools/instagram/render_tekst_reel.py` (beats van 2-4 sec, 12-16 sec totaal, levert ook cover.jpg). Rendert ±1 min per reel; vereist imageio-ffmpeg.

## Contentmix (±5 posts per week, geen vaste dagen of tijden)

| Soort | Inhoud | Hoe vaak |
|---|---|---|
| Carrousel | Automation Simplified, Myth Check, anonieme cases | 2 à 3 per week |
| Reel | Fictieve demo-schermopname (bewijs) of bewegende tekst | samen ±2 à 3 per week, demo's vaker dan tekst |
| Actualiteit | AI-nieuws, dubbel gecheckt | ±1 per week |
| Losse afbeelding | The Fork | af en toe |
| Story-tekst | The Other Shift, achter de schermen | voorstel, Oussama zet het op een eigen foto |

## Muziekadvies (bij elk concept met video)

Bij elke reel in het Telegram-bericht één korte regel muziekadvies, passend bij inhoud én kleur. Voorbeelden: navy/uitleg → rustige lo-fi of zachte piano; zwart/rood Myth Check → strakke, licht spannende beat; groen stappenplan → luchtig, positief akoestisch; actualiteit → neutraal, licht nieuwsachtig ritme. Video met stem (09-11, getest met voorbeeldmuziek): uptempo en vrolijk (±110-120 BPM), zonder zang, zacht eronder (muziek ±15%, origineel geluid 100%); zoektermen 'upbeat corporate', 'positive tech', 'happy commercial'. Rustige piano afgewezen: voelde plechtig/somber. Geen specifiek nummer verzinnen; type/sfeer en eventueel een zoekterm voor de Instagram-muziekbibliotheek. Oussama voegt de muziek zelf toe bij het plaatsen.

## Demo-reels

**Zo echt mogelijk (04-11):** desktop-software op een echt beeldscherm, met inzoomen op waar geklikt wordt, herkenbare situaties uit de praktijk (bijv. cv-ketel vervangen, ROAS per advertentiekanaal), realistische cijfers die onderling kloppen. Doel: de kijker denkt "dit gaat over mij". Fictieve bedrijven en gegevens, maar alleen functionaliteit die echt gebouwd kan worden. Onderwerpen: offerte-maker, dashboard, binnenkomende factuur, WhatsApp-bericht, klantenservice-chat, rekentool, calculaties. Zonder n8n.

- Demo-pagina's: `tools/instagram/demos/<naam>.html` + standaardscript `<naam>.json`. Valuta altijd **US dollar** (besluit 05-11). Klaar (7):
  `offerte` (beeldscherm, cv-ketel vervangen), `dashboard` (beeldscherm, omzet/ROAS per kanaal), `calculatie` (laptop, dakdekker),
  `factuur` (beeldscherm, donkere app, factuur automatisch uitgelezen), `whatsapp` (telefoon, kapper boekt via WhatsApp),
  `klantenservice` (tablet, webshop-chat met overdracht naar mens), `rekentool` (telefoon, Insightance-rekentool, formule = website).
- **Afwisseling:** wissel toestel (beeldscherm, laptop, telefoon, tablet) én app-opmaak (zijbalk/bovenbalk, licht/donker, accentkleur). Chat/WhatsApp altijd op een telefoon. Op een telefoon niet inzoomen (snijdt af), telefoon is groot genoeg.
- Opnemen: `python tools/instagram/opname_demo.py tools/instagram/demos/offerte.json` → reel.mp4 + cover.jpg. Frame voor frame (scherp), ±45 sec renderen.
- Nieuwe demo: zelfde opbouw (`_demo.css`/`_demo.js`), velden via `focusVeld`/`typLetter`, animaties via CSS of `animeer()`. Geen native `<select>` (popup komt niet in beeld), gebruik een eigen lijst.
- Fictieve namen: generiek, geen bestaande merken, e-mail/domein op `.example` of een algemeen voorbeeldadres.

## Stappen per concept

1. `python tools/instagram/wachtrij.py volgende` → onderwerp uit de bron (of een actualiteit, zie boven).
2. Tekst schrijven volgens de regels hierboven; feiten checken.
3. `python tools/instagram/wachtrij.py kleur` en `... hashtags` voor kleurenset en recent gebruikte hashtags.
4. Spec (JSON) maken en renderen: `python tools/instagram/render_carrousel.py spec.json`.
5. Vastleggen: `python tools/instagram/wachtrij.py opslaan spec.json`.
6. Naar Telegram ter goedkeuring: `python tools/instagram/telegram_review.py stuur <id>`. Knoppen en feedback verwerkt `... luister` (draait straks altijd op de server). Feedback staat in tabel `instagram_feedback` (verwerkt=0) en wordt door de agent opgepakt. Content-bot: @Insightance_content_bot, `.env`: INSTAGRAM_BOT_TOKEN + INSTAGRAM_CHAT_ID (privéchat, NIET de groep-ID van TELEGRAM_CHAT_ID).

## Video met voice-over (Typer-stijl, sinds 06-11)

- Stem: Eric via ElevenLabs (`tools/instagram/stem.py`, cache in `.tmp/instagram/stem_cache/`). Oussama's eigen stem getest en afgewezen.
- Renderen: `python tools/instagram/render_stem_video.py tools/instagram/video/<naam>.json` (scènes in `tools/instagram/video/typer.html`).
- **De agent maakt ze zelf (stap d, 09-11):** soort `stem_video` in `apps/content/agent.py` (±14% van de mix). Kiest de volgende dienst, laat Claude het script schrijven, controleert vóór de opname (5-7 beats, 35-70 woorden, kop = gesproken woorden in dezelfde volgorde, alleen tags [confident]/[curious]/[warm]/[excited], tijden als '9 PM', 'op'-woorden worden echt gezegd, maxima per scène), zet ' [long pause]' achter de laatste zin, één inademing op een willekeurige plek, en meet na de opname toon en volume per zin (volume automatisch gelijk; zakt een zin weg en is er tegoed: één nieuwe opname). Alleen als er ≥700 ElevenLabs-tekens over zijn, anders een ander soort post. Gratis proef: `python apps/content/agent.py maak --soort stem_video --zonder-stem` (geen Eric, niet naar Telegram).
- Algemene scènes voor alle diensten: hook, telefoon (AI-telefoniste), chat (web/WhatsApp), agenda, inbox, document (scannen + velden), dashboard (tegels + grafiek + waarschuwing), checklist, notificaties, eind.
- Scènes in `video/typer.html`: getal, mandje, mails, meldingen (cart-recovery) en klok, offerte, totaal, pdf, akkoord (offerte-tool, 09-11), eind. Nieuwe scènes eerst zonder stem bekijken (geen tegoed), pas daarna Eric laten inspreken. Specs: `video/cart_recovery.json`, `video/offerte.json`. Soort in de wachtrij: `stem_video`.
- **Onderwerpen = de diensten op de website (besluit 09-11).** Elke video met stem gaat over één dienst uit het overzicht op insightance.ai (`docs/automations.html`, 28 diensten in 6 categorieën: sales, klantcontact, finance, HR, data, intern). `python tools/instagram/diensten.py volgende` kiest: eerst elke dienst één keer, nooit twee keer achter elkaar dezelfde categorie; nieuwe diensten op de site komen vanzelf mee. Per video: herkenbaar probleem → wat de AI doet → resultaat, fictief bedrijf, volgens de 12 controleregels. Een dienst zonder passende scènes krijgt eerst nieuwe scènes (zonder stem bekijken, geen tegoed), pas daarna Eric. De dienst gaat mee in de spec (`"dienst"`) zodat de wachtrij bijhoudt wat al geweest is.
- Stem: profiel `eric_v3` (nieuwste model, stability 0.0 = proef D, regie-tags per zin zoals [confident], [understated], [softly]). Eric ademt zelf af en toe; dat blijft staan. Spec: per beat `zegt` (woorden) + `uitspraak` (met tags).
- Tempo: hele stem 10% sneller (`"tempo": 1.1`, gratis, toon blijft gelijk; gekozen 09-11).
- Pauzes: de tool maakt elke pauze gelijk (1,0 s rust in beeld + 0,25 s voorloop) door alleen echte stilte (onder -60 dB) in te korten of te verlengen. **Nooit zelf een ademhaling toevoegen**: een vaste ademhaling voor elke zin klonk nep (06-11). Zinsgrenzen worden op het geluid gemeten: de woordtijden van v3 lopen uit.

- **Tijden zoals mensen ze zeggen (09-11):** Eric zegt "It's 9 PM", nooit "nine at night". Schrijf in `zegt`/`uitspraak` dus "9 PM" (zelfde als in beeld).
- **Geluid even lang als beeld (09-11):** stopte het geluidsspoor eerder dan het beeld, dan haperde het einde op de telefoon. De tool vult het geluid nu aan met stilte (apad).
- **Laatste woord niet laten afkappen (09-11):** ElevenLabs v3 kapt het laatste woord soms af (video hapert aan het eind). Zet altijd " [long pause]" achter de laatste zin in `uitspraak`; de tool geeft een melding en fadet uit als het toch gebeurt.

### Controleregels (vóór Oussama een video ziet, besluit 06-11)

Automatisch (de tool stopt bij een fout):
1. Eén doorlopende opname, nooit per zin inspreken.
2. Beeld blijft na het laatste woord van elke zin 1,0 s staan (gekozen 09-11; 1,5 s voelde te lang, 0,75 s te krap).
3. Elke scène minstens 3,0 s in beeld.
4. Stem = gekozen profiel; aantal gehoorde woorden = aantal woorden in het script.
5. Bedragen kloppen op elk moment (subtotaal = som, teller = som van de meldingen die al in beeld zijn).

Zelf bekijken op `controle.png` (per scène begin, midden, rust):
6. Tekst in beeld volgt de woordvolgorde van wat Eric zegt.
7. Niets valt buiten beeld of overlapt, alles binnen de veilige zone.
8. Rustig tempo, elementen op het gesproken woord, niet te veel tegelijk.
9. Kleurenset klopt, tekst goed leesbaar.
10. Cijfers met bron gecheckt, geen klantnamen, geen gedachtestreepjes.

Bij elke nieuwe versie:
11. Vergelijken met de laatst goedgekeurde versie en melden wat er veranderd is, ook bijeffecten.
12. Alleen veranderen wat gevraagd is.

## Geleerd

- **Stem bijstellen (09-11):** regie-tags [understated] en [softly] laten Eric omlaag gaan in toon; gebruik [confident] voor zinnen die even krachtig moeten blijven. Tempo/volume per zin gratis bijstellen via `"stem"` in de spec (toonhoogte kunstmatig verhogen NIET doen: verandert de klankkleur, klonk als een andere stem; een zinseinde gaat van nature iets omlaag en dat is goed), eerst `--alleen-stem` laten beluisteren, pas daarna de video (alleen nieuwe opnames kosten tegoed). Een zin mag uit een tweede opname van hetzelfde hele script komen (`"opname": "alt"`); toonhoogte per zin nameten.
- **Voice-over (06-11):** zelf toegevoegde stilte was niet het probleem (ElevenLabs-pauzes zijn ook digitale stilte); wel het knippen door een ademhaling en een vlakkere opname. Hele script in één keer inspreken, niet per zin: per zin klonk elke beat als een herstart met een dode pauze ertussen. Tekst in beeld volgt exact de woordvolgorde van wat gezegd wordt (anders hoor je iets anders dan je leest). Animaties rustig (±0,7 s in) en op het gesproken woord, niet "tak tak tak". Scènes lopen in elkaar over (inhoud glijdt weg net voor de volgende zin).
