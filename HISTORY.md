# Workspace History

> Chronologisch logboek van alles wat gebouwd is in deze workspace. Wordt bijgewerkt elke sessie.
> Meest recente entries bovenaan. Elke entry heeft een datum, titel en bullet points.
>
> **Hoe het werkt:** Als je `/commit` uitvoert na betekenisvol werk, voegt Claude hier automatisch een entry aan toe.
> Je hoeft dit bestand niet zelf bij te houden.

---

## 2026-10-13

### Insightance Website — Landingspagina voor webshops

- Nieuwe pagina insightance.ai/webshops (NL/EN, automatische taalkeuze), bedoeld als bestemming voor de webshop-outreach; niet in het menu, wel in de footer ("Voor webshops") en de sitemap
- Kop "7 van de 10 winkelmandjes worden nooit afgerekend. Haal die omzet terug." met een realistische voorbeeldmail van een verzonnen webshop (Saelvo) en de uitleg dat het in de eigen huisstijl komt
- Rekentool: bestellingen per maand x orderbedrag, 70% verlaten mandjes, 5-10% terug te halen (voorzichtig gerekend)
- Hoe het werkt (3 mails), wat je krijgt (Klaviyo; Shopify, WooCommerce e.a.), bewijs met de reeks in beeld en quotes van MHL en FTUK, werkwijze zoals op de homepage, FAQ
- Bron: `outputs/landingspagina-webshops/_maak_webshops.py`
- Advies outreach: link in mail 2-4 en ondertekening, op Instagram pas na een reactie

### Insightance Website — Tweede kritische ronde

- Zoekmachines (Googlebot e.d.) krijgen altijd de Nederlandse versie; bezoekers nog steeds hun eigen taal
- FAQ "Wat gebeurt er met mijn gegevens?" eerlijker: gegevens gaan alleen langs de diensten waarop het systeem draait (AI, beveiligde server)
- Naam in het browsertabblad wisselt mee met NL/EN
- Grotere tikvlakken rond kleine links op touchscreens (footer, demo-/case-links, Terug), zonder zichtbare verandering
- Bewust niet gedaan: bronnen bij de cijfers in "Het probleem", prijsindicatie, Nederlandse Calendly; KvK-nummer volgt na inschrijving

---

## 2026-10-12

### Insightance — Engels voor internationaal

- Website kiest zelf de taal: toestel met Nederlands als eerste taal krijgt NL, alle andere EN; eigen keuze via NL/EN-knop blijft onthouden
- Linkvoorbeeld (tegel + titel/tekst) in het Engels: "Less manual work. More room to grow."
- Engelse LinkedIn-banner gemaakt (`outputs/linkedin-banner-2026/linkedin-banner-navy-EN-UPLOAD.png`); Engelse websitekop blijft bewust "Manual work disappears. Growth takes over."
- LinkedIn voor/na-post met BEFORE/AFTER-afbeelding (`outputs/website-metamorfose/post/linkedin-voor-na-mobiel.png`)

---

## 2026-10-11

### Insightance Website — WhatsApp terug en frisse-blik-screening

- WhatsApp-knop, WhatsApp-links en telefoonnummer weer zichtbaar (tijdelijk verborgen geweest voor de voor/na-story)
- Volledige screening live site: geen fouten, kapotte links of afbeeldingen op desktop en mobiel
- Linkvoorbeeld toegevoegd: bij delen op LinkedIn/WhatsApp verschijnt een navy kaart met logo en kopregel (`docs/images/og-insightance.png`, bron `outputs/logo-2026/_maak_og.py`)
- Sitemap, robots.txt en bedrijfsgegevens voor Google; klanttools (MHL, FTUK) uit de zoekresultaten gehouden
- Eigen 404-pagina in de huisstijl
- Oude previewpagina's en 30 testscreenshots uit de bouwfase verwijderd
- Pop-up/nieuwsbrief-idee geparkeerd in `todo/README.md` tot er bezoekerscijfers zijn

---

## 2026-10-09

