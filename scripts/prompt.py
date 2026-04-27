"""
Daily Brief — Adaptive Mega-Prompt Builder

Assembles all available intelligence into a single prompt for Gemini:
- Business context (from ContextOS files)
- Funnel metrics (from DataOS database)
- Meeting transcripts (from IntelOS, if installed)
- Slack messages (from IntelOS, if installed)

The prompt adapts to what the user actually has — if they don't have
meetings or Slack, those sections are simply omitted.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# BRIEF PRESETS — Configurable report structures
# ============================================================

PRESETS = {
    "solo": {
        "name": "Solo Operator",
        "sections": [
            "executive_summary",
            "key_signals",
            "metrics_analysis",
            "action_items",
        ],
        "word_budget": 1500,
        "pdf_pages": "1-2",
    },
    "small_team": {
        "name": "Small Team",
        "sections": [
            "executive_summary",
            "key_signals",
            "metrics_analysis",
            "meeting_highlights",
            "slack_digest",
            "strategic_recommendations",
            "action_items",
        ],
        "word_budget": 3000,
        "pdf_pages": "3-5",
    },
    "agency": {
        "name": "Agency",
        "sections": [
            "executive_summary",
            "key_signals",
            "metrics_analysis",
            "department_analysis",
            "meeting_highlights",
            "slack_digest",
            "cross_stream_patterns",
            "strategic_recommendations",
            "action_items",
        ],
        "word_budget": 6000,
        "pdf_pages": "8-15",
    },
}


# ============================================================
# CONTEXT LOADING
# ============================================================

def load_business_context():
    """Load business context from ContextOS files.

    Reads whatever context files exist — adapts to the user's setup.
    Returns a single text block with all context concatenated.
    """
    # Priority-ordered list of context files to try
    context_files = [
        "context/overview.md",
        "context/group/overview.md",
        "context/strategy.md",
        "context/group/strategy.md",
        "context/team.md",
        "context/group/team.md",
        "context/about-me.md",
        "context/current-state.md",
        "context/funnel.md",
        "context/group/funnel.md",
        "context/group/key-metrics.md",
        "context/key-metrics.md",
    ]

    blocks = []
    loaded = set()

    for rel_path in context_files:
        full_path = WORKSPACE_ROOT / rel_path
        if full_path.exists():
            # Avoid loading both context/X.md and context/group/X.md
            filename = full_path.name
            if filename in loaded:
                continue
            loaded.add(filename)

            try:
                content = full_path.read_text()
                if content.strip():
                    blocks.append(f"=== {rel_path} ===\n{content}")
            except Exception:
                pass

    return "\n\n".join(blocks) if blocks else "No business context available."


def load_meeting_transcripts(conn, target_date):
    """Load meeting transcripts from IntelOS database tables.

    Groups by department/stream if the meetings table has been classified.
    Returns formatted text block, or empty string if no meetings table.
    """
    try:
        # Check if meetings table exists
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='meetings'"
        ).fetchone()
        if not row:
            return ""

        # Pull meetings from the target date
        meetings = conn.execute(
            "SELECT * FROM meetings WHERE date = ? ORDER BY start_time",
            (target_date,),
        ).fetchall()

        if not meetings:
            # Try a wider window (some recorders have lag)
            yesterday = (
                datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)
            ).strftime("%Y-%m-%d")
            meetings = conn.execute(
                "SELECT * FROM meetings WHERE date BETWEEN ? AND ? ORDER BY date, start_time",
                (yesterday, target_date),
            ).fetchall()

        if not meetings:
            return ""

        blocks = []
        for i, m in enumerate(meetings, 1):
            m = dict(m)
            title = m.get("title") or "Untitled"
            date = m.get("date", "")
            duration = m.get("duration_minutes") or "?"
            stream = m.get("stream") or "general"
            participants = m.get("participants") or "Unknown"
            transcript = m.get("transcript_text") or "(No transcript)"

            header = (
                f"--- CALL {i}: {title} | {date} | {duration} min ---\n"
                f"Department: {stream}\n"
                f"Participants: {participants}"
            )
            blocks.append(f"{header}\n\n{transcript}")

        return "\n\n\n".join(blocks)

    except Exception:
        return ""


def load_slack_messages(conn, target_date):
    """Load Slack messages from IntelOS database tables.

    Returns formatted text block, or empty string if no Slack data.
    """
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='slack_messages'"
        ).fetchone()
        if not row:
            return ""

        # Pull messages from the target date
        messages = conn.execute(
            "SELECT * FROM slack_messages WHERE date(ts) = ? "
            "ORDER BY workspace, channel_name, ts",
            (target_date,),
        ).fetchall()

        # Fall back to collected_at date if ts doesn't have date component
        if not messages:
            messages = conn.execute(
                "SELECT * FROM slack_messages WHERE date(collected_at) = ? "
                "ORDER BY workspace, channel_name, ts",
                (target_date,),
            ).fetchall()

        if not messages:
            return ""

        # Group by workspace → channel
        grouped = {}
        for msg in messages:
            msg = dict(msg)
            workspace = msg.get("workspace", "main")
            channel = msg.get("channel_name") or msg.get("channel_id", "unknown")
            key = f"{workspace}/{channel}"
            if key not in grouped:
                grouped[key] = []
            user = msg.get("user_name") or "Unknown"
            text = msg.get("text") or ""
            grouped[key].append(f"[{user}] {text}")

        blocks = []
        for channel, msgs in grouped.items():
            blocks.append(f"--- #{channel} ({len(msgs)} messages) ---")
            blocks.append("\n".join(msgs[:50]))  # Cap at 50 per channel

        return "\n\n".join(blocks)

    except Exception:
        return ""


# ============================================================
# MEGA-PROMPT ASSEMBLY
# ============================================================

def build_mega_prompt(metrics_text, context_text, meetings_text="",
                      slack_text="", preset="small_team",
                      custom_sections=None):
    """Assemble the full mega-prompt for Gemini.

    Args:
        metrics_text: Formatted funnel metrics (from metrics.py)
        context_text: Business context (from load_business_context)
        meetings_text: Meeting transcripts (from load_meeting_transcripts)
        slack_text: Slack messages (from load_slack_messages)
        preset: Which preset template to use
        custom_sections: Override preset sections with a custom list

    Returns:
        Complete prompt string ready for Gemini
    """
    config = PRESETS.get(preset, PRESETS["small_team"])
    sections = custom_sections or config["sections"]
    word_budget = config["word_budget"]

    # Build the section instruction
    section_instructions = _build_section_instructions(
        sections, word_budget, bool(meetings_text), bool(slack_text)
    )

    prompt_parts = [
        _build_system_instruction(sections, word_budget),
        "\n\n=== BUSINESS CONTEXT ===\n",
        context_text,
        "\n\n=== FUNNEL METRICS ===\n",
        metrics_text,
    ]

    if meetings_text:
        prompt_parts.append("\n\n=== MEETING TRANSCRIPTS ===\n")
        prompt_parts.append(meetings_text)

    if slack_text:
        prompt_parts.append("\n\n=== SLACK MESSAGES ===\n")
        prompt_parts.append(slack_text)

    prompt_parts.append("\n\n=== OUTPUT INSTRUCTIONS ===\n")
    prompt_parts.append(section_instructions)

    return "".join(prompt_parts)


def _build_system_instruction(sections, word_budget):
    """Build the system-level instruction for Gemini."""
    return f"""Je schrijft een dagelijkse intelligentiebriefing voor een Nederlandse ondernemer. Je hebt toegang tot zijn volledige bedrijfscontext, funnelmetrics en (indien beschikbaar) vergadertranscripten van de afgelopen dag.

