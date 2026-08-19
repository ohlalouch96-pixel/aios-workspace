# Business Funnel

> Hoe Oussama's AI-agency aandacht omzet naar omzet.
> Aangemaakt tijdens Daily Brief setup. Gelezen door /prime en Daily Brief.

## Valuta
EUR

## Fases

### 1. Outreach
Webshops benaderen via Instagram DM voor cart-recovery e-mailautomatisering.
- Totaal benaderd → outreach (COUNT WHERE status != 'Te versturen')
- Benaderd deze week → outreach (COUNT WHERE substr(datum_dm1,7,4)||'-'||substr(datum_dm1,4,2)||'-'||substr(datum_dm1,1,2) >= date('now','-7 days'))

### 2. Respons
Prospects die reageren op de outreach.
- Gereageerd → outreach (COUNT WHERE gereageerd = 'Ja')

### 3. Deal
Klanten die akkoord gaan met een AI-workflow.
- Deals gesloten → outreach (COUNT WHERE status = 'Deal')

### 4. Afgewezen
Prospects die niet geïnteresseerd zijn.
- Afgewezen → outreach (COUNT WHERE status = 'Afgewezen')

## Conversie
- Doel conversieratio: 10-20% van benaderd naar deal
- Huidig product: Afspraken-workflow voor kappers — €1.500 eenmalig, ~7 dagen werk

## Maandelijkse Doelen
- Benaderd: 20+ per maand
- Deals: 2-3 per maand
- Omzet: €3.000-4.500 per maand (richting ziekenhuissalaris)
