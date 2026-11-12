# UTM-links voor outreach

Sinds 2026-11-03 meet insightance.ai bezoekers met Google Analytics 4 (alleen na akkoord in de cookiemelding, zie `docs/consent.js`).
Elke link naar de site in een outreachbericht krijgt UTM-parameters, zodat in GA4 te zien is welk kanaal en welk bericht bezoekers oplevert.

## Vaste opbouw

```
insightance.ai/<pagina>?utm_source=<kanaal>&utm_medium=outreach&utm_campaign=<bericht>
```

| Parameter      | Waarden                                                    |
| -------------- | ---------------------------------------------------------- |
| `utm_source`   | `email`, `instagram`, `linkedin`                           |
| `utm_medium`   | altijd `outreach`                                          |
| `utm_campaign` | het bericht: `mail1` t/m `mail4`, `dm2`, `li1`, `li2`, `voorbeeld` |

Welke landingspagina (webshops of vakbedrijven) staat al in de URL, dus die hoeft niet in de campagnenaam.

## Kant-en-klare links

| Waar                                       | Link |
| ------------------------------------------ | ---- |
| Webshop-mail 1 (ondertekening)             | `insightance.ai/webshops?utm_source=email&utm_medium=outreach&utm_campaign=mail1` |
| Webshop-mail 2 (onder de rekensom)         | `insightance.ai/webshops?utm_source=email&utm_medium=outreach&utm_campaign=mail2` |
| Webshop-mail 3 (ondertekening)             | `insightance.ai/webshops?utm_source=email&utm_medium=outreach&utm_campaign=mail3` |
| Webshop-mail 4 (ondertekening)             | `insightance.ai/webshops?utm_source=email&utm_medium=outreach&utm_campaign=mail4` |
| Instagram DM2                              | `insightance.ai/webshops?utm_source=instagram&utm_medium=outreach&utm_campaign=dm2` |
| Ondernemers e-mail bericht 2               | `insightance.ai/vakbedrijven?utm_source=email&utm_medium=outreach&utm_campaign=mail2` |
| Ondernemers LinkedIn bericht 1 (handmatig, InMail, zie outreach-ondernemers-email-strategie.md) | `insightance.ai/vakbedrijven?utm_source=linkedin&utm_medium=outreach&utm_campaign=li1` |
| LinkedIn Outreach Agent — bericht 2 (follow-up zonder reactie), volledige URL | `insightance.ai/vakbedrijven?utm_source=linkedin&utm_medium=outreach&utm_campaign=li2` |
| LinkedIn Outreach Agent — bericht 2, korte link (dit is wat daadwerkelijk in het bericht staat) | `insightance.ai/offerte` (korte link, `docs/offerte/index.html`, stuurt door naar de regel hierboven) |
| Voorbeeldmail via Instagram                | `insightance.ai/voorbeeld/<shop>.html?utm_source=instagram&utm_medium=outreach&utm_campaign=voorbeeld` |
| Voorbeeldmail via e-mail                   | `insightance.ai/voorbeeld/<shop>.html?utm_source=email&utm_medium=outreach&utm_campaign=voorbeeld` |

## Eigen kanalen (geen outreach)

Zelfde opbouw, maar `utm_medium` zegt waar de link staat.

| Waar                         | Link |
| ---------------------------- | ---- |
| Instagram-bio (persoonlijk)  | `insightance.ai/ig` (korte link, `docs/ig/index.html`, stuurt door naar `insightance.ai/?utm_source=instagram&utm_medium=bio`) |
| Instagram-bio (merkpagina)   | `insightance.ai/go` (korte link, `docs/go/index.html`, stuurt door naar `insightance.ai/?utm_source=instagram&utm_medium=bio&utm_campaign=merkpagina`) |
| Instagram-story (linksticker) | `insightance.ai/?utm_source=instagram&utm_medium=story&utm_campaign=<onderwerp>` |
| LinkedIn-profiel (website/uitgelicht) | `insightance.ai/li` (korte link, `docs/li/index.html`, stuurt door naar `insightance.ai/?utm_source=linkedin&utm_medium=profiel`) |
| LinkedIn-post                | `insightance.ai/<pagina>?utm_source=linkedin&utm_medium=post&utm_campaign=<onderwerp>` |
| WhatsApp Business-profiel    | `insightance.ai/wa` (korte link, `docs/wa/index.html`, stuurt door naar `insightance.ai/?utm_source=whatsapp&utm_medium=profiel`) |
| Gmail-handtekening           | zichtbaar `insightance.ai`, link `insightance.ai/?utm_source=email&utm_medium=handtekening` (bron: `outputs/logo-2026/handtekening-kopieren.html`) |
| LinkedIn-post rekentool (geboost, okt) | `https://insightance.ai/?utm_source=linkedin&utm_medium=post&utm_campaign=rekentool#rekentool` |
| Google Bedrijfsprofiel (website-veld, sinds 12-11) | `https://insightance.ai/?utm_source=google&utm_medium=bedrijfsprofiel` |
| QR visitekaartje (bij herdruk) | `insightance.ai/?utm_source=visitekaartje&utm_medium=qr` |

`<onderwerp>` kort en in kleine letters, bv. `rekentool`, `mhl-case`, `myth-check`.
De visitekaartjes van oktober 2026 hebben een QR naar `insightance.ai` zonder label; die scans tellen in GA4 als "direct".

## Acties die GA4 meet (sinds 2026-11-03)

`gesprek_ingepland` (Calendly-afspraak geboekt), `contactformulier_verstuurd`, `whatsapp_klik`, `email_klik` (deze vier als sleutelgebeurtenis), plus `agenda_geopend`, `contact_knop_klik`, `rekentool_gebruikt`, `offertetool_demo_gebruikt`. Code in `docs/consent.js`.

## Regels

- Kleine letters, geen spaties. Een afwijkende schrijfwijze (`Email` i.p.v. `email`) wordt in GA4 een aparte bron.
- Geen punt direct achter de link zetten: sommige apps nemen die mee in de link.
- Gmail-handtekening heeft sinds 03-11 een onzichtbaar UTM-label (`utm_medium=handtekening`), los van de link in de mailtekst.
- Terugzien in GA4: Rapporten > Acquisitie > Verkeersacquisitie, dimensie "Sessiebron/-medium" of "Sessiecampagne".
- Bezoekers die de cookiemelding weigeren worden niet gemeten. De cijfers zijn dus een ondergrens.
