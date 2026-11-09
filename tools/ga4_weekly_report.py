"""
Website — Wekelijkse GA4-samenvatting insightance.ai

Haalt de cijfers van de afgelopen 7 volledige dagen op uit Google Analytics 4
en zet ze naast de 7 dagen daarvoor: bezoekers, bronnen (Instagram, e-mail,
LinkedIn, Google), UTM-campagnes uit de outreach, populairste pagina's met
leestijd, en de acties die docs/consent.js meet. Claude maakt daar daarna een
korte samenvatting in gewone taal van (zie workflows/ga4_weekly_report.md).

Gebruik (CLI):
    python tools/ga4_weekly_report.py                    # 7 dagen t/m gisteren
    python tools/ga4_weekly_report.py --end 2026-11-15   # 7 dagen t/m die datum
    python tools/ga4_weekly_report.py --json             # ruwe data als JSON

Toegang: service account uit GOOGLE_SERVICE_ACCOUNT_JSON heeft rol Kijker op
property GA4_PROPERTY_ID (beide in .env). Gebruikt de GA4 Data API (REST),
geen extra pakketten nodig naast google-auth.

Bots: bezoeken uit bekende datacentersteden (Meta, Amazon, Google) worden
uitgefilterd en apart geteld. Zie BOT_CITIES. Sinds 03-11 laadt consent.js
GA ook niet meer voor herkenbare bots, dus dit is een tweede vangnet.
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))

from config import get_env, get_google_credentials_path  # noqa: E402
from google.oauth2 import service_account  # noqa: E402
from google.auth.transport.requests import AuthorizedSession  # noqa: E402

API = "https://analyticsdata.googleapis.com/v1beta"
OUT_DIR = WORKSPACE_ROOT / ".tmp" / "ga4"

# datacentersteden waar link-checkers en crawlers vandaan komen (03-11: Meta-bots na IG-bio-wijziging)
BOT_CITIES = [
    "Ashburn", "Boardman", "Prineville", "Luleå", "Lulea", "Council Bluffs",
    "The Dalles", "Clonee", "Odense", "Forest City", "Altoona", "Papillion",
    "Los Lunas", "New Albany", "Fort Worth", "Henrico", "Eemshaven", "Middenmeer",
    "Springfield",  # 09-11: Meta-linkcheckers na bio-wijzigingen geolokaliseren hier (0s, geen engagement)
]

# acties uit docs/consent.js, met leesbare naam
EVENTS = {
    "gesprek_ingepland": "Gesprek ingepland",
    "contactformulier_verstuurd": "Contactformulier verstuurd",
    "whatsapp_klik": "WhatsApp-klik",
    "email_klik": "E-mailklik",
    "agenda_geopend": "Agenda geopend",
    "contact_knop_klik": "Contactknop geklikt",
    "rekentool_gebruikt": "Rekentool gebruikt",
    "offertetool_demo_gebruikt": "Offertetool-demo gebruikt",
}

NOT_A_CAMPAIGN = {"(not set)", "(direct)", "(organic)", "(referral)", "(none)", ""}


def session():
    creds_path = get_google_credentials_path()
    if not creds_path:
        sys.exit("GOOGLE_SERVICE_ACCOUNT_JSON ontbreekt of bestand niet gevonden (.env)")
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=["https://www.googleapis.com/auth/analytics.readonly"])
    return AuthorizedSession(creds)


def city_filter(exclude=True):
    f = {"filter": {"fieldName": "city", "inListFilter": {"values": BOT_CITIES}}}
    return {"notExpression": f} if exclude else f


def report(s, prop, start, end, dims, metrics, extra_filter=None, bots=False, limit=50, order=None):
    """Eén runReport-aanroep; geeft lijst dicts terug {dim..., metric...}."""
    flt = city_filter(exclude=not bots)
    if extra_filter:
        flt = {"andGroup": {"expressions": [flt, extra_filter]}}
    body = {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "dimensions": [{"name": d} for d in dims],
        "metrics": [{"name": m} for m in metrics],
        "dimensionFilter": flt,
        "limit": limit,
    }
    if order:
        body["orderBys"] = [{"metric": {"metricName": order}, "desc": True}]
    r = s.post(f"{API}/properties/{prop}:runReport", json=body)
    j = r.json()
    if "error" in j:
        sys.exit(f"GA4 API-fout: {j['error'].get('message')}")
    rows = []
    for row in j.get("rows", []):
        d = {k: v["value"] for k, v in zip(dims, row.get("dimensionValues", []))}
        d.update({k: float(v["value"]) for k, v in zip(metrics, row["metricValues"])})
        rows.append(d)
    return rows


def collect(s, prop, end):
    start = end - timedelta(days=6)
    pstart, pend = start - timedelta(days=7), start - timedelta(days=1)
    tot_m = ["activeUsers", "newUsers", "sessions", "engagedSessions", "screenPageViews", "userEngagementDuration"]

    def totals(a, b):
        rows = report(s, prop, a, b, [], tot_m)
        return rows[0] if rows else {m: 0.0 for m in tot_m}

    def by(dims, metrics, a, b, **kw):
        return report(s, prop, a, b, dims, metrics, order=metrics[0], **kw)

    ev_filter = {"filter": {"fieldName": "eventName", "inListFilter": {"values": list(EVENTS)}}}
    data = {
        "periode": {"start": start.isoformat(), "end": end.isoformat()},
        "vorige_periode": {"start": pstart.isoformat(), "end": pend.isoformat()},
        "totaal": totals(start, end),
        "totaal_vorige": totals(pstart, pend),
        "bronnen": by(["sessionSource", "sessionMedium"], ["sessions", "engagedSessions"], start, end),
        "bronnen_vorige": by(["sessionSource", "sessionMedium"], ["sessions", "engagedSessions"], pstart, pend),
        "campagnes": [r for r in by(["sessionCampaignName", "sessionSource", "sessionMedium", "landingPage"],
                                    ["sessions", "engagedSessions"], start, end)
                      if r["sessionCampaignName"] not in NOT_A_CAMPAIGN],
        "paginas": by(["pagePath"], ["screenPageViews", "activeUsers", "userEngagementDuration"], start, end, limit=15),
        "acties": by(["eventName", "sessionSource"], ["eventCount"], start, end, extra_filter=ev_filter),
        "acties_vorige": by(["eventName"], ["eventCount"], pstart, pend, extra_filter=ev_filter),
        "landen": by(["country"], ["activeUsers"], start, end, limit=8),
        "bots": by(["city"], ["sessions"], start, end, bots=True),
    }
    return data


def delta(now, prev):
    if prev == 0:
        return "nieuw" if now else "="
    pct = round((now - prev) / prev * 100)
    return f"{'+' if pct >= 0 else ''}{pct}%"


def mmss(sec):
    sec = int(round(sec))
    return f"{sec // 60}:{sec % 60:02d}"


def to_markdown(d):
    t, p = d["totaal"], d["totaal_vorige"]
    L = [f"# Weekrapport insightance.ai  {d['periode']['start']} t/m {d['periode']['end']}",
         f"_Vergeleken met {d['vorige_periode']['start']} t/m {d['vorige_periode']['end']}. "
         "Alleen bezoekers die 'Akkoord' klikten; bots uitgefilterd._", "",
         "## Totaal", "| | Deze week | Vorige week | Verschil |", "|---|---|---|---|"]
    for key, label in [("activeUsers", "Bezoekers"), ("newUsers", "Nieuwe bezoekers"), ("sessions", "Bezoeken"),
                       ("engagedSessions", "Betrokken bezoeken (>10s of 2+ pagina's)"), ("screenPageViews", "Paginaweergaven")]:
        L.append(f"| {label} | {int(t[key])} | {int(p[key])} | {delta(t[key], p[key])} |")
    avg_now = t["userEngagementDuration"] / t["activeUsers"] if t["activeUsers"] else 0
    avg_prev = p["userEngagementDuration"] / p["activeUsers"] if p["activeUsers"] else 0
    L.append(f"| Gem. actieve tijd per bezoeker (m:ss) | {mmss(avg_now)} | {mmss(avg_prev)} | {delta(avg_now, avg_prev)} |")

    prev_src = {(r["sessionSource"], r["sessionMedium"]): r["sessions"] for r in d["bronnen_vorige"]}
    L += ["", "## Bronnen (waar komen ze vandaan)", "| Bron / medium | Bezoeken | Betrokken | Vorige week |", "|---|---|---|---|"]
    for r in d["bronnen"]:
        L.append(f"| {r['sessionSource']} / {r['sessionMedium']} | {int(r['sessions'])} | {int(r['engagedSessions'])} | "
                 f"{int(prev_src.get((r['sessionSource'], r['sessionMedium']), 0))} |")
    if not d["bronnen"]:
        L.append("| (geen bezoeken) | | | |")

    L += ["", "## Outreach- en profiellinks (UTM)", "| Campagne | Bron / medium | Landingspagina | Bezoeken | Betrokken |", "|---|---|---|---|---|"]
    for r in d["campagnes"]:
        L.append(f"| {r['sessionCampaignName']} | {r['sessionSource']} / {r['sessionMedium']} | {r['landingPage']} | "
                 f"{int(r['sessions'])} | {int(r['engagedSessions'])} |")
    if not d["campagnes"]:
        L.append("| (geen bezoeken via UTM-links) | | | | |")

    L += ["", "## Populairste pagina's", "| Pagina | Weergaven | Bezoekers | Gem. actieve tijd (m:ss) |", "|---|---|---|---|"]
    for r in d["paginas"]:
        avg = r["userEngagementDuration"] / r["activeUsers"] if r["activeUsers"] else 0
        L.append(f"| {r['pagePath']} | {int(r['screenPageViews'])} | {int(r['activeUsers'])} | {mmss(avg)} |")

    acts, prev_acts = {}, {r["eventName"]: r["eventCount"] for r in d["acties_vorige"]}
    for r in d["acties"]:
        a = acts.setdefault(r["eventName"], {"n": 0, "src": []})
        a["n"] += r["eventCount"]
        a["src"].append(f"{r['sessionSource']} ({int(r['eventCount'])})")
    L += ["", "## Acties", "| Actie | Deze week | Vorige week | Via |", "|---|---|---|---|"]
    for name, label in EVENTS.items():
        if name in acts or prev_acts.get(name):
            a = acts.get(name, {"n": 0, "src": []})
            L.append(f"| {label} | {int(a['n'])} | {int(prev_acts.get(name, 0))} | {', '.join(a['src'])} |")
    if not acts and not prev_acts:
        L.append("| (geen acties) | | | |")

    L += ["", "## Landen", ", ".join(f"{r['country']} ({int(r['activeUsers'])})" for r in d["landen"]) or "(geen)"]
    bots = int(sum(r["sessions"] for r in d["bots"]))
    L += ["", f"_Weggefilterd als bot (datacentersteden): {bots} bezoeken"
          + (f" uit {', '.join(r['city'] for r in d['bots'])}" if bots else "") + "._"]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Wekelijkse GA4-samenvatting insightance.ai")
    ap.add_argument("--end", help="laatste dag van de week (YYYY-MM-DD), standaard gisteren")
    ap.add_argument("--json", action="store_true", help="ruwe data als JSON printen")
    args = ap.parse_args()

    prop = get_env("GA4_PROPERTY_ID")
    if not prop:
        sys.exit("GA4_PROPERTY_ID ontbreekt in .env")
    end = date.fromisoformat(args.end) if args.end else date.today() - timedelta(days=1)

    data = collect(session(), prop, end)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = to_markdown(data)
    (OUT_DIR / f"weekrapport_{end.isoformat()}.md").write_text(md, encoding="utf-8")
    (OUT_DIR / f"weekrapport_{end.isoformat()}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(data, indent=2, ensure_ascii=False) if args.json else md)


if __name__ == "__main__":
    main()
