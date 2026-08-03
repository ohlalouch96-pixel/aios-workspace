# E-commerce Email Outreach Strategie
**Datum:** 2026-06-26
**Status:** Actief plan

---

## Het Idee in één Zin

Vind Nederlandse webshops die geen abandoned cart flows hebben, benader ze met een gerichte pitch, en bouw die flows voor ze in Klaviyo.

---

## Waarom Dit Werkt

Abandoned cart flows zijn de hoogst renderende e-mail automation die bestaat. Gemiddeld verlaat 70% van de bezoekers een webshop zonder te kopen. Een goede flow haalt 10-15% van hen terug. Voor een webshop met €50.000/maand omzet is dat al snel €5.000-€7.500 extra per maand.

Jij loopt binnen met concrete data, niet met een vaag verkooppraatje.

---

## Fase 1: Setup — Wat je Nodig Hebt

### Accounts activeren (eenmalig)

| Tool | Waarvoor | Kosten | Actie |
|------|----------|--------|-------|
| **oussama@insightance.ai** | Outreach-e-mails sturen (professioneel) | Google Workspace ~€6/mnd | Activeren |
| **Klaviyo** | Email flows bouwen voor klanten | Gratis (client betaalt eigen account) | Account aanmaken op klaviyo.com |
| **Hunter.io** | Contactgegevens opzoeken van webshops | Gratis (25/mnd) | Account aanmaken |
| **Shopify Partners** | Toegang tot klant-stores | Gratis | Aanmaken op partners.shopify.com |
| **Wappalyzer** (browser ext.) | Snel tech stack checken | Gratis | Installeren in Chrome |

### Al aanwezig
- n8n draait op n8n.insightance.ai
- Google Sheets
- insightance.ai website

---

## Fase 2: Prospecting — Webshops Vinden

### Waar zoeken

1. **Thuiswinkel.org** — ledenlijst van Nederlandse webshops, gesorteerd per categorie
2. **Google zoeken** — "nederlandse webshop [niche]", "bestel online [product] nl"
3. **Instagram/TikTok ads** — als een webshop adverteert, hebben ze budget
4. **Shopify app store reviews** — Nederlandse shops die Shopify apps reviewen

### Selectiecriteria voor goede prospects

- Webshop met eigen domein (geen bol.com seller)
- Duidelijk product en merk (niet een dropshipping rommelwinkel)
- Actieve social media of advertising (= ze investeren al in marketing)
- Niche: mode, beauty, supplement, sport, lifestyle, home decor — emotionele producten converteren beter met e-mail

### Output: een lijst van 50-100 URLs in Google Sheets

---

## Fase 3: Kwalificeren — Hebben Ze Flows?

### Hoe detecteren zonder 2 dagen te wachten

Je hoeft nooit meer te wachten. Claude doet dit voor jou:

1. Geef een lijst van URLs
2. Claude haalt de broncode van elke website op
3. Claude zoekt naar e-mail marketing scripts in de HTML:
   - `klaviyo.com` → ze gebruiken Klaviyo (mogelijk flows, maar niet zeker)
   - `mailchimp` → waarschijnlijk alleen nieuwsbrief, geen automation
   - `omnisend`, `activecampaign`, `sendgrid` → afhankelijk van implementatie
   - **Niets gevonden** → geen email tool → **warm prospect**

### Kwalificatie-logica

| Situatie | Beoordeling |
|----------|-------------|
| Geen email tool gevonden | Heet prospect — stuur direct |
| Mailchimp of basic tool | Warm prospect — waarschijnlijk geen flows |
| Klaviyo aanwezig | Lagere prioriteit, maar niet uitsluiten |

### Output: gefilterde lijst in Google Sheets met kolom `email_tool` en prioriteit

---

## Fase 4: Contact Vinden

Voor elke webshop op de prospect-lijst:

1. **Hunter.io** — zoek op het domein → geeft e-mailadressen terug
2. **LinkedIn** — zoek de eigenaar of marketing manager
3. **Website zelf** — contact pagina, about pagina, Instagram bio

Doel: naam + e-mailadres van de beslisser (eigenaar of marketingmanager).

---

## Fase 5: Outreach — De Benadering

### Kanaal
**E-mail eerst** (vanuit oussama@insightance.ai). Als geen reactie na 3 e-mails: LinkedIn of Instagram DM.

### De Outreach Structuur (3 e-mails)

**E-mail 1 — Observatie + Propositie**
```
Onderwerp: [Winkel] — je laat bezoekers weggaan zonder follow-up

Hey [naam],

Ik ben Oussama, ik help Nederlandse webshops meer halen uit bezoekers die ze al hebben.

Ik keek naar [winkel] en zag dat jullie geen follow-up sturen naar mensen die iets in het winkelmandje leggen maar niet afrekenen.

Gemiddeld verlaat 70% van de bezoekers een webshop zonder te kopen. Een goede abandoned cart flow haalt 10-15% van hen terug — zonder extra advertentiebudget.

Ik bouw die flows voor webshops in Klaviyo. Geïnteresseerd in een kort gesprek van 15 minuten?

Oussama
insightance.ai
```

