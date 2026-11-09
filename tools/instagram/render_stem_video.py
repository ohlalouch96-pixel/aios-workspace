"""
Instagram — video met voice-over in "Typer"-stijl (@insightance.ai)

Elke beat = één zin + één scène uit tools/instagram/video/typer.html (getal,
mandje, mails, meldingen, eind). Eric (tools/instagram/stem.py) spreekt het
hele script in één keer in, zodat het als één verhaal klinkt; de scènes worden
op zijn woordtijden geknipt en beeld verschijnt op het gesproken woord.

Pauzes: elke pauze tussen twee zinnen wordt precies PAUZE_DOEL lang gemaakt door
alleen echte stilte (onder -60 dB) korter of langer te maken. Alles wat Eric
zelf laat horen, zoals het uitklinken van een woord of een ademhaling die hij uit
zichzelf neemt, blijft staan. Nooit zelf een ademhaling toevoegen: een vaste
ademhaling voor elke zin klinkt nep (06-11). Zo blijft het beeld na elke zin
1,5 s staan en klinkt het als één doorlopend gesprek.

Geen lopende ondertitels (aan te zetten met "ondertitels": true). "kleurenset"
volgt de kleurregel. Geen gezicht, geen muziek (Oussama voegt die zelf toe).
Voor het renderen controleert de tool de regels uit workflows/instagram_content.md
(woorden per zin, rust na elke zin, minimale scèneduur) en stopt bij een fout.

Frames worden een voor een gerenderd op het exacte tijdstip (scherp, vast
tempo) en met ffmpeg samengevoegd met de stem. Levert reel.mp4 (1080x1920,
30 fps, met geluid) en cover.jpg.

Spec:
    {
      "onderwerp": "Cart recovery flow", "stem": "eric_v3", "kleurenset": "navy",
      "beats": [
        {"zegt": "Seven out of ten shoppers leave their cart behind.",
         "uitspraak": "[confident] Seven out of ten shoppers leave their cart behind.",
         "scene": {"type": "getal", "tot": 70, "suf": "%", "tekst": "of online carts get abandoned.",
                   "bron": "Baymard Institute, average of 50 studies"}},
        ...
      ]
    }
"zegt" = de woorden (voor timing en controle), "uitspraak" = optioneel dezelfde zin met regie-tags.
Andere opname voor een zin: in de spec "opnames": {"a": {"seed": 21, "uitspraak": {"1": "[confident] ..."}}}
en bij die beat "opname": "a". De tool maakt dan een extra opname van het hele script (zelfde samenhang,
met de aangepaste uitspraak per beatnummer) en neemt alleen die zinnen eruit; er wordt alleen in de stilte
tussen zinnen geknipt. Nooit losse zinnen apart laten inspreken.
Gratis bijstellen van een bestaande opname (kost geen ElevenLabs-tegoed), per beat:
    "stem": {"tempo": 1.1, "volume_db": 3}            hele zin iets sneller / harder
    "stem": {"volume_db": 1.2, "vanaf": "while"}      alleen vanaf dat woord harder (toon: zie bewerk())
    "inademing": true                                  één korte, zachte inademing vlak voor deze zin
                                                       (Erics eigen inademing uit de goedgekeurde versie
                                                       van 06-11; spaarzaam gebruiken, nooit voor elke zin)
In de spec "tempo": 1.1 = de hele stem 10% sneller (gratis, toonhoogte blijft gelijk).
Alleen de stem beluisteren, zonder video: --alleen-stem (levert stem.mp3).

Gebruik (CLI):
    python tools/instagram/render_stem_video.py spec.json [--uit map/]
Kost ElevenLabs-tegoed alleen voor een script dat nog niet in de cache staat.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_carrousel import TMP  # noqa: E402
from stem import STEMMEN, inspreken  # noqa: E402

PAGINA = Path(__file__).resolve().parent / "video" / "typer.html"
INADEMING = Path(__file__).resolve().parent / "video" / "inademing_eric.wav"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 30
SR = 44100
BEGIN = 0.3        # stilte voor de eerste zin
VOORLOOP = 0.25    # nieuwe scène verschijnt net voordat het eerste woord klinkt
STAART = 1.4       # eindkaart blijft nog even staan
MAX_WOORDEN = 4    # woorden per ondertitelblok
PAUZE_DOEL = 1.75  # stilte tussen twee zinnen => beeld blijft 1,5 s staan (zoals de versie die Oussama goed vond)
VOORKLANK = 0.06   # zin begint net voor de eerste klank (zachte inzet blijft heel)
MIN_RUST = 1.5     # regel: beeld blijft na het laatste woord minstens zo lang staan
MIN_SCENE = 3.0    # regel: elke scène minstens zo lang in beeld

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
    # pauze- en regie-tags (<break .../>, [confident]) en losse puntjes tellen niet mee
    return not any(c in w for c in "<>=[]") and w.strip(".") != ""


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


def script(spec, naam=None):
    beats, stem = spec["beats"], spec.get("stem", "eric")
    anders = spec.get("opnames", {}).get(naam, {}).get("uitspraak", {}) if naam else {}
    zinnen = [anders.get(str(n)) or b.get("uitspraak", b["zegt"]) for n, b in enumerate(beats)]
    if STEMMEN[stem]["model_id"] == "eleven_v3":  # v3 kent geen <break>; lengte wordt later gelijkgetrokken
        return " [long pause] ".join(zinnen)
    return " ".join(z + (' <break time="1.0s" />' if n < len(zinnen) - 1 else "") for n, z in enumerate(zinnen))


def pcm(pad):
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(pad), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def sec(t):
    return int(round(t * SR))


def niveau(x, van, tot):
    """Per blok van 20 ms het geluidsniveau in dB."""
    blok, stuk = sec(0.02), x[sec(van):sec(tot)]
    return [20 * np.log10(np.sqrt(np.mean(stuk[k:k + blok] ** 2)) + 1e-9) for k in range(0, len(stuk) - blok, blok)]


def opname(spec, naam=None):
    """Het hele script in één keer ingesproken (naam: een extra opname uit spec["opnames"]).
    Geeft (audio, woorden per beat) en controleert of het aantal woorden klopt."""
    beats = spec["beats"]
    seed = spec["opnames"][naam].get("seed") if naam else spec.get("seed")
    mp3, alle = inspreken(script(spec, naam), spec.get("stem", "eric"), seed=seed)
    alle = [w for w in alle if is_woord(w["w"])]
    verwacht = sum(len(b["zegt"].split()) for b in beats)
    if len(alle) != verwacht:
        raise SystemExit(f"Controle: {len(alle)} woorden gehoord, {verwacht} verwacht. Klopt de uitspraak met 'zegt'?")
    per_beat, i = [], 0
    for beat in beats:
        n = len(beat["zegt"].split())
        per_beat.append(alle[i:i + n])
        i += n
    return pcm(mp3), per_beat


def zinnen(x, per_beat):
    """Knipt een opname in zinnen op het echte geluid (de woordtijden van v3 lopen uit).
    Per zin: (audio van net voor de eerste klank tot waar de stem stopt, woorden relatief aan dat begin)."""
    uit, vorig_eind = [], 0.0
    for n, ws in enumerate(per_beat):
        zoek = niveau(x, vorig_eind, ws[0]["s"] + 0.6)
        klank = vorig_eind + next((k for k, d in enumerate(zoek) if d > -30), 0) * 0.02
        begin = max(klank - VOORKLANK, vorig_eind)
        delta = klank - ws[0]["s"]
        tot = (per_beat[n + 1][0]["s"] + 0.6) if n + 1 < len(per_beat) else len(x) / SR
        van = max(ws[-1]["s"] + delta - 0.2, klank)
        l, nodig = [d > -50 for d in niveau(x, van, tot)], int(0.3 / 0.02)
        k = next((k for k in range(len(l) - nodig) if not any(l[k:k + nodig])), None)
        eind = van + k * 0.02 if k is not None else tot
        woorden = [{**w, "s": w["s"] + delta - begin, "e": w["e"] + delta - begin} for w in ws]
        woorden[-1]["e"] = eind - begin
        uit.append((x[sec(begin):sec(eind)].copy(), woorden))
        vorig_eind = eind
    return uit


def bewerk(audio, woorden, bew, n):
    """Gratis bijstellen van één zin: tempo, volume en toonhoogte (eventueel pas vanaf een woord).
    toon 1.1 = 10% hoger, zonder dat het tempo verandert. LET OP: dit verschuift ook de klankkleur; al bij
    14% klonk het als een andere stem (09-11). Liever een andere opname kiezen; toon hooguit 1.03."""
    tempo, vol, toon = bew.get("tempo", 1.0), bew.get("volume_db", 0.0), bew.get("toon", 1.0)
    filt = ",".join(f for f in [f"asetrate={int(SR * toon)},aresample={SR},atempo={1 / toon:.5f}" if toon != 1.0 else "",
                                f"atempo={tempo}" if tempo != 1.0 else "", f"volume={vol}dB" if vol else ""] if f)
    if not filt:
        return audio, woorden
    vanaf = 0.0
    woord = bew.get("vanaf") or bew.get("volume_vanaf")
    if woord:
        doel = next((w for w in woorden if w["w"].lower().strip(".,?!") == woord), None)
        if doel is None:
            raise SystemExit(f"Controle: woord '{woord}' niet gevonden in zin {n + 1}")
        l = [d > -50 for d in niveau(audio, 0, doel["s"] + 0.3)]
        stil = [k for k in range(len(l) - 5) if not any(l[k:k + 5])]  # laatste korte stilte voor dat woord
        vanaf = (stil[-1] + 5) * 0.02 if stil else 0.0
    ruw = audio[sec(vanaf):]
    nieuw = np.frombuffer(subprocess.run([FFMPEG, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                                          "-af", filt, "-f", "f32le", "-"], input=ruw.tobytes(), capture_output=True,
                                         check=True).stdout, dtype=np.float32)
    rek = len(nieuw) / max(len(ruw), 1)
    schaal = lambda t: t if t < vanaf else vanaf + (t - vanaf) * rek  # noqa: E731
    return (np.concatenate([audio[:sec(vanaf)], nieuw]),
            [{**w, "s": schaal(w["s"]), "e": schaal(w["e"])} for w in woorden])


def monteer(stukken, beats, uit_wav):
    """Zinnen achter elkaar met tussen elke zin precies PAUZE_DOEL stilte (gemeten van waar de stem
    stopt tot de eerste klank van de volgende zin). Eventueel één inademing vlak voor een zin."""
    inademing = pcm(INADEMING) if any(b.get("inademing") for b in beats) else None
    delen, per_beat, t = [], [], 0.0
    for n, (audio, woorden) in enumerate(stukken):
        if n:
            gat = np.zeros(sec(PAUZE_DOEL - VOORKLANK), dtype=np.float32)
            if inademing is not None and beats[n].get("inademing"):
                k = min(len(inademing), len(gat))
                gat[len(gat) - k:] += inademing[len(inademing) - k:]
            delen.append(gat)
            t += len(gat) / SR
        delen.append(audio)
        per_beat.append([{**w, "s": w["s"] + t, "e": w["e"] + t} for w in woorden])
        t += len(audio) / SR
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(uit_wav)],
                   input=np.concatenate(delen).tobytes(), check=True)
    return per_beat


def tijdlijn(spec, uit):
    """Spreekt het hele script in één keer in (doorlopende intonatie, geen herstart per zin), knipt het
    op het echte geluid in zinnen, zet ze met gelijke pauzes achter elkaar en knipt de scènes op de
    woordtijden. Beats met "opname": "<naam>" komen uit een extra opname van hetzelfde hele script."""
    beats = spec["beats"]
    stukken = zinnen(*opname(spec))
    for naam in {b["opname"] for b in beats if b.get("opname")}:
        extra = zinnen(*opname(spec, naam))
        stukken = [extra[n] if b.get("opname") == naam else stukken[n] for n, b in enumerate(beats)]
    tempo = spec.get("tempo", 1.0)  # hele stem sneller/langzamer (toonhoogte blijft gelijk), pauzes blijven PAUZE_DOEL
    stukken = [bewerk(a, w, {**b.get("stem", {}), "tempo": b.get("stem", {}).get("tempo", 1.0) * tempo}, n)
               for n, ((a, w), b) in enumerate(zip(stukken, beats))]
    wav = uit / "stem.wav"
    per_beat = monteer(stukken, beats, wav)
    starts = [0.0] + [BEGIN + w[0]["s"] - VOORLOOP for w in per_beat[1:]]
    totaal = BEGIN + per_beat[-1][-1]["e"] + STAART
    scenes, captions = [], []
    for n, (beat, woorden) in enumerate(zip(beats, per_beat)):
        start = starts[n]
        eind = starts[n + 1] if n + 1 < len(beats) else totaal
        w_scene = [{"w": w["w"], "s": BEGIN + w["s"] - start, "e": BEGIN + w["e"] - start} for w in woorden]
        scenes.append({**beat["scene"], "start": start, "dur": eind - start, "woorden": w_scene})
        captions += ondertitels(woorden, BEGIN)
    lijn = {"scenes": scenes, "kleuren": VIDEO_KLEUREN[spec.get("kleurenset", "navy")]}
    if spec.get("ondertitels"):  # standaard uit: de teksten in beeld vertellen het verhaal al (besluit 06-11)
        lijn["captions"] = captions
    return lijn, [(wav, 0.0, totaal, BEGIN)], totaal


def controleer(lijn):
    """Regels uit de workflow: rust na elke zin en minimale scèneduur. Stopt bij een fout."""
    fouten = []
    print(f"{'scène':<10} {'in beeld':>9} {'rust na laatste woord':>22}")
    for n, sc in enumerate(lijn["scenes"]):
        rust = sc["dur"] - sc["woorden"][-1]["e"]
        print(f"{sc['type']:<10} {sc['dur']:>8.2f}s {rust:>21.2f}s")
        if sc["dur"] < MIN_SCENE:
            fouten.append(f"{sc['type']}: {sc['dur']:.2f}s in beeld, minimaal {MIN_SCENE}s")
        if n < len(lijn["scenes"]) - 1 and rust < MIN_RUST - 0.02:
            fouten.append(f"{sc['type']}: rust {rust:.2f}s, minimaal {MIN_RUST}s")
    if fouten:
        raise SystemExit("Controle mislukt:\n  " + "\n  ".join(fouten))
    print("Controle: alle regels in orde.")


def render(spec, uit):
    uit.mkdir(parents=True, exist_ok=True)
    frames = uit / "_frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    lijn, audio, totaal = tijdlijn(spec, uit)
    controleer(lijn)
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
    (uit / "stem.wav").unlink(missing_ok=True)
    controleblad(video, lijn, uit / "controle.png")
    return video


def controleblad(video, lijn, pad):
    """Eén overzicht om zelf te bekijken voor Oussama de video ziet: per scène (kolom) drie momenten
    (rij): net na het eerste woord, midden in de zin, en tijdens de rust na de zin."""
    tmp = pad.parent / "_controle"
    tmp.mkdir(exist_ok=True)
    rijen = []
    for r, moment in enumerate(["begin", "midden", "rust"]):
        cellen = []
        for k, sc in enumerate(lijn["scenes"]):
            w = sc["woorden"]
            t = sc["start"] + {"begin": w[0]["s"] + 0.6, "midden": w[len(w) // 2]["s"] + 0.4, "rust": w[-1]["e"] + 1.0}[moment]
            cel = tmp / f"{r}_{k}.png"
            subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", "scale=270:-1", str(cel)], check=True)
            cellen.append(cel)
        rij = tmp / f"rij{r}.png"
        subprocess.run([FFMPEG, "-y", "-v", "error", *sum((["-i", str(c)] for c in cellen), []),
                        "-filter_complex", f"hstack={len(cellen)}", str(rij)], check=True)
        rijen.append(rij)
    subprocess.run([FFMPEG, "-y", "-v", "error", *sum((["-i", str(x)] for x in rijen), []),
                    "-filter_complex", f"vstack={len(rijen)}", str(pad)], check=True)
    shutil.rmtree(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--uit")
    ap.add_argument("--alleen-stem", action="store_true", help="alleen stem.mp3 maken om te beluisteren (geen video)")
    args = ap.parse_args()
    spec_pad = Path(args.spec)
    uit = (Path(args.uit) if args.uit else TMP / spec_pad.stem).resolve()
    spec = json.loads(spec_pad.read_text(encoding="utf-8"))
    if args.alleen_stem:
        uit.mkdir(parents=True, exist_ok=True)
        lijn, _, _ = tijdlijn(spec, uit)
        controleer(lijn)
        mp3 = uit / "stem.mp3"
        subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(uit / "stem.wav"), "-af", f"adelay={int(BEGIN * 1000)}",
                        "-b:a", "192k", str(mp3)], check=True)
        (uit / "stem.wav").unlink()
        print(mp3)
    else:
        print(render(spec, uit))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
