"""
Instagram — geluidseffecten onder een video (@insightance.ai)

Maakt de geluiden zelf (numpy, geen samples), dus vrij te gebruiken in advertenties: tikjes bij typen,
swoosh bij versturen, plop bij een binnenkomend bericht, ding/chime, klik, opbouw (riser), zachte klap
en eventueel een rustig achtergrondtoontje. Muziek zit hier bewust niet in: die kiest Oussama in
Instagram uit de Meta Sound Collection (mag in advertenties; gewone muziek uit de bibliotheek niet).

Gebruik in een demo-spec (opname_demo.py), tijden in seconden van de video:
    "geluid": [
      {"s": "typen", "van": 0.3, "tot": 2.2, "cps": 25, "soort": "telefoon"},   # of "toetsenbord"
      {"s": "klok", "van": 0.5, "tot": 12.5, "elke": 1.0},
      {"s": "swoosh", "t": 2.2}, {"s": "plop", "t": 3.4}, {"s": "ding", "t": 4.1, "hz": 523},
      {"s": "klik", "t": 6.8}, {"s": "chime", "t": 7.2}, {"s": "check", "t": 11.8}, {"s": "riser", "t": 7.3, "duur": 5},
      {"s": "klap", "t": 12.9}, {"s": "pad", "van": 0, "tot": 17.5},
      {"s": "kras", "t": 2.5}, {"s": "stempel", "t": 2.6},   # plaat-kras (beeld bevriest) en stempel-dreun
      {"s": "kassa", "t": 10.7}   # ka-ching bij "Paid"
    ]
    optioneel per regel "vol" (1 = standaard).

CLI (alleen geluid opnieuw onder een bestaande video):
    python tools/instagram/geluid.py spec.json map/   (map met reel.mp4)
"""

import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np

SR = 44100
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
RNG = np.random.default_rng(7)  # vaste "toeval": elke render klinkt hetzelfde


def _t(duur):
    return np.arange(int(duur * SR)) / SR


def _laag(x, k):
    """Eenvoudig laagdoorlaatfilter (voortschrijdend gemiddelde over k samples)."""
    return np.convolve(x, np.ones(k) / k, mode="same")


def toets(telefoon=False):
    """Eén aanslag: telefoon = zacht hoog tikje, toetsenbord = korte doffe klik."""
    if telefoon:
        t = _t(0.025)
        return (np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 260) * 0.18).astype(np.float32)
    t = _t(0.05)
    ruis = RNG.standard_normal(len(t))
    klik = _laag(ruis, 6) * np.exp(-t * 110) * 0.55 + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 60) * 0.25
    return (klik * RNG.uniform(0.6, 1.0)).astype(np.float32)


def klok_tik():
    t = _t(0.03)
    return (np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 300) * 0.12).astype(np.float32)


def swoosh(duur=0.35, klein=False):
    t = _t(duur)
    ruis = _laag(RNG.standard_normal(len(t)), 9 if klein else 5)
    omhul = np.sin(np.pi * t / duur) ** 2
    return (ruis * omhul * (0.18 if klein else 0.35)).astype(np.float32)


def plop():
    t = _t(0.12)
    f = 520 + 520 * (t / 0.12)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32) * 0.45).astype(np.float32)


def ding(hz=880, duur=0.7):
    t = _t(duur)
    toon = np.sin(2 * np.pi * hz * t) + 0.35 * np.sin(2 * np.pi * hz * 2 * t) + 0.12 * np.sin(2 * np.pi * hz * 3 * t)
    return (toon * np.exp(-t * 6) * np.minimum(1, t / 0.004) * 0.32).astype(np.float32)


def chime():
    """Succes: twee tonen kort na elkaar (E6, B6)."""
    a, b = ding(1319, 0.9), ding(1976, 0.9)
    uit = np.zeros(len(a) + int(0.09 * SR), dtype=np.float32)
    uit[:len(a)] += a
    uit[int(0.09 * SR):] += b
    return uit * 0.8


def check():
    """Afgevinkt: twee korte tonen omhoog (G5, C6), zacht en positief."""
    a, b = ding(784, 0.45), ding(1047, 0.6)
    uit = np.zeros(int(0.12 * SR) + len(b), dtype=np.float32)
    uit[:len(a)] += a
    uit[int(0.12 * SR):] += b
    return uit * 0.75


def klik():
    t = _t(0.04)
    return (np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 180) * 0.4 + _laag(RNG.standard_normal(len(t)), 3) * np.exp(-t * 250) * 0.25).astype(np.float32)


def riser(duur=4.0):
    """Opbouw: ruis + stijgende toon, steeds harder; eindigt zacht zodat de klap erna vrij is."""
    t = _t(duur)
    f = 220 * (4 ** (t / duur))
    toon = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.10
    ruis = _laag(RNG.standard_normal(len(t)), 7) * 0.18
    omhul = (t / duur) ** 2 * np.minimum(1, (duur - t) / 0.08)
    return ((toon + ruis) * omhul).astype(np.float32)


def klap():
    t = _t(0.6)
    return (np.sin(2 * np.pi * (55 + 40 * np.exp(-t * 18)) * t) * np.exp(-t * 7) * 0.7
            + _laag(RNG.standard_normal(len(t)), 4) * np.exp(-t * 40) * 0.25).astype(np.float32)