### Insightance Website — Verbeteringen na de lancering

- Echte favicon-bestanden (navy logo), zodat Google het logo kan tonen in plaats van een wereldbol
- "Hoe Insightance werkt" en "Tarieven" samengevoegd tot één sectie "Werkwijze": 5 stappen met wat elke stap kost (gratis kennismaking en voorstel, 50% bij akkoord, 50% als alles werkt), menu aangepast
- Over Insightance: nieuwe tekst ("goed werk begint bij goede systemen") en de zin over het werk dat gedaan zou moeten worden onder de quote
- Klantcases op mobiel: wolkjes en FTUK-dashboard passen nu in het vlak (homepage en resultaten)
- Demo-pagina: blauwe lijn loopt altijd door tot onderaan
- Voor wie: pagina verspringt niet meer op mobiel; FAQ: één vraag tegelijk open
- Contactformulier: bedrijfsnaam optioneel; demo-links heten "Bekijk een demo"

---

## 2026-10-08

### Insightance Website — Nieuwe Website Live (licht/blauw redesign)

**Nieuwe look op alle pagina's** (homepage, automations, resultaten, demo, privacybeleid)
- Van donker/goud naar licht/blauw, met de doorlopende blauwe lijn ("rode draad")
- Overal je-vorm, rustigere letters (Playfair alleen voor koppen), meer witruimte tussen secties
- Lettertypes staan nu op de eigen site (`docs/fonts/`), geen Google Fonts meer
- Nieuwe demo-pagina met 4 afspeelbare scenario's, resultatenpagina met sectorkeuze

**Inhoud**
- Werkwijze in 4 stappen met per stap wat de klant krijgt, 50/50-betaling benoemd
- AI-assessment van €300 geschrapt: na het gesprek een gratis voorstel met vaste prijs
- WhatsApp-knop in plaats van chat, Calendly-agenda als pop-up bij Contact
- Contactformulier verstuurt via Formspree (telefoon optioneel), cookiemelding behouden
- Privacybeleid vernieuwd (Calendly, WhatsApp), datum 8 oktober 2026
- MHL-schermafbeelding vervangen door versie met onleesbare klantgegevens

**Back-up oude site:** `outputs/website-backup-live-2026-10-08/`

---

## 2026-06-25

### Insightance Website — Subpagina's Gesynchroniseerd & UX Verbeterd

**Resultaten sectie (homepage)**
- Titel gewijzigd naar "Wat we bouwen, werkt", oude titel werd subtitel
- Navbar anchor fix: "Resultaten" link verwees naar #cases, nu correct #resultaten
- FTUK "Bekijk case study" link gaat nu direct naar `resultaten.html#ftuk` (anchor op Case 02)

