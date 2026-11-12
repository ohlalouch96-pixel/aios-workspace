# To-do — Geparkeerd

> Dingen die Oussama nog wil doen maar op dit moment even parkeert.
> Geen deadline, geen prioriteit-volgorde — gewoon een plek om ze niet kwijt te raken.
> Verplaats een item naar `plans/` met `/create-plan` zodra je het echt oppakt.

---

## Warm netwerk raadplegen (familie en kennissen)

**Status:** Geparkeerd sinds 2026-11-10 ("nu geen tijd, later oppakken")
**Idee van Oussama:** Eén persoonlijk WhatsApp-bericht schrijven en sturen naar neven, ooms, tantes en andere bekenden. Misschien kennen zij een ondernemer of webshop die geholpen kan worden, en zo komt er een potentiële klant uit.
**Waarom:** Het doel is de eerste betalende klant, in welke branche ook. Een introductie via iemand die je kent is veel warmer dan een koud bericht.
**Wat er moet gebeuren:**
1. Lijstje maken van wie het bericht krijgt.
2. Bericht schrijven: kort, persoonlijk, in gewone taal uitleggen wat Insightance doet en één concrete vraag ("ken jij iemand met een eigen bedrijf of webshop die...?").
3. Versturen en bijhouden wie iemand doorgeeft.

---

## E-maillijst / nieuwsbrief via de website

**Status:** Geparkeerd sinds 2026-10-11
**Idee van Oussama:** welkomstpop-up waarmee bezoekers zich aanmelden voor een nieuwsbrief, om een community op te bouwen en daaruit klanten te halen.
**Waarom nog niet:** nog weinig bezoekers, er staat al een cookiemelding (twee pop-ups is opdringerig, Google straft pop-ups op mobiel af), en korting (bijv. 50% op de eerste automation) botst met "vaste prijs" en "max. 3 klanten per maand".
**Beter alternatief later:** rustig aanmeldblok onderaan de site met iets nuttigs gratis (bijv. "5 taken die elke ondernemer vandaag kan automatiseren"), privacybeleid aanpassen, afmeldlink.
**Trigger om op te pakken:** zodra de bezoekersteller (Cloudflare Web Analytics) laat zien dat er genoeg verkeer is.

---

## n8n Docker-image bijwerken

**Status:** Geparkeerd sinds 2026-08-19
**Waarom geparkeerd:** Geen actieve klant op n8n op het moment dat dit speelde, dus geen urgentie.
**Wat er moet gebeuren:** De Docker-image is verouderd. Updaten raakt de `encryption key` in de container-env-vars — een fout daarin maakt alle opgeslagen n8n-credentials onbruikbaar. Zorgvuldig doen, niet zomaar even.
**Trigger om op te pakken:** Zodra er weer een klant op n8n draait (bijv. eerste e-commerce klant met een cart-recovery workflow).

---

## Kennisbank / blogsectie op de website

**Status:** Geparkeerd sinds 2026-06-22
**Waarom geparkeerd:** Idee geopperd, nooit opgevolgd.
**Wat het is:** Een artikelensectie op insightance.ai, vergelijkbaar met een blog. Meer waarde voor bezoekers, autoriteit opbouwen, SEO.
**Openstaande vraag:** Los tabblad of sectie op de hoofdpagina? Eerste stap is waarschijnlijk een simpele artikelpagina.

---

## KvK-registratie

**Status:** INGESCHREVEN op 2026-11-12. KvK-nummer: 42220238. Btw-nummer en omzetbelastingnummer (OB) komen binnen 2 weken per post (verwacht uiterlijk ~26-11). Nog open: KvK in websitefooter, Google Bedrijfsprofiel, reviews MHL/FTUK, btw-nummer doorgeven zodra binnen.
**Waarom geparkeerd:** Was volgens `context/strategy.md` gepland "zodra eerste klant in zicht" — nog niet zover.
**Trigger om op te pakken:** Zodra een klant ja zegt (bijv. Millenaar | Peijnenburg na het eerste gesprek). Dan direct een afspraak inplannen, niet pas na de betaling.
**Wat er moet gebeuren:** Bedrijf inschrijven bij de Kamer van Koophandel. Online formulier via DigiD (ca. 15 min), daarna afspraak op een KvK-kantoor met ID. Kosten 2026: €85,15 eenmalig.
**Tijdlijn:** KvK-nummer krijg je bij de afspraak. Het btw-nummer komt per post van de Belastingdienst, normaal binnen 10 werkdagen, soms langer. Een factuur moet een btw-nummer hebben, dus de eerste factuur pas sturen als dat binnen is.
**Keuzes om vooraf te maken:**
- **Adres:** bezoekadres van een eenmanszaak mag je zonder reden laten afschermen, maar dan moet er een openbaar postadres komen (bijv. postadres-service of adres van familie met hun toestemming). Gebruik je een ander adres als vestiging, dan heb je bewijs nodig dat je het mag gebruiken.
- **Kleineondernemersregeling (KOR):** geen btw rekenen, maar ook geen btw terugvragen. Bij zakelijke klanten maakt btw voor hen niet uit (zij vragen het terug).
- **Zakelijke rekening:** niet verplicht voor een eenmanszaak. Besluit 10-11: openen zodra een klant ja zegt (nu nog geen inkomsten, dus geen maandkosten zonder reden).
**Volgorde bij de eerste klant:**
1. ~~KvK-inschrijving~~ (gedaan 12-11, KvK 42220238; btw-nummer volgt).
2. Klant zegt ja → direct zakelijke rekening openen (goedkope online bank, geen lange contractduur). Loopt tegelijk met het wachten op het btw-nummer, dus geen tijdverlies.
3. Tweede gesprek: voorstel laten zien en akkoord krijgen, nog zonder factuur.
4. Btw-nummer binnen en zakelijke rekening klaar → pas dan de factuur voor de eerste betaling sturen (met het zakelijke rekeningnummer).
**Kosten:** domein, Workspace, Claude, server mogen via de privérekening. Facturen bewaren (later op te voeren als bedrijfskosten), vanaf inschrijving op bedrijfsnaam laten zetten.
**Daarna:** KvK-nummer doorgeven aan Claude, zodat het in de footer van de (nieuwe) website komt. "KVK: volgt" is in het nieuwe ontwerp weggehaald tot het nummer er is.

