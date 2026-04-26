"""
IntelOS — Master Collection Script

Haalt meetings op van Fathom en slaat ze op in de database.
Draai dit dagelijks of handmatig na een meeting.

Gebruik:
    python scripts/intel/collect_all.py              # Alles
    python scripts/intel/collect_all.py --days 30   # Laatste 30 dagen
    python scripts/intel/collect_all.py --meetings-only
"""

import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts" / "intel"))

from db import get_connection, write_meeting, get_meeting_stats
from collect_fathom import collect as fathom_collect


def run(days: int = 7, meetings_only: bool = True):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] IntelOS collectie gestart (laatste {days} dagen)")

    conn = get_connection()
    total_new = 0

    # Fathom meetings ophalen
    print("  Fathom meetings ophalen...", end="", flush=True)
    meetings = fathom_collect(days=days)

    if meetings:
        new = 0
        for m in meetings:
            if write_meeting(conn, m):
                new += 1
        print(f" OK ({new} nieuw van {len(meetings)} totaal)")
        total_new += new
    else:
        print(" Geen nieuwe meetings")

    conn.close()

    stats_conn = get_connection()
    stats = get_meeting_stats(stats_conn)
    stats_conn.close()

    print(f"[{timestamp}] Klaar — {total_new} nieuwe records. Totaal in database: {stats['total_meetings']} meetings")
    return total_new


def main():
    parser = argparse.ArgumentParser(description="IntelOS data verzamelen")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--meetings-only", action="store_true")
    args = parser.parse_args()
    run(days=args.days, meetings_only=True)


if __name__ == "__main__":
    main()
