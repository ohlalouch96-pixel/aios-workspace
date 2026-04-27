# Business Funnel

> Hoe Oussama's AI-agency aandacht omzet naar omzet.
> Aangemaakt tijdens Daily Brief setup. Gelezen door /prime en Daily Brief.

## Valuta
EUR

## Fases

### 1. Outreach
Kappers, beautysalons en andere kleine ondernemers benaderen via Instagram, WhatsApp, LinkedIn of persoonlijk contact.
- Totaal benaderd → outreach (COUNT WHERE status != '')
- Benaderd deze week → outreach (COUNT WHERE status = 'benaderd')

### 2. Respons
Prospects die reageren op de outreach.
- Gereageerd → outreach (COUNT WHERE status = 'gereageerd')

### 3. Deal
Klanten die akkoord gaan met een AI-workflow voor €1.500 eenmalig.
- Deals gesloten → outreach (COUNT WHERE status = 'deal')
- Omzet potentieel → outreach (SUM omzet_potentieel WHERE status = 'deal')

### 4. Afgewezen
Prospects die niet geïnteresseerd zijn.
- Afgewezen → outreach (COUNT WHERE status = 'afgewezen')

## Conversie
- Doel conversieratio: 10-20% van benaderd naar deal
- Huidig product: Afspraken-workflow voor kappers — €1.500 eenmalig, ~7 dagen werk

## Maandelijkse Doelen
- Benaderd: 20+ per maand
- Deals: 2-3 per maand
- Omzet: €3.000-4.500 per maand (richting ziekenhuissalaris)
