# Workspace History

> Chronologisch logboek van alles wat gebouwd is in deze workspace. Wordt bijgewerkt elke sessie.
> Meest recente entries bovenaan. Elke entry heeft een datum, titel en bullet points.
>
> **Hoe het werkt:** Als je `/commit` uitvoert na betekenisvol werk, voegt Claude hier automatisch een entry aan toe.
> Je hoeft dit bestand niet zelf bij te houden.

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
