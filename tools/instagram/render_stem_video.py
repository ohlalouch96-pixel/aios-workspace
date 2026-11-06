"""
Instagram — video met voice-over in "Typer"-stijl (@insightance.ai)

Elke beat = één zin + één scène uit tools/instagram/video/typer.html (getal,
mandje, mails, meldingen, eind). Eric (tools/instagram/stem.py) spreekt het
hele script in één keer in, zodat het als één verhaal klinkt; de scènes worden
op zijn woordtijden geknipt en beeld verschijnt op het gesproken woord.
Na elke zin ±1 s stilte waarin het beeld blijft staan (per beat aan te passen met "pauze").
Geen lopende ondertitels (aan te zetten met "ondertitels": true). "kleurenset" volgt de kleurregel.
Regel: tekst in beeld volgt dezelfde woordvolgorde als wat Eric zegt. Ondertitels lopen woord voor woord mee. Donkere en lichte
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
VOORLOOP = 0.25  # nieuwe scène verschijnt net voordat het eerste woord klinkt
STAART = 1.4     # eindkaart blijft nog even staan
MAX_WOORDEN = 4  # woorden per ondertitelblok
PAUZE = 1.0      # pauze-tag na elke zin (ElevenLabs maakt er in de praktijk ±0,6 s van)
RUST = 0.7       # extra stilte die we zelf tussen de zinnen leggen: beeld blijft staan zodat je het kunt lezen

# Kleurensets voor video, zelfde namen als de kleurregel (wachtrij.kies_kleur): navy is de basis.
# donker/dfg = donkere scène, licht/lfg = lichte scène, acc = accent op donker, mark = markeerstift op licht.
VIDEO_KLEUREN = {
    "navy":  dict(donker="#0F2547", dfg="#FFFFFF", acc="#7FA8FF", accfg="#0F2547", licht="#F5F8FC", lfg="#17345F", mark="#C9DAFF", pos="#2F9E6B", kaart="#17345F", rand="#24477A", grijs="#8FA3C2"),
    "zwart": dict(donker="#0A0A0A", dfg="#FFFFFF", acc="#D4F53C", accfg="#0A0A0A", licht="#F4F3EE", lfg="#0A0A0A", mark="#D4F53C", pos="#5BB82E", kaart="#1A1A1A", rand="#2A2A2A", grijs="#8A8A85"),
    "blauw": dict(donker="#1F5EFF", dfg="#FFFFFF", acc="#FFD84D", accfg="#17345F", licht="#FFFFFF", lfg="#17345F", mark="#FFEFA8", pos="#2F9E6B", kaart="#1A4FDB", rand="#3D74FF", grijs="#C7D6FF"),
    "groen": dict(donker="#153B2E", dfg="#FFFFFF", acc="#B6F36B", accfg="#153B2E", licht="#F2F6EE", lfg="#153B2E", mark="#DDF7BD", pos="#3E9B4F", kaart="#1D4A3A", rand="#2A5C49", grijs="#9DB5A8"),
    "creme": dict(donker="#2B2420", dfg="#F3EDE2", acc="#F0784A", accfg="#2B2420", licht="#F3EDE2", lfg="#2B2420", mark="#FFD9C9", pos="#3E8E5B", kaart="#3A312B", rand="#4A3F37", grijs="#A89A8C"),
    "rood":  dict(donker="#7E1F18", dfg="#FFFFFF", acc="#FFC9B8", accfg="#7E1F18", licht="#FFF7F3", lfg="#2A1512", mark="#FFD2C4", pos="#3E8E5B", kaart="#93281F", rand="#A8362C", grijs="#E4AFA6"),
    "paars": dict(donker="#2D1B5A", dfg="#FFFFFF", acc="#F59BD0", accfg="#2D1B5A", licht="#F7F4FD", lfg="#2D1B5A", mark="#F6CDE6", pos="#3E9B6B", kaart="#3A2670", rand="#4B3586", grijs="#B3A6D6"),
}


def is_woord(w):
    return not any(c in w for c in "<>=")  # pauze-tags (<break time="0.4s" />) tellen niet mee


def ondertitels(woorden, start):
    """Woorden in blokken van max. 4, gelijk verdeeld, nieuw blok na het eind van een zin."""
    blokken = -(-len(woorden) // MAX_WOORDEN)
    per = -(-len(woorden) // blokken)
    uit, blok = [], []
    for w in woorden:
        blok.append({"w": w["w"], "s": start + w["s"], "e": start + w["e"]})
        if len(blok) == per or w["w"][-1] in ".?!":
            uit.append({"s": blok[0]["s"], "e": blok[-1]["e"], "w": blok})
            blok = []
    if blok:
        uit.append({"s": blok[0]["s"], "e": blok[-1]["e"], "w": blok})
    return uit


def tijdlijn(spec):
    """Spreekt het hele script in één keer in (doorlopende intonatie, geen herstart per zin)
    en knipt de scènes op de woordtijden: elke scène begint net voor haar eerste woord."""
    beats = spec["beats"]
    delen = []
    for beat in beats:
        delen.append(beat["zegt"])
        if beat is not beats[-1]:
            delen.append(f'<break time="{beat.get("pauze", PAUZE)}s" />')
    mp3, alle = inspreken(" ".join(delen), spec.get("stem", "eric"))
    alle = [w for w in alle if is_woord(w["w"])]
    per_beat, i = [], 0
    for beat in beats:
        n = len(beat["zegt"].split())
        per_beat.append(alle[i:i + n])
        i += n
    # Eén opname, op de stiltes tussen de zinnen in stukken gezet, met extra rust ertussen.
    knip = [0.0] + [(a[-1]["e"] + b[0]["s"]) / 2 for a, b in zip(per_beat, per_beat[1:])] + [alle[-1]["e"] + 0.3]
    stukken = [(mp3, knip[n], knip[n + 1], BEGIN + knip[n] + n * RUST) for n in range(len(beats))]
    per_beat = [[{**w, "s": w["s"] + n * RUST, "e": w["e"] + n * RUST} for w in ws] for n, ws in enumerate(per_beat)]
    starts = [0.0] + [BEGIN + w[0]["s"] - VOORLOOP for w in per_beat[1:]]
    totaal = BEGIN + per_beat[-1][-1]["e"] + STAART
    scenes, captions = [], []
    for n, (beat, woorden) in enumerate(zip(beats, per_beat)):
        start = starts[n]
        eind = starts[n + 1] if n + 1 < len(beats) else totaal
        w_scene = [{"w": w["w"], "s": BEGIN + w["s"] - start} for w in woorden]
        scenes.append({**beat["scene"], "start": start, "dur": eind - start, "woorden": w_scene})
        captions += ondertitels(woorden, BEGIN)
    lijn = {"scenes": scenes, "kleuren": VIDEO_KLEUREN[spec.get("kleurenset", "navy")]}
    if spec.get("ondertitels"):  # standaard uit: de teksten in beeld vertellen het verhaal al (besluit 06-11)
        lijn["captions"] = captions
    return lijn, stukken, totaal


def render(spec, uit):
    uit.mkdir(parents=True, exist_ok=True)
    frames = uit / "_frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    lijn, audio, totaal = tijdlijn(spec)
    cover_t = lijn["scenes"][0]["dur"] - 0.3
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
    for mp3, *_ in audio:
        cmd += ["-i", str(mp3)]
    mix = "".join(f"[{i + 1}:a]atrim={van:.3f}:{tot:.3f},asetpts=PTS-STARTPTS,adelay={int(op * 1000)}:all=1[a{i}];"
                  for i, (_, van, tot, op) in enumerate(audio))
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
