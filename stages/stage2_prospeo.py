"""
Stage 2 — Find Decision-Makers via Prospeo /search-person
New API: POST https://api.prospeo.io/search-person
Auth: X-KEY header
"""

import time
import requests
from utils.logger import log, log_warning

PROSPEO_BASE = "https://api.prospeo.io"


def find_decision_makers(companies: list[dict], config: dict) -> list[dict]:
    api_key = config["PROSPEO_API_KEY"]
    headers = {"X-KEY": api_key, "Content-Type": "application/json"}

    all_contacts = []

    for i, company in enumerate(companies):
        domain = company["domain"]
        name = company["name"]
        log(f"  [{i+1}/{len(companies)}] Searching decision-makers @ {domain}...")

        contacts = _search_people(domain, name, headers)
        log(f"    → {len(contacts)} decision-maker(s) found")
        all_contacts.extend(contacts)

        if i < len(companies) - 1:
            time.sleep(0.5)

    # Deduplicate by person_id or linkedin_url
    seen = set()
    unique = []
    for c in all_contacts:
        key = c.get("person_id") or c.get("linkedin_url") or c.get("full_name", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def _search_people(domain: str, company_name: str, headers: dict) -> list[dict]:
    payload = {
        "filters": {
            "company": {
                "websites": {"include": [domain]}
            },
            "person_seniority": {
                "include": ["C-Suite", "Vice President", "Director", "Founder/Owner", "Partner"]
            },
            "max_person_per_company": 3,
        },
        "page": 1,
    }

    try:
        resp = requests.post(
            f"{PROSPEO_BASE}/search-person",
            headers=headers,
            json=payload,
            timeout=20,
        )

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 10))
            log_warning(f"Rate limited on {domain}. Waiting {retry_after}s...")
            time.sleep(retry_after)
            resp = requests.post(f"{PROSPEO_BASE}/search-person", headers=headers, json=payload, timeout=20)

        if resp.status_code != 200:
            log_warning(f"Prospeo error {resp.status_code} for {domain}: {resp.text[:150]}")
            return []

        data = resp.json()
        if data.get("error"):
            log_warning(f"Prospeo error for {domain}: {data.get('error_code', 'unknown')}")
            return []

        people = [r.get("person", r) for r in (data.get("results", []) or [])]
        contacts = []
        for p in people:
            first = p.get("first_name", "")
            last = p.get("last_name", "")
            full = p.get("full_name") or f"{first} {last}".strip()
            contacts.append({
                "person_id": p.get("person_id", ""),
                "full_name": full,
                "first_name": first or (full.split()[0] if full else ""),
                "last_name": last or (full.split()[-1] if full and " " in full else ""),
                "title": p.get("current_job_title", ""),
                "linkedin_url": p.get("linkedin_url", ""),
                "company_domain": domain,
                "company_name": company_name,
            })
        return contacts

    except requests.RequestException as e:
        log_warning(f"Request failed for {domain}: {e}")
        return []
