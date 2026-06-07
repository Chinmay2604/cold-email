"""
config.py — Load API keys from environment / .env file
"""

import os
import sys
from pathlib import Path


def load_config() -> dict:
    """
    Load API keys from a .env file or environment variables.
    Returns a dict with all required keys.
    Exits loudly if any required key is missing.
    """
    _load_dotenv()

    required = {
        "OCEAN_API_KEY": "Ocean.io API key",
        "PROSPEO_API_KEY": "Prospeo API key",
        "BREVO_API_KEY": "Brevo (Sendinblue) API key",
        "SENDER_EMAIL": "Your verified sender email address",
        "SENDER_NAME": "Your name / company name",
    }

    config = {}
    missing = []

    for key, description in required.items():
        value = os.environ.get(key, "").strip()
        if not value:
            missing.append(f"  {key}  ({description})")
        else:
            config[key] = value

    if missing:
        print("\n[ERROR] Missing required environment variables:")
        for m in missing:
            print(m)
        print("\nCreate a .env file next to main.py with these values.")
        print("See .env.example for the template.\n")
        sys.exit(1)

    return config


def _load_dotenv():
    """
    Minimal .env loader — no external dependency needed.
    Reads KEY=VALUE lines; ignores comments and blank lines.
    """
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Don't overwrite real env vars
            if key and key not in os.environ:
                os.environ[key] = value