---

## AVG: verwerkersovereenkomst regelen

**Status:** Geparkeerd sinds 2026-10-04
**Waarom geparkeerd:** Kwam naar voren bij de privacyvraag in de FAQ van het website-redesign. Nu geen tijd, wel nodig.
**Wat er moet gebeuren:**
1. Sjabloon verwerkersovereenkomst maken (startpunt: gratis model van Nederland ICT). Hierin staan welke gegevens Insightance verwerkt, hoe ze beveiligd zijn en welke sub-verwerkers worden ingeschakeld (Hetzner, Anthropic/Claude, eventueel OpenAI).
2. Bij elke nieuwe klant laten tekenen, bijvoorbeeld als bijlage bij de offerte. Voor bestaande klanten (MHL) alsnog regelen.
3. Eigen afspraken met leveranciers checken: Anthropic (zit in zakelijke voorwaarden), Hetzner (AV-contract afsluiten in het account).
4. Privacybeleid op de website nalopen bij het live zetten van het nieuwe ontwerp.
**Let op:** Wettelijk verplicht zodra Insightance persoonsgegevens van klanten verwerkt. Eén keer laten checken door een jurist is verstandig.

---

## OLVG SEH-rooster met AI (constraint solver + roosteraar)

**Status:** Geparkeerd sinds 2026-10-04
**Waarom geparkeerd:** Hersenspinsel van Oussama over het SEH-rooster bij OLVG, waar het team ontevreden over is (40-uurs roosteraar, trage/foutgevoelige handmatige planning). Nog te vroeg: eerste prioriteit blijft de eerste betalende e-commerce-klant, en dit project (eigen werkgever, patiëntveiligheid, nul foutmarge) is qua complexiteit en risico een flinke stap boven wat Oussama tot nu toe gebouwd heeft.
**Wat het is:** AI-ondersteund roostersysteem voor de SEH. Geen LLM die direct een rooster genereert (dat gaat fout bij harde regels zoals rusttijd/arbeidstijdenwet), maar een constraint solver (bijv. Google OR-Tools) als deterministische kern, met AI als laag eromheen voor het verzamelen van voorkeuren en het toelichten van de uitkomst. Roosteraar blijft eindverantwoordelijk voor de check (±2 uur in plaats van 40 uur/week).
**Kansen:** Als het bij OLVG werkt, is het een sterke case study richting andere ziekenhuizen/zorgorganisaties. Het is een erkend, veelvoorkomend probleem (het "Nurse Scheduling Problem" in de operations research).
**Risico's om vooraf te dekken:** patiëntveiligheid (fout rooster op de SEH is geen kleinigheid), privacy/IT-governance van personeelsgegevens, en de politieke gevoeligheid van het mogelijk overbodig maken van de roosteraarsfunctie (beter positioneren als hulpmiddel dan als vervanging).
**Trigger om op te pakken:** Oussama gooit zelf het balletje op bij OLVG ICT zodra het relevant voelt, bijvoorbeeld na de eerste succesvolle klantlevering in de e-commerce-outreach. Geen actie van Claude nodig tot dat moment.

---

## ~~Contentagent voor Instagram~~ — gebouwd 2026-11-04 t/m 11-09

Fase 1 af: agent maakt carrousels, kaarten, tekst-reels, demo-reels, actualiteiten, stories en video's met stem (Eric), Oussama keurt goed in Telegram en plaatst zelf. Draait op de server. Zie `workflows/instagram_content.md` en `plans/2026-11-04-instagram-contentagent.md`.
**Nog open:** dagelijkse concepten om 08:15 staan aan (10-11); posten vanaf 16-11; na 2-3 weken video met/zonder stem vergelijken.
**Fase 2 (later):** automatisch posten na ✅.

---

## ElevenLabs voice agent

**Status:** Geparkeerd sinds 2026-11-02, geen trigger-datum
**Waarom geparkeerd:** Idee van de zwager, nog geen concreet, herhalend proces dat het zou moeten vervangen. Nu bouwen zou een oplossing zijn zonder scherp probleem.
**Wat het is:** ElevenLabs is een voice-agent/conversational AI waarmee je kunt praten en die dingen voor je bijhoudt of vastlegt (vergelijkbaar met hoe IntelOS/Fathom meetings al vastlegt, maar dan losstaand via spraak).
**Trigger om op te pakken:** Geen vaste datum. Wel: zodra Oussama vraagt of er nog dingen te doen zijn/opgepakt kunnen worden, dit item proactief opperen.

---

## ~~LinkedIn Pijler 2 ("Herkenbare pijn") fine-tunen~~ — afgerond 2026-08-21

Hernoemd naar "The Other Shift", volledig uitgewerkt: wekelijks woensdag 11:00, geen CTA, geen afbeelding, hashtag-regel, 4 posts klaar. Zie `outputs/linkedin-content-serie.md`.
