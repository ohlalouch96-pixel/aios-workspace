"""
Instagram-contentagent (@insightance.ai) — het brein

Kiest wat er gemaakt wordt, laat Claude de tekst schrijven volgens
workflows/instagram_content.md, controleert de uitkomst, roept de renderers
in tools/instagram/ aan, legt het concept vast in de wachtrij en stuurt het
via de content-bot naar Oussama. Verwerkt ook ✏️-feedback tot een nieuwe versie.
Plaatst nooit zelf iets op Instagram (fase 1).

Kosten: elke Claude-aanroep wordt berekend (tokens × prijs + webzoekopdrachten)
en opgeslagen in instagram_kosten. Melding in Telegram bij $15, stop bij $20 per maand.
Video met stem (stem_video): onderwerp = volgende dienst van de website (tools/instagram/diensten.py),
alleen als er genoeg ElevenLabs-tegoed is; anders wordt een ander soort post gekozen.

Gebruik (CLI):
    python apps/content/agent.py maak [--soort carrousel|kaart|tekst_reel|demo_reel|stem_video|actualiteit|story]
    python apps/content/agent.py maak --soort stem_video --zonder-stem   # gratis proef: script + beeld, geen Eric, niet naar Telegram
    python apps/content/agent.py verwerk          # openstaande ✏️-feedback verwerken
    python apps/content/agent.py dagelijks        # buffer aanvullen (max 2 nieuwe concepten per keer)
    python apps/content/agent.py kosten           # uitgaven deze maand
"""

import argparse
import html
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

import anthropic

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS = WORKSPACE_ROOT / "tools" / "instagram"
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
sys.path.insert(0, str(TOOLS))
from config import get_env  # noqa: E402,F401  (laadt .env)
import wachtrij  # noqa: E402
import telegram_review  # noqa: E402
import diensten  # noqa: E402
import stem  # noqa: E402
import hookscore  # noqa: E402  (MIT, uit instagram-agent-skill; scoort de eerste regel)

