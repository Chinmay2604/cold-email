import time
import requests
from utils.logger import log, log_warning

OCEAN_BASE = "https://api.ocean.io/v3"

def find_lookalike_companies(seed_domain: str, config: dict, limit: int = 10) -> list[dict]:
    api_key = config["OCEAN_API_KEY"]
    log(f"Fetching lookalike companies for: {seed_domain}")
    payload = {
        "size": limit,
        "companiesFilters": {"lookalikeDomains": [seed_domain]},
    }
    try:
        resp = requests.post(
            f"{OCEAN_BASE}/search/companies",
            params={"apiToken": api_key},
            json=payload,
            timeout=30,
        )
        if resp.status_code != 200:
            log_warning(f"Ocean.io API error {resp.status_code}: {resp.text[:300]}")
            return []
        data = resp.json()
        raw_companies = data.get("companies", [])
        companies = []
        for raw in raw_companies:
            domain = (raw.get("company", raw).get("domain") or "").replace("https://", "").replace("http://", "").rstrip("/")
            if not domain:
                continue
            companies.append({
                "name": raw.get("company", raw).get("name", domain),
                "domain": domain,
                "employee_count": raw.get("company", raw).get("employeeCountOcean"),
                "industry": (raw.get("company", raw).get("industryCategories") or [""])[0],
                "ocean_id": raw.get("company", raw).get("id", ""),
            })
        return companies[:limit]
    except requests.RequestException as e:
        log_warning(f"Request failed: {e}")
        return []
