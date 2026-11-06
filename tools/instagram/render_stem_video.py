"""
Instagram — video met voice-over in "Typer"-stijl (@insightance.ai)

Elke beat = één zin die Eric inspreekt (tools/instagram/stem.py) + één scène
uit tools/instagram/video/typer.html (getal, mandje, mails, meldingen, eind).
De scène duurt zo lang als de zin plus een korte adempauze, dus beeld en stem
lopen altijd gelijk. Ondertitels lopen woord voor woord mee. Donkere en lichte
scènes wisselen met een harde cut. Geen gezicht, geen muziek (Oussama voegt
muziek zelf toe in Instagram).

Frames worden een voor een gerenderd op het exacte tijdstip (scherp, vast
tempo) en met ffmpeg samengevoegd met de stem. Levert reel.mp4 (1080x1920,
30 fps, met geluid) en cover.jpg.

Spec:
    {
      "onderwerp": "Cart recovery flow",
      "stem": "eric",
      "beats": [
        {"zegt": "Seven out of ten shoppers leave their cart behind.",
         "scene": {"type": "getal", "tot": 70, "suf": "%", "tekst": "of online carts get abandoned.",
                   "bron": "Baymard Institute, average of 50 studies"}},
        ...
      ]
    }

Gebruik (CLI):
    python tools/instagram/render_stem_video.py spec.json [--uit map/]
Kost ElevenLabs-tegoed alleen voor zinnen die nog niet in de cache staan.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_carrousel import TMP  # noqa: E402
from stem import inspreken  # noqa: E402

PAGINA = Path(__file__).resolve().parent / "video" / "typer.html"
FPS = 30
BEGIN = 0.3      # stilte voor de eerste zin
ADEM = 0.45      # pauze tussen zinnen
STAART = 1.2     # eindkaart blijft nog even staan
MAX_WOORDEN = 4  # woorden per ondertitelblok


def tijdlijn(spec):
    """Spreekt elke zin in en zet scènes, stem en ondertitels op één tijdlijn."""
    scenes, audio, captions, t = [], [], [], 0.0
    for n, beat in enumerate(spec["beats"]):
        mp3, woorden = inspreken(beat["zegt"], spec.get("stem", "eric"))
        start_stem = t + (BEGIN if n == 0 else 0)
        lengte = woorden[-1]["e"]
        dur = (start_stem - t) + lengte + ADEM + (STAART if n == len(spec["beats"]) - 1 else 0)
        dur = max(dur, beat.get("min", 0))
        # woordtijden binnen de scène, zodat beeld op het gesproken woord kan verschijnen
        w_scene = [{"w": w["w"], "s": start_stem - t + w["s"]} for w in woorden]
        scenes.append({**beat["scene"], "start": t, "dur": dur, "woorden": w_scene})
        audio.append((mp3, start_stem))
        blokken = -(-len(woorden) // MAX_WOORDEN)
        per = -(-len(woorden) // blokken)  # gelijk verdelen, geen los woord aan het eind
        blok = []
        for w in woorden:  # nieuw blok na `per` woorden of na het eind van een zin
            blok.append({"w": w["w"], "s": start_stem + w["s"], "e": start_stem + w["e"]})
            if len(blok) == per or w["w"][-1] in ".?!":
                captions.append({"s": blok[0]["s"], "e": blok[-1]["e"], "w": blok})
                blok = []
        if blok:
            captions.append({"s": blok[0]["s"], "e": blok[-1]["e"], "w": blok})
        t += dur
    return {"scenes": scenes, "captions": captions}, audio, t


def render(spec, uit):
    uit.mkdir(parents=True, exist_ok=True)
    frames = uit / "_frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    lijn, audio, totaal = tijdlijn(spec)
    cover_t = lijn["scenes"][0]["dur"] - ADEM
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(PAGINA.resolve().as_uri())
        pg.evaluate("document.fonts.ready")
        pg.evaluate("(s) => window.__laad(s)", lijn)
        for n in range(int(totaal * FPS)):
            pg.evaluate(f"window.__zet({n / FPS:.4f})")
            pg.screenshot(path=str(frames / f"f{n:05d}.png"))
        pg.evaluate(f"window.__zet({cover_t:.4f})")
        pg.evaluate("document.getElementById('cap').innerHTML = ''")
        pg.screenshot(path=str(uit / "cover.jpg"), type="jpeg", quality=95)
        browser.close()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%05d.png")]
    for mp3, _ in audio:
        cmd += ["-i", str(mp3)]
    mix = "".join(f"[{i + 1}:a]adelay={int(s * 1000)}:all=1[a{i}];" for i, (_, s) in enumerate(audio))
    mix += "".join(f"[a{i}]" for i in range(len(audio))) + f"amix=inputs={len(audio)}:normalize=0:duration=longest[a]"
    video = uit / "reel.mp4"
    cmd += ["-filter_complex", mix, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{totaal:.2f}", "-movflags", "+faststart", str(video)]
    subprocess.run(cmd, check=True)
    shutil.rmtree(frames)
    return video


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--uit")
    args = ap.parse_args()
    spec_pad = Path(args.spec)
    uit = (Path(args.uit) if args.uit else TMP / spec_pad.stem).resolve()
    print(render(json.loads(spec_pad.read_text(encoding="utf-8")), uit))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
