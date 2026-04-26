"""
IntelOS — Fathom Collector

Haalt meeting-opnames en transcripts op via de Fathom API.
Slaat alles op in de lokale database voor AI-zoekfuncties.

Vereiste .env variabelen:
    FATHOM_API_KEY — vanuit app.fathom.video > Settings > Integrations > API

Tabellen: meetings
"""

import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

try:
    import requests
except ImportError:
    raise ImportError("Ontbrekend package — draai: pip install requests")

BASE_URL = "https://api.fathom.ai/external/v1"


def collect(days: int = 7) -> list[dict]:
    api_key = os.getenv("FATHOM_API_KEY", "").strip()
    if not api_key:
        print("OVERGESLAGEN: FATHOM_API_KEY niet ingesteld in .env")
        return []

    headers = {"X-Api-Key": api_key}
    meetings = []

    try:
        params = {"include_summary": "true", "include_transcript": "true"}
        r = requests.get(f"{BASE_URL}/meetings", headers=headers, params=params, timeout=30)

        if r.status_code == 401:
            print("FOUT: Ongeldige Fathom API-sleutel")
            return []
        r.raise_for_status()

        data = r.json()
        items = data if isinstance(data, list) else data.get("data", data.get("meetings", []))

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        for item in items:
            # Datum verwerken
            date_str = item.get("started_at") or item.get("date") or item.get("created_at", "")
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    if dt < cutoff:
                        continue
                    date_only = dt.strftime("%Y-%m-%d")
                    time_only = dt.strftime("%H:%M:%S")
                except Exception:
                    date_only = date_str[:10] if len(date_str) >= 10 else date_str
                    time_only = None
            else:
                date_only = None
                time_only = None

            # Deelnemers
            participants = item.get("attendees") or item.get("participants") or []
            if isinstance(participants, list):
                participants_json = json.dumps([
                    {"name": p.get("name", p) if isinstance(p, dict) else str(p),
                     "email": p.get("email", "") if isinstance(p, dict) else ""}
                    for p in participants
                ])
            else:
                participants_json = json.dumps([])

            # Transcript
            transcript = item.get("transcript") or item.get("transcript_text") or ""
            if isinstance(transcript, list):
                transcript = " ".join([
                    f"{t.get('speaker', '')}: {t.get('text', '')}"
                    for t in transcript
                ])

            # Samenvatting
            summary = item.get("summary") or item.get("summary_text") or ""
            if isinstance(summary, dict):
                summary = summary.get("text", str(summary))

            meetings.append({
                "meeting_id": str(item.get("id") or item.get("uuid") or item.get("call_id", "")),
                "source": "fathom",
                "title": item.get("title") or item.get("name") or "Naamloos gesprek",
                "date": date_only,
                "start_time": time_only,
                "duration_minutes": item.get("duration") or item.get("duration_minutes"),
                "participants": participants_json,
                "transcript_text": transcript,
                "summary": summary,
                "action_items_raw": json.dumps(item.get("action_items", [])),
                "external_url": item.get("url") or item.get("share_url") or "",
                "stream": "general"
            })

        return meetings

    except requests.RequestException as e:
        print(f"FOUT bij ophalen Fathom meetings: {e}")
        return []


if __name__ == "__main__":
    print("Fathom meetings ophalen (laatste 30 dagen)...")
    meetings = collect(days=30)
    if meetings:
        print(f"{len(meetings)} meeting(s) gevonden:")
        for m in meetings:
            print(f"  {m['date']} — {m['title']} ({m['duration_minutes'] or '?'} min)")
    else:
        print("Geen meetings gevonden. Heeft Fathom al een gesprek opgenomen?")
        print("Tip: Fathom neemt pas op als het aan een Google Meet / Zoom uitgenodigd is.")
