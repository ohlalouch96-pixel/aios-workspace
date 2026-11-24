"""
Instagram — concepten ter goedkeuring via Telegram (@insightance.ai, fase 1)

Stuurt een concept naar Oussama via de aparte content-bot: de beelden of de
video, de volledige caption (tekst + vaste afsluiter + hashtags), muziekadvies
bij reels en bij actualiteiten de bronlinks. Met knoppen:
    ✅ Goedkeuren  → status goedgekeurd, plaatsklaar pakket (originele bestanden + caption om te kopiëren) + knop 📤 Geplaatst
    ✏️ Aanpassen   → vraagt wat er anders moet; getypt of ingesproken (Whisper) antwoord komt in instagram_feedback
    ❌ Overslaan   → status overgeslagen
    📤 Geplaatst   → status geplaatst
Er wordt nooit iets op Instagram gezet: plaatsen doet Oussama zelf (fase 1).

Een concept is een map met spec.json (zelfde spec als de renderers + caption, hashtags, muziek,
bronnen) en de bestanden: slide-*.png (carrousel), kaart.png (losse afbeelding) of reel.mp4 (+ cover.jpg).

Gebruik (CLI):
    python tools/instagram/telegram_review.py test             # verbinding testen
    python tools/instagram/telegram_review.py stuur 12         # post 12 uit de wachtrij versturen
    python tools/instagram/telegram_review.py luister          # knoppen en feedback verwerken (blijft draaien)

.env: INSTAGRAM_BOT_TOKEN (content-bot), INSTAGRAM_CHAT_ID (privéchat Oussama met die bot), OPENAI_API_KEY (alleen voor ingesproken feedback).
"""

import argparse
import html
import json
import re
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

HIER = Path(__file__).resolve().parent
WORKSPACE_ROOT = HIER.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
sys.path.insert(0, str(HIER))
from config import get_env  # noqa: E402
from wachtrij import verbind, volledige_caption  # noqa: E402

SOORT_LABEL = {"carrousel": "Carrousel", "kaart": "Losse afbeelding", "fork": "The Fork", "tekst_reel": "Reel · bewegende tekst",
               "demo_reel": "Reel · demo", "stem_video": "Reel · video met stem", "actualiteit": "Actualiteit",
               "story": "Story-tekst", "advertentie": "Advertentie · reel",
               "openbaar": "Losse post · bouwen in het openbaar"}


class Bot:
    def __init__(self):
        self.token = get_env("INSTAGRAM_BOT_TOKEN")
        self.chat = get_env("INSTAGRAM_CHAT_ID")
        if not self.token or not self.chat:
            sys.exit("INSTAGRAM_BOT_TOKEN of INSTAGRAM_CHAT_ID ontbreekt in .env")
        self.api = f"https://api.telegram.org/bot{self.token}"

    def call(self, methode, files=None, **data):
        for k, v in list(data.items()):
            if isinstance(v, (dict, list)):
                data[k] = json.dumps(v)
        r = requests.post(f"{self.api}/{methode}", data=data, files=files, timeout=120)
        resultaat = r.json()
        if not resultaat.get("ok"):
            raise RuntimeError(f"Telegram {methode}: {resultaat.get('description')}")
        return resultaat["result"]

    def tekst(self, tekst, knoppen=None):
        extra = {"reply_markup": {"inline_keyboard": knoppen}} if knoppen else {}
        return self.call("sendMessage", chat_id=self.chat, text=tekst, parse_mode="HTML", disable_web_page_preview=True, **extra)

    def media(self, paden, als_document=False):
        """Afbeeldingen als album (max 10), of als documenten (originele kwaliteit, voor het plaatsen)."""
        soort = "document" if als_document else "photo"
        groep, files = [], {}
        for i, pad in enumerate(paden[:10]):
            files[f"f{i}"] = open(pad, "rb")
            groep.append({"type": soort, "media": f"attach://f{i}"})
        try:
            if len(groep) == 1:
                methode = "sendDocument" if als_document else "sendPhoto"
                return self.call(methode, files={soort: files["f0"]}, chat_id=self.chat)
            return self.call("sendMediaGroup", files=files, chat_id=self.chat, media=groep)
        finally:
            for f in files.values():
                f.close()

    def video(self, pad, cover=None, als_document=False):
        files = {"document" if als_document else "video": open(pad, "rb")}
        if cover and not als_document:
            files["thumbnail"] = open(cover, "rb")
        try:
            if als_document:
                return self.call("sendDocument", files=files, chat_id=self.chat)
            extra = {"thumbnail": "attach://thumbnail"} if cover else {}
            return self.call("sendVideo", files=files, chat_id=self.chat, supports_streaming=True, width=1080, height=1920, **extra)
        finally:
            for f in files.values():
                f.close()


