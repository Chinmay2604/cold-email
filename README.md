# Cold Outreach Pipeline

One input. Four stages. A full outreach engine.

```
company.domain → Ocean.io → Prospeo → Email Finder → Brevo → sent
```

## Setup

```bash
# 1. Clone / download this folder
# 2. Install dependencies (only 'requests' needed)
pip install -r requirements.txt

# 3. Create your .env file
cp .env.example .env
# Edit .env and fill in your API keys

# 4. Run it
python main.py stripe.com
```

## Usage

```
python main.py <seed_domain> [options]

Options:
  --limit N          Max lookalike companies to process (default: 10)
  --dry-run          Run all stages but don't actually send emails
  --skip-checkpoint  Skip the confirmation prompt before sending
```

## Examples

```bash
# Full run — finds lookalikes of stripe.com, resolves emails, sends outreach
python main.py stripe.com

# Safe test — runs all stages, shows what would be sent, but doesn't send
python main.py stripe.com --dry-run

# Limit to 5 companies
python main.py stripe.com --limit 5
```

## Pipeline Stages

| Stage | Tool | What it does |
|-------|------|--------------|
| 1 | Ocean.io | Finds companies similar to your seed domain |
| 2 | Prospeo `/domain-search` | Finds C-suite / VP decision-makers per company |
| 3 | Prospeo `/linkedin-email-finder` | Resolves verified work emails |
| 4 | Brevo | Sends personalized outreach emails |

## Safety Features

- **Dry run mode** — test without sending a single email
- **Safety checkpoint** — shows full send list before any email fires
- **Email status filtering** — only sends to `valid` / `verified` emails
- **Rate limit handling** — auto-retries on 429 with backoff
- **Partial failure resilience** — one bad stage doesn't crash the whole run

## Customising the Email Copy

Edit `stages/stage4_brevo.py` → `_compose_email()`. The template already
personalises by role (CEO vs CTO vs Sales), but the value proposition line
is a placeholder you must fill in:

```python
# Replace this:
"We help companies like yours [your value prop in one line — edit this]"
# With your actual pitch
```

## Project Structure

```
outreach_pipeline/
├── main.py                  # CLI entry point
├── config.py                # .env loader
├── requirements.txt
├── .env.example             # copy → .env, fill in keys
├── stages/
│   ├── stage1_ocean.py      # Find lookalike companies
│   ├── stage2_prospeo.py    # Find decision-makers
│   ├── stage3_email.py      # Resolve work emails
│   └── stage4_brevo.py      # Send outreach
└── utils/
    ├── logger.py            # Coloured terminal output
    └── checkpoint.py        # Pre-send confirmation prompt
```
