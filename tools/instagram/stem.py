"""
Instagram — voice-over via ElevenLabs (@insightance.ai)

Spreekt een zin in met de vaste merkstem en geeft de timing per letter terug
(voor ondertitels en het gelijklopen van beeld en stem). Elke tekst wordt
bewaard in .tmp/instagram/stem_cache/, dus opnieuw renderen kost geen tegoed.

Stem (besluit 06-11): Eric, iets sneller (speed 1.1), eleven_multilingual_v2.
Meer pit na feedback: stability 0.25, style 0.45 (gekozen uit 4 proeven, 06-11).
Oussama's eigen stem is getest en afgewezen.

Gebruik (CLI):
    python tools/instagram/stem.py "Seven out of ten shoppers leave their cart behind."
    python tools/instagram/stem.py --tegoed
"""

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

import requests

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE = WORKSPACE_ROOT / ".tmp" / "instagram" / "stem_cache"
API = "https://api.elevenlabs.io/v1"

STEMMEN = {
    "eric": {"voice_id": "cjVigY5qzO86Huf0OWal", "model_id": "eleven_multilingual_v2",
             "voice_settings": {"stability": 0.25, "similarity_boost": 0.75, "style": 0.45, "speed": 1.1}},
    # Nieuwste model, regie per zin met tags als [confident], [understated]. Stability 0.0 (proef D, 06-11):
    # levendigste intonatie en Eric ademt zelf af en toe. Kent geen <break>-tags; pauzes via " [long pause] ",
    # daarna gelijkgetrokken in render_stem_video.py.
    "eric_v3": {"voice_id": "cjVigY5qzO86Huf0OWal", "model_id": "eleven_v3",
                "voice_settings": {"stability": 0.0, "similarity_boost": 0.75, "style": 0.45, "speed": 1.1}},
}


def env(naam):
    for regel in (WORKSPACE_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if regel.startswith(naam + "="):
            return regel.split("=", 1)[1].strip()
    return None


def sleutel():
    for regel in (WORKSPACE_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if regel.startswith("ELEVENLABS_API_KEY="):
            return regel.split("=", 1)[1].strip()
    raise SystemExit("ELEVENLABS_API_KEY ontbreekt in .env")


def inspreken(tekst, stem="eric", settings=None, model=None, seed=None):
    """Geeft (pad naar mp3, woorden) terug. Woorden: [{"w", "s", "e"}] in seconden.
    settings: optioneel andere voice_settings (bv. om intonatie te testen)."""
    instelling = STEMMEN[stem]
    if settings:
        instelling = {**instelling, "voice_settings": {**instelling["voice_settings"], **settings}}
    if model:
        instelling = {**instelling, "model_id": model}
    if seed is not None:
        instelling = {**instelling, "seed": seed}
    code = hashlib.sha1(json.dumps([tekst, instelling], sort_keys=True).encode()).hexdigest()[:16]
    mp3, meta = CACHE / f"{code}.mp3", CACHE / f"{code}.json"
    if not (mp3.exists() and meta.exists()):
        CACHE.mkdir(parents=True, exist_ok=True)
        r = requests.post(f"{API}/text-to-speech/{instelling['voice_id']}/with-timestamps",
                          headers={"xi-api-key": sleutel()},
                          json={"text": tekst, "model_id": instelling["model_id"], "voice_settings": instelling["voice_settings"],
                                **({"seed": instelling["seed"]} if "seed" in instelling else {})},
                          timeout=120)
        r.raise_for_status()
        d = r.json()
        mp3.write_bytes(base64.b64decode(d["audio_base64"]))
        meta.write_text(json.dumps(d["alignment"]), encoding="utf-8")
    return mp3, woorden(json.loads(meta.read_text(encoding="utf-8")))


def woorden(al):
    uit, huidig = [], None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if huidig:
                uit.append(huidig)
            huidig = None
        elif huidig is None:
            huidig = {"w": ch, "s": s, "e": e}
        else:
            huidig["w"] += ch
            huidig["e"] = e
    if huidig:
        uit.append(huidig)
    return uit


def tegoed():
    d = requests.get(f"{API}/user/subscription", headers={"xi-api-key": sleutel()}, timeout=20).json()
    return d["tier"], d["character_count"], d["character_limit"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tekst", nargs="?")
    ap.add_argument("--stem", default="eric")
    ap.add_argument("--tegoed", action="store_true")
    args = ap.parse_args()
    if args.tegoed:
        tier, gebruikt, limiet = tegoed()
        print(f"{tier}: {gebruikt} / {limiet} tekens gebruikt")
    elif args.tekst:
        mp3, w = inspreken(args.tekst, args.stem)
        print(mp3, f"({w[-1]['e']:.2f} s)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
