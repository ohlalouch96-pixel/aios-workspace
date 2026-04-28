#!/usr/bin/env python3
"""GTD inbox writer — voeg items toe aan gtd/inbox.md.

Voegt items veilig toe aan de GTD inbox vanuit elke bron
(scripts, Telegram, pipelines).

Gebruik:
    # Als module
    from inbox_writer import capture_to_inbox
    capture_to_inbox("Kapper Hassan bellen over afspraak", source="telegram")

    # Via commandoregel
    python3 scripts/inbox_writer.py "Kapper Hassan bellen over afspraak"
"""

import sys
from datetime import datetime
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _SCRIPT_DIR.parent
if not (_WORKSPACE_ROOT / "gtd").is_dir():
    _WORKSPACE_ROOT = _WORKSPACE_ROOT.parent

INBOX_PATH = _WORKSPACE_ROOT / "gtd" / "inbox.md"
EMPTY_MARKER = "_(Leeg — inbox staat op nul)_"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def capture_to_inbox(item: str, source: str = "manual") -> str:
    """
    Voeg een item toe aan gtd/inbox.md.

    Args:
        item: De tekst om vast te leggen
        source: Bronidentificatie (manual, telegram, claude, voice)

    Returns:
        De geformatteerde regel die is geschreven
    """
    if not INBOX_PATH.exists():
        raise FileNotFoundError(
            f"Inbox niet gevonden op {INBOX_PATH} — zorg dat je in je workspace root bent "
            f"en dat de GTD-module is geïnstalleerd (gtd/inbox.md moet bestaan)"
        )

    timestamp = _timestamp()
    line = f"- [{timestamp}] (bron:{source}) {item}"

    content = INBOX_PATH.read_text(encoding="utf-8")

    if EMPTY_MARKER in content:
        content = content.replace(EMPTY_MARKER, "").rstrip()

    if content and not content.endswith("\n"):
        content += "\n"

    content += line + "\n"
    INBOX_PATH.write_text(content, encoding="utf-8")

    return line


def capture_batch(items: list, source: str = "manual") -> int:
    """Voeg meerdere items tegelijk toe aan de inbox."""
    for item in items:
        capture_to_inbox(item, source=source)
    return len(items)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        result = capture_to_inbox(text, source="cli")
        print(f"Vastgelegd: {result}")
    else:
        print("Gebruik: python scripts/inbox_writer.py 'Jouw taak hier'")
