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
| `utm_campaign` | het bericht: `mail1` t/m `mail4`, `dm2`, `li1`, `voorbeeld` |

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
| Ondernemers LinkedIn bericht 1             | `insightance.ai/vakbedrijven?utm_source=linkedin&utm_medium=outreach&utm_campaign=li1` |
| Voorbeeldmail via Instagram                | `insightance.ai/voorbeeld/<shop>.html?utm_source=instagram&utm_medium=outreach&utm_campaign=voorbeeld` |
| Voorbeeldmail via e-mail                   | `insightance.ai/voorbeeld/<shop>.html?utm_source=email&utm_medium=outreach&utm_campaign=voorbeeld` |

## Regels

- Kleine letters, geen spaties. Een afwijkende schrijfwijze (`Email` i.p.v. `email`) wordt in GA4 een aparte bron.
- Geen punt direct achter de link zetten: sommige apps nemen die mee in de link.
- De Gmail-handtekening (insightance.ai) blijft zonder UTM.
- Terugzien in GA4: Rapporten > Acquisitie > Verkeersacquisitie, dimensie "Sessiebron/-medium" of "Sessiecampagne".
- Bezoekers die de cookiemelding weigeren worden niet gemeten. De cijfers zijn dus een ondergrens.
