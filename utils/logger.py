"""
utils/logger.py — Simple coloured terminal logger
"""

import sys

# ANSI colour codes
RESET  = "\033[0m"
BOLD   = "\033[1m"
BLUE   = "\033[94m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[2m"


def log(msg: str):
    print(msg)


def log_success(msg: str):
    print(f"{GREEN}✓ {msg}{RESET}")


def log_warning(msg: str):
    print(f"{YELLOW}⚠ {msg}{RESET}", file=sys.stderr)


def log_section(title: str):
    bar = "─" * 60
    print(f"\n{CYAN}{BOLD}{bar}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{bar}{RESET}")