MODEL = "claude-opus-5-5"
EFFORT = "medium"
# $ per 1M tokens: invoer, uitvoer, cache lezen, cache schrijven (5 min); webzoeken $10 per 1.000
PRIJZEN = {"claude-opus-5-5": (4.0, 20.0, 0.20, 5.0), "claude-opus-5": (5.0, 25.0, 0.50, 6.25), "claude-opus-4-8": (5.0, 25.0, 0.50, 6.25),
           "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5)}
PRIJS_ZOEKEN = 0.01
LIMIET, WAARSCHUWING = 20.0, 15.0
CONCEPTEN = WORKSPACE_ROOT / ".tmp" / "instagram" / "concepten"
VERBODEN = ["mhl", "ftuk", "millenaar", "peijnenburg", "installatieservice"]  # nooit klantnamen
DEMOS = ["offerte", "dashboard", "calculatie", "factuur", "whatsapp", "klantenservice", "rekentool"]
SCENES = ["bureau", "kantoor", "ipad", "scherm", "krant", "whiteboard", "servet"]
DIAGRAMMEN = ["venn", "fork", "lijst", "voor_na", "stappen", "grafiek", "loop"]
# mix per week (±5 posts): ongeveer half informatie, half bewijs
MIX = {"carrousel": 0.30, "demo_reel": 0.18, "stem_video": 0.14, "tekst_reel": 0.10, "kaart": 0.12, "actualiteit": 0.09, "story": 0.07}
STEM_MIN_TEGOED = 700  # ElevenLabs-tekens nodig voor een video met stem (één opname ±450 + marge)
STEM_SCENES = ["hook", "telefoon", "chat", "agenda", "inbox", "document", "dashboard", "checklist", "notificaties", "eind"]
STEM_TAGS = {"[confident]", "[curious]", "[warm]", "[excited]", "[long pause]"}  # [understated]/[softly] laten Eric wegzakken
STEM_MUZIEK = ("Uptempo en vrolijk (±110-120 BPM), zonder zang, zacht onder de stem: muziek ±15%, origineel geluid 100%. "
               "Zoekterm: 'upbeat corporate', 'positive tech' of 'happy commercial'.")

client = anthropic.Anthropic()


# ---------- kosten ----------
def kosten_tabel(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS instagram_kosten (
        id INTEGER PRIMARY KEY, maand TEXT, post_id INTEGER, stap TEXT, model TEXT,
        invoer INTEGER, uitvoer INTEGER, cache_lees INTEGER, cache_schrijf INTEGER, zoekopdrachten INTEGER, usd REAL,
        gemaakt_op TEXT DEFAULT (datetime('now')))""")
    conn.execute("CREATE TABLE IF NOT EXISTS instagram_meldingen (maand TEXT, soort TEXT, PRIMARY KEY (maand, soort))")


def maand():
    return date.today().strftime("%Y-%m")


def uitgegeven(conn):
    return conn.execute("SELECT COALESCE(SUM(usd), 0) FROM instagram_kosten WHERE maand = ?", (maand(),)).fetchone()[0]


def melding_eenmalig(conn, soort, tekst):
    if conn.execute("SELECT 1 FROM instagram_meldingen WHERE maand = ? AND soort = ?", (maand(), soort)).fetchone():
        return
    conn.execute("INSERT INTO instagram_meldingen VALUES (?, ?)", (maand(), soort))
    conn.commit()
    telegram_review.Bot().tekst(tekst)


def budget_check(conn):
    besteed = uitgegeven(conn)
    if besteed >= LIMIET:
        melding_eenmalig(conn, "stop", f"⛔ Maandlimiet bereikt: ${besteed:.2f} van ${LIMIET:.0f}. De agent maakt deze maand geen nieuwe concepten meer. Wil je de limiet verhogen? Zeg het in de chat met Claude.")
        sys.exit("Maandlimiet bereikt")
    if besteed >= WAARSCHUWING:
        melding_eenmalig(conn, "waarschuwing", f"⚠️ Instagram-agent: ${besteed:.2f} van ${LIMIET:.0f} uitgegeven deze maand.")


def boek(conn, post_id, stap, resp):
    u = resp.usage
    p = PRIJZEN.get(resp.model, PRIJZEN[MODEL])
    lees, schrijf = getattr(u, "cache_read_input_tokens", 0) or 0, getattr(u, "cache_creation_input_tokens", 0) or 0
    zoek = getattr(getattr(u, "server_tool_use", None), "web_search_requests", 0) or 0
    usd = (u.input_tokens * p[0] + u.output_tokens * p[1] + lees * p[2] + schrijf * p[3]) / 1e6 + zoek * PRIJS_ZOEKEN
    conn.execute("INSERT INTO instagram_kosten (maand, post_id, stap, model, invoer, uitvoer, cache_lees, cache_schrijf, zoekopdrachten, usd) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (maand(), post_id, stap, resp.model, u.input_tokens, u.output_tokens, lees, schrijf, zoek, usd))
    conn.commit()
    print(f"  [{stap}] ${usd:.3f} ({u.input_tokens} in, {u.output_tokens} uit, {zoek} zoekopdrachten)")
    return usd


# ---------- Claude ----------
def systeem():
    regels = (WORKSPACE_ROOT / "workflows" / "instagram_content.md").read_text(encoding="utf-8")
    return [{"type": "text", "cache_control": {"type": "ephemeral"}, "text": (
        "You write Instagram content for @insightance.ai, the page of Oussama, an ER nurse who builds AI automation systems for business owners. "
        "Everything you write for the post is in natural, idiomatic English. Follow the content rules below exactly (they are written in Dutch). "
        "Never invent statistics or facts: use only facts that appear in the source text you are given or in verified research you are given. "
        "Never mention real client names. Never use em dashes. Avoid AI-sounding phrasing (simply, seamless, leverage, robust, 'Not X. Not Y.', 'That's it.').\n\n"
        "=== CONTENT RULES ===\n" + regels)}]


def vraag(conn, post_id, stap, prompt, schema=None, zoeken=False, max_tokens=16000):
    """Eén Claude-aanroep; met schema: gegarandeerde JSON; met zoeken: webzoeken en pagina's lezen."""
    budget_check(conn)
    kwargs = dict(model=MODEL, max_tokens=max_tokens, system=systeem(), output_config={"effort": EFFORT},
                  messages=[{"role": "user", "content": prompt}], betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    if schema:
        kwargs["output_config"]["format"] = {"type": "json_schema", "schema": schema}
    if zoeken:
        kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 10},
                           {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 6}]
    resp = client.beta.messages.create(**kwargs)
    boek(conn, post_id, stap, resp)
    while resp.stop_reason == "pause_turn":  # server-zoekronde nog niet klaar: hervatten
        kwargs["messages"] = kwargs["messages"] + [{"role": "assistant", "content": resp.content}]
        resp = client.beta.messages.create(**kwargs)
        boek(conn, post_id, stap, resp)
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Claude weigerde ({stap})")
    tekst = "".join(b.text for b in resp.content if b.type == "text")
    return json.loads(tekst) if schema else tekst


# ---------- schema's ----------
def obj(props, req=None):
    return {"type": "object", "properties": props, "required": req or list(props), "additionalProperties": False}


S, A = {"type": "string"}, lambda item: {"type": "array", "items": item}
BASIS = {"caption": S, "hashtags": A(S), "muziek": S, "onderwerp": S}
SLIDE = obj({"type": {"type": "string", "enum": ["cover", "citaat", "tekst", "cijfer", "slot"]}, "titel": S, "sub": S, "label": S, "tekst": S, "cijfer": S, "bron": S, "knop": S})
SCHEMA = {
    "carrousel": obj({**BASIS, "serie": S, "slides": A(SLIDE)}),
    "tekst_reel": obj({**BASIS, "serie": S, "beats": A(obj({"label": S, "tekst": S, "duur": {"type": "number"}}))}),
    "kaart": obj({**BASIS, "diagram": {"type": "string", "enum": DIAGRAMMEN}, "titel": S, "links": S, "rechts": S, "midden": S,
                  "keuze_a": S, "uitkomst_a": A(S), "keuze_b": S, "uitkomst_b": S, "items": A(obj({"tekst": S, "ok": {"type": "boolean"}})),
                  "links_kop": S, "links_lijst": A(S), "rechts_kop": S, "rechts_lijst": A(S), "stappen": A(S), "lijn": S, "notitie": S, "x": S, "y": S}),
    "demo_reel": obj(BASIS),
    "stem_video": obj({**BASIS, "beats": A(obj({"zegt": S, "uitspraak": S, "scene": obj({
        "type": {"type": "string", "enum": STEM_SCENES}, "kop": S, "groot": S, "tekst": S, "bedrijf": S, "kanaal": S,
        "items": A(obj({"a": S, "b": S, "c": S, "d": S, "nieuw": {"type": "boolean"}})), "op": A(S), "resultaat": S,
        "getallen": A({"type": "number"}), "knop": S, "handle": S})}))}),
    "story": obj({"onderwerp": S, "tekst": S, "foto_idee": S}),
}
CONTROLE = obj({"bevestigd": {"type": "boolean"}, "kern": S, "bron_1": S, "bron_2": S, "datum": S, "toelichting": S})


# ---------- keuzes ----------
def vorige(conn, n=6):
    return [dict(zip(["soort", "kleurenset", "hashtags"], r)) for r in
            conn.execute("SELECT soort, kleurenset, hashtags FROM instagram_posts WHERE status != 'overgeslagen' ORDER BY id DESC LIMIT ?", (n,))]


def stem_tegoed():
    """Resterende ElevenLabs-tekens deze maand (0 als de stand niet op te vragen is)."""
    try:
        _, gebruikt, limiet = stem.tegoed()
        return limiet - gebruikt
    except Exception:
        return 0


REEL_SOORTEN = {"tekst_reel", "demo_reel", "stem_video"}
VOORRAAD = 10  # sinds 24-11 twee posts per werkdag (5 x 2), was 5


def kies_soort(conn):
    """Soort volgens MIX, maar de voorraad blijft half reels, half beeldposts (24-11: per dag één reel en één beeldpost)."""
    laatste = [v["soort"] for v in vorige(conn, 2)]
    opties = {s: w for s, w in MIX.items() if not laatste or s != laatste[0]}
    voorraad = [r[0] for r in conn.execute("SELECT soort FROM instagram_posts WHERE status IN ('concept', 'goedgekeurd') AND soort NOT IN ('advertentie', 'story')")]
    reels = sum(s in REEL_SOORTEN for s in voorraad)
    if reels != len(voorraad) - reels:  # het soort dat achterloopt krijgt voorrang
        meer_reels = reels < len(voorraad) - reels
        opties = {s: w for s, w in opties.items() if (s in REEL_SOORTEN) == meer_reels} or opties
    if "stem_video" in opties and stem_tegoed() < STEM_MIN_TEGOED:
        del opties["stem_video"]  # te weinig tegoed: dan een ander soort post
    return random.choices(list(opties), weights=list(opties.values()))[0]


def hashtag_eisen(conn):
    recent = wachtrij.recente_hashtags(conn, 1)
    vorige_tags = recent[0] if recent else []
    aantal = random.choice([n for n in range(3, 6) if n != len(vorige_tags)])  # Instagram: max 5 hashtags (sinds dec 2025)
    return aantal, vorige_tags


def taalregels(aantal, verboden_tags):
    return (f"Hashtags: exactly {aantal}, relevant to this specific post, varied (not a fixed set). Do NOT use any of these from the previous post: "
            f"{', '.join(verboden_tags) or 'none'}. Caption: first sentence must stop the scroll (allowed to challenge, never untrue); then at most two short paragraphs (together max ~35 words; as short as possible, Oussama wants no walls of text) "
            "and one closing question or nudge. Keep it compact, no wall of text. Every sentence must follow logically from the one before: never refer to 'they', 'them' or a group that was not clearly introduced first. This also applies to slides and reel beats, read in order. Do NOT write the fixed sign-off line or the hashtags inside the caption; they are added automatically. "
            "Music: one short line with the type and mood of background music that fits this content and colour, e.g. 'calm lo-fi beat, search: lofi chill'; empty string for images.")


# ---------- controle ----------
def controleer(spec, aantal, verboden_tags):
    tekst = json.dumps(spec, ensure_ascii=False).lower()
    fouten = [f"contains forbidden client name '{w}'" for w in VERBODEN if w in tekst]
    if "—" in tekst:
        fouten.append("contains an em dash (—); rewrite without it")
    tags = spec.get("hashtags")
    if tags is not None:
        if len(tags) != aantal:
            fouten.append(f"must have exactly {aantal} hashtags, has {len(tags)}")
        dubbel = {t.lower() for t in tags} & {t.lower() for t in verboden_tags}
        if dubbel:
            fouten.append(f"reuses hashtags from the previous post: {', '.join(dubbel)}")
    return fouten


def woorden(tekst):
    return [w for w in re.sub(r"[^a-z0-9' ]", " ", tekst.lower().replace("’", "'")).split() if w]


def controleer_stem(spec):
    """De regels voor een video met stem die vóór de opname te controleren zijn (opname kost tegoed)."""
    fouten, beats = [], spec.get("beats", [])
    if not 5 <= len(beats) <= 7:
        fouten.append(f"needs 5 to 7 beats, has {len(beats)}")
    if beats and beats[-1]["scene"]["type"] != "eind":
        fouten.append("the last beat must be scene type 'eind'")
    if beats and beats[0]["scene"]["type"] == "eind":
        fouten.append("the first beat must be the hook, not 'eind'")
    totaal = sum(len(woorden(b["zegt"])) for b in beats)
    if not 35 <= totaal <= 70:
        fouten.append(f"the spoken script must be 35 to 70 words in total, is {totaal}")
    for n, b in enumerate(beats, 1):
        zegt, sc = woorden(b["zegt"]), b["scene"]
        if len(zegt) > 15:
            fouten.append(f"beat {n}: max 15 spoken words, has {len(zegt)}")
        tags = set(re.findall(r"\[[^\]]+\]", b["uitspraak"]))
        if tags - STEM_TAGS:
            fouten.append(f"beat {n}: only these tags are allowed: {', '.join(sorted(STEM_TAGS))}; remove {', '.join(sorted(tags - STEM_TAGS))}")
        if woorden(re.sub(r"\[[^\]]+\]", " ", b["uitspraak"])) != zegt:
            fouten.append(f"beat {n}: 'uitspraak' must be exactly 'zegt' plus tags, same words")
        if re.search(r"\b(at night|in the (morning|evening|afternoon)|o'clock)\b", b["zegt"].lower()) and re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b", b["zegt"].lower()):
            fouten.append(f"beat {n}: say times the way people say them, e.g. 'It's 9 PM', never 'nine at night'")
        kop = woorden(sc["kop"].replace("*", ""))
        it = iter(woorden(b["zegt"].lower().replace("wanna", "want to")))  # in beeld netjes 'Want to', Eric zegt 'wanna' (22-11)
        if kop and not all(w in it for w in kop):
            fouten.append(f"beat {n}: every word of 'kop' must also be spoken in 'zegt', in the same order (on screen = what Eric says)")
        for w in sc["op"]:
            if w and woorden(w)[:1] and woorden(w)[0] not in zegt:
                fouten.append(f"beat {n}: 'op' word '{w}' is not spoken in this beat")
        if sc["type"] in ("telefoon", "chat") and any(i["a"] not in ("klant", "ai") for i in sc["items"]):
            fouten.append(f"beat {n}: for {sc['type']} every item 'a' must be 'klant' or 'ai'")
        if sc["type"] == "agenda" and any(i["a"] not in ("Mon", "Tue", "Wed", "Thu", "Fri") or not re.fullmatch(r"\d\d:\d\d", i["b"]) or not re.fullmatch(r"\d\d:\d\d", i["c"]) for i in sc["items"]):
            fouten.append(f"beat {n}: agenda items need a=Mon..Fri, b and c as HH:MM between 08:00 and 16:00")
        grens = {"telefoon": 3, "chat": 4, "inbox": 4, "document": 4, "dashboard": 2, "checklist": 4, "notificaties": 3, "agenda": 6}.get(sc["type"])
        if grens and len(sc["items"]) > grens:
            fouten.append(f"beat {n}: scene {sc['type']} takes at most {grens} items")
    return fouten


def schrijf(conn, soort, prompt, aantal, verboden_tags, post_id=None, hook=None):
    def check(spec):
        return (controleer(spec, aantal, verboden_tags) + (controleer_stem(spec) if soort == "stem_video" else [])
                + (controleer_hook(spec, hook, soort) if hook else []))
    spec = vraag(conn, post_id, f"schrijven:{soort}", prompt, SCHEMA[soort])
    fouten = check(spec)
    if fouten:  # één herkansing met de concrete fouten erbij
        spec = vraag(conn, post_id, f"herschrijven:{soort}", prompt + "\n\nYour previous attempt had these problems, fix them:\n- " + "\n- ".join(fouten)
                     + "\n\nPrevious attempt:\n" + json.dumps(spec, ensure_ascii=False), SCHEMA[soort])
        fouten = check(spec)
    if hook:
        spec["hook"] = hook
        if fouten:
            raise RuntimeError("Concept haalt de controle niet: " + "; ".join(fouten))
    return spec


# ---------- hook (besluit 21-11: 3 opties uit vaste formules, scoren, de sterkste wint) ----------
# Formules uit tools/instagram/hooks.json die bij "without the hype" passen en geen eigen cijfers/klanten vereisen.
HOOK_FORMULES = {2, 3, 5, 7, 9, 10, 11, 12, 13, 14, 16, 17, 18, 20, 22, 23, 24}
HOOK_MIN = 60
HOOKSTAP_AAN = True  # aan sinds 22-11 (Oussama), voor alle soorten posts
HOOK = obj({"opties": A(obj({"formule": S, "lijn": S, "scherm": S}))})
# waar de hook in beeld komt, per soort (22-11: carrousel-cover in HOOFDLETTERS, reels/schetsen gewone zinsopbouw)
HOOK_PLEK = {
    "carrousel": "the cover slide title (it is shown in CAPITALS)",
    "actualiteit": "the cover slide title (it is shown in CAPITALS)",
    "tekst_reel": "the first text on screen, visible from frame 1",
    "demo_reel": "the big text above the screen recording, visible from frame 1",
    "stem_video": "the on-screen headline of the first beat: use ONLY words from 'lijn', in the same order (the voice says 'lijn')",
    "kaart": "the title of the hand-drawn sketch",
}


def formules_tekst():
    d = json.loads((TOOLS / "hooks.json").read_text(encoding="utf-8"))
    regels = "\n".join(f"- {r}" for r in d["rules"])
    lijst = "\n".join(f"- {h['name']}: {h['template']} | e.g. \"{h['example']}\" (on screen: {h['on_screen']}) | trap: {h['trap']}"
                      for h in d["hooks"] if h["id"] in HOOK_FORMULES)
    return regels, lijst


def recente_formules(conn, n=3):
    uit = []
    for (m,) in conn.execute("SELECT map FROM instagram_posts WHERE map IS NOT NULL ORDER BY id DESC LIMIT ?", (n,)):
        try:
            uit.append(json.loads((Path(m) / "spec.json").read_text(encoding="utf-8"))["hook"]["formule"])
        except (OSError, ValueError, KeyError, TypeError):
            pass
    return uit


def score_hook(optie, bron, soort):
    """Deterministische score (hookscore.py) plus onze eigen eisen; None = optie valt af."""
    lijn, scherm = optie["lijn"].strip(), optie["scherm"].replace("*", "").strip()
    if "—" in lijn + scherm or not scherm or len(scherm.split()) > 6:
        return None
    if any(g not in bron for g in re.findall(r"\d[\d,.]*", lijn + " " + scherm)):  # geen verzonnen cijfers
        return None
    if soort == "stem_video":  # in beeld alleen woorden die Eric zegt, in dezelfde volgorde
        it = iter(woorden(lijn))
        if not all(w in it for w in woorden(scherm)):
            return None
    res, totaal, oordeel, vlaggen = hookscore.run(lijn)
    zwakst = min(res, key=lambda c: res[c][0])
    return {**optie, "score": round(totaal), "oordeel": oordeel, "zwakst": f"{zwakst}: {res[zwakst][1]}", "vlaggen": vlaggen}


DUIDELIJK = obj({"oordelen": A(obj({"nr": {"type": "integer"}, "begrijpelijk": {"type": "boolean"}, "reden": S}))})


def duidelijk(conn, opties, soort):
    """Duidelijkheidscheck (22-11, na 'Dear customer is the robot'): de score meet vorm, niet of iemand het snapt.
    Een hook die een drukke ondernemer zonder context niet in één seconde begrijpt, valt af."""
    if not opties:
        return []
    lijst = "\n".join(f"{i}. on screen: \"{o['scherm'].replace('*', '')}\" | first caption line: \"{o['lijn']}\"" for i, o in enumerate(opties))
    oordeel = vraag(conn, None, f"hook-duidelijk:{soort}", (
        "You are a busy small-business owner scrolling Instagram. You know nothing about the post or its source. For each hook below, judge: "
        "do you understand within one second what it is about and why it matters to you, from the on-screen text ALONE (no caption, no context)? "
        "Cryptic, clever-but-unclear, inside references or wordplay you have to decode = not understandable. Be strict. "
        "Answer per number with begrijpelijk true/false and a short reason in Dutch.\n\n" + lijst), DUIDELIJK, max_tokens=2000)["oordelen"]
    nee = {o["nr"]: o["reden"] for o in oordeel if not o["begrijpelijk"]}
    for i, r in nee.items():
        if 0 <= i < len(opties):
            print(f"  Hook valt af (onduidelijk): {opties[i]['scherm']} ({r})")
    return [o for i, o in enumerate(opties) if i not in nee]


def kies_hook(conn, soort, bron):
    """3 opties uit verschillende formules, scoren, de sterkste wint (min. HOOK_MIN, anders één nieuwe ronde)."""
    regels, lijst = formules_tekst()
    vermijd = recente_formules(conn)
    prompt = (f"Write 3 hook options for an Instagram {soort.replace('_', ' ')} about the source below. Use 3 DIFFERENT formulas from the list"
              f"{' and not these recently used ones: ' + ', '.join(vermijd) if vermijd else ''}.\n"
              f"Per option: 'formule' = the formula name; 'lijn' = the first line of the caption"
              f"{' and the first sentence the voice says' if soort == 'stem_video' else ''}, 5 to 12 words, what makes someone stop scrolling; "
              f"'scherm' = {HOOK_PLEK.get(soort, 'the first text on screen')}, max 6 words, the blunter on-screen version, in sentence case, "
              "with *asterisks* around the one key word.\n"
              "Hard rules: true to the source, never hype or clickbait (the brand is 'AI automation without the hype'), no numbers unless they appear in the source, "
              "no greeting, no emoji, no hashtag, no em dash. Front-load the interesting word and speak to the viewer ('you') where it fits.\n"
              f"Hook rules:\n{regels}\n\nFormulas:\n{lijst}\n\n{bron}")
    beste, gezien = None, []
    for _ in range(2):
        opties = vraag(conn, None, f"hook:{soort}", prompt, HOOK, max_tokens=4000)["opties"]
        gescoord = duidelijk(conn, [s for s in (score_hook(o, bron, soort) for o in opties) if s], soort)
        gezien += gescoord
        beste = max(gezien, key=lambda s: s["score"], default=None)
        if beste and beste["score"] >= HOOK_MIN:
            break
        prompt += ("\n\nThese options scored too low or were unclear without context (weakest property in brackets), write 3 better, clearer ones:\n"
                   + "\n".join(f"- {s['score']} \"{s['lijn']}\" ({s['zwakst']})" for s in gescoord))
    if not beste:
        raise RuntimeError("Geen bruikbare hook gevonden")
    if soort in ("carrousel", "actualiteit"):
        beste["scherm"] = beste["scherm"].upper()  # A: carrousel-cover in hoofdletters (22-11)
    beste["alle"] = sorted(({"formule": s["formule"], "lijn": s["lijn"], "scherm": s["scherm"], "score": s["score"]} for s in gezien),
                           key=lambda s: -s["score"])
    print(f"Hook ({beste['formule']}, {beste['score']}): {beste['lijn']} | {beste['scherm']}")
    return beste


def hook_instructie(hook, soort):
    if not hook:
        return ""
    plek = {"carrousel": "the cover slide 'titel'", "actualiteit": "the cover slide 'titel'", "tekst_reel": "beat 1 'tekst'",
            "kaart": "'titel'", "stem_video": "beat 1 'scene.kop'"}.get(soort)
    eerst = f"{plek} = \"{hook['scherm']}\" (keep the *asterisks*); " if plek else ""
    if soort == "stem_video":
        eerst += f"beat 1 'zegt' starts with exactly this sentence: \"{hook['lijn']}\" (and 'uitspraak' the same words with tags); "
    return (f"\nHOOK (already chosen and tested, use it exactly): {eerst}"
            f"the caption starts with exactly this sentence: \"{hook['lijn']}\". Deliver what the hook promises before the halfway point.")


def controleer_hook(spec, hook, soort):
    def vlak(s):
        return re.sub(r"\s+", " ", (s or "").replace("*", "")).strip().lower()
    fouten = []
    eerste = {"carrousel": lambda: spec["slides"][0]["titel"], "actualiteit": lambda: spec["slides"][0]["titel"],
              "tekst_reel": lambda: spec["beats"][0]["tekst"], "kaart": lambda: spec["titel"],
              "stem_video": lambda: spec["beats"][0]["scene"]["kop"]}.get(soort)
    if eerste and vlak(eerste()) != vlak(hook["scherm"]):
        fouten.append(f"the first on-screen text must be exactly \"{hook['scherm']}\"")
    if soort == "stem_video" and not vlak(spec["beats"][0]["zegt"]).startswith(vlak(hook["lijn"])):
        fouten.append(f"beat 1 'zegt' must start with exactly \"{hook['lijn']}\"")
    if not vlak(spec.get("caption")).startswith(vlak(hook["lijn"])):
        fouten.append(f"the caption must start with exactly \"{hook['lijn']}\"")
    return fouten


# ---------- per soort ----------
def bron_tekst(rij):
    if rij[0] is None:  # een dienst van insightance.ai/automations in plaats van een LinkedIn-post
        return f"Source: one of the automations Oussama builds (insightance.ai/automations). Explain what it does and why it matters for a business owner; no claims or numbers you cannot back up:\n\"\"\"\n{rij[3]}\n\"\"\""
    return f"Source ({rij[1]}), already fact-checked LinkedIn post:\n\"\"\"\n{rij[3]}\n\"\"\""


def prompt_carrousel(rij, aantal, tags):
    serie = "MYTH CHECK" if rij[1] == "myth_check" else "AUTOMATION SIMPLIFIED"
    return (f"Turn this into an Instagram carousel (4 to 6 slides) for the series {serie}.\n{bron_tekst(rij)}\n\n"
            "Slides: first slide type 'cover' (or 'citaat' for a myth, with the myth as the title), then 'tekst' slides (label + short title + one or two short sentences), "
            "slide 2 says in one sentence why this matters to the viewer and must make sense on its own (Instagram re-shows carousels starting at slide 2), "
            "optionally one 'cijfer' slide ONLY if the source contains a real number (with its source in 'bron'), last slide type 'slot' with a closing line and a short 'knop' "
            "(a varied follow-style call to action ending with ⚡). Mark the key word in titles with *asterisks*. One thought per slide, short. Leave unused fields empty. "
            f"'serie' must be '{serie}'.\n{taalregels(aantal, tags)}")


def prompt_tekst_reel(rij, aantal, tags):
    serie = "MYTH CHECK" if rij[1] == "myth_check" else "AUTOMATION SIMPLIFIED"
    return (f"Turn this into a 12 to 16 second vertical text reel: 4 to 6 beats of 2.2 to 3.6 seconds each.\n{bron_tekst(rij)}\n\n"
            "Beat 1 is the hook (about 3 s). Each beat is max ~10 words; mark the key word with *asterisks*; 'label' is an optional small tag (e.g. 'Step 1'), empty if not needed. "
            "There is no voice-over: the text and the music carry the reel. "
            f"Last beat lands the point. 'serie' must be '{serie}'.\n{taalregels(aantal, tags)}")


def prompt_kaart(rij, diagram, aantal, tags):
    return (f"Turn this into ONE hand-drawn style sketch image, diagram type '{diagram}'.\n{bron_tekst(rij)}\n\n"
            "Fill only the fields this diagram uses, keep every label very short (max ~6 words), leave the rest empty:\n"
            "venn: titel, links, rechts, midden | fork: titel, keuze_a, uitkomst_a (2 items), keuze_b, uitkomst_b | lijst: titel, items (3-5, ok=false for the odd one out) | "
            "voor_na: titel, links_kop, links_lijst (3), rechts_kop, rechts_lijst (3) | stappen: titel, stappen (3-4) | grafiek: titel, lijn ('stijgend' or 'dalend'), notitie, x, y | "
            f"loop: titel, stappen (3), midden.\nThe Fork posts have a minimal caption (one short line) and no hashtags; otherwise normal caption.\n{taalregels(aantal, tags)}")


def prompt_demo(demo, aantal, tags):
    beschrijving = json.loads((TOOLS / "demos" / f"{demo}.json").read_text(encoding="utf-8"))
    return (f"Write the caption for a screen-recording reel that demos this (fictional business, real capability):\n{json.dumps(beschrijving, ensure_ascii=False)}\n\n"
            "This is proof content: show what is possible, concrete and recognisable for a business owner. Do not claim it is a real client. "
            f"'onderwerp' is a short Dutch description.\n{taalregels(aantal, tags)}")


def prompt_stem_video(dienst, aantal, tags):
    return (f"Write a 20 to 25 second vertical video with a voice-over (the voice is 'Eric', calm, confident, American) about this service Oussama builds:\n"
            f"SERVICE: {dienst['naam']}: {dienst['wat']}\n\n"
            "Goal: a business owner recognises their own problem and sees what is possible. Structure: beat 1 = a recognisable problem (hook), "
            "middle beats = what the AI does, step by step, shown in a realistic app screen, one beat = the result for the owner, last beat = scene 'eind'. "
            "5 to 7 beats, 35 to 70 spoken words in total, max ~12 words per beat. Use a fictional but realistic small business (US, dollars, generic names, "
            "e-mail domains on .example), never real brands or clients. No statistics or claims you cannot back up; describe what the system does.\n\n"
            "Per beat: 'zegt' = the exact spoken sentence(s). 'uitspraak' = the same words with delivery tags in front of sentences: use ONLY [confident], [curious], "
            "[warm], [excited] (never [understated] or [softly]: they make the voice drop). Say times like people do ('It's 9 PM', never 'nine at night'). "
            "'scene.kop' = the on-screen headline: ONLY words that Eric also says in this beat, in the same order, short (max ~8 words), mark 1 to 3 key words "
            "with *asterisks*. 'scene.op' = for each item, the spoken word (from this beat) at which it appears, in order.\n\n"
            "Scene types (fill only the fields listed, leave the rest empty, numbers as plain numbers):\n"
            "- hook (dark): kop, groot (optional big text like '3 missed calls' or '9:12 PM'), tekst (optional small chip, e.g. 'Voicemail full').\n"
            "- telefoon (dark, a live call handled by an AI receptionist): kop, bedrijf, items max 3 lines {a:'klant'|'ai', b:line}, resultaat (e.g. 'Booked: Thu 10:30 AM').\n"
            "- chat (light, a chat on a phone): kop, bedrijf, kanaal ('whatsapp' or 'web'), items max 4 {a:'klant'|'ai', b:message, c:time like '21:14'}.\n"
            "- agenda (light, week calendar): kop, bedrijf, items max 6 {a:'Mon'..'Fri', b:start 'HH:MM', c:end 'HH:MM' (08:00-16:00), d:short title, nieuw:true for the 2-3 that get booked automatically}.\n"
            "- inbox (light, emails get labelled): kop, bedrijf (an address on .example), items max 4 {a:sender, b:subject, c:label}, resultaat (e.g. '3 replies drafted').\n"
            "- document (light, a document is scanned and fields are extracted): kop, bedrijf (document title), tekst (small tag like 'SCANNED'), items max 4 {a:field, b:value}, resultaat.\n"
            "- dashboard (light): kop, items exactly 2 KPI tiles {a:LABEL, b:number as text, c:prefix like '$', d:suffix like '%'}, getallen (6-8 numbers for the line chart), resultaat (optional warning line).\n"
            "- checklist (light, tasks tick themselves off): kop, bedrijf, tekst (small tag), items max 4 {a:task}, resultaat.\n"
            "- notificaties (dark, phone notifications): kop, items max 3 {a:one symbol like ✓ $ ★, b:title, c:subtitle, d:time like '9:16'}.\n"
            "- eind (dark, last beat): kop exactly 'Want to *know more?*' (on screen in correct written English, Eric still says 'wanna'), knop 'Send me a DM ⚡', handle '@insightance.ai'. "
            "Spoken text for eind: exactly 'You wanna know more? Send me a DM.' (zegt) and '[warm] You wanna know more? Send me a DM.' (uitspraak)\n"
            "Every number on screen must add up and match what is said. 'onderwerp' is a short Dutch description including the service name.\n"
            f"{taalregels(aantal, tags)}")


def prompt_story(rij):
    return (f"Write an Instagram story text (The Other Shift: diary tone, light humour, no explanation, no AI word, no CTA) based on this:\n{bron_tekst(rij)}\n"
            "'tekst' max 2 short lines to put on a photo; 'foto_idee' is one short Dutch suggestion for what photo Oussama could take (without his face).")


def onderzoek_actualiteit(conn):
    """Eén ronde: nieuws zoeken, de originele bron lezen en de feiten daartegen controleren. Klopt het niet, dan geen concept."""
    gebruikt = [r[0] for r in conn.execute("SELECT onderwerp FROM instagram_posts WHERE soort = 'actualiteit' ORDER BY id DESC LIMIT 15")]
    return vraag(conn, None, "actualiteit:zoeken+check", (
        f"Today is {date.today().isoformat()}. Find ONE piece of AI or automation news from the last 10 days that matters to small and mid-sized business owners "
        "(not purely technical). Only use announcements from the company itself (official newsroom or blog), government bodies, research institutes, or established "
        "news outlets (e.g. Reuters, AP, The Verge, TechCrunch, Bloomberg). Skip blogs, SEO articles and summaries. "
        f"Avoid these topics already covered: {gebruikt or 'none'}. Open and read the source and check every fact (names, numbers, dates) against it. "
        "bevestigd=true only if you read the source yourself and the facts hold. 'kern': ONLY the checked facts, no examples or claims you could not check. "
        "bron_1 = the source URL you read, bron_2 = a second URL if you used one (else empty). 'datum' = publication date, 'toelichting' = one line in Dutch."),
        schema=CONTROLE, zoeken=True)


# ---------- maken ----------
def nieuwe_map(naam):
    pad = CONCEPTEN / f"{date.today().isoformat()}-{re.sub(r'[^a-z0-9]+', '-', naam.lower())[:40].strip('-')}-{random.randint(100, 999)}"
    pad.mkdir(parents=True, exist_ok=True)
    return pad


def render(soort, spec, kleur, map_, extra=None):
    if soort in ("carrousel", "actualiteit", "openbaar"):
        import render_carrousel
        render_carrousel.render({"serie": spec["serie"], "kleurenset": kleur, "slides": spec["slides"]}, map_)
    elif soort == "tekst_reel":
        import render_tekst_reel
        # alleen tekst + muziek, geen stem (besluit 10-11; de stem blijft voor stem_video)
        render_tekst_reel.render({"serie": spec["serie"], "kleurenset": kleur, "beats": spec["beats"]}, map_)
    elif soort == "kaart":
        import render_kaart
        d = spec["diagram"]
        k = {"type": d, "titel": spec["titel"], "links": spec["links"], "rechts": spec["rechts"], "midden": spec["midden"], "keuze_a": spec["keuze_a"],
             "uitkomst_a": (spec["uitkomst_a"] + ["", ""])[:2], "keuze_b": spec["keuze_b"], "uitkomst_b": spec["uitkomst_b"], "items": spec["items"],
             "links_kop": spec["links_kop"], "links": spec["links_lijst"] if d == "voor_na" else spec["links"], "rechts_kop": spec["rechts_kop"],
             "rechts": spec["rechts_lijst"] if d == "voor_na" else spec["rechts"], "stappen": spec["stappen"], "lijn": spec["lijn"] or "stijgend",
             "notitie": spec["notitie"], "x": spec["x"], "y": spec["y"]}
        render_kaart.render(k, map_ / "kaart.png", extra)
    elif soort == "demo_reel":
        import opname_demo
        demo = json.loads((TOOLS / "demos" / f"{extra}.json").read_text(encoding="utf-8"))
        if (spec or {}).get("hook"):  # gekozen hook vervangt de vaste openingstekst van de demo (22-11)
            demo["hook"] = spec["hook"]["scherm"]
        opname_demo.render(demo, map_)  # zonder stem (10-11)
    elif soort == "stem_video":
        import render_stem_video
        return render_stem_video.render(video_spec(spec, kleur), map_, zonder_stem=bool(extra))


def video_spec(spec, kleur):
    """Van Claudes concept naar de spec van render_stem_video (vaste stem, tempo en regels)."""
    import render_stem_video
    beats = render_stem_video.regie([{"zegt": b["zegt"], "uitspraak": b["uitspraak"], "scene": b["scene"]} for b in spec["beats"]], tags=False)
    uit = {"onderwerp": spec.get("onderwerp", ""), **render_stem_video.ERIC, "kleurenset": kleur, "beats": beats}
    if spec.get("seed") is not None:
        uit["seed"] = spec["seed"]
    return uit


def opslaan(conn, soort, spec, kleur, map_, bron_id=None, bronnen=None):
    (map_ / "spec.json").write_text(json.dumps({**spec, "soort": soort, "kleurenset": kleur}, ensure_ascii=False, indent=2), encoding="utf-8")
    tags = [] if soort == "kaart" and spec.get("diagram") == "fork" else spec.get("hashtags", [])
    cur = conn.execute("INSERT INTO instagram_posts (bron_id, soort, onderwerp, kleurenset, hashtags, caption, bronnen, map, muziek, dienst) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (bron_id, "fork" if soort == "kaart" and spec.get("diagram") == "fork" else soort, spec.get("onderwerp") or "", kleur,
                        json.dumps(tags), spec.get("caption") or spec.get("tekst"), json.dumps(bronnen or []), str(map_), spec.get("muziek") or None,
                        spec.get("dienst")))
    conn.commit()
    return cur.lastrowid


