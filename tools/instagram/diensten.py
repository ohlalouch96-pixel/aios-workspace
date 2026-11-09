"""
Instagram — onderwerpen voor video's met stem: de diensten op insightance.ai (@insightance.ai)

Leest de lijst met automatiseringen van de website (docs/automations.html, alleen lezen,
de live site wordt nooit aangepast) en kiest welke dienst de volgende video krijgt:
- eerst elke dienst één keer voordat er een herhaalt;
- nooit twee keer achter elkaar dezelfde categorie (sales, klantcontact, finance, ...);
- nieuwe diensten op de website komen vanzelf mee.
Welke dienst al een video had, staat in instagram_posts.dienst (soort stem_video).

Gebruik (CLI):
    python tools/instagram/diensten.py lijst       # alle diensten + hoe vaak er al een video was
    python tools/instagram/diensten.py volgende    # de dienst die nu aan de beurt is
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wachtrij import verbind  # noqa: E402

PAGINA = Path(__file__).resolve().parent.parent.parent / "docs" / "automations.html"
TEKST = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""


def diensten():
    """[{categorie, naam, wat}] in het Engels, zoals op de website (S('cat', 'NL', 'EN', 'NL-tekst', 'EN-tekst', ...))."""
    t = PAGINA.read_text(encoding="utf-8")
    uit = []
    for m in re.finditer(rf"S\(\s*'(\w+)',\s*({TEKST}),\s*({TEKST}),\s*({TEKST}),\s*({TEKST})", t):
        cat, _, naam, _, wat = (g[1:-1] if g[0] in "'\"" else g for g in m.groups())
        uit.append({"categorie": cat, "naam": naam.replace("\\'", "'"), "wat": wat.replace("\\'", "'")})
    return uit


def gebruikt(conn):
    rij = conn.execute("SELECT dienst, COUNT(*) FROM instagram_posts WHERE dienst IS NOT NULL AND status != 'overgeslagen' GROUP BY dienst")
    return dict(rij.fetchall())


def volgende(conn):
    alle, telling = diensten(), gebruikt(conn)
    laatst = conn.execute("SELECT dienst FROM instagram_posts WHERE dienst IS NOT NULL AND status != 'overgeslagen' ORDER BY id DESC LIMIT 1").fetchone()
    vorige_cat = next((d["categorie"] for d in alle if laatst and d["naam"] == laatst[0]), None)
    minst = min(telling.get(d["naam"], 0) for d in alle)
    kandidaten = [d for d in alle if telling.get(d["naam"], 0) == minst and d["categorie"] != vorige_cat]
    return (kandidaten or [d for d in alle if telling.get(d["naam"], 0) == minst])[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["lijst", "volgende"])
    args = ap.parse_args()
    conn = verbind()
    if args.cmd == "lijst":
        telling = gebruikt(conn)
        for d in diensten():
            print(f"{telling.get(d['naam'], 0)}x  {d['categorie']:<8} {d['naam']}")
    else:
        print(json.dumps(volgende(conn), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
