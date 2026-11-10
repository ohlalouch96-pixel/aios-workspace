"""
Instagram — reel met bewegende tekst (@insightance.ai)

Maakt een verticale video (1080x1920, 30 fps, mp4) uit een reeks korte
teksten ("beats"). Met --stem leest Eric elke beat voor (zelfde stem en regels als
render_stem_video: één doorlopende opname, 1 s rust na elke zin, minimaal 3 s per
beat) en verschijnt elk woord op het moment dat hij het zegt; "duur" wordt dan
genegeerd. Een label dat een gewoon woord is ("Myth", "Truth") zegt hij ook. Woorden verschijnen een voor een, het kernwoord
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
    python tools/instagram/render_tekst_reel.py spec.json [--uit map/] [--stem | --zonder-stem]
--zonder-stem = gratis proef met geschatte stemtiming (geen geluid, geen tegoed).
Vereist: playwright (Chrome) en imageio-ffmpeg (pip install imageio-ffmpeg).
"""

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_carrousel import KLEUREN, FONTS, TMP, logo, maat, opmaak  # noqa: E402
import render_stem_video as rsv  # noqa: E402

FPS = 30
IN, UIT_ANIM, STAGGER = 0.45, 0.35, 0.09


def pagina(spec, scenes=None, totaal=None):
    """scenes (met stem): per beat start, duur en woordtijden; elk woord verschijnt net voordat Eric het zegt."""
    k = KLEUREN[spec.get("kleurenset", "navy")]
    beats, t = [], 0.0
    totaal = totaal or sum(b["duur"] for b in spec["beats"])
    for nr, b in enumerate(spec["beats"]):
        laatste = nr == len(spec["beats"]) - 1
        sc = scenes[nr] if scenes else None
        if sc:
            t, b = sc["start"], {**b, "duur": sc["dur"]}
            tijden = [t + w["s"] for w in sc["woorden"]][len(gesproken_label(b)):]
        # woorden in losse spans, <em>-delen (kernwoord) krijgen de accentkleur
        woorden = opmaak(b["tekst"]).replace("<em>", " <em>").replace("</em>", "</em> ").split()
        spans, open_em, i, wi = [], False, 0, 0
        for w in woorden:
            if w.startswith("<em>"):
                open_em, w = True, w[4:]
            sluit = w.endswith("</em>")
            if sluit:
                w = w[:-5]
            if w:
                cls = ' class="acc"' if open_em else ""
                if sc:  # met stem: op het gesproken woord (losse leestekens met het woord ervoor mee)
                    echt = re.search(r"\w", w) is not None
                    start = tijden[min(wi if echt else max(wi - 1, 0), len(tijden) - 1)] - 0.08
                    wi += echt
                else:
                    start = t + 0.15 + i * STAGGER
                span = f'<span{cls} style="animation-delay:{start:.2f}s">{w}</span>'
                if spans and re.search(r"\w", w) is None:  # los leesteken na een kernwoord: vast aan dat woord, geen spatie ervoor
                    spans[-1] += span
                else:
                    spans.append(span)
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


def gesproken_label(b):
    """Een label als "Myth" of "Truth" zegt Eric ook; "Step 1" of "Cost #1" niet."""
    lab = (b.get("label") or "").strip()
    return [lab] if lab and lab.isalpha() else []


def stem_beats(spec):
    """De beats zoals Eric ze uitspreekt: label (als het een woord is) + de tekst zonder *sterretjes*."""
    beats = []
    for b in spec["beats"]:
        zegt = " ".join(w + "." for w in gesproken_label(b)) + " " + b["tekst"].replace("*", "")
        beats.append({"zegt": " ".join(zegt.split())})
    return rsv.regie(beats)


def render(spec, uit, stem=False, zonder_stem=False):
    uit.mkdir(parents=True, exist_ok=True)
    frames = uit / "_frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    scenes, audio, lijn = None, [], None
    if stem or zonder_stem:
        stemspec = {**rsv.ERIC, **{k: spec[k] for k in ("seed", "rust") if k in spec}, "beats": stem_beats(spec)}
        scenes, audio, totaal, info = rsv.stemspoor(stemspec, uit, zonder_stem)
        lijn = {"scenes": [{**sc, "type": f"beat{n + 1}"} for n, sc in enumerate(scenes)], "stem": info}
        rsv.controle(lijn, uit, spec.get("rust"))
        doc, totaal = pagina(spec, scenes, totaal)
    else:
        doc, totaal = pagina(spec)
    tmp = uit / "_reel.html"
    tmp.write_text(doc, encoding="utf-8")
    n = int(totaal * FPS)
    eerste = scenes[0]["dur"] if scenes else spec["beats"][0]["duur"]
    hook_klaar = min(eerste - UIT_ANIM - 0.05, scenes[0]["woorden"][-1]["e"] + 0.4 if scenes else 2.2)
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
    video = rsv.samenvoegen(frames, audio, n / FPS, uit / "reel.mp4")
    tmp.unlink()
    if lijn:
        rsv.controleblad(video, lijn, uit / "controle.png")
    return video


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--uit")
    ap.add_argument("--stem", action="store_true", help="Eric leest de tekst voor (kost ElevenLabs-tegoed als het niet in de cache staat)")
    ap.add_argument("--zonder-stem", action="store_true", help="gratis proef met geschatte stemtiming, zonder geluid")
    args = ap.parse_args()
    spec_pad = Path(args.spec)
    uit = (Path(args.uit) if args.uit else TMP / spec_pad.stem).resolve()
    print(render(json.loads(spec_pad.read_text(encoding="utf-8")), uit, stem=args.stem, zonder_stem=args.zonder_stem))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