**E-mail 2 — Follow-up (3 dagen later)**
```
Onderwerp: Re: [Winkel]

Hey [naam],

Korte follow-up op mijn vorige mail.

Ik zag dat [winkel] actief is op [platform/advertentie/etc.] — dat betekent dat je al investeert in traffic. Jammer als die bezoekers weggaan zonder nog een kans te krijgen.

Ik heb dit recent ook voor [FTUK] opgezet — [kort resultaat].

15 minuten plannen?

Oussama
```

**E-mail 3 — Laatste poging (5 dagen later)**
```
Onderwerp: Laatste bericht van mij

Hey [naam],

Ik stuur je na dit geen mails meer.

Als abandoned cart flows nu geen prioriteit zijn: prima. Maar als je ooit wil kijken hoeveel omzet je laat liggen — je weet me te vinden.

Oussama
insightance.ai
```

---

## Fase 6: Discovery Call

Duur: 20-30 minuten. Doel: begrijpen wat ze verkopen, hoeveel traffic ze hebben, of ze al een e-maillijst hebben.

**Vragen:**
- Hoeveel bezoekers per maand?
- Wat is je gemiddelde orderwaarde?
- Heb je al een e-maillijst? Hoe groot?
- Gebruik je nu al enige vorm van e-mail marketing?
- Wat is je grootste uitdaging met conversie?

**Na de call:** stuur een korte offerte binnen 24 uur.

---

## Fase 7: Oplevering — Wat Je Van de Klant Nodig Hebt

Zodra ze akkoord gaan:

| Wat | Waarvoor |
|-----|----------|
| Toegang webshop (Shopify/WooCommerce admin) | Integratie met Klaviyo |
| Klaviyo account (of ze maken er een aan) | Hier worden de flows in gebouwd |
| Logo, kleuren, huisstijl | E-mails opmaken |
| Tone of voice / voorbeeld teksten | Copy schrijven |
| Bestaande e-maillijst (indien aanwezig) | Importeren in Klaviyo |
| Goedkeuring op e-mailteksten | Voordat flows live gaan |

---

## Fase 8: Bouwen — De Flows

Gebouwd in **Klaviyo**, niet in n8n. n8n gebruik je voor de outreach-automatisering, Klaviyo voor de daadwerkelijke e-mails.

### Abandoned Cart Flow (standaard pakket)

- **E-mail 1** — 1 uur na verlaten winkelmandje: herinnering, product afbeelding
- **E-mail 2** — 24 uur later: social proof / reviews
- **E-mail 3** — 48 uur later: urgentie of kleine incentive (optioneel)

### Upsell flows (voor retainer)

- Welcome series (3 e-mails voor nieuwe subscribers)
- Post-purchase flow (dankmail + cross-sell)
- Win-back flow (inactieve klanten)

---

## Prijsstrategie

| Pakket | Wat | Prijs |
|--------|-----|-------|
| Starter | Abandoned cart flow (3 e-mails) | €1.500 eenmalig |
| Volledig | Abandoned cart + welcome + post-purchase | €2.500 eenmalig |
| Retainer | Maandelijkse optimalisatie + rapportage | +€500-750/mnd |

Pitch altijd vanuit ROI: "Als jouw webshop €20.000/mnd omzet doet en we halen 10% terug van verlaten mandjes, dan verdien je deze investering terug in de eerste maand."

---

## n8n Automatisering van de Outreach

Zodra je de strategie begrijpt, bouwen we in n8n:

1. **Stap 1:** URL-lijst in Google Sheets
2. **Stap 2:** n8n haalt de broncode van elke URL op
3. **Stap 3:** n8n checkt op aanwezigheid van email tools
4. **Stap 4:** n8n logt resultaat (heeft_email_tool: ja/nee, welke tool) terug naar Sheets
5. **Stap 5:** Gefilterde lijst → Claude of jij zoekt contact op via Hunter.io
6. **Stap 6:** Outreach e-mails sturen (handmatig of via n8n + Gmail)

---

## Volgorde van Acties

1. [ ] oussama@insightance.ai activeren
2. [ ] Klaviyo account aanmaken
3. [ ] Hunter.io account aanmaken
4. [ ] Shopify Partners account aanmaken
5. [ ] Wappalyzer installeren in browser
6. [ ] Eerste lijst van 50 webshops samenstellen in Google Sheets
7. [ ] Claude laten checken welke sites geen email tool hebben
8. [ ] Contactgegevens opzoeken voor de top 20 prospects
9. [ ] Eerste outreach-mails sturen
10. [ ] n8n workflow bouwen voor automatische tech-stack detectie
