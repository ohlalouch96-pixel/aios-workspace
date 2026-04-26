"""
DataOS — FX Rates Collector (Starter)

Haalt wisselkoersen op via de Frankfurter API (gratis, geen API-sleutel nodig).
Dient als test om de pipeline te verifiëren.

Tabellen: fx_rates
"""

import sqlite3
from datetime import datetime, timezone

import requests

API_URL = "https://api.frankfurter.app/latest"
TARGET_CURRENCIES = ["EUR", "GBP", "USD", "AUD", "CAD"]


def collect():
    try:
        currencies = ",".join(TARGET_CURRENCIES)
        response = requests.get(f"{API_URL}?from=EUR&to={currencies}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "source": "fx_rates",
            "status": "success",
            "data": {
                "base": data.get("base", "EUR"),
                "date": data.get("date"),
                "rates": data.get("rates", {}),
            }
        }
    except Exception as e:
        return {"source": "fx_rates", "status": "error", "reason": str(e)}


def write(conn, result, date):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fx_rates (
            date TEXT NOT NULL,
            currency TEXT NOT NULL,
            rate REAL NOT NULL,
            base TEXT DEFAULT 'EUR',
            collected_at TEXT,
            PRIMARY KEY (date, currency)
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    data = result["data"]
    rates = data.get("rates", {})
    rate_date = data.get("date", date)
    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0

    for currency, rate in rates.items():
        conn.execute(
            "INSERT OR REPLACE INTO fx_rates (date, currency, rate, base, collected_at) VALUES (?, ?, ?, ?, ?)",
            (rate_date, currency, rate, "EUR", collected_at)
        )
        records += 1

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        print(f"Wisselkoersen voor {result['data']['date']}:")
        for curr, rate in sorted(result["data"]["rates"].items()):
            print(f"  EUR -> {curr}: {rate:.4f}")
    else:
        print(f"Fout: {result.get('reason')}")
