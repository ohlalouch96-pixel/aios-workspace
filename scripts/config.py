"""
DataOS — Configuration Loader

Leest API-sleutels uit het .env bestand in de workspace root.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = WORKSPACE_ROOT / ".env"

load_dotenv(ENV_PATH)


def get_env(key, required=True):
    value = os.getenv(key, "").strip()
    if not value:
        return None
    return value


def get_google_credentials_path():
    path = get_env("GOOGLE_SERVICE_ACCOUNT_JSON")
    if path is None:
        return None
    full_path = Path(path)
    if not full_path.is_absolute():
        full_path = WORKSPACE_ROOT / path
    if not full_path.exists():
        return None
    return str(full_path)
