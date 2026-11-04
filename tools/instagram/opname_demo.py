"""
Instagram — schermopname-reel van een fictieve demo (@insightance.ai)

Opent een demo-pagina uit tools/instagram/demos/ (fictieve bedrijven, alleen
functionaliteit die echt gebouwd kan worden, nooit klantnamen) en speelt een
script af: muisaanwijzer bewegen, klikken, letter voor letter typen. De tijd
wordt door deze tool bestuurd (CSS-animaties en tweens per frame verzet),
dus elk frame is scherp en het tempo is altijd gelijk. De app staat op een
beeldscherm; "zoom" laat de camera inzoomen op een element, "ondertitel" zet
een korte uitleg onder het scherm. Levert reel.mp4
(1080x1920, 30 fps, zonder geluid) en cover.jpg.

Spec:
    {
      "demo": "offerte", "kleurenset": "navy",
      "hook": "A quote, built and sent in *under a minute.*",
      "stappen": [
        {"doe": "wacht", "s": 0.8},
        {"doe": "typ", "id": "naam", "tekst": "James Carter"},
        {"doe": "klik", "sel": "#klus"},
        {"doe": "klik", "sel": "#klus-lijst [data-v=boiler]"},
        {"doe": "zoom", "factor": 1.8, "sel": "#naam"},
        {"doe": "ondertitel", "tekst": "Pick the job. *The lines fill themselves.*"},
        {"doe": "klik", "sel": "#maak"}
      ]
    }

Gebruik (CLI):
    python tools/instagram/opname_demo.py spec.json [--uit map/]
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
from render_carrousel import KLEUREN, TMP, opmaak  # noqa: E402

DEMOS = Path(__file__).resolve().parent / "demos"
FPS = 30
MS = 1000 / FPS

STAP_JS = """(ms) => {
  window.__tick(ms);
  let actief = window.__bezig();
  document.getAnimations().forEach(a => {
    if (a.playState === 'finished' || a.playState === 'idle') return;
    a.pause();
    a.currentTime = (a.currentTime || 0) + ms;
    if (a.playState !== 'finished') actief++;
  });
  return actief;
}"""


class Opname:
    def __init__(self, pg, frames):
        self.pg, self.frames, self.n = pg, frames, 0
        self.cx, self.cy = 700.0, 700.0  # desktop-pixels (#desk, 1280x800)
        self.vorige, self.bewogen = None, True

    def frame(self):
        actief = self.pg.evaluate(STAP_JS, MS)
        pad = self.frames / f"f{self.n:05d}.png"
        if actief or self.bewogen or self.vorige is None:
            self.pg.screenshot(path=str(pad))
        else:
            shutil.copyfile(self.vorige, pad)  # niets veranderd: vorig frame hergebruiken
        self.vorige, self.bewogen, self.n = pad, False, self.n + 1

    def wacht(self, s):
        for _ in range(int(s * FPS)):
            self.frame()

    def beweeg(self, x, y, duur=0.45):
        x0, y0, stappen = self.cx, self.cy, max(1, int(duur * FPS))
        for i in range(1, stappen + 1):
            t = i / stappen
            e = 1 - (1 - t) ** 3
            self.cx, self.cy = x0 + (x - x0) * e, y0 + (y - y0) * e
            self.pg.evaluate(f"window.__cursor({self.cx:.1f}, {self.cy:.1f})")
            self.bewogen = True
            self.frame()

    def midden(self, sel):
        return self.pg.evaluate("(s) => window.__doel(s)", sel)

    def zoom(self, factor, sel=None, x=640, y=400):
        if sel:
            x, y = self.midden(sel)
        self.pg.evaluate("([z, x, y]) => window.__camera(z, x, y)", [factor, x, y])
        self.bewogen = True

    def klik(self, sel):
        x, y = self.midden(sel)
        self.beweeg(x, y)
        self.pg.evaluate("([x, y]) => window.__klikEffect(x, y)", [x, y])
        self.pg.evaluate("(s) => { const el = document.querySelector(s); el.classList.add('hover'); el.click(); }", sel)
        self.bewogen = True
        self.wacht(0.35)

    def typ(self, veld_id, tekst):
        self.klik(f"#{veld_id}")
        self.pg.evaluate(f"window.focusVeld('{veld_id}')")
        self.bewogen = True
        for ch in tekst:
            self.pg.evaluate("([id, ch]) => window.typLetter(id, ch)", [veld_id, ch])
            self.bewogen = True
            self.frame()
            self.frame()
        self.wacht(0.25)


def render(spec, uit):
    uit.mkdir(parents=True, exist_ok=True)
    frames = uit / "_frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    k = KLEUREN[spec.get("kleurenset", "navy")]
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto((DEMOS / f"{spec['demo']}.html").as_uri())
        pg.evaluate("document.fonts.ready")
        pg.evaluate("([bg, fg, acc]) => { const s = document.body.style; s.setProperty('--hookbg', bg); s.setProperty('--hookfg', fg); s.setProperty('--hookacc', acc); }",
                    [k["cbg"], k["cfg"], k["acc"]])
        pg.evaluate("document.getAnimations().forEach(a => a.finish())")
        rec = Opname(pg, frames)
        rec.wacht(0.3)
        pg.evaluate("(h) => window.__hook(h)", opmaak(spec["hook"]))
        rec.bewogen = True
        rec.wacht(0.7)
        pg.screenshot(path=str(uit / "cover.jpg"), type="jpeg", quality=95)
        for st in spec["stappen"]:
            doe = st["doe"]
            if doe == "wacht":
                rec.wacht(st["s"])
            elif doe == "klik":
                rec.klik(st["sel"])
            elif doe == "typ":
                rec.typ(st["id"], st["tekst"])
            elif doe == "beweeg":
                rec.beweeg(*rec.midden(st["sel"]))
            elif doe == "zoom":
                rec.zoom(st.get("factor", 1), st.get("sel"), st.get("x", 640), st.get("y", 400))
            elif doe == "ondertitel":
                pg.evaluate("(h) => window.__ondertitel(h)", opmaak(st["tekst"]))
                rec.bewogen = True
            elif doe == "js":
                pg.evaluate(st["code"])
                rec.bewogen = True
            else:
                raise ValueError(f"Onbekende stap: {doe}")
        browser.close()
    video = uit / "reel.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], check=True)
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
