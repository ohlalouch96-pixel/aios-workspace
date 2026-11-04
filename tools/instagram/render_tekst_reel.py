"""
Instagram — reel met bewegende tekst (@insightance.ai)

Maakt een verticale video (1080x1920, 30 fps, mp4, zonder geluid) uit een
reeks korte teksten ("beats"). Woorden verschijnen een voor een, het kernwoord
in de accentkleur, elke beat schuift weg voor de volgende. Zelfde kleurensets
en letters als de carrousels. Tekst blijft binnen de veilige zone van Reels
(niet onder de knoppen of de caption).

Frames worden een voor een gerenderd (animaties stilgezet op het exacte
tijdstip) en daarna met ffmpeg samengevoegd: daardoor blijft de tekst scherp.
Levert ook een cover-afbeelding (moment waarop de hook volledig in beeld is).

Spec:
    {
      "onderwerp": "...", "serie": "AUTOMATION SIMPLIFIED", "kleurenset": "navy",
      "beats": [
        {"tekst": "Free tools aren't *free.*", "duur": 3.0},
        {"label": "Cost #1", "tekst": "The *paywall.*", "duur": 2.2},
        {"tekst": "The real price isn't on the *pricing page.*", "duur": 3.5}
      ]
    }

Gebruik (CLI):
    python tools/instagram/render_tekst_reel.py spec.json [--uit map/]
Vereist: playwright (Chrome) en imageio-ffmpeg (pip install imageio-ffmpeg).
"""

import argparse
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_carrousel import KLEUREN, FONTS, TMP, logo, maat, opmaak  # noqa: E402

FPS = 30
IN, UIT_ANIM, STAGGER = 0.45, 0.35, 0.09


def pagina(spec):
    k = KLEUREN[spec.get("kleurenset", "navy")]
    beats, t = [], 0.0
    totaal = sum(b["duur"] for b in spec["beats"])
    for nr, b in enumerate(spec["beats"]):
        laatste = nr == len(spec["beats"]) - 1
        # woorden in losse spans, <em>-delen (kernwoord) krijgen de accentkleur
        woorden = opmaak(b["tekst"]).replace("<em>", " <em>").replace("</em>", "</em> ").split()
        spans, open_em, i = [], False, 0
        for w in woorden:
            if w.startswith("<em>"):
                open_em, w = True, w[4:]
            sluit = w.endswith("</em>")
            if sluit:
                w = w[:-5]
            if w:
                cls = ' class="acc"' if open_em else ""
                spans.append(f'<span{cls} style="animation-delay:{t + 0.15 + i * STAGGER:.2f}s">{w}</span>')
                i += 1
            if sluit:
                open_em = False
        weg = "" if laatste else f"animation:weg {UIT_ANIM}s ease-in {t + b['duur'] - UIT_ANIM:.2f}s both;"
        label = f'<div class="lab" style="animation-delay:{t:.2f}s">{html.escape(b["label"])}</div>' if b.get("label") else ""
        grootte = maat(b["tekst"], 128, 28, 80)
        beats.append(f'<div class="beat" style="{weg}"><div>{label}<h1 style="font-size:{grootte}px">{" ".join(spans)}</h1></div></div>')
        t += b["duur"]
    css = f"""
@font-face{{font-family:Inter;font-weight:100 900;src:url('{FONTS}/inter-latin.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden}}
.s{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{k['cbg']};color:{k['cfg']};font-family:Inter}}
.glow{{position:absolute;width:1400px;height:1400px;left:-160px;top:260px;border-radius:50%;background:radial-gradient(circle,{k['acc']}33,transparent 62%);animation:drijf {totaal:.2f}s linear both}}
@keyframes drijf{{from{{transform:translate(-80px,-60px) scale(1)}}to{{transform:translate(80px,60px) scale(1.12)}}}}
.top{{position:absolute;left:90px;right:90px;top:250px;display:flex;justify-content:space-between;font:600 28px Inter;letter-spacing:.14em;opacity:.8}}
.balk{{position:absolute;left:90px;right:90px;top:310px;height:6px;border-radius:3px;background:{k['cfg']}22;overflow:hidden}}
.balk i{{display:block;height:100%;background:{k['acc']};animation:vul {totaal:.2f}s linear both}}
@keyframes vul{{from{{width:0}}to{{width:100%}}}}
.beat{{position:absolute;left:90px;right:90px;top:520px;height:900px;display:flex;align-items:center}}
h1{{font-weight:800;line-height:1.02;letter-spacing:-.035em}}
h1 span{{display:inline-block;animation:in {IN}s cubic-bezier(.2,.8,.2,1) both}}
.acc{{color:{k['acc']}}}
.lab{{display:inline-block;font:700 30px Inter;letter-spacing:.16em;text-transform:uppercase;color:{k['cbg']};background:{k['acc']};padding:14px 26px;border-radius:40px;margin-bottom:40px;animation:in {IN}s ease-out both}}
@keyframes in{{from{{opacity:0;transform:translateY(46px)}}to{{opacity:1;transform:none}}}}
@keyframes weg{{from{{opacity:1;transform:none}}to{{opacity:0;transform:translateY(-60px)}}}}
.bot{{position:absolute;left:90px;right:90px;top:1480px;display:flex;align-items:center;gap:16px;font:600 30px Inter;opacity:.85}}
"""
    body = (f'<div class="s"><div class="glow"></div><div class="top"><span>{html.escape(spec["serie"])}</span></div>'
            f'<div class="balk"><i></i></div>{"".join(beats)}'
            f'<div class="bot">{logo(k["cfg"], k["acc"], 44)}@insightance.ai</div></div>')
    return f'<html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>', totaal


def render(spec, uit):
    uit.mkdir(parents=True, exist_ok=True)
    frames = uit / "_frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    doc, totaal = pagina(spec)
    tmp = uit / "_reel.html"
    tmp.write_text(doc, encoding="utf-8")
    n = int(totaal * FPS)
    hook_klaar = min(spec["beats"][0]["duur"] - UIT_ANIM - 0.05, 2.2)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(tmp.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.evaluate("document.getAnimations().forEach(a => a.pause())")
        for f in range(n):
            pg.evaluate(f"document.getAnimations().forEach(a => a.currentTime = {f * 1000 / FPS:.1f})")
            pg.screenshot(path=str(frames / f"f{f:05d}.png"))
        pg.evaluate(f"document.getAnimations().forEach(a => a.currentTime = {hook_klaar * 1000:.0f})")
        pg.screenshot(path=str(uit / "cover.jpg"), type="jpeg", quality=95)
        browser.close()
    video = uit / "reel.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], check=True)
    shutil.rmtree(frames)
    tmp.unlink()
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
