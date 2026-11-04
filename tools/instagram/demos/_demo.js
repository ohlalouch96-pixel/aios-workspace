// Gedeelde helpers voor de demo-pagina's (alleen voor Instagram-opnames, niet op de live site).
// De opname-tool (opname_demo.py) bestuurt de tijd: window.__tick(ms) laat tweens verder lopen,
// CSS-animaties worden via document.getAnimations() per frame gezet.

(function () {
  const tweens = [];
  window.__klok = 0;

  // waarde laten meelopen over tijd, bijv. een getal dat optelt
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

  window.__bezig = function () {
    return tweens.length;
  };

  window.telOp = function (el, van, naar, duur, opmaak) {
    animeer(duur || 900, (t) => (el.textContent = opmaak(van + (naar - van) * t)));
  };

  window.euro = (n) => "€" + Math.round(n).toLocaleString("en-GB");

  // zichtbare muisaanwijzer
  const cursor = document.createElement("div");
  cursor.id = "__cursor";
  cursor.innerHTML =
    '<svg width="54" height="54" viewBox="0 0 24 24"><path d="M4 2 L4 19 L8.5 14.8 L11.6 21.5 L14.3 20.3 L11.2 13.7 L17.5 13.7 Z" fill="#111" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>';
  Object.assign(cursor.style, { position: "fixed", left: "0", top: "0", zIndex: 9999, pointerEvents: "none", transform: "translate(540px,1500px)" });
  document.addEventListener("DOMContentLoaded", () => document.body.appendChild(cursor));

  window.__cursor = function (x, y) {
    cursor.style.transform = `translate(${x}px,${y}px)`;
  };

  window.__klikEffect = function (x, y) {
    const r = document.createElement("div");
    r.className = "__ripple";
    Object.assign(r.style, { left: x - 30 + "px", top: y - 30 + "px" });
    document.body.appendChild(r);
    setTimeout(() => r.remove(), 2000);
  };

  // hook-tekst bovenin (wordt door de opname-tool gezet)
  window.__hook = function (html) {
    const h = document.getElementById("hook");
    if (h) {
      h.innerHTML = "<span>" + html + "</span>";
      h.classList.add("aan");
    }
  };
})();
