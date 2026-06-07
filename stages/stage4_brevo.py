"""
Stage 4 — Send Personalized Outreach via Brevo (formerly Sendinblue)
Input  : list of verified contact dicts (from Stage 3)
Output : list of result dicts { name, email, status, message_id }
"""

import time
import requests
from utils.logger import log, log_warning

BREVO_BASE = "https://api.brevo.com/v3"


def send_outreach(contacts: list[dict], config: dict) -> list[dict]:
    """
    Send a personalized cold email to each contact via Brevo.
    Returns a list of send results.
    """
    api_key = config["BREVO_API_KEY"]
    sender_email = config["SENDER_EMAIL"]
    sender_name = config["SENDER_NAME"]

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    results = []

    for i, contact in enumerate(contacts):
        name = contact.get("full_name", "there")
        email = contact["email"]
        company = contact.get("company_name", "your company")
        title = contact.get("title", "")

        log(f"  [{i+1}/{len(contacts)}] Sending to {name} <{email}>...")

        subject, html_body, text_body = _compose_email(
            contact, sender_name
        )

        result = _send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            sender_email=sender_email,
            sender_name=sender_name,
            headers=headers,
        )

        result["name"] = name
        result["email"] = email
        results.append(result)

        if result["status"] == "sent":
            log(f"    ✓ Sent (message_id={result.get('message_id', '?')})")
        else:
            log_warning(f"    ✗ Failed: {result.get('error', 'unknown error')}")

        # Brevo rate limit: 300 emails/min on starter; ~0.2s gap is safe
        if i < len(contacts) - 1:
            time.sleep(0.3)

    return results


def _compose_email(contact: dict, sender_name: str) -> tuple[str, str, str]:
    """
    Compose a personalized cold email.
    The copy is short, specific, and non-spammy.
    Personalization tokens: first name, company name, title.
    """
    first_name = contact.get("first_name") or contact.get("full_name", "").split()[0] or "there"
    company = contact.get("company_name", "your company")
    title = contact.get("title", "")

    # Role-aware opener
    if "cto" in title.lower() or "tech" in title.lower() or "engineer" in title.lower():
        angle = f"noticed {company} is scaling its tech stack"
    elif "ceo" in title.lower() or "founder" in title.lower() or "president" in title.lower():
        angle = f"saw {company} is on an impressive growth trajectory"
    elif "marketing" in title.lower() or "growth" in title.lower() or "cmo" in title.lower():
        angle = f"noticed {company}'s recent push in demand generation"
    elif "sales" in title.lower() or "revenue" in title.lower():
        angle = f"saw {company} expanding its sales motion"
    else:
        angle = f"came across {company} and was impressed by what you're building"

    subject = f"Quick note for {first_name} @ {company}"

    text_body = f"""Hi {first_name},

I {angle} — wanted to reach out directly.

We help companies like yours [your value prop in one line — edit this]. I think there's a clear fit, and I'd love to show you what that could look like for {company}.

Would a 15-minute call this week make sense?

{sender_name}

P.S. Happy to share a few relevant case studies upfront if that's useful.
"""

    html_body = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
             font-size: 15px; line-height: 1.6; color: #111; max-width: 560px; margin: 0 auto; padding: 16px;">

<p>Hi {first_name},</p>

<p>I {angle} — wanted to reach out directly.</p>

<p>We help companies like yours <strong>[your value prop in one line — edit this]</strong>.
I think there's a clear fit, and I'd love to show you what that could look like for {company}.</p>

<p>Would a 15-minute call this week make sense?</p>

<p style="margin-top: 24px;">
{sender_name}<br>
</p>

<p style="font-size: 13px; color: #888;">
P.S. Happy to share a few relevant case studies upfront if that's useful.
</p>

</body>
</html>
"""

    return subject, html_body, text_body


def _send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_body: str,
    text_body: str,
    sender_email: str,
    sender_name: str,
    headers: dict,
) -> dict:
    """
    Send a single transactional email via Brevo API.
    """
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_body,
        "textContent": text_body,
        # Unsubscribe header — good practice for cold outreach
        "headers": {
            "List-Unsubscribe": f"<mailto:{sender_email}?subject=unsubscribe>",
        },
    }

    try:
        resp = requests.post(
            f"{BREVO_BASE}/smtp/email",
            headers=headers,
            json=payload,
            timeout=20,
        )

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 10))
            log_warning(f"Brevo rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            resp = requests.post(
                f"{BREVO_BASE}/smtp/email",
                headers=headers,
                json=payload,
                timeout=20,
            )

        if resp.status_code in (200, 201):
            data = resp.json()
            return {
                "status": "sent",
                "message_id": data.get("messageId", ""),
            }

        return {
            "status": "failed",
            "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
        }

    except requests.RequestException as e:
        return {"status": "failed", "error": str(e)}
