"""
utils/checkpoint.py — Safety checkpoint before emails fire
Shows a summary table and asks for explicit confirmation.
"""


def show_checkpoint(contacts: list[dict]) -> bool:
    """
    Display a summary of who will receive emails and ask for confirmation.
    Returns True if the user says yes, False to abort.
    """
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              ⚠  SAFETY CHECKPOINT  ⚠                        ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  {len(contacts)} email(s) will be sent:                              ")
    print("╠══════════════════════════════════════════════════════════════╣")

    for i, c in enumerate(contacts, 1):
        name = c.get("full_name", "Unknown")[:28]
        email = c.get("email", "?")[:35]
        company = c.get("company_name", "?")[:20]
        print(f"║  {i:>2}. {name:<28}  {email:<35}")
        print(f"║      {c.get('title', '')[:30]:<30} @ {company}")
        print("║")

    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    while True:
        answer = input("  Proceed and send all emails? [yes / no]: ").strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n", ""):
            return False
        print("  Please type 'yes' or 'no'.")