def laatst_gebruikt(conn, soort, opties):
    gebruikt = [r[0] for r in conn.execute("SELECT kleurenset FROM instagram_posts WHERE soort = ? ORDER BY id DESC", (soort,))]
    nooit = [o for o in opties if o not in gebruikt]
    return random.choice(nooit) if nooit else max(opties, key=gebruikt.index)  # gebruikt: nieuwste eerst, dus hoogste index = langst geleden


def maak_stem_video(conn, aantal, tags, zonder_stem=False):
    """Video met Erics stem over de volgende dienst van de website. Zonder stem: gratis proef, alleen lokaal."""
    if not zonder_stem and stem_tegoed() < STEM_MIN_TEGOED:
        raise RuntimeError("Te weinig ElevenLabs-tegoed voor een video met stem")
    dienst = diensten.volgende(conn)
    print(f"Dienst: {dienst['naam']}")
    hook = kies_hook(conn, "stem_video", f"Source: a service Oussama builds. {dienst['naam']}: {dienst['wat']}") if HOOKSTAP_AAN else None
    spec = schrijf(conn, "stem_video", prompt_stem_video(dienst, aantal, tags) + hook_instructie(hook, "stem_video"), aantal, tags, hook=hook)
    spec["dienst"], spec["muziek"] = dienst["naam"], STEM_MUZIEK
    kleur, map_ = wachtrij.kies_kleur(conn, video=True), nieuwe_map(("proef-" if zonder_stem else "") + dienst["naam"])
    render("stem_video", spec, kleur, map_, zonder_stem)
    meldingen = json.loads((map_ / "controle.json").read_text(encoding="utf-8")).get("stem", {}) or {}
    if not zonder_stem and meldingen.get("meldingen") and stem_tegoed() >= STEM_MIN_TEGOED:
        print("Stem zakt weg, één nieuwe opname:", meldingen["meldingen"])
        spec["seed"] = random.randint(1, 10_000)
        render("stem_video", spec, kleur, map_)
    (map_ / "spec.json").write_text(json.dumps({**spec, "soort": "stem_video", "kleurenset": kleur}, ensure_ascii=False, indent=2), encoding="utf-8")
    return spec, kleur, map_


