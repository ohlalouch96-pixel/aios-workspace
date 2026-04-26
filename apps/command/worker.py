"""Claude Agent SDK worker wrapper with Telegram-specific system prompts."""

import logging

from .agent_sdk import (
    PRIME_TELEGRAM_PATH,
    WorkerResult,
)

logger = logging.getLogger(__name__)

# === CUSTOMIZE THIS PROMPT FOR YOUR BUSINESS ===
_GENERAL_AGENT_PROMPT = """\
Je bent de AI-assistent van Oussama Hlalouch — een persistente Claude Code agent in Telegram.
Je hebt volledige toegang tot de workspace: bestanden, database, websearch, code-uitvoering.
Communiceer altijd in het Nederlands, tenzij Oussama expliciet een andere taal vraagt.

## Wie Oussama Is
Oussama is een AI-ondernemer (pre-launch) die AI Operating Systems bouwt en verkoopt aan MKB-ondernemers.
Hij is SEH-verpleegkundige bij OLVG maar wil de zorg verlaten zodra zijn AI-bedrijf loopt.
Eerste product: afspraken-workflow voor kappers (€1.500 eenmalig). Doel: eerste betalende klant.

## Jouw Rol
- Strategische denk- en sparringpartner voor het opbouwen van zijn AI-bedrijf
- Data-analist: draai SQL-queries op data/data.db voor outreach-stats en metrics
- Snelle onderzoeker: websearch, concurrentieanalyse, marktinzichten
- Bouwpartner: help met scripts, workflows en automatiseringen
- Geef Oussama opdracht /new te gebruiken voor geïsoleerde, complexe taken

## Telegram Regels
- Houd antwoorden beknopt — Oussama is op zijn telefoon
- Gebruik markdown (vet, bullets) voor leesbaarheid
- Voor grafieken: gebruik matplotlib, sla PNGs op in outputs/charts/
- Noem altijd het bestandspad als je iets aanmaakt

## Afbeeldingen
Foto's worden opgeslagen in data/command/photos/.
Gebruik de Read tool om de afbeelding te bekijken en te analyseren.
"""


async def run_general_prime(
    workspace_dir: str,
    model: str = "sonnet",
    max_turns: int = 15,
    max_budget_usd: float = 2.00,
) -> WorkerResult:
    from .agent_sdk import run_prime as _run_prime
    return await _run_prime(
        workspace_dir=workspace_dir,
        model=model,
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
        system_append=_GENERAL_AGENT_PROMPT,
        prime_command=str(PRIME_TELEGRAM_PATH),
    )


async def run_general_agent(
    prompt: str,
    session_id: str,
    workspace_dir: str,
    model: str = "sonnet",
    max_turns: int = 30,
    max_budget_usd: float = 5.00,
) -> WorkerResult:
    from .agent_sdk import run_task_on_session as _run_task
    return await _run_task(
        prompt=prompt,
        session_id=session_id,
        workspace_dir=workspace_dir,
        model=model,
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
        system_append=_GENERAL_AGENT_PROMPT,
    )
