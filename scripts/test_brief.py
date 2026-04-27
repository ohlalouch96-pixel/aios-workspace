import sys
import os
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from dotenv import load_dotenv
load_dotenv()

from scripts.daily_brief import run_daily_brief

result = run_daily_brief(preset="solo", dry_run=True, deliver=False)
if result:
    output_path = __import__('pathlib').Path(__file__).resolve().parent.parent / "outputs" / "brief-test.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")
    print(f"Brief opgeslagen: {output_path}")
else:
    print("Brief generatie mislukt.")
