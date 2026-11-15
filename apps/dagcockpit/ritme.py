"""
Dagcockpit — vast weekritme

Hier staat welke taken op welke dag terugkomen en wanneer er LinkedIn-content
live gaat. Aanpassen = dit bestand bewerken; de cockpit leest het bij elke
paginaweergave opnieuw in (geen herstart nodig voor de inhoud, wel voor nieuwe
velden).

Dagen: 0 = maandag ... 6 = zondag.
"""

ALLE_DAGEN = {0, 1, 2, 3, 4, 5, 6}

# Kaarten in de cockpit, in deze volgorde. "kleur" bepaalt het labeltje.
CHATS = {
    "LinkedIn": "blauw",
    "Webshops": "blauw",
    "Ondernemers en makelaars": "oranje",
    "Instagram": "paars",
    "Website": "paars",
    "Content": "oranje",
    "Algemeen": "grijs",
}

# Terugkerende taken. "dagen" = set weekdagen, of "laatste_zaterdag" voor de
# laatste zaterdag van de maand. "kort" = korte omschrijving voor de weekstrook.
# "vanaf": "JJJJ-MM-DD" = taak telt pas vanaf die datum.
# "toon_altijd": True = staat elke dag in de kaart (met het ritme-label erachter), ook op dagen buiten "dagen".
TAKEN = [
    {"id": "linkedin_verversen", "titel": "Dashboard verversen", "chat": "LinkedIn", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "linkedin_connecties", "titel": "Nieuwe connecties maken", "chat": "LinkedIn", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "linkedin_followups", "titel": "Follow-ups versturen", "chat": "LinkedIn", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "linkedin_check", "titel": "LinkedIn-content checken: hoe deden de posts het?", "chat": "LinkedIn", "ritme": "Donderdag", "dagen": {3}, "kort": "LinkedIn-check"},
    {"id": "webshop_followups", "titel": "Follow-ups versturen", "chat": "Webshops", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "webshop_nieuw", "titel": "Minimaal 10 nieuwe berichten", "chat": "Webshops", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "instagram_post", "titel": "Instagram-post plaatsen /plannen", "chat": "Instagram", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "instagram_kwartier", "titel": "Kwartiertje reageren", "chat": "Instagram", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "ondernemers_followups", "titel": "Follow-ups versturen", "chat": "Ondernemers en makelaars", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "belronde", "titel": "Belronde", "chat": "Ondernemers en makelaars", "ritme": "Ma t/m do", "dagen": {0, 1, 2, 3}, "kort": "Belronde", "toon_altijd": True},
    {"id": "ga4", "titel": "Websitecijfers bekijken (GA4)", "chat": "Website", "ritme": "Maandag", "dagen": {0}, "kort": "Websitecijfers"},
    {"id": "instagram_klaarzetten", "titel": "Instagram-content volgende week inplannen", "chat": "Instagram-content", "ritme": "Zaterdag", "dagen": {5}, "kort": "Instagram inplannen", "vanaf": "2026-11-21"},
    {"id": "content_maand", "titel": "Content volgende maand klaarzetten (LinkedIn + Telegram)", "chat": "Content", "ritme": "Laatste zaterdag", "dagen": "laatste_zaterdag", "kort": "Content klaarzetten"},
]

# Volgorde waarin een dag zijn label in de weekstrook krijgt (eerste die die dag valt wint).
WEEKSTROOK_VOORRANG = ["content_maand", "instagram_klaarzetten", "ga4", "linkedin_check", "belronde"]

# LinkedIn-content die automatisch live gaat (ingepland in LinkedIn's planner).
# Zie outputs/linkedin-content-serie.md voor de pijlers.
LINKEDIN_WEKELIJKS = [
    {"dag": 1, "tijd": "10:30", "pijler": "Automation Simplified"},
    {"dag": 2, "tijd": "11:00", "pijler": "The Other Shift"},
    {"dag": 3, "tijd": "10:30", "pijler": "Automation Simplified"},
    {"dag": 0, "tijd": "09:30", "pijler": "Myth Check"},
]

# Instagram: standaard aantal ingeplande posts per dag (per dag aan te passen in de cockpit).
# Wekelijks op zaterdag klaargezet, eerste keer za 21-11-2026.
INSTAGRAM_STANDAARD_AANTAL = 1

# Korte pijlernamen voor de contenttegel.
PIJLER_KORT = {"Automation Simplified": "Automation", "The Other Shift": "Other Shift", "Myth Check": "Myth Check", "The Fork": "The Fork"}

# The Fork: 2x per maand op woensdag 16:00, vaste datums (JJJJ-MM-DD). Aanvullen bij het klaarzetten van een nieuwe maand.
LINKEDIN_LOS = [
    {"datum": "2026-11-11", "tijd": "16:00", "pijler": "The Fork"},
    {"datum": "2026-11-25", "tijd": "16:00", "pijler": "The Fork"},
]

SNELKOPPELINGEN = [
    # (titel, url of None = wordt in cockpit.py ingevuld)
    ("Outreach-tracker", None),
    ("LinkedIn-cockpit", None),
    ("Google Bedrijfsprofiel", "https://share.google/IeAqzslBZK05QWRRy"),
    ("Google Analytics", "https://analytics.google.com/"),
    ("Search Console", "https://search.google.com/search-console?resource_id=sc-domain:insightance.ai"),
    ("insightance.ai", "https://insightance.ai/"),
]

# Eenmalige herinneringen die bij de allereerste start worden ingeladen (daarna via "Taak toevoegen").
STARTHERINNERINGEN = [
    {"titel": "Reviewlink naar MHL en FTUK sturen", "chat": "Algemeen", "datum": "2026-11-14"},
    {"titel": "Bing checken: staat Insightance erop?", "chat": "Algemeen", "datum": "2026-11-24"},
    {"titel": "Vervolgafspraak fysiotherapeut", "chat": "Algemeen", "datum": "2026-11-25"},
    {"titel": "Btw-nummer binnen?", "chat": "Algemeen", "datum": "2026-11-26"},
    {"titel": "Google-post plaatsen", "chat": "Algemeen", "datum": "2026-11-28"},
    {"titel": "SEO-gesprek: eerste cijfers Search Console", "chat": "Algemeen", "datum": "2026-11-28"},
]

# Quote bovenaan de cockpit: elke dag een willekeurige (blijft de hele dag hetzelfde).
QUOTES = [
    "Iedere dag een klein beetje beter. Een beetje slimmer, een beetje sterker.",
    "Vandaag word je een betere versie van jezelf dan gisteren.",
    "Hou vol. Succes ligt om de hoek.",
    "Eén gesprek kan alles veranderen. Voer het vandaag.",
    "Kleine stappen, elke dag. Zo bouw je iets groots.",
    "Discipline brengt je verder dan motivatie ooit zal doen.",
    "Je eerste klant komt niet door wachten, maar door doen.",
    "Wie elke dag zaait, oogst vroeg of laat.",
]

# Vaste taken die ook in de tegel Binnenkort komen (naast de eenmalige herinneringen).
BINNENKORT_VAST = ["ga4", "linkedin_check", "content_maand"]
