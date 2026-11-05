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
import subprocess
import sys
import time
from pathlib import Path

import requests

HIER = Path(__file__).resolve().parent
WORKSPACE_ROOT = HIER.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
sys.path.insert(0, str(HIER))
from config import get_env  # noqa: E402
from wachtrij import verbind, volledige_caption  # noqa: E402

SOORT_LABEL = {"carrousel": "Carrousel", "kaart": "Losse afbeelding", "fork": "The Fork", "tekst_reel": "Reel · bewegende tekst",
               "demo_reel": "Reel · demo", "actualiteit": "Actualiteit", "story": "Story-tekst"}


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
    if p["muziek"]:
        delen.append(f"🎵 <b>Muziek:</b> {html.escape(p['muziek'])}")
    if p["bronnen"]:
        delen.append("🔎 <b>Bronnen (zelf nog checken):</b>\n" + "\n".join(f"• {html.escape(b)}" for b in p["bronnen"]))
    bot.tekst("\n\n".join(delen), [[{"text": "✅ Goedkeuren", "callback_data": f"ok:{post_id}"},
                                     {"text": "✏️ Aanpassen", "callback_data": f"edit:{post_id}"},
                                     {"text": "❌ Overslaan", "callback_data": f"skip:{post_id}"}]])


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
                bot.call("answerCallbackQuery", callback_query_id=cq["id"])
                bot.call("editMessageReplyMarkup", chat_id=bot.chat, message_id=cq["message"]["message_id"], reply_markup={"inline_keyboard": []})
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
                if wacht_op_feedback is None:
                    bot.tekst("Druk eerst op ✏️ Aanpassen bij het concept waar je feedback op hebt.")
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


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
