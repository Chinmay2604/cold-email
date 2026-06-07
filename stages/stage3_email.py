"""
Stage 3 — Resolve Verified Work Emails via Prospeo /enrich-person
New API: POST https://api.prospeo.io/enrich-person
Auth: X-KEY header

Uses person_id from Stage 2 search results for best accuracy.
Falls back to linkedin_url or name+domain.
"""

import time
import requests
from utils.logger import log, log_warning

PROSPEO_BASE = "https://api.prospeo.io"


def resolve_emails(contacts: list[dict], config: dict) -> list[dict]:
    api_key = config["PROSPEO_API_KEY"]
    headers = {"X-KEY": api_key, "Content-Type": "application/json"}

    resolved = []

    for i, contact in enumerate(contacts):
        name = contact.get("full_name", "Unknown")
        domain = contact.get("company_domain", "")
        log(f"  [{i+1}/{len(contacts)}] Resolving email for {name} @ {domain}...")

        email, status = _enrich_person(contact, headers)

        if email:
            log(f"    ✓ {email} [{status}]")
            resolved.append({**contact, "email": email, "email_status": status})
        else:
            log(f"    ✗ No verified email found")

        if i < len(contacts) - 1:
            time.sleep(1.0)

    return resolved


def _enrich_person(contact: dict, headers: dict) -> tuple:
    # Build data payload — use person_id if available (most accurate)
    data = {}

    if contact.get("person_id"):
        data["person_id"] = contact["person_id"]
    elif contact.get("linkedin_url"):
        data["linkedin_url"] = contact["linkedin_url"]
    else:
        first = contact.get("first_name", "")
        last = contact.get("last_name", "")
        domain = contact.get("company_domain", "")
        if not (first and last and domain):
            return None, None
        data["first_name"] = first
        data["last_name"] = last
        data["company_website"] = domain

    payload = {
        "only_verified_email": True,
        "data": data,
    }

    try:
        resp = requests.post(
            f"{PROSPEO_BASE}/enrich-person",
            headers=headers,
            json=payload,
            timeout=20,
        )

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 10))
            log_warning(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            resp = requests.post(f"{PROSPEO_BASE}/enrich-person", headers=headers, json=payload, timeout=20)

        if resp.status_code != 200:
            return None, None

        data_resp = resp.json()
        if data_resp.get("error"):
            return None, None

        person = data_resp.get("person", {}) or {}
        email_obj = person.get("email", {}) or {}
        email = email_obj.get("email")
        status = email_obj.get("status", "").lower()

        # Only return if actually revealed (not masked)
        if email and "*" not in email and status == "verified":
            return email, status

        return None, None

    except requests.RequestException as e:
        log_warning(f"Enrich-person failed: {e}")
        return None, None
