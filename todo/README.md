# To-do — Geparkeerd

> Dingen die Oussama nog wil doen maar op dit moment even parkeert.
> Geen deadline, geen prioriteit-volgorde — gewoon een plek om ze niet kwijt te raken.
> Verplaats een item naar `plans/` met `/create-plan` zodra je het echt oppakt.

---

## E-mail-follow-ups als concept in Gmail klaarzetten (DEZE WEEK)

**Status:** Gepland voor de week van 2026-10-06, nog niet opgepakt
**Waarom:** Door de outreach-volumes lopen follow-ups snel op (elke nieuwe DM = 3 berichten, elke nieuwe mail = 4). E-mail is het enige kanaal dat veilig te automatiseren is.
**Stap 1 (nu):** Claude zet de e-mail-follow-ups (webshops mail 2/3/4 + ondernemers bericht 2/3) als concept klaar in Gmail via de Gmail-koppeling. Oussama klikt alleen op versturen.
**Stap 2 (later, na vertrouwen):** Volledig automatisch versturen via n8n, binnen het dagmaximum.
**Randvoorwaarde:** Dagmaximum aanhouden: ~40 Instagram + ~40 e-mail per dag (nieuw + follow-ups samen).

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

**Status:** Geparkeerd — moet nog steeds gebeuren
**Waarom geparkeerd:** Was volgens `context/strategy.md` gepland "zodra eerste klant in zicht" — nog niet zover.
**Wat er moet gebeuren:** Bedrijf inschrijven bij de Kamer van Koophandel.
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

## Visitekaartjes laten drukken

**Status:** Geparkeerd sinds 2026-10-04
**Waarom geparkeerd:** Website en logo (kleur) worden nog aangepast, wachten tot dat vastligt voor consistente kleuren op het kaartje.
**Wat er moet gebeuren:** Visitekaartje ontwerpen en bestellen in de nieuwe huisstijlkleuren, zodra het nieuwe logo en de website live staan.
**Waar:** Vistaprint of Drukwerkdeal (prijs/kwaliteit vergeleken op 2026-10-04, zie gesprekshistorie).
**Trigger om op te pakken:** Zodra de vernieuwde website (met nieuw logo) live staat op insightance.ai — Claude moet Oussama hier dan actief aan herinneren.

---

## OLVG SEH-rooster met AI (constraint solver + roosteraar)

**Status:** Geparkeerd sinds 2026-10-04
**Waarom geparkeerd:** Hersenspinsel van Oussama over het SEH-rooster bij OLVG, waar het team ontevreden over is (40-uurs roosteraar, trage/foutgevoelige handmatige planning). Nog te vroeg: eerste prioriteit blijft de eerste betalende e-commerce-klant, en dit project (eigen werkgever, patiëntveiligheid, nul foutmarge) is qua complexiteit en risico een flinke stap boven wat Oussama tot nu toe gebouwd heeft.
**Wat het is:** AI-ondersteund roostersysteem voor de SEH. Geen LLM die direct een rooster genereert (dat gaat fout bij harde regels zoals rusttijd/arbeidstijdenwet), maar een constraint solver (bijv. Google OR-Tools) als deterministische kern, met AI als laag eromheen voor het verzamelen van voorkeuren en het toelichten van de uitkomst. Roosteraar blijft eindverantwoordelijk voor de check (±2 uur in plaats van 40 uur/week).
**Kansen:** Als het bij OLVG werkt, is het een sterke case study richting andere ziekenhuizen/zorgorganisaties. Het is een erkend, veelvoorkomend probleem (het "Nurse Scheduling Problem" in de operations research).
**Risico's om vooraf te dekken:** patiëntveiligheid (fout rooster op de SEH is geen kleinigheid), privacy/IT-governance van personeelsgegevens, en de politieke gevoeligheid van het mogelijk overbodig maken van de roosteraarsfunctie (beter positioneren als hulpmiddel dan als vervanging).
**Trigger om op te pakken:** Oussama gooit zelf het balletje op bij OLVG ICT zodra het relevant voelt, bijvoorbeeld na de eerste succesvolle klantlevering in de e-commerce-outreach. Geen actie van Claude nodig tot dat moment.

---

## ~~LinkedIn Pijler 2 ("Herkenbare pijn") fine-tunen~~ — afgerond 2026-08-21

Hernoemd naar "The Other Shift", volledig uitgewerkt: wekelijks woensdag 11:00, geen CTA, geen afbeelding, hashtag-regel, 4 posts klaar. Zie `outputs/linkedin-content-serie.md`.