def kras():
    """Plaat-kras (record scratch): ruis met een toonhoogte die snel heen en weer zwiept, zoals een plaat die wordt
    tegengehouden; de toon zakt aan het eind weg (de muziek stopt). Gebruik: het beeld bevriest (robot-reel, 22-11)."""
    duur = 0.42
    t = _t(duur)
    # snelheid van de 'plaat': vooruit, terug, vooruit, dan stilstand
    v = np.interp(t, [0, 0.07, 0.16, 0.26, 0.34, duur], [1.0, 2.2, -1.6, 1.8, 0.4, 0.0])
    fase = np.cumsum(np.abs(v)) / SR
    toon = np.sign(np.sin(2 * np.pi * 420 * fase)) * 0.25 + np.sin(2 * np.pi * 840 * fase) * 0.3
    ruis = RNG.standard_normal(len(t)) * (0.35 + 0.65 * np.abs(v) / 2.2)
    ruis = ruis - _laag(ruis, 12)  # hoog doorlaten: krassend
    omhul = np.minimum(1, t / 0.005) * np.minimum(1, (duur - t) / 0.05)
    return (_laag(toon + ruis * 0.6, 2) * omhul * 0.5).astype(np.float32)


def stempel():
    """Stempel die op tafel knalt: diepe dreun + korte doffe tik (harder en korter dan klap)."""
    t = _t(0.5)
    dreun = np.sin(2 * np.pi * (48 + 70 * np.exp(-t * 30)) * t) * np.exp(-t * 9) * 0.9
    tik = _laag(RNG.standard_normal(len(t)), 3) * np.exp(-t * 90) * 0.55
    return (np.tanh((dreun + tik) * 1.6) * 0.75).astype(np.float32)


def kassa():
    """Ka-ching (betaald): korte mechanische klik ('ka'), dan een heldere belklank met metalen boventonen ('ching')."""
    ka = np.zeros(int(0.08 * SR), dtype=np.float32)
    tk = _t(0.03)
    ka[:len(tk)] = (_laag(RNG.standard_normal(len(tk)), 2) * np.exp(-tk * 220) * 0.5).astype(np.float32)
    t = _t(1.1)
    bel = sum(g * np.sin(2 * np.pi * f * t) for f, g in ((2637, 1.0), (3520, 0.6), (5274, 0.25), (7040, 0.12)))
    bel = bel * np.exp(-t * 4.5) * np.minimum(1, t / 0.003) * 0.22
    uit = np.zeros(len(ka) + len(bel), dtype=np.float32)
    uit[:len(ka)] += ka
    uit[len(ka):] += bel.astype(np.float32)
    return uit


def pad(duur):
    """Rustig achtergrondtoontje (A-akkoord), heel zacht, langzaam golvend, in- en uitfaden."""
    t = _t(duur)
    toon = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate((110, 164.8, 220, 277.2)))
    golf = 0.75 + 0.25 * np.sin(2 * np.pi * 0.15 * t)
    fade = np.minimum(1, np.minimum(t / 1.5, (duur - t) / 1.5))
    return (_laag(toon, 20) * golf * fade * 0.025).astype(np.float32)


def maak(regels, duur, wav):
    spoor = np.zeros(int(duur * SR) + SR, dtype=np.float32)

    def leg(geluid, t, vol=1.0):
        i = int(t * SR)
        if 0 <= i < len(spoor):
            stuk = geluid[: len(spoor) - i] * vol
            spoor[i:i + len(stuk)] += stuk

    for r in regels:
        s, vol = r["s"], r.get("vol", 1.0)
        if s == "typen":
            tel, stap = r.get("soort") == "telefoon", 1 / r["cps"]
            for k in range(int((r["tot"] - r["van"]) / stap)):
                leg(toets(tel), r["van"] + k * stap + RNG.uniform(-0.012, 0.012), vol)
        elif s == "klok":
            t = r["van"]
            while t < r["tot"]:
                leg(klok_tik(), t, vol)
                t += r.get("elke", 1.0)
        elif s == "pad":
            leg(pad(r["tot"] - r["van"]), r["van"], vol)
        else:
            maker = {"swoosh": lambda: swoosh(klein=r.get("klein", False)), "plop": plop, "ding": lambda: ding(r.get("hz", 880)),
                     "chime": chime, "check": check, "klik": klik, "kras": kras, "stempel": stempel, "kassa": kassa, "riser": lambda: riser(r.get("duur", 4.0)), "klap": klap}[s]
            leg(maker(), r["t"], vol)
    spoor = spoor[: int(duur * SR)]
    piek = float(np.max(np.abs(spoor))) or 1.0
    spoor = spoor / piek * 0.85  # piek op ±-1,4 dBFS
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", str(wav)],
                   input=spoor.astype(np.float32).tobytes(), check=True)
    return wav


def onder_video(regels, video):
    """Zet het geluid onder een bestaande (stille) reel.mp4; beeld wordt niet opnieuw gecodeerd."""
    video = Path(video)
    info = subprocess.run([FFMPEG, "-i", str(video)], capture_output=True, text=True).stderr
    u, m, s = info.split("Duration: ")[1].split(",")[0].split(":")
    duur = int(u) * 3600 + int(m) * 60 + float(s)
    wav = maak(regels, duur, video.parent / "_geluid.wav")
    tmp = video.parent / "_met_geluid.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(video), "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-t", f"{duur:.2f}", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(video)
    wav.unlink()
    return video


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(onder_video(spec["geluid"], Path(sys.argv[2]) / "reel.mp4"))
