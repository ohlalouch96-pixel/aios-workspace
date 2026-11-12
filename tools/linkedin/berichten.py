"""
LinkedIn Outreach — Berichtsjablonen per niche

Pure templating, geen Claude-aanroep en geen Sheet-schrijfactie hier. Zie
workflows/linkedin_outreach.md voor de regels achter deze teksten (geen
gedachtestreepjes, "Dag [voornaam]," vast, enters zonder lege regel ertussen).
Wordt gebruikt door zowel handmatige toevoegingen als tools/linkedin/vind_prospects.py.
"""


def installatiebedrijven(voornaam, bedrijf):
    b1 = f"""Dag {voornaam},
Bedankt voor het accepteren! Ik volg wat installatiebedrijven in de regio bezighoudt.
Hoe loopt het bij {bedrijf} op dit moment, veel aanvragen binnen of relatief rustig?"""
    b2 = f"""Dag {voornaam},
Ik help installatiebedrijven met het automatiseren van tijdrovende klusjes, zoals het opstellen van offertes, calculaties maken of de facturatie bijhouden. Ik vroeg me af hoe dit bij {bedrijf} gaat.
Zou je het interessant vinden om vrijblijvend te kijken wat er mogelijk is voor {bedrijf}?
Hier alvast een voorbeeld van zo'n offertetool: insightance.ai/offerte
Ik hoor graag van je."""
    b3 = f"""Dag {voornaam},
Ik laat het hierbij, geen verdere berichten van mijn kant. Mocht het ooit relevant worden, dan weet je me te vinden.
Succes met {bedrijf}!"""
    return b1, b2, b3


def makelaars(voornaam, bedrijf):
    b1 = f"""Dag {voornaam},
Bedankt voor het accepteren! Ik volg wat er speelt bij makelaars en adviseurs in de regio rond opvolging van lopende aanvragen.
Hoe gaat dat bij {bedrijf}, blijft een aanvraag of advies weleens even liggen voordat er opvolging is?"""
    b2 = f"""Dag {voornaam},
Ik help makelaars en adviseurs met het uit handen nemen van tijdrovende taken, zoals het bijhouden en herinneren van openstaande aanvragen of de opvolging na een eerste contact. Ik vroeg me af hoe dit bij {bedrijf} gaat, en of dit wel eens wordt vergeten.
Zou je het interessant vinden om vrijblijvend te kijken wat er mogelijk is voor {bedrijf}?
Ik hoor graag van je."""
    b3 = f"""Dag {voornaam},
Ik laat het hierbij, geen verdere berichten van mijn kant. Mocht het ooit relevant worden, dan weet je me te vinden.
Succes met {bedrijf}!"""
    return b1, b2, b3


PER_NICHE = {"installatiebedrijven": installatiebedrijven, "makelaars": makelaars}