**Resultaten pagina (resultaten.html)**
- Navbar volledig gesynchroniseerd met hoofdwebsite: NL/EN pill-toggle, transparante CTA-knop
- Nav-links vervangen door "← Terug naar homepage" (verwijst terug naar #resultaten sectie)
- NL/EN toggle bug opgelost: `textContent` overschreef de spans, nu correct
- Footer vervangen door exacte kopie van hoofdwebsite (met e-mail/WhatsApp/LinkedIn iconen)
- CTA blok onder cases: kleinere lettergrootte, niet meer vetgedrukt

**Diensten pagina (automations.html)**
- Navbar gesynchroniseerd met hoofdwebsite: zelfde NL/EN pill, CTA-knop stijl
- Nav-links vervangen door "← Terug naar homepage" (verwijst terug naar #services sectie)
- Footer toegevoegd (ontbrak volledig) — exacte kopie van hoofdwebsite

---

## 2026-06-18

### Insightance Website — Logo's & Case Study Verbeterd

**Logo's tool-strip (echte merkkleuren)**
- Slack: vervangen door officieel 4-kleurig SVG (rood, blauw, groen, geel)
- Anthropic/Claude: vervangen door officieel starburst SVG (#D97757 terracotta)
- Google AI: vervangen door Gemini-ster SVG met gradient (blauw → paars → rood)
- Lovable: vervangen door officieel L-shape SVG met gradient (oranje → roze → blauw)
- Gmail: vervangen door officieel 5-kleurig SVG via Wikimedia (Google merkkleurem)
- Make: vervangen door inline SVG met officiële paarse gradient (#EE2FEE → #240342)

**Navigatie**
- "Resultaten" toegevoegd aan desktop- en mobiel menu (link naar #cases)
- "AI-systemen" verwijderd uit nav
- "jouw" gewijzigd naar "uw" in CTA-tekst

**MHL case study — story-first herstructurering**
- Labels gewijzigd van Situatie/Oplossing naar Vroeger/Nu
- Vroeger-tekst uitgebreid met concreet stappenproces (Word openen, kopiëren, PDF exporteren, mailen)
- 90%-metric verplaatst naar linkerkolom onderaan
- Rechterkolom: quote Mohammed → screenshot systeem → "Herkent u dit?" → CTA
- Aparte donkere demo-sectie verwijderd, alles geïntegreerd in één kaart
- Demo-banner tekst vereenvoudigd (uitprobeer-tekst verwijderd)
- Screenshot van systeem toegevoegd als statisch beeld (docs/images/mhl-demo-preview.jpg)
- CTA aangepast naar "Wat zou dit voor uw bedrijf opleveren?"

**Bio geschreven voor Looma (netwerk platform)**
- "I build AI automations for small businesses looking to cut down on manual work, early days but already working with my first clients. Always keen to connect with people in AI, tech or entrepreneurship. Based in Amsterdam."

---

## 2026-06-15

### Insightance — Eerste Klant & Infrastructuur Live

**FTUK project (gratis pilot)**
- Analyse van FTUK gedaan: prop trading firm, €50k/maand adspend, gebruikt HYROS
- Voorstel #002 gemaakt: AI Media Intelligence systeem (creative intelligence, competitor monitoring, geo trends)
- Akkoord ontvangen: gratis pilot (Abdelilah is familie)
- Hetzner server opgezet (91.99.172.227, CPX22, Ubuntu 22.04)
- n8n geïnstalleerd via Docker op eigen server
- Workflow 1 gebouwd: dagelijks rapport (Schedule → Claude → Brevo email)
- Workflow 2 gebouwd: Telegram alerts via @ftuk_alerts_bot
- Wacht op: WooCommerce API en HYROS viewer toegang van Abdelilah Ibrahimi

**MHL Installatieservice (gratis pilot)**
- Analyse gedaan van mhl-installatieservice.nl
- Intake vragenlijst opgesteld
- Voorstel #001 gemaakt (gratis pilot, €0)
- Offerte aanvraagformulier gebouwd (outputs/offerte-formulier-mhl.html)
- Volgende stap: formulier plaatsen op Wix website (vader uitnodigen als editor)

**Insightance infrastructuur**
- Website live op https://insightance.ai (GitHub Pages + Cloudflare)
- Email live: oussama@insightance.ai (Google Workspace, Gmail geactiveerd)
- DNS volledig omgezet naar Cloudflare
- Google Workspace MX records en DKIM ingesteld
- HTTPS bevestigd werkend via Cloudflare SSL

---

## 2026-04-25

### InfraOS Installatie
- Git geïnitialiseerd en workspace getrackt
- .gitignore aangemaakt (beschermt .env en credentials)
- .env.example aangemaakt als publieke sleutelsjabloon
- Drie kern-API-sleutels ingesteld: Anthropic, OpenAI, Google Gemini
- HISTORY.md aangemaakt (dit bestand)
- docs/ systeem aangemaakt met routing-index en sjablonen
- /commit commando geïnstalleerd
- /prime en /implement bijgewerkt met InfraOS-bewustzijn

### ContextOS Installatie
- Alle 4 context-bestanden geschreven op basis van CV, LinkedIn en chat-interview
- CLAUDE.md gepersonaliseerd met Context Summary voor Oussama's AI-agency
- /prime getest en werkend bevestigd