def maak(conn, soort=None, zonder_stem=False):
    soort = soort or kies_soort(conn)
    aantal, tags = hashtag_eisen(conn)
    print(f"Nieuw concept: {soort}")
    if soort == "stem_video" and zonder_stem:
        _, _, map_ = maak_stem_video(conn, aantal, tags, zonder_stem=True)
        print(f"Proefvideo zonder stem (niet naar Telegram): {map_ / 'reel.mp4'}")
        return None
    bot = telegram_review.Bot()
    if soort == "story":
        rij = wachtrij.volgende(conn, "the_other_shift")
        spec = vraag(conn, None, "schrijven:story", prompt_story(rij), SCHEMA["story"])
        map_ = nieuwe_map(spec["onderwerp"])
        pid = opslaan(conn, "story", spec, None, map_, bron_id=rij[0])
        bot.tekst(f"<b>Story-idee #{pid} · The Other Shift</b>\n\n<pre>{html.escape(spec['tekst'])}</pre>\n📸 Foto: {html.escape(spec['foto_idee'])}",
                  [[{"text": "✅ Goedkeuren", "callback_data": f"ok:{pid}"}, {"text": "✏️ Aanpassen", "callback_data": f"edit:{pid}"},
                    {"text": "❌ Overslaan", "callback_data": f"skip:{pid}"}]])
        return pid
    if soort == "actualiteit":
        c = onderzoek_actualiteit(conn)
        if not c["bevestigd"]:
            print("Actualiteit niet bevestigd, vervalt:", c["toelichting"])
            return None
        prompt = (f"Turn this verified news into an Instagram carousel (4 to 6 slides) in the series 'AI NEWS'. Lens: 'what this actually means for your business'.\n"
                  f"Verified facts (use ONLY these, add nothing else, not even 'examples' the company gives unless they are listed here): {c['kern']} (date: {c['datum']}).\nSlides as for a normal carousel: cover, tekst slides, optional cijfer slide only with a "
                  f"verified number (bron = publication name), slot slide with a ⚡ call to action. 'serie' must be 'AI NEWS'. Include one hashtag about this specific news.\n"
                  f"{taalregels(aantal, tags)}")
        hook = kies_hook(conn, "actualiteit", f"Source: verified AI news (use only these facts): {c['kern']} (date: {c['datum']})") if HOOKSTAP_AAN else None
        spec = schrijf(conn, "carrousel", prompt + hook_instructie(hook, "actualiteit"), aantal, tags, hook=hook)
        kleur, map_ = wachtrij.kies_kleur(conn), nieuwe_map(spec["onderwerp"])
        (map_ / "onderzoek.json").write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")  # herleidbaar: waar komt elke bewering vandaan
        render("actualiteit", spec, kleur, map_)
        pid = opslaan(conn, "actualiteit", spec, kleur, map_, bronnen=[b for b in (c["bron_1"], c["bron_2"]) if b])
    elif soort == "stem_video":
        spec, kleur, map_ = maak_stem_video(conn, aantal, tags)
        pid = opslaan(conn, "stem_video", spec, kleur, map_)
    elif soort == "demo_reel":
        recent = wachtrij.recente_kleuren(conn, 1)
        opties = [d for d in DEMOS if not (recent and recent[0] in wachtrij.BLAUWIG and wachtrij.echte_kleur(d) in wachtrij.BLAUWIG)]
        demo = laatst_gebruikt(conn, "demo_reel", opties or DEMOS)  # demo's hebben een vaste kleur: geen blauw na blauw
        hook = kies_hook(conn, "demo_reel", "Source (a screen-recording demo, fictional business, real capability):\n"
                         + (TOOLS / "demos" / f"{demo}.json").read_text(encoding="utf-8")) if HOOKSTAP_AAN else None
        spec = schrijf(conn, "demo_reel", prompt_demo(demo, aantal, tags) + hook_instructie(hook, "demo_reel"), aantal, tags, hook=hook)
        map_ = nieuwe_map(demo)
        render("demo_reel", spec, None, map_, demo)
        pid = opslaan(conn, "demo_reel", spec, demo, map_)
    else:
        if soort == "kaart":
            pijler = random.choice(["the_fork", "automation_simplified"])
        else:
            laatste = [r[0] for r in conn.execute("SELECT b.pijler FROM instagram_posts p JOIN instagram_bron b ON b.id = p.bron_id ORDER BY p.id DESC LIMIT 1")]
            pijler = "myth_check" if laatste == ["automation_simplified"] else "automation_simplified"
        rij = wachtrij.volgende(conn, pijler) or wachtrij.volgende(conn, "automation_simplified")
        dienst = None
        if soort in ("carrousel", "tekst_reel") and random.random() < 0.35:  # af en toe een dienst van de website (besluit 20-11)
            dienst = diensten.volgende(conn)
            rij = (None, "automation_simplified", dienst["naam"], f"{dienst['naam']}: {dienst['wat']}")
        if soort == "kaart":
            diagram = "fork" if rij[1] == "the_fork" else random.choice([d for d in DIAGRAMMEN if d != "fork"])
            if diagram == "fork":
                aantal, tags = 0, []
            hook = kies_hook(conn, "kaart", bron_tekst(rij)) if HOOKSTAP_AAN else None
            spec = schrijf(conn, "kaart", prompt_kaart(rij, diagram, aantal, tags) + hook_instructie(hook, "kaart"), aantal, tags, hook=hook)
            scene = laatst_gebruikt(conn, "kaart", SCENES)
            map_ = nieuwe_map(spec["onderwerp"])
            render("kaart", spec, None, map_, scene)
            pid = opslaan(conn, "kaart", spec, scene, map_, bron_id=rij[0])
        else:
            maker = prompt_carrousel if soort == "carrousel" else prompt_tekst_reel
            hook = kies_hook(conn, soort, bron_tekst(rij)) if HOOKSTAP_AAN else None
            spec = schrijf(conn, soort, maker(rij, aantal, tags) + hook_instructie(hook, soort), aantal, tags, hook=hook)
            if dienst:
                spec["dienst"] = dienst["naam"]
            kleur, map_ = wachtrij.kies_kleur(conn), nieuwe_map(spec["onderwerp"])
            render(soort, spec, kleur, map_)
            pid = opslaan(conn, soort, spec, kleur, map_, bron_id=rij[0])
    telegram_review.stuur(bot, conn, pid)
    print(f"Concept #{pid} verstuurd naar Telegram.")
    return pid


