"""Runtime configuration.

Values resolve in this precedence order:
1. process environment variables,
2. a local ``.env`` file (loaded via python-dotenv),
3. built-in defaults for the deployed QA environment.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Root of the git repository (parent of this package's directory).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env (does not override already-set OS env vars).
load_dotenv(PROJECT_ROOT / ".env", override=False)

API_BASE_URL: str = os.getenv("API_BASE_URL").rstrip("/")
QA_USER_ID: str = os.getenv("QA_USER_ID")
UI_URL: str = f"{API_BASE_URL}/?user-id={QA_USER_ID}"

USER_ID_HEADER = "x-user-id"
API_TIMEOUT_SECONDS: float = 2.0
UI_TIMEOUT_SECONDS: float = 10.0

# Seconds to let a balance reset/persist settle before reading it back.
SETTLE_SECONDS: float = 1.2

# Run Chrome headless (set HEADLESS=false for a visible run).
HEADLESS: bool = os.getenv("HEADLESS", "true") == "true"

# Money/validation constants from the feature spec / OpenAPI.
STAKE_MIN = 1.00
STAKE_MAX = 100.00
CURRENCY = "EUR"