def post_laden(conn, post_id):
    rij = conn.execute("SELECT id, soort, onderwerp, kleurenset, hashtags, caption, bronnen, map, muziek, status FROM instagram_posts WHERE id = ?", (post_id,)).fetchone()
    if not rij:
        sys.exit(f"Post {post_id} niet gevonden")
    p = dict(zip(["id", "soort", "onderwerp", "kleurenset", "hashtags", "caption", "bronnen", "map", "muziek", "status"], rij))
    p["hashtags"], p["bronnen"] = json.loads(p["hashtags"] or "[]"), json.loads(p["bronnen"] or "[]")
    p["map"] = Path(p["map"]) if p["map"] else None
    return p


def bestanden(p):
    m = p["map"]
    if m and (m / "reel.mp4").exists():
        return "video", [m / "reel.mp4"], m / "cover.jpg" if (m / "cover.jpg").exists() else None
    if m:
        slides = sorted(m.glob("slide-*.png"), key=lambda x: int(x.stem.split("-")[1]))
        if slides:
            return "beeld", slides, None
        losse = sorted(m.glob("*.png"))
        if losse:
            return "beeld", losse[:1], None
    return "tekst", [], None


def stuur(bot, conn, post_id):
    p = post_laden(conn, post_id)
    soort, paden, cover = bestanden(p)
    if soort == "video":
        bot.video(paden[0], cover)
    elif soort == "beeld":
        bot.media(paden)
    caption = volledige_caption(p["caption"] or "", p["hashtags"], p["soort"])
    delen = [f"<b>Concept #{p['id']} · {SOORT_LABEL.get(p['soort'], p['soort'])}</b>\n{html.escape(p['onderwerp'])}",
             f"<b>Caption</b>\n<pre>{html.escape(caption)}</pre>"]
    try:  # hook-score (sinds 21-11): welke formule won en met welk cijfer
        h = json.loads((Path(p["map"]) / "spec.json").read_text(encoding="utf-8")).get("hook")
    except (OSError, ValueError, TypeError):
        h = None
    if h:
        delen.append(f"🎣 <b>Hook:</b> {h['score']}/100 · {html.escape(h['formule'])}")
    if p["muziek"]:
        delen.append(f"🎵 <b>Muziek:</b> {html.escape(p['muziek'])}")
    if p["bronnen"]:
        delen.append("🔎 <b>Bronnen (zelf nog checken):</b>\n" + "\n".join(f"• {html.escape(b)}" for b in p["bronnen"]))
    bot.tekst("\n\n".join(delen), [[{"text": "✅ Goedkeuren", "callback_data": f"ok:{post_id}"},
                                     {"text": "✏️ Aanpassen", "callback_data": f"edit:{post_id}"},
                                     {"text": "❌ Overslaan", "callback_data": f"skip:{post_id}"}]])


PER_DAG = 2  # sinds 24-11 twee posts per werkdag (was 1 om 14:00): één beeldpost en één reel, nooit twee reels op een dag
TIJD_BEELD, TIJD_REEL = "14:00", "19:00"  # 24-11: 14:00 = lunch VK + ochtend VS; 19:00 = avond NL/VK + lunch VS (11:00 mist de VS)
REELS = {"tekst_reel", "demo_reel", "stem_video"}
DAGEN = ["ma", "di", "wo", "do", "vr", "za", "zo"]
MAANDEN = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


VOL_BESTAND = WORKSPACE_ROOT / "data" / "instagram_planning_vol.json"  # ["2026-11-23", ...] dagen die Oussama zelf al gevuld heeft


