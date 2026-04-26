"""
IntelOS — Database Framework

Beheert de SQLite database voor meetings en transcripts.
Deelt de bestaande data.db database met DataOS.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            title TEXT,
            date TEXT,
            start_time TEXT,
            duration_minutes INTEGER,
            participants TEXT,
            transcript_text TEXT,
            summary TEXT,
            action_items_raw TEXT,
            external_url TEXT,
            stream TEXT DEFAULT 'general',
            collected_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS staff_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT NOT NULL,
            role TEXT,
            team TEXT DEFAULT 'company',
            department TEXT DEFAULT 'general'
        )
    """)
    conn.commit()


def get_meeting_stats(conn):
    total = conn.execute("SELECT COUNT(*) as n FROM meetings").fetchone()["n"]
    latest = conn.execute("SELECT MAX(date) as d FROM meetings").fetchone()["d"]
    team = conn.execute("SELECT COUNT(*) as n FROM staff_registry").fetchone()["n"]
    return {
        "total_meetings": total,
        "total_slack_messages": 0,
        "team_members": team,
        "latest_meeting_date": latest
    }


def write_meeting(conn, meeting: dict) -> bool:
    try:
        conn.execute("""
            INSERT OR REPLACE INTO meetings
            (meeting_id, source, title, date, start_time, duration_minutes,
             participants, transcript_text, summary, action_items_raw, external_url,
             stream, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meeting["meeting_id"], meeting["source"], meeting.get("title"),
            meeting.get("date"), meeting.get("start_time"), meeting.get("duration_minutes"),
            meeting.get("participants"), meeting.get("transcript_text"),
            meeting.get("summary"), meeting.get("action_items_raw"),
            meeting.get("external_url"), meeting.get("stream", "general"),
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    conn = get_connection()
    stats = get_meeting_stats(conn)
    print(f"Database: {DB_PATH}")
    print(f"Meetings: {stats['total_meetings']}")
    print(f"Teamleden: {stats['team_members']}")
    conn.close()