def maak_openbaar(conn, verhaal):
    """Wekelijkse serie 'Building in public' (24-11): Oussama vertelt (Nederlands, vaak ingesproken) wat hij deed en
    leerde; dat wordt een carrousel in de stijl van #10 (32 calls, de best lopende post). Alleen zijn eigen feiten."""
    aantal, tags = hashtag_eisen(conn)
    bron = f"Source: Oussama's own story of this week (Dutch, possibly a voice transcript; use ONLY these facts and numbers, invent nothing):\n\"\"\"\n{verhaal}\n\"\"\""
    prompt = (f"Turn this into an Instagram carousel (3 to 5 slides) in the series 'BUILDING IN PUBLIC': an honest first-person update from Oussama, "
              f"a solo founder building an AI automation business.\n{bron}\n\n"
              "Model it on his best performing post: cover = the concrete thing he did (a real number from the story if there is one); then 'tekst' slides with "
              "what happened and 2 or 3 short lessons, at least one where he was wrong or surprised; last slide type 'slot' with a question to the viewer in 'titel' "
              "and an empty 'knop'. Things that did NOT work are just as welcome as wins (e.g. 'I thought X was the problem. It wasn't.'): be honest about why it failed "
              "and make the lesson about Oussama's own choice or assumption, never look down on or blame a group of people. "
              "First person ('I'), plain and honest, no hype, no selling, no client or company names.Mark the key word in titles with *asterisks*. "
              "'serie' must be 'BUILDING IN PUBLIC'. Leave unused fields empty.\n"
              "Caption for THIS series (overrides the length rule below): first line = the hook, then what he did and the numbered lessons, max ~80 words, "
              "ending with a short question to the reader (no 'send me a DM'). One hashtag must be #buildinpublic.\n"
              f"{taalregels(aantal, [t for t in tags if t.lower() != '#buildinpublic'])}")
    hook = kies_hook(conn, "carrousel", bron) if HOOKSTAP_AAN else None
    spec = schrijf(conn, "carrousel", prompt + hook_instructie(hook, "carrousel"), aantal, [t for t in tags if t.lower() != "#buildinpublic"], hook=hook)
    kleur, map_ = wachtrij.kies_kleur(conn), nieuwe_map(spec["onderwerp"])
    (map_ / "verhaal.txt").write_text(verhaal, encoding="utf-8")  # herleidbaar: waar komen de feiten vandaan
    render("carrousel", spec, kleur, map_)
    pid = opslaan(conn, "openbaar", spec, kleur, map_)
    telegram_review.stuur(telegram_review.Bot(), conn, pid)
    print(f"Bouwen in het openbaar: concept #{pid} verstuurd naar Telegram.")
    return pid


