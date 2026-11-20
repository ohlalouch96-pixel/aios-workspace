"""
Instagram — wachtrij en administratie (@insightance.ai)

Houdt in data/data.db bij welke onderwerpen er zijn (instagram_bron) en welke
posts er gemaakt zijn (instagram_posts), met kleurenset, hashtags, bronnen en
status: concept -> goedgekeurd -> geplaatst (of overgeslagen). Bewaakt de
kleurregel en de hashtag-afwisseling uit workflows/instagram_content.md.

Gebruik (CLI):
    python tools/instagram/wachtrij.py stand                      # overzicht
    python tools/instagram/wachtrij.py volgende [--pijler myth_check]
    python tools/instagram/wachtrij.py kleur                      # kleurenset voor de volgende post
    python tools/instagram/wachtrij.py hashtags                   # hashtags van de laatste posts (niet herhalen)
    python tools/instagram/wachtrij.py opslaan pad/naar/spec.json # concept vastleggen
    python tools/instagram/wachtrij.py status 12 goedgekeurd
"""

import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"

NAVY = "navy"
ANDERE_KLEUREN = ["zwart", "blauw", "groen", "creme", "rood", "paars"]
STATUSSEN = ["concept", "goedgekeurd", "geplaatst", "overgeslagen"]
CARROUSEL_PIJLERS = ["automation_simplified", "myth_check"]


