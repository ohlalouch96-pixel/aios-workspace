"""
DataOS — Collection Orchestrator

Ontdekt en draait alle actieve collectors (collect_*.py bestanden in deze map).
Na collectie wordt key-metrics.md opnieuw gegenereerd.

Gebruik:
    python scripts/collect.py                           # Alle collectors
    python scripts/collect.py --sources outreach,fx     # Specifieke collectors
    python scripts/collect.py --date 2026-04-26         # Datum overschrijven
"""

import sys
import argparse
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def discover_collectors():
    collectors = {}
    for filepath in sorted(SCRIPT_DIR.glob("collect_*.py")):
        name = filepath.stem.replace("collect_", "")
        collectors[name] = filepath
    return collectors


def import_collector(name, filepath):
    spec = importlib.util.spec_from_file_location(f"collect_{name}", str(filepath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser(description="Verzamel data van alle bronnen")
    parser.add_argument("--sources", type=str, default=None)
    parser.add_argument("--date", type=str, default=None)
    args = parser.parse_args()

    today = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    available = discover_collectors()
    if not available:
        print(f"[{timestamp}] Geen collectors gevonden. Voeg collect_*.py bestanden toe aan scripts/")
        sys.exit(1)

    if args.sources:
        names = [s.strip() for s in args.sources.split(",")]
        names = [s for s in names if s in available]
    else:
        names = list(available.keys())

    sys.path.insert(0, str(SCRIPT_DIR))
    from db import init_db, log_collection

    conn = init_db()
    print(f"[{timestamp}] Collectie gestart — {len(names)} bronnen voor datum={today}")

    results = []
    for name in names:
        filepath = available[name]
        print(f"  Verzamelen {name}...", end="", flush=True)

        try:
            mod = import_collector(name, filepath)
            result = mod.collect()
            status = result.get("status", "unknown")

            if status == "success":
                records = mod.write(conn, result, today)
                log_collection(conn, name, "success", records)
                print(f" OK ({records} records)")
                results.append((name, "success", records))
            elif status == "skipped":
                reason = result.get("reason", "")
                log_collection(conn, name, "skipped", reason=reason)
                print(f" OVERGESLAGEN ({reason})")
                results.append((name, "skipped", 0))
            else:
                reason = result.get("reason", "")
                log_collection(conn, name, "error", reason=reason)
                print(f" FOUT ({reason})")
                results.append((name, "error", 0))

        except Exception as e:
            log_collection(conn, name, "exception", reason=str(e))
            print(f" UITZONDERING ({e})")
            results.append((name, "exception", 0))

    conn.close()

    successes = sum(1 for _, s, _ in results if s == "success")
    total_records = sum(r for _, _, r in results)
    skipped = sum(1 for _, s, _ in results if s == "skipped")
    errors = sum(1 for _, s, _ in results if s in ("error", "exception"))

    print(f"[{timestamp}] Klaar: {successes} geslaagd, {skipped} overgeslagen, {errors} fouten, {total_records} records totaal")

    if successes > 0:
        try:
            from generate_metrics import main as regen
            regen()
            print(f"[{timestamp}] Key metrics opnieuw gegenereerd")
        except Exception as e:
            print(f"[{timestamp}] Waarschuwing: metrics regeneratie mislukt: {e}")

    sys.exit(0 if successes > 0 else 1)


if __name__ == "__main__":
    main()