# ---------- feedback ----------
def verwerk(conn):
    for fid, pid, tekst in conn.execute("SELECT id, post_id, tekst FROM instagram_feedback WHERE verwerkt = 0 ORDER BY id").fetchall():
        rij = conn.execute("SELECT soort, kleurenset, map, hashtags FROM instagram_posts WHERE id = ?", (pid,)).fetchone()
        soort, kleur, map_ = rij[0], rij[1], Path(rij[2])
        oud = json.loads((map_ / "spec.json").read_text(encoding="utf-8"))
        schema_soort = {"actualiteit": "carrousel", "openbaar": "carrousel", "fork": "kaart"}.get(soort, soort)
        aantal = len(json.loads(rij[3] or "[]"))
        print(f"Feedback #{fid} op concept #{pid}: {tekst}")
        prompt = (f"Revise this Instagram concept based on Oussama's feedback (he writes in Dutch). Change only what the feedback asks; keep everything else, "
                  f"including the facts. Keep exactly {aantal} hashtags unless the feedback is about hashtags.\nFEEDBACK: {tekst}\n\nCURRENT CONCEPT:\n"
                  + json.dumps({k: v for k, v in oud.items() if k not in ("soort", "kleurenset")}, ensure_ascii=False))
        spec = vraag(conn, pid, f"aanpassen:{soort}", prompt, SCHEMA[schema_soort])
        fouten = [f for f in controleer(spec, aantal or len(spec.get("hashtags", [])), []) if "hashtags" not in f]
        if fouten:
            telegram_review.Bot().tekst(f"⚠️ Aanpassing van #{pid} haalde de controle niet ({'; '.join(fouten)}). Ik heb niets veranderd.")
            conn.execute("UPDATE instagram_feedback SET verwerkt = 1 WHERE id = ?", (fid,))
            conn.commit()
            continue
        if oud.get("hook"):
            spec["hook"] = oud["hook"]  # formule onthouden voor de vergelijking met de echte views
        if soort == "stem_video":
            spec["dienst"], spec["muziek"] = oud.get("dienst"), STEM_MUZIEK
            if [b["uitspraak"] for b in spec["beats"]] != [b["uitspraak"] for b in oud["beats"]] and stem_tegoed() < STEM_MIN_TEGOED:
                telegram_review.Bot().tekst(f"⚠️ Aanpassing van #{pid} vraagt een nieuwe opname van Eric, maar het ElevenLabs-tegoed is te laag. Ik heb niets veranderd.")
                conn.execute("UPDATE instagram_feedback SET verwerkt = 1 WHERE id = ?", (fid,))
                conn.commit()
                continue
            render("stem_video", spec, kleur, map_)
        elif soort not in ("story", "demo_reel"):  # bij een demo verandert alleen de tekst, de video blijft
            for f in list(map_.glob("slide-*.png")) + list(map_.glob("*.mp4")) + list(map_.glob("kaart.png")):
                f.unlink()
            render({"fork": "kaart"}.get(soort, soort), spec, kleur, map_, kleur if soort in ("kaart", "fork") else None)
        (map_ / "spec.json").write_text(json.dumps({**spec, "soort": soort, "kleurenset": kleur}, ensure_ascii=False, indent=2), encoding="utf-8")
        conn.execute("UPDATE instagram_posts SET caption = ?, hashtags = ?, muziek = ?, status = 'concept', bijgewerkt_op = datetime('now') WHERE id = ?",
                     (spec.get("caption") or spec.get("tekst"), json.dumps(spec.get("hashtags", [])), spec.get("muziek") or None, pid))
        conn.execute("UPDATE instagram_feedback SET verwerkt = 1 WHERE id = ?", (fid,))
        conn.commit()
        bot = telegram_review.Bot()
        bot.tekst(f"✏️ Aangepast op je feedback: <i>{html.escape(tekst)}</i>")
        if soort == "story":
            bot.tekst(f"<b>Story-idee #{pid}</b>\n\n<pre>{html.escape(spec['tekst'])}</pre>\n📸 Foto: {html.escape(spec['foto_idee'])}",
                      [[{"text": "✅ Goedkeuren", "callback_data": f"ok:{pid}"}, {"text": "✏️ Aanpassen", "callback_data": f"edit:{pid}"},
                        {"text": "❌ Overslaan", "callback_data": f"skip:{pid}"}]])
        else:
            telegram_review.stuur(bot, conn, pid)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("maak")
    m.add_argument("--soort", choices=list(MIX))
    m.add_argument("--zonder-stem", action="store_true", help="stem_video als gratis proef zonder Eric, niet naar Telegram")
    sub.add_parser("verwerk")
    d = sub.add_parser("dagelijks")
    d.add_argument("--vol", action="store_true", help="vul aan tot een hele week (10) zonder dagmaximum; zaterdag 07:00 vóór de weekplanning")
    o = sub.add_parser("openbaar", help="bouwen in het openbaar: concept uit Oussama's eigen verhaal (via de content-bot)")
    o.add_argument("verhaal")
    sub.add_parser("kosten")
    args = ap.parse_args()
    conn = wachtrij.verbind()
    kosten_tabel(conn)
    if args.cmd == "maak":
        maak(conn, args.soort, args.zonder_stem)
    elif args.cmd == "verwerk":
        verwerk(conn)
    elif args.cmd == "openbaar":
        try:
            maak_openbaar(conn, args.verhaal)
        except Exception as fout:
            telegram_review.Bot().tekst(f"⚠️ Het bouwen-in-het-openbaar-concept lukte niet ({html.escape(str(fout))[:300]}). Stuur je verhaal nog een keer?")
            raise
    elif args.cmd == "dagelijks":
        # voorraad van 5 posts die een dag in de weekplanning vullen (advertenties en story-ideeën tellen niet mee);
        # normaal max 2 nieuwe per dag, zaterdag 07:00 (--vol) zoveel als nodig zodat de planning van 09:00 vol is
        telling = "SELECT COUNT(*) FROM instagram_posts WHERE status IN ('concept', 'goedgekeurd') AND soort NOT IN ('advertentie', 'story')"
        doel = len(telegram_review.vrije_dagen()[1]) * telegram_review.PER_DAG if args.vol else VOORRAAD  # zaterdag: precies de vrije plekken van volgende week
        nodig = max(0, doel - conn.execute(telling).fetchone()[0])
        for _ in range(nodig + 3 if args.vol else min(2, nodig)):  # +3 ruimte voor een story-idee of mislukte poging
            if conn.execute(telling).fetchone()[0] >= doel:
                break
            try:
                maak(conn)
            except Exception as fout:  # één mislukt concept mag de rest niet tegenhouden
                print("Concept mislukt:", fout)
    elif args.cmd == "kosten":
        print(f"Uitgegeven in {maand()}: ${uitgegeven(conn):.2f} van ${LIMIET:.0f}")
        for stap, n, usd in conn.execute("SELECT stap, COUNT(*), SUM(usd) FROM instagram_kosten WHERE maand = ? GROUP BY stap", (maand(),)):
            print(f"  {stap}: {n}x, ${usd:.2f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
