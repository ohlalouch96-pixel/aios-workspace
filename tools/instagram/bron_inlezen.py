"""
Instagram — LinkedIn-serie inlezen als bron voor Instagram-posts

Leest outputs/linkedin-content-serie.md en zet elk uitgewerkt onderwerp in de
tabel instagram_bron (data/data.db): Automation Simplified (sectie "Klaar om te
posten"), Myth Check, The Other Shift (codeblokken) en The Fork (genummerde
lijst). Bestaande onderwerpen worden overgeslagen, dus veilig om vaker te
draaien, bijvoorbeeld nadat er nieuwe LinkedIn-posts bij zijn gekomen.

Gebruik (CLI):
    python tools/instagram/bron_inlezen.py          # inlezen + telling per pijler
    python tools/instagram/bron_inlezen.py --toon   # ook alle titels tonen
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wachtrij import verbind  # noqa: E402

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
BRON = WORKSPACE_ROOT / "outputs" / "linkedin-content-serie.md"

# sectiekop in de LinkedIn-serie -> pijler
SECTIES = {
    "## Klaar om te posten": "automation_simplified",
    "## Pijler 2": "the_other_shift",
    "## Pijler 3": "the_fork",
    "## Pijler 4": "myth_check",
}


def schoon(blok):
    """Episode-tag en hashtagregels eruit; die worden voor Instagram opnieuw gemaakt."""
    regels = [r for r in blok if not r.startswith("#") and not r.startswith("Episode ")]
    return "\n".join(regels).strip()


def lees():
    items, pijler, blok = [], None, None
    for regel in BRON.read_text(encoding="utf-8").splitlines():
        if regel.startswith("## "):
            pijler = next((p for kop, p in SECTIES.items() if regel.startswith(kop)), None)
            continue
        if pijler is None:
            continue
        if regel.startswith("```"):
            if blok is None:
                blok = []
            else:
                tekst = schoon(blok)
                if tekst:
                    items.append((pijler, tekst.splitlines()[0].strip(), tekst))
                blok = None
            continue
        if blok is not None:
            blok.append(regel)
        elif pijler == "the_fork":
            m = re.match(r"^(\d+)\. (.+?) — (.+)$", regel)
            if m:
                inhoud = re.sub(r"\s*\*\(.*?\)\*\s*$", "", m.group(3)).strip()
                items.append((pijler, m.group(2).strip(), inhoud))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--toon", action="store_true")
    args = ap.parse_args()
    conn = verbind()
    nieuw = 0
    for pijler, titel, tekst in lees():
        cur = conn.execute("INSERT OR IGNORE INTO instagram_bron (pijler, titel, tekst) VALUES (?, ?, ?)", (pijler, titel, tekst))
        nieuw += cur.rowcount
    conn.commit()
    print(f"{nieuw} nieuwe onderwerpen ingelezen.")
    for pijler, n in conn.execute("SELECT pijler, COUNT(*) FROM instagram_bron GROUP BY pijler ORDER BY pijler"):
        print(f"  {pijler}: {n}")
    if args.toon:
        for pijler, titel in conn.execute("SELECT pijler, titel FROM instagram_bron ORDER BY pijler, id"):
            print(f"  [{pijler}] {titel}")


if __name__ == "__main__":
    main()
