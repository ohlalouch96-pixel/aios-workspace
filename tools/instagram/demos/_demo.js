// Gedeelde helpers voor de demo-pagina's (alleen voor Instagram-opnames, niet op de live site).
// De opname-tool (opname_demo.py) bestuurt de tijd: window.__tick(ms) laat tweens verder lopen,
// CSS-animaties worden via document.getAnimations() per frame gezet.
// Coördinaten van cursor en klikken zijn in desktop-pixels (#desk, 1280x800), zodat ze meezoomen.

(function () {
  const tweens = [];
  const BREED = 1280, HOOG = 800, SCHERM_B = 960, SCHERM_H = 600, BASIS = SCHERM_B / BREED;
  window.__klok = 0;

  window.animeer = function (duur, stap, klaar) {
    tweens.push({ start: window.__klok, duur, stap, klaar });
  };
  window.__tick = function (ms) {
    window.__klok += ms;
    for (let i = tweens.length - 1; i >= 0; i--) {
      const tw = tweens[i];
      const t = Math.min(1, (window.__klok - tw.start) / tw.duur);
      tw.stap(1 - Math.pow(1 - t, 3));
      if (t >= 1) {
        tweens.splice(i, 1);
        if (tw.klaar) tw.klaar();
      }
    }
  };
  window.__bezig = () => tweens.length;
  window.na = (ms, fn) => animeer(ms, () => {}, fn);
  window.telOp = (el, van, naar, duur, opmaak) => animeer(duur || 900, (t) => (el.textContent = opmaak(van + (naar - van) * t)));
  window.geld = (n, teken, dec) => (teken || "€") + n.toLocaleString("en-GB", { minimumFractionDigits: dec || 0, maximumFractionDigits: dec || 0 });

  const desk = () => document.getElementById("desk");
  let cursor;
  document.addEventListener("DOMContentLoaded", () => {
    cursor = document.createElement("div");
    cursor.id = "__cursor";
    cursor.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2 L4 19 L8.5 14.8 L11.6 21.5 L14.3 20.3 L11.2 13.7 L17.5 13.7 Z" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    cursor.style.transform = "translate(700px,700px)";
    desk().appendChild(cursor);
  });

  // midden van een element in desktop-pixels (los van zoom)
  window.__doel = function (sel) {
    const el = document.querySelector(sel), d = desk().getBoundingClientRect(), r = el.getBoundingClientRect(), s = d.width / BREED;
    return [(r.left - d.left + r.width / 2) / s, (r.top - d.top + r.height / 2) / s];
  };
  window.__cursor = (x, y) => (cursor.style.transform = `translate(${x - 4}px,${y - 2}px)`);
  window.__klikEffect = function (x, y) {
    const r = document.createElement("div");
    r.className = "__ripple";
    Object.assign(r.style, { left: x - 18 + "px", top: y - 18 + "px" });
    desk().appendChild(r);
    na(700, () => r.remove());
  };

  // camera: inzoomen op een punt (desktop-pixels), z=1 is het hele scherm
  window.__camera = function (z, fx, fy) {
    const s = BASIS * z;
    let tx = SCHERM_B / 2 - fx * s, ty = SCHERM_H / 2 - fy * s;
    tx = Math.min(0, Math.max(SCHERM_B - BREED * s, tx));
    ty = Math.min(0, Math.max(SCHERM_H - HOOG * s, ty));
    document.getElementById("camera").style.transform = `translate(${tx}px,${ty}px) scale(${s})`;
  };

  window.__hook = function (html) {
    const h = document.getElementById("hook");
    h.innerHTML = "<span>" + html + "</span>";
    h.classList.add("aan");
  };
  window.__ondertitel = function (html) {
    const o = document.getElementById("ondertitel");
    const oud = o.querySelector("span");
    if (oud) oud.remove();
    const s = document.createElement("span");
    s.innerHTML = html;
    o.appendChild(s);
    void s.offsetWidth;
    s.classList.add("aan");
  };
})();