Jouw taak is SYNTHETISEREN — niet samenvatten. Verbind informatie. Spot patronen. Markeer wat aandacht nodig heeft.

TAAL EN STIJL:
- Schrijf ALTIJD volledig in het Nederlands
- Direct, concreet en zonder omhaal — als een vertrouwde adviseur
- Gebruik EUR als valuta

OPMAAK:
- Gebruik ## markdown headers voor elke sectie
- Gebruik tabellen (markdown) voor metrics, vergelijkingen en actie-items waar dat overzicht geeft
- Maak heldere alinea's met witregels ertussen
- Gebruik **vetgedrukt** voor de meest kritische cijfers en signalen
- Gebruik emoji's spaarzaam maar effectief (⚠️ risico, 🔥 win, 💡 kans, 📊 metric)

INHOUD:
- Totale output: ongeveer {word_budget} woorden
- Begin met het belangrijkste signaal — het ene ding dat de eigenaar als eerste moet weten
- Wees specifiek: "€1.500 van 1 deal" niet "goede dag"
- Als data ontbreekt voor een sectie, sla die dan volledig over
"""


def _build_section_instructions(sections, word_budget, has_meetings, has_slack):
    """Build per-section output instructions."""
    # Word budget per section (roughly proportional)
    budget_map = {
        "executive_summary": 300,
        "key_signals": 200,
        "metrics_analysis": 400,
        "meeting_highlights": 500,
        "department_analysis": 800,
        "slack_digest": 400,
        "cross_stream_patterns": 400,
        "strategic_recommendations": 500,
        "action_items": 200,
    }

    section_defs = {
        "executive_summary": (
            "## De Dag in het Kort\n"
            "Schrijf een narratief van 200-300 woorden dat vertelt wat er is gebeurd. "
            "Vloeiende tekst in alinea's, geen bullet points. Begin met het belangrijkste signaal. "
            "Verbind metrics aan oorzaken. "
            "Sluit af met één zin over wat je vandaag in de gaten moet houden."
        ),
        "key_signals": (
            "## Belangrijkste Signalen\n"
            "6-10 signalen van één regel, elk beginnend met een emoji:\n"
            "🔥 = winst, momentum, deals gesloten\n"
            "⚠️ = risico's, dalingen, blokkades\n"
            "📌 = terugkerende patronen, strategische thema's\n"
            "💡 = kansen, ideeën\n"
            "📊 = opvallende metricbewegingen\n"
            "Elk signaal moet specifiek zijn: namen, cijfers. Geen generieke observaties."
        ),
        "metrics_analysis": (
            "## Metrics Analyse\n"
            "Analyseer de funnelmetrics per fase. Gebruik een tabel voor de cijfers:\n"
            "| Fase | Metric | Waarde | Doel | Status |\n"
            "|------|--------|--------|------|--------|\n"
            "Schrijf daarna per fase een korte analyse:\n"
            "- Wat er is gebeurd (specifieke cijfers)\n"
            "- Wat dit betekent voor het bedrijf\n"
            "- Wat er nu moet gebeuren\n"
            "Focus op bewegingen en afwijkingen."
        ),
        "meeting_highlights": (
            "## Vergaderingen & Gesprekken\n"
            "Per gesprek:\n"
            "- Genomen beslissingen\n"
            "- Actiepunten (wie, wat, wanneer)\n"
            "- Opvallende signalen (prospects, risico's, kansen)\n"
            if has_meetings
            else None
        ),
        "department_analysis": (
            "## Afdeling Analyse\n"
            "Verdeel vergaderingen per afdeling. Per afdeling:\n"
            "- Wat werkt, wat worstelt\n"
            "- Individuele prestatie-signalen\n"
            "- Pipeline gezondheid\n"
            "Wees specifiek — noem mensen en citeer ze."
            if has_meetings
            else None
        ),
        "slack_digest": (
            "## Slack Samenvatting\n"
            "Belicht de belangrijkste Slack-threads:\n"
            "- Genomen beslissingen\n"
            "- Verzoeken die een reactie nodig hebben\n"
            "- Wat de eigenaar moet weten of beantwoorden\n"
            if has_slack
            else None
        ),
        "cross_stream_patterns": (
            "## Patronen over Bronnen\n"
            "Identificeer 2-4 patronen die alleen zichtbaar worden door informatie te combineren. "
            "Elk patroon: naam in vet, bewijs uit 2+ bronnen, waarom het nu belangrijk is."
            if (has_meetings or has_slack)
            else None
        ),
        "strategic_recommendations": (
            "## Strategische Aanbevelingen\n"
            "Op basis van alles wat je hebt gelezen:\n"
            "**Zorgen** (1-3) — dingen die aandacht vereisen. Wees specifiek.\n"
            "**Kansen** (1-3) — dingen om nu op in te spelen.\n"
            "Elke aanbeveling moet uitvoerbaar zijn."
        ),
        "action_items": (
            "## Actielijst\n"
            "Maak een overzichtelijke tabel van alles wat gedaan moet worden:\n"
            "| # | Actie | Prioriteit | Deadline |\n"
            "|---|-------|-----------|----------|\n"
            "Sorteer op urgentie. Maximaal 8 items."
        ),
    }

    instructions = [
        "Produceer de volgende secties in deze exacte volgorde. "
        "Gebruik ## markdown headers precies zoals aangegeven. "
        "Schrijf ALLES in het Nederlands.\n"
    ]

    for section in sections:
        definition = section_defs.get(section)
        if definition is None:
            continue
        budget = budget_map.get(section, 300)
        instructions.append(f"\n{definition}\n(~{budget} words)")

    return "\n".join(instructions)


if __name__ == "__main__":
    """Quick test — show what context is available."""
    ctx = load_business_context()
    token_estimate = len(ctx) // 4
    print(f"Business context loaded: ~{token_estimate:,} tokens")
    print(f"Files found: {ctx.count('===') // 2}")
    print()
    for preset_key, preset_val in PRESETS.items():
        print(f"Preset '{preset_key}' ({preset_val['name']}):")
        print(f"  Sections: {', '.join(preset_val['sections'])}")
        print(f"  Word budget: ~{preset_val['word_budget']} words")
        print(f"  PDF length: {preset_val['pdf_pages']} pages")
