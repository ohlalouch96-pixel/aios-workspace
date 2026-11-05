"""
Instagram-contentagent (@insightance.ai) — het brein

Kiest wat er gemaakt wordt, laat Claude de tekst schrijven volgens
workflows/instagram_content.md, controleert de uitkomst, roept de renderers
in tools/instagram/ aan, legt het concept vast in de wachtrij en stuurt het
via de content-bot naar Oussama. Verwerkt ook ✏️-feedback tot een nieuwe versie.
Plaatst nooit zelf iets op Instagram (fase 1).

Kosten: elke Claude-aanroep wordt berekend (tokens × prijs + webzoekopdrachten)
en opgeslagen in instagram_kosten. Melding in Telegram bij $15, stop bij $20 per maand.

Gebruik (CLI):
    python apps/content/agent.py maak [--soort carrousel|kaart|tekst_reel|demo_reel|actualiteit|story]
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
MIX = {"carrousel": 0.32, "demo_reel": 0.25, "tekst_reel": 0.13, "kaart": 0.12, "actualiteit": 0.10, "story": 0.08}

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
    "story": obj({"onderwerp": S, "tekst": S, "foto_idee": S}),
}
CONTROLE = obj({"bevestigd": {"type": "boolean"}, "kern": S, "bron_1": S, "bron_2": S, "datum": S, "toelichting": S})


# ---------- keuzes ----------
def vorige(conn, n=6):
    return [dict(zip(["soort", "kleurenset", "hashtags"], r)) for r in
            conn.execute("SELECT soort, kleurenset, hashtags FROM instagram_posts WHERE status != 'overgeslagen' ORDER BY id DESC LIMIT ?", (n,))]


def kies_soort(conn):
    laatste = [v["soort"] for v in vorige(conn, 2)]
    opties = {s: w for s, w in MIX.items() if not laatste or s != laatste[0]}
    return random.choices(list(opties), weights=list(opties.values()))[0]


def hashtag_eisen(conn):
    recent = wachtrij.recente_hashtags(conn, 1)
    vorige_tags = recent[0] if recent else []
    aantal = random.choice([n for n in range(3, 7) if n != len(vorige_tags)])
    return aantal, vorige_tags


def taalregels(aantal, verboden_tags):
    return (f"Hashtags: exactly {aantal}, relevant to this specific post, varied (not a fixed set). Do NOT use any of these from the previous post: "
            f"{', '.join(verboden_tags) or 'none'}. Caption: first sentence must stop the scroll (allowed to challenge, never untrue); then at most two short paragraphs (together max ~55 words) "
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


def schrijf(conn, soort, prompt, aantal, verboden_tags, post_id=None):
    spec = vraag(conn, post_id, f"schrijven:{soort}", prompt, SCHEMA[soort])
    fouten = controleer(spec, aantal, verboden_tags)
    if fouten:  # één herkansing met de concrete fouten erbij
        spec = vraag(conn, post_id, f"herschrijven:{soort}", prompt + "\n\nYour previous attempt had these problems, fix them:\n- " + "\n- ".join(fouten)
                     + "\n\nPrevious attempt:\n" + json.dumps(spec, ensure_ascii=False), SCHEMA[soort])
        fouten = controleer(spec, aantal, verboden_tags)
        if fouten:
            raise RuntimeError("Concept haalt de controle niet: " + "; ".join(fouten))
    return spec


# ---------- per soort ----------
def bron_tekst(rij):
    return f"Source ({rij[1]}), already fact-checked LinkedIn post:\n\"\"\"\n{rij[3]}\n\"\"\""


def prompt_carrousel(rij, aantal, tags):
    serie = "MYTH CHECK" if rij[1] == "myth_check" else "AUTOMATION SIMPLIFIED"
    return (f"Turn this into an Instagram carousel (4 to 6 slides) for the series {serie}.\n{bron_tekst(rij)}\n\n"
            "Slides: first slide type 'cover' (or 'citaat' for a myth, with the myth as the title), then 'tekst' slides (label + short title + one or two short sentences), "
            "optionally one 'cijfer' slide ONLY if the source contains a real number (with its source in 'bron'), last slide type 'slot' with a closing line and a short 'knop' "
            "(a varied follow-style call to action ending with ⚡). Mark the key word in titles with *asterisks*. One thought per slide, short. Leave unused fields empty. "
            f"'serie' must be '{serie}'.\n{taalregels(aantal, tags)}")


def prompt_tekst_reel(rij, aantal, tags):
    serie = "MYTH CHECK" if rij[1] == "myth_check" else "AUTOMATION SIMPLIFIED"
    return (f"Turn this into a 12 to 16 second vertical text reel: 4 to 6 beats of 2.2 to 3.6 seconds each.\n{bron_tekst(rij)}\n\n"
            "Beat 1 is the hook (about 3 s). Each beat is max ~10 words; mark the key word with *asterisks*; 'label' is an optional small tag (e.g. 'Step 1'), empty if not needed. "
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
    if soort in ("carrousel", "actualiteit"):
        import render_carrousel
        render_carrousel.render({"serie": spec["serie"], "kleurenset": kleur, "slides": spec["slides"]}, map_)
    elif soort == "tekst_reel":
        import render_tekst_reel
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
        opname_demo.render(json.loads((TOOLS / "demos" / f"{extra}.json").read_text(encoding="utf-8")), map_)


def opslaan(conn, soort, spec, kleur, map_, bron_id=None, bronnen=None):
    (map_ / "spec.json").write_text(json.dumps({**spec, "soort": soort, "kleurenset": kleur}, ensure_ascii=False, indent=2), encoding="utf-8")
    tags = [] if soort == "kaart" and spec.get("diagram") == "fork" else spec.get("hashtags", [])
    cur = conn.execute("INSERT INTO instagram_posts (bron_id, soort, onderwerp, kleurenset, hashtags, caption, bronnen, map, muziek) VALUES (?,?,?,?,?,?,?,?,?)",
                       (bron_id, "fork" if soort == "kaart" and spec.get("diagram") == "fork" else soort, spec.get("onderwerp") or "", kleur,
                        json.dumps(tags), spec.get("caption") or spec.get("tekst"), json.dumps(bronnen or []), str(map_), spec.get("muziek") or None))
    conn.commit()
    return cur.lastrowid


def laatst_gebruikt(conn, soort, opties):
    gebruikt = [r[0] for r in conn.execute("SELECT kleurenset FROM instagram_posts WHERE soort = ? ORDER BY id DESC", (soort,))]
    nooit = [o for o in opties if o not in gebruikt]
    return random.choice(nooit) if nooit else max(opties, key=gebruikt.index)  # gebruikt: nieuwste eerst, dus hoogste index = langst geleden


def maak(conn, soort=None):
    soort = soort or kies_soort(conn)
    aantal, tags = hashtag_eisen(conn)
    print(f"Nieuw concept: {soort}")
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
        spec = schrijf(conn, "carrousel", prompt, aantal, tags)
        kleur, map_ = wachtrij.kies_kleur(conn), nieuwe_map(spec["onderwerp"])
        (map_ / "onderzoek.json").write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")  # herleidbaar: waar komt elke bewering vandaan
        render("actualiteit", spec, kleur, map_)
        pid = opslaan(conn, "actualiteit", spec, kleur, map_, bronnen=[b for b in (c["bron_1"], c["bron_2"]) if b])
    elif soort == "demo_reel":
        demo = laatst_gebruikt(conn, "demo_reel", DEMOS)
        spec = schrijf(conn, "demo_reel", prompt_demo(demo, aantal, tags), aantal, tags)
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
        if soort == "kaart":
            diagram = "fork" if rij[1] == "the_fork" else random.choice([d for d in DIAGRAMMEN if d != "fork"])
            if diagram == "fork":
                aantal, tags = 0, []
            spec = schrijf(conn, "kaart", prompt_kaart(rij, diagram, aantal, tags), aantal, tags)
            scene = laatst_gebruikt(conn, "kaart", SCENES)
            map_ = nieuwe_map(spec["onderwerp"])
            render("kaart", spec, None, map_, scene)
            pid = opslaan(conn, "kaart", spec, scene, map_, bron_id=rij[0])
        else:
            maker = prompt_carrousel if soort == "carrousel" else prompt_tekst_reel
            spec = schrijf(conn, soort, maker(rij, aantal, tags), aantal, tags)
            kleur, map_ = wachtrij.kies_kleur(conn), nieuwe_map(spec["onderwerp"])
            render(soort, spec, kleur, map_)
            pid = opslaan(conn, soort, spec, kleur, map_, bron_id=rij[0])
    telegram_review.stuur(bot, conn, pid)
    print(f"Concept #{pid} verstuurd naar Telegram.")
    return pid


# ---------- feedback ----------
def verwerk(conn):
    for fid, pid, tekst in conn.execute("SELECT id, post_id, tekst FROM instagram_feedback WHERE verwerkt = 0 ORDER BY id").fetchall():
        rij = conn.execute("SELECT soort, kleurenset, map, hashtags FROM instagram_posts WHERE id = ?", (pid,)).fetchone()
        soort, kleur, map_ = rij[0], rij[1], Path(rij[2])
        oud = json.loads((map_ / "spec.json").read_text(encoding="utf-8"))
        schema_soort = {"actualiteit": "carrousel", "fork": "kaart"}.get(soort, soort)
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
        if soort not in ("story", "demo_reel"):  # bij een demo verandert alleen de tekst, de video blijft
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
    sub.add_parser("verwerk")
    sub.add_parser("dagelijks")
    sub.add_parser("kosten")
    args = ap.parse_args()
    conn = wachtrij.verbind()
    kosten_tabel(conn)
    if args.cmd == "maak":
        maak(conn, args.soort)
    elif args.cmd == "verwerk":
        verwerk(conn)
    elif args.cmd == "dagelijks":
        open_ = conn.execute("SELECT COUNT(*) FROM instagram_posts WHERE status IN ('concept', 'goedgekeurd')").fetchone()[0]
        for _ in range(max(0, min(2, 3 - open_))):  # buffer van ±3 klaarstaande concepten, max 2 per dag
            maak(conn)
    elif args.cmd == "kosten":
        print(f"Uitgegeven in {maand()}: ${uitgegeven(conn):.2f} van ${LIMIET:.0f}")
        for stap, n, usd in conn.execute("SELECT stap, COUNT(*), SUM(usd) FROM instagram_kosten WHERE maand = ? GROUP BY stap", (maand(),)):
            print(f"  {stap}: {n}x, ${usd:.2f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