def volle_dagen():
    try:
        return set(json.loads(VOL_BESTAND.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


TIJDEN_BESTAND = WORKSPACE_ROOT / "data" / "instagram_vaste_tijden.json"  # {"17": "14:00"}: post-id met een eigen tijdstip


def vaste_tijden():
    try:
        return {int(k): v for k, v in json.loads(TIJDEN_BESTAND.read_text(encoding="utf-8")).items()}
    except (OSError, ValueError):
        return {}


def vrije_dagen(vandaag=None):
    """De werkdagen (ma-vr) van de komende week, zonder de dagen die al vol staan."""
    vandaag = vandaag or date.today()
    maandag = vandaag + timedelta(days=(7 - vandaag.weekday()) % 7 or 7)
    vol = volle_dagen()
    return maandag, [maandag + timedelta(days=d) for d in range(5) if (maandag + timedelta(days=d)).isoformat() not in vol]


def _thema(soort, map_):
    """Soort onderwerp van een post: de serie uit spec.json (Myth Check, Automation Simplified, ...) of anders het soort."""
    try:
        serie = json.loads((Path(map_) / "spec.json").read_text(encoding="utf-8")).get("serie")
    except (OSError, ValueError, TypeError):
        serie = None
    return (serie or soort or "").strip().upper()


def weekplanning(conn, vandaag=None, bewaar=True):
    """Voorstel voor de komende week (ma t/m vr, PER_DAG posts per dag: beeldpost om TIJD_BEELD, reel om TIJD_REEL).
    Regels (Oussama 24-11), steeds tussen twee posts die direct na elkaar komen, ook over het weekend heen
    (vrijdag 19:00 -> maandag 14:00) en met de vooraf vastgezette posts:
      - nooit dezelfde kleur en nooit allebei blauwig;
      - nooit hetzelfde soort onderwerp (serie/soort) of dezelfde dienst;
      - nooit twee reels op één dag.
    Actualiteit alleen op woensdag. Bouwen in het openbaar gaat voor; verder willekeurig door elkaar.
    Vooraf op een dag (en eventueel tijd, TIJDEN_BESTAND) gezette posts blijven staan. Dagen in VOL_BESTAND slaat hij over.
    Advertenties en story-ideeën hebben geen vaste dag en staan apart."""
    import random
    import wachtrij
    maandag, dagen = vrije_dagen(vandaag)
    kol = "id, soort, status, onderwerp, gepland_op, kleurenset, dienst, map"
    rijen = conn.execute(f"SELECT {kol} FROM instagram_posts WHERE status IN ('concept', 'goedgekeurd') "
                         "AND soort NOT IN ('advertentie', 'story') ORDER BY id").fetchall()
    stories = [r[0] for r in conn.execute("SELECT id FROM instagram_posts WHERE status IN ('concept', 'goedgekeurd') AND soort = 'story'")]
    vol, vaste = volle_dagen(), vaste_tijden()
    is_reel = lambda r: r[1] in REELS  # noqa: E731
    std_tijd = lambda r: vaste.get(r[0]) or (TIJD_REEL if is_reel(r) else TIJD_BEELD)  # noqa: E731
    over = [r for r in rijen if r[4] not in vol]  # door Oussama zelf op een volle dag gezet: blijft daar
    week = {d.isoformat() for d in dagen}
    vast = [r for r in over if r[4] in week]  # vooraf op een dag van deze week gezet (bv. robotvideo di 1-12 14:00)
    over = [r for r in over if r not in vast]
    random.shuffle(over)  # lekker door elkaar (24-11)
    over.sort(key=lambda r: r[1] != "openbaar")  # bouwen in het openbaar (1x per week) gaat voor, verder willekeurig

    # alle tijdstippen van de week op volgorde; vastgezette posts eerst op hun plek
    woensdag = any(d.weekday() == 2 for d in dagen)
    plekken = [(d, t) for d in dagen for t in sorted((TIJD_BEELD, TIJD_REEL))]
    bezet = {}
    for r in vast:
        t = std_tijd(r)
        if (date.fromisoformat(r[4]), t) in bezet:
            t = TIJD_BEELD if t == TIJD_REEL else TIJD_REEL
        bezet[(date.fromisoformat(r[4]), t)] = r

    # de laatste post vóór deze week (meestal vrijdag 19:00): maandag 14:00 moet daar ook van verschillen
    vorige = conn.execute(f"SELECT {kol} FROM instagram_posts WHERE gepland_op < ? AND status != 'overgeslagen' "
                          "AND soort NOT IN ('advertentie', 'story') ORDER BY gepland_op DESC", (maandag.isoformat(),)).fetchall()
    vorige = max((r for r in vorige if r[4] == vorige[0][4]), key=std_tijd) if vorige else None

    def botst(a, b, zwaar=True):
        if a is None or b is None:
            return False
        ka, kb = wachtrij.echte_kleur(a[5]), wachtrij.echte_kleur(b[5])
        if ka == kb or (ka in wachtrij.BLAUWIG and kb in wachtrij.BLAUWIG):
            return True
        if zwaar and (a[1] == b[1] or _thema(a[1], a[7]) == _thema(b[1], b[7]) or (a[6] and a[6] == b[6])):
            return True
        return False

    for i, (dag, tijd) in enumerate(plekken):
        if (dag, tijd) in bezet:
            continue
        vorig = bezet.get(plekken[i - 1]) if i else vorige
        volgend = bezet.get(plekken[i + 1]) if i + 1 < len(plekken) else None
        ander = bezet.get((dag, TIJD_REEL if tijd == TIJD_BEELD else TIJD_BEELD))  # de andere post van dezelfde dag
        wil_reel = (not is_reel(ander)) if ander else tijd == TIJD_REEL
        kies_uit = [r for r in over if r[1] != "actualiteit" or dag.weekday() == 2 or not woensdag]  # actualiteit alleen op woensdag
        if dag.weekday() == 2:  # woensdag: actualiteit eerst (besluit 20-11)
            kies_uit.sort(key=lambda r: r[1] != "actualiteit")
        geen_twee_reels = lambda r: not (ander and is_reel(ander) and is_reel(r))  # noqa: E731
        keuze = None
        for eis in (lambda r: is_reel(r) == wil_reel and not botst(r, vorig) and not botst(r, volgend),
                    lambda r: is_reel(r) == wil_reel and not botst(r, vorig, False) and not botst(r, volgend, False),
                    lambda r: geen_twee_reels(r) and not botst(r, vorig) and not botst(r, volgend),
                    lambda r: is_reel(r) == wil_reel,
                    geen_twee_reels):
            keuze = next((r for r in kies_uit if eis(r)), None)
            if keuze:
                break
        if keuze:
            over.remove(keuze)
            bezet[(dag, tijd)] = keuze

    nieuwe_tijden = dict(vaste)
    regels = []
    for dag in dagen:
        regels.append(f"<b>{DAGEN[dag.weekday()]} {dag.day} {MAANDEN[dag.month - 1]}</b>")
        for tijd in sorted((TIJD_BEELD, TIJD_REEL)):
            r = bezet.get((dag, tijd))
            if not r:
                regels.append(f"   {tijd} · <i>nog leeg: de agent stuurt deze week nog een concept</i>")
                continue
            pid, soort, st, onderwerp = r[:4]
            wacht = " ⏳ <i>nog goedkeuren</i>" if st == "concept" else ""
            regels.append(f"   <b>{tijd}</b> · #{pid} {html.escape(SOORT_LABEL.get(soort, soort))}{wacht}\n      {html.escape((onderwerp or '')[:70])}")
            if bewaar:  # onthouden voor het automatisch afvinken om 20:00 en zodat 'planning' daarna hetzelfde laat zien
                conn.execute("UPDATE instagram_posts SET gepland_op = ? WHERE id = ?", (dag.isoformat(), pid))
                if tijd != std_tijd(r):
                    nieuwe_tijden[pid] = tijd
    if bewaar and nieuwe_tijden != vaste:
        TIJDEN_BESTAND.write_text(json.dumps({str(k): v for k, v in nieuwe_tijden.items()}), encoding="utf-8")
    eind = maandag + timedelta(days=4)
    tekst = f"📅 <b>Weekplanning {maandag.day} {MAANDEN[maandag.month - 1]} t/m {eind.day} {MAANDEN[eind.month - 1]}</b>\n\n" + "\n".join(regels)
    if over:
        tekst += "\n\n<b>Daarna:</b> " + ", ".join(f"#{r[0]}" for r in over) + " (volgende week)"
    if stories:
        tekst += "\n\n📸 <b>Story-ideeën</b> (elke dag mogelijk): " + ", ".join(f"#{s}" for s in stories)
    return tekst + "\n\nDruk na het inplannen of plaatsen op 📤 Geplaatst, dan maakt de agent nieuwe concepten. Typ <b>planning</b> om dit opnieuw te zien."


def afvinken(bot, conn, vandaag=None):
    """Afspraak 20-11: is de geplande dag voorbij (draait elke dag om 20:00), dan geldt de post als geplaatst.
    Klopt dat een keer niet, dan zegt Oussama het en wordt de status teruggezet."""
    vandaag = (vandaag or date.today()).isoformat()
    rijen = conn.execute("SELECT id FROM instagram_posts WHERE gepland_op IS NOT NULL AND gepland_op <= ? "
                         "AND status IN ('concept', 'goedgekeurd') ORDER BY gepland_op, id", (vandaag,)).fetchall()
    for (pid,) in rijen:
        status(conn, pid, "geplaatst")
    return [p for (p,) in rijen]  # stil: geen bericht in Telegram (Oussama wil geen bevestiging, 20-11)


def status(conn, post_id, nieuw):
    conn.execute("UPDATE instagram_posts SET status = ?, bijgewerkt_op = datetime('now') WHERE id = ?", (nieuw, post_id))
    conn.commit()


def plaatsklaar(bot, conn, post_id):
    p = post_laden(conn, post_id)
    soort, paden, _ = bestanden(p)
    bot.tekst(f"✅ <b>Concept #{post_id} goedgekeurd.</b> Hieronder de bestanden in originele kwaliteit. Opslaan op je telefoon, caption kopiëren (tik op het blok), plaatsen.")
    if soort == "video":
        bot.video(paden[0], als_document=True)
    elif soort == "beeld":
        bot.media(paden, als_document=True)
    caption = volledige_caption(p["caption"] or "", p["hashtags"], p["soort"])
    extra = f"\n\n🎵 Muziek toevoegen in de app: {html.escape(p['muziek'])}" if p["muziek"] else ""
    bot.tekst(f"<pre>{html.escape(caption)}</pre>{extra}", [[{"text": "📤 Geplaatst", "callback_data": f"posted:{post_id}"}]])


def transcribeer(bot, file_id):
    sleutel = get_env("OPENAI_API_KEY")
    if not sleutel:
        return None
    info = bot.call("getFile", file_id=file_id)
    audio = requests.get(f"https://api.telegram.org/file/bot{bot.token}/{info['file_path']}", timeout=60).content
    r = requests.post("https://api.openai.com/v1/audio/transcriptions", headers={"Authorization": f"Bearer {sleutel}"},
                      files={"file": ("voice.ogg", audio)}, data={"model": "whisper-1"}, timeout=120)
    return r.json().get("text", "").strip() or None


def luister(bot, conn):
    offset, wacht_op_feedback = None, None
    print("Content-bot luistert. Stoppen met Ctrl+C.")
    while True:
        try:
            updates = bot.call("getUpdates", timeout=50, offset=offset, allowed_updates=["message", "callback_query"])
        except Exception as fout:  # netwerk hapert: even wachten en opnieuw
            print("Fout bij ophalen:", fout)
            time.sleep(5)
            continue
        for u in updates:
            offset = u["update_id"] + 1
            if "callback_query" in u:
                cq = u["callback_query"]
                if str(cq["message"]["chat"]["id"]) != str(bot.chat):
                    continue
                actie, pid = cq["data"].split(":")
                pid = int(pid)
                try:  # een te oude klik (bot lag even plat) mag het verwerken niet tegenhouden
                    bot.call("answerCallbackQuery", callback_query_id=cq["id"])
                    bot.call("editMessageReplyMarkup", chat_id=bot.chat, message_id=cq["message"]["message_id"], reply_markup={"inline_keyboard": []})
                except Exception as fout:
                    print("Knop bevestigen lukte niet (wordt toch verwerkt):", fout)
                if actie == "ok":
                    status(conn, pid, "goedgekeurd")
                    plaatsklaar(bot, conn, pid)
                elif actie == "edit":
                    wacht_op_feedback = pid
                    bot.tekst(f"✏️ Wat moet er anders aan concept #{pid}? Typ het of spreek het in.")
                elif actie == "skip":
                    status(conn, pid, "overgeslagen")
                    bot.tekst(f"❌ Concept #{pid} overgeslagen.")
                elif actie == "posted":
                    status(conn, pid, "geplaatst")
                    bot.tekst(f"📤 Top, concept #{pid} staat als geplaatst genoteerd.")
                print(f"{actie} op post {pid}")
            elif "message" in u:
                msg = u["message"]
                if str(msg["chat"]["id"]) != str(bot.chat):
                    continue
                if msg.get("text", "").startswith("/start"):
                    bot.tekst("Hoi Oussama 👋 Hier komen je Instagram-concepten binnen ter goedkeuring.")
                    continue
                if msg.get("text", "").strip().lower().lstrip("/") == "planning":
                    bot.tekst(weekplanning(conn))
                    conn.commit()
                    continue
                if wacht_op_feedback is None:
                    tekst = msg.get("text") or (transcribeer(bot, msg["voice"]["file_id"]) if msg.get("voice") else None)
                    treffer = re.match(r"^\W*(bouwen in het openbaar|openbaar)\b\W*", tekst or "", re.I)
                    if treffer and len(tekst[treffer.end():].split()) >= 5:
                        verhaal = tekst[treffer.end():].strip()
                        bot.tekst(f"🏗️ Genoteerd voor <b>bouwen in het openbaar</b>:\n<i>{html.escape(verhaal)}</i>\n\nHet concept komt over een paar minuten hier binnen.")
                        print(f"openbaar: {verhaal}")
                        subprocess.Popen([sys.executable, str(WORKSPACE_ROOT / "apps" / "content" / "agent.py"), "openbaar", verhaal], cwd=str(WORKSPACE_ROOT))
                        continue
                    bot.tekst("Druk eerst op ✏️ Aanpassen bij het concept waar je feedback op hebt.\n\n"
                              "Wil je een post voor <b>bouwen in het openbaar</b>? Begin je bericht (getypt of ingesproken) met het woord <b>openbaar</b> en vertel wat je deed en leerde.")
                    continue
                tekst = msg.get("text") or (transcribeer(bot, msg["voice"]["file_id"]) if msg.get("voice") else None)
                if not tekst:
                    bot.tekst("Dat kon ik niet lezen. Probeer het als tekst?")
                    continue
                conn.execute("INSERT INTO instagram_feedback (post_id, tekst) VALUES (?, ?)", (wacht_op_feedback, tekst))
                status(conn, wacht_op_feedback, "concept")
                conn.commit()
                bot.tekst(f"👍 Genoteerd voor concept #{wacht_op_feedback}: <i>{html.escape(tekst)}</i>\nJe krijgt de aangepaste versie zo terug.")
                print(f"feedback op post {wacht_op_feedback}: {tekst}")
                wacht_op_feedback = None
                # de agent maakt meteen een nieuwe versie (los proces, zodat de bot blijft luisteren)
                subprocess.Popen([sys.executable, str(WORKSPACE_ROOT / "apps" / "content" / "agent.py"), "verwerk"], cwd=str(WORKSPACE_ROOT))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("test")
    s = sub.add_parser("stuur")
    s.add_argument("id", type=int)
    sub.add_parser("luister")
    sub.add_parser("afvinken", help="posts waarvan de geplande dag voorbij is op geplaatst zetten (elke dag 20:00)")
    sub.add_parser("planning", help="weekplanning naar Telegram (zondag 09:00 via instagram-planning.timer)")
    args = ap.parse_args()
    bot, conn = Bot(), verbind()
    if args.cmd == "test":
        bot.tekst("✅ Content-bot verbonden. Hier komen je Instagram-concepten binnen.")
        print("Testbericht verstuurd.")
    elif args.cmd == "stuur":
        stuur(bot, conn, args.id)
        print(f"Concept {args.id} verstuurd.")
    elif args.cmd == "luister":
        luister(bot, conn)
    elif args.cmd == "planning":
        bot.tekst(weekplanning(conn))
        conn.commit()
    elif args.cmd == "afvinken":
        print("Op geplaatst gezet:", afvinken(bot, conn))
        if date.today().weekday() == 3:  # donderdag 20:00: vraag om het verhaal voor de wekelijkse bouwen-in-het-openbaar-post (24-11)
            bot.tekst("🏗️ <b>Bouwen in het openbaar</b>\n\nWat deed je deze week voor je bedrijf, en wat leerde je ervan? "
                      "Spreek een minuutje in (of typ het) en begin met het woord <b>openbaar</b>. Bijvoorbeeld:\n"
                      "<i>openbaar: deze week 40 kantoren gebeld, 3 gesprekken, geleerd dat ...</i>\n\n"
                      "Het concept staat dan zaterdag klaar voor de weekplanning.")
        print("Weekplanning verstuurd.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
