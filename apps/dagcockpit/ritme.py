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
    "Instagram": "paars",
    "Webshops": "blauw",
    "Installatiebedrijven en makelaars": "oranje",
    "Accountants en administratiekantoren": "blauw",
    "Website": "paars",
    "Content": "oranje",
    "Algemeen": "grijs",
}

# Terugkerende taken. "dagen" = set weekdagen, of "laatste_zaterdag" voor de
# laatste zaterdag van de maand. "kort" = korte omschrijving voor de weekstrook.
# "vanaf": "JJJJ-MM-DD" = taak telt pas vanaf die datum.
# "toon_altijd": True = staat elke dag in de kaart; op dagen buiten "dagen" grijs, niet aan te vinken en telt niet mee.
# "agenda": kortere titel voor de Agenda-tegel.
TAKEN = [
    # linkedin_verversen/connecties/followups gepauzeerd 23-11: outreach (connectieverzoeken +
    # berichten opvolgen) staat op een lager pitje, weinig reacties, focus nu op de accountants-
    # /administratiekantoren-coldcaller. LinkedIn-posten (linkedin_check + LINKEDIN_WEKELIJKS)
    # loopt gewoon door. Terugzetten zodra outreach weer wordt opgepakt.
    {"id": "linkedin_check", "titel": "Posts evalueren", "chat": "LinkedIn", "ritme": "Donderdag", "dagen": {3}, "kort": "LinkedIn-check", "agenda": "LinkedIn-posts evalueren"},
    {"id": "webshop_followups", "titel": "Follow-ups versturen", "chat": "Webshops", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "instagram_post", "titel": "Post plaatsen / plannen", "chat": "Instagram", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    {"id": "instagram_kwartier", "titel": "Kwartiertje reageren", "chat": "Instagram", "ritme": "Dagelijks", "dagen": ALLE_DAGEN},
    # ondernemers_followups verwijderd 24-11: geen follow-ups meer naar installatiebedrijven/makelaars.
    {"id": "belronde", "titel": "Belronde", "chat": "Installatiebedrijven en makelaars", "ritme": "Ma t/m vr", "dagen": {0, 1, 2, 3, 4}, "kort": "Belronde", "toon_altijd": True},
    {"id": "accountants_belronde", "titel": "Belronde", "chat": "Accountants en administratiekantoren", "ritme": "Ma t/m vr", "dagen": {0, 1, 2, 3, 4}, "toon_altijd": True},
    {"id": "ga4", "titel": "Websitecijfers (GA4)", "chat": "Website", "ritme": "Maandag", "dagen": {0}, "kort": "Websitecijfers", "agenda": "Websitecijfers (GA4)"},
    {"id": "instagram_klaarzetten", "titel": "Instagram-content volgende week inplannen", "chat": "Instagram-content", "ritme": "Zaterdag", "dagen": {5}, "kort": "Instagram inplannen", "vanaf": "2026-11-21", "agenda": "Instagram-content volgende week inplannen"},
    {"id": "content_maand", "titel": "Content volgende maand klaarzetten (LinkedIn + Telegram)", "chat": "Content", "ritme": "Laatste zaterdag", "dagen": "laatste_zaterdag", "kort": "Content klaarzetten", "agenda": "LinkedIn-content volgende maand klaarzetten"},
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
# Dagen waarop Instagram post (ma-vr sinds 24-11). Andere dagen: grijs "geen post", niet aan te passen.
INSTAGRAM_POSTDAGEN = {0, 1, 2, 3, 4}

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
    ("Administratie", "/administratie"),
]

# Eenmalige herinneringen die bij de allereerste start worden ingeladen (daarna via "Taak toevoegen").
STARTHERINNERINGEN = [
    {"titel": "Reviewlink naar MHL en FTUK sturen", "chat": "Algemeen", "datum": "2026-11-14"},
    {"titel": "Bing checken: staat Insightance erop?", "chat": "Algemeen", "datum": "2026-11-24"},
    {"titel": "Vervolgafspraak fysiotherapeut", "chat": "Algemeen", "datum": "2026-11-18"},
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
    "Je kunt niet verliezen als je niet opgeeft.",
]

# Vaste taken die ook in de tegel Binnenkort komen (naast de eenmalige herinneringen).
BINNENKORT_VAST = ["ga4", "linkedin_check", "content_maand", "instagram_klaarzetten"]
