#!/usr/bin/env python3
"""
Cold Outreach Pipeline — Engineering Take-Home
One input (company.domain) → four stages → emails sent automatically.
"""

import sys
import argparse
from config import load_config
from stages.stage1_ocean import find_lookalike_companies
from stages.stage2_prospeo import find_decision_makers
from stages.stage3_email import resolve_emails
from stages.stage4_brevo import send_outreach
from utils.logger import log, log_section, log_success, log_warning
from utils.checkpoint import show_checkpoint


def parse_args():
    parser = argparse.ArgumentParser(
        description="Automated cold-outreach pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py stripe.com
  python main.py stripe.com --limit 5
  python main.py stripe.com --dry-run
        """,
    )
    parser.add_argument("domain", help="Seed company domain (e.g. stripe.com)")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max lookalike companies to process (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run all stages but skip sending emails (safety mode)",
    )
    parser.add_argument(
        "--skip-checkpoint",
        action="store_true",
        help="Skip the safety checkpoint before sending emails",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    seed_domain = args.domain.strip().lower()

    log_section("COLD OUTREACH PIPELINE")
    log(f"Seed domain : {seed_domain}")
    log(f"Limit       : {args.limit} companies")
    log(f"Dry run     : {args.dry_run}")
    print()

    # Load API keys from .env
    config = load_config()

    # ── STAGE 1: Find lookalike companies via Ocean.io ────────────────────────
    log_section("STAGE 1 — Find Lookalike Companies (Ocean.io)")
    companies = find_lookalike_companies(seed_domain, config, limit=args.limit)
    if not companies:
        log_warning("No lookalike companies found. Exiting.")
        sys.exit(1)
    log_success(f"Found {len(companies)} companies")
    for c in companies:
        log(f"  • {c['name']} — {c['domain']}")
    print()

    # ── STAGE 2: Find decision-makers via Prospeo ─────────────────────────────
    log_section("STAGE 2 — Find Decision-Makers (Prospeo)")
    contacts = find_decision_makers(companies, config)
    if not contacts:
        log_warning("No decision-makers found. Exiting.")
        sys.exit(1)
    log_success(f"Found {len(contacts)} decision-maker(s)")
    for c in contacts:
        log(f"  • {c.get('full_name', 'Unknown')} — {c.get('title', '')} @ {c.get('company_domain', '')}")
    print()

    # ── STAGE 3: Resolve verified work emails via Prospeo Email Finder ────────
    log_section("STAGE 3 — Resolve Work Emails (Prospeo Email Finder)")
    contacts_with_emails = resolve_emails(contacts, config)
    if not contacts_with_emails:
        log_warning("No verified emails resolved. Exiting.")
        sys.exit(1)
    log_success(f"Resolved {len(contacts_with_emails)} verified email(s)")
    for c in contacts_with_emails:
        log(f"  • {c['full_name']} — {c['email']}")
    print()

    # ── SAFETY CHECKPOINT ─────────────────────────────────────────────────────
    if not args.skip_checkpoint and not args.dry_run:
        proceed = show_checkpoint(contacts_with_emails)
        if not proceed:
            log_warning("Aborted at checkpoint. No emails sent.")
            sys.exit(0)
        print()

    # ── STAGE 4: Send personalized outreach via Brevo ─────────────────────────
    log_section("STAGE 4 — Send Personalized Outreach (Brevo)")
    if args.dry_run:
        log_warning("DRY RUN — skipping actual email send")
        for c in contacts_with_emails:
            log(f"  [DRY RUN] Would email {c['full_name']} <{c['email']}>")
    else:
        results = send_outreach(contacts_with_emails, config)
        sent = sum(1 for r in results if r["status"] == "sent")
        failed = sum(1 for r in results if r["status"] == "failed")
        log_success(f"Sent: {sent} | Failed: {failed}")
        for r in results:
            icon = "✓" if r["status"] == "sent" else "✗"
            log(f"  {icon} {r['name']} <{r['email']}> — {r['status']}")

    print()
    log_section("PIPELINE COMPLETE")


if __name__ == "__main__":
    main()