def verbind():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS instagram_bron (
            id INTEGER PRIMARY KEY,
            pijler TEXT NOT NULL,
            titel TEXT NOT NULL UNIQUE,
            tekst TEXT NOT NULL,
            ingelezen_op TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS instagram_feedback (
            id INTEGER PRIMARY KEY,
            post_id INTEGER NOT NULL REFERENCES instagram_posts(id),
            tekst TEXT NOT NULL,
            verwerkt INTEGER NOT NULL DEFAULT 0,
            gemaakt_op TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS instagram_posts (
            id INTEGER PRIMARY KEY,
            bron_id INTEGER REFERENCES instagram_bron(id),
            soort TEXT NOT NULL,
            onderwerp TEXT NOT NULL,
            kleurenset TEXT,
            hashtags TEXT,
            caption TEXT,
            bronnen TEXT,
            map TEXT,
            status TEXT NOT NULL DEFAULT 'concept',
            gemaakt_op TEXT DEFAULT (datetime('now')),
            bijgewerkt_op TEXT DEFAULT (datetime('now'))
        );
    """)
    kolommen = {r[1] for r in conn.execute("PRAGMA table_info(instagram_posts)")}
    if "muziek" not in kolommen:
        conn.execute("ALTER TABLE instagram_posts ADD COLUMN muziek TEXT")
    if "dienst" not in kolommen:  # welke dienst van de website een video met stem had (tools/instagram/diensten.py)
        conn.execute("ALTER TABLE instagram_posts ADD COLUMN dienst TEXT")
    if "gepland_op" not in kolommen:  # dag uit de weekplanning (JJJJ-MM-DD); na die dag 20:00 automatisch 'geplaatst'
        conn.execute("ALTER TABLE instagram_posts ADD COLUMN gepland_op TEXT")
    return conn


AFSLUITER = ("I build AI systems for business owners, so you and your team can focus on the work that actually matters.\n"
             "Send me a DM and I'll show you what's possible for your business ⚡")


def volledige_caption(caption, hashtags, soort):
    """Caption zoals hij op Instagram komt: tekst, vaste afsluiter, hashtags. The Fork: alleen de tekst."""
    if soort == "fork":
        return caption.strip()
    if soort in ("advertentie", "openbaar"):  # advertentie eindigt op "Follow for more", bouwen-in-het-openbaar op een vraag: geen DM-afsluiter
        return f"{caption.strip()}\n\n{' '.join(hashtags)}".strip()
    caption = caption.replace(AFSLUITER, "").strip()  # staat de afsluiter er al in, dan niet dubbel
    return f"{caption}\n\n{AFSLUITER}\n\n{' '.join(hashtags)}".strip()


BLAUWIG = {NAVY, "blauw", "wit"}  # wit = logokleuren (navy/blauw) op wit: oogt ook blauw


def echte_kleur(k):
    """Demo-reels en advertenties staan in de wachtrij met hun demonaam (bijv. 'calculatie'); vertaal naar hun kleurenset."""
    if k in ANDERE_KLEUREN + [NAVY, "wit"]:
        return k
    spec = Path(__file__).resolve().parent / "demos" / f"{k}.json"
    try:
        return json.loads(spec.read_text(encoding="utf-8")).get("kleurenset", NAVY)
    except (OSError, ValueError):
        return NAVY  # schets-ondergronden e.d. tellen als neutraal/navy


def recente_kleuren(conn, n=8):
    rows = conn.execute("SELECT kleurenset FROM instagram_posts WHERE status != 'overgeslagen' AND kleurenset IS NOT NULL ORDER BY id DESC LIMIT ?", (n,))
    return [echte_kleur(r[0]) for r in rows]


def kies_kleur(conn, video=False):
    """Kleurregel (aangepast 15-11, Oussama: te veel blauw): navy ongeveer 1 op de 3, nooit twee blauwige posts
    (navy, blauw, wit) achter elkaar, en verder de kleur die het langst niet gebruikt is (zwart, groen, creme,
    rood, paars; blauw en bij video ook wit). video=True: 'wit' bestaat alleen voor video's met stem."""
    recent = recente_kleuren(conn)
    andere = ANDERE_KLEUREN + (["wit"] if video else [])
    if recent and recent[0] in BLAUWIG:
        andere = [k for k in andere if k not in BLAUWIG]
    elif NAVY not in recent[:2] and random.random() < 0.5:
        return NAVY
    # langst niet gebruikt eerst; bij gelijke stand willekeurig
    nooit = [k for k in andere if k not in recent]
    if nooit:
        return random.choice(nooit)
    return max(andere, key=recent.index)


def recente_hashtags(conn, n=3):
    rows = conn.execute("SELECT hashtags FROM instagram_posts WHERE status != 'overgeslagen' AND hashtags IS NOT NULL ORDER BY id DESC LIMIT ?", (n,))
    return [json.loads(r[0]) for r in rows]


def volgende(conn, pijler=None):
    """Een willekeurig onderwerp dat nog niet gebruikt is (geen vaste volgorde, besluit 20-11; de bron bevat zowel
    geplaatste als nog geplande LinkedIn-posts). Zonder pijler: de carrousel-pijler die het langst niet aan de beurt was."""
    if pijler is None:
        laatst = {p: 0 for p in CARROUSEL_PIJLERS}
        for p, pid in conn.execute("SELECT b.pijler, MAX(p.id) FROM instagram_posts p JOIN instagram_bron b ON b.id = p.bron_id GROUP BY b.pijler"):
            if p in laatst:
                laatst[p] = pid
        pijler = min(laatst, key=laatst.get)
    return conn.execute("""
        SELECT id, pijler, titel, tekst FROM instagram_bron
        WHERE pijler = ? AND id NOT IN (SELECT bron_id FROM instagram_posts WHERE bron_id IS NOT NULL AND status != 'overgeslagen')
        ORDER BY RANDOM() LIMIT 1""", (pijler,)).fetchone()


def opslaan(conn, spec_pad):
    spec = json.loads(Path(spec_pad).read_text(encoding="utf-8"))
    cur = conn.execute(
        "INSERT INTO instagram_posts (bron_id, soort, onderwerp, kleurenset, hashtags, caption, bronnen, map, muziek, dienst) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (spec.get("bron_id"), spec["soort"], spec["onderwerp"], spec.get("kleurenset"), json.dumps(spec.get("hashtags", [])),
         spec.get("caption"), json.dumps(spec.get("bronnen", [])), spec.get("map"), spec.get("muziek"), spec.get("dienst")))
    conn.commit()
    return cur.lastrowid


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stand")
    v = sub.add_parser("volgende")
    v.add_argument("--pijler")
    sub.add_parser("kleur")
    sub.add_parser("hashtags")
    o = sub.add_parser("opslaan")
    o.add_argument("spec")
    s = sub.add_parser("status")
    s.add_argument("id", type=int)
    s.add_argument("status", choices=STATUSSEN)
    args = ap.parse_args()
    conn = verbind()

    if args.cmd == "stand":
        print("Bron (ongebruikt / totaal):")
        for p, tot, vrij in conn.execute("""SELECT pijler, COUNT(*), SUM(id NOT IN (SELECT bron_id FROM instagram_posts WHERE bron_id IS NOT NULL AND status != 'overgeslagen'))
                                            FROM instagram_bron GROUP BY pijler ORDER BY pijler"""):
            print(f"  {p}: {vrij} / {tot}")
        print("Posts per status:")
        for st, n in conn.execute("SELECT status, COUNT(*) FROM instagram_posts GROUP BY status"):
            print(f"  {st}: {n}")
    elif args.cmd == "volgende":
        rij = volgende(conn, args.pijler)
        print(json.dumps(dict(zip(["bron_id", "pijler", "titel", "tekst"], rij)), ensure_ascii=False, indent=2) if rij else "Geen ongebruikte onderwerpen meer in deze pijler.")
    elif args.cmd == "kleur":
        print(kies_kleur(conn))
    elif args.cmd == "hashtags":
        print(json.dumps(recente_hashtags(conn), ensure_ascii=False))
    elif args.cmd == "opslaan":
        print(f"Opgeslagen als post {opslaan(conn, args.spec)}")
    elif args.cmd == "status":
        conn.execute("UPDATE instagram_posts SET status = ?, bijgewerkt_op = datetime('now') WHERE id = ?", (args.status, args.id))
        conn.commit()
        print(f"Post {args.id} -> {args.status}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
