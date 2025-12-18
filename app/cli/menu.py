
from typing import Optional, List


def choose_from_list(
    items: List[str],
    title: str = "Available videos:",
    prompt: str = "Type the number of the video you want to process",
) -> Optional[str]:
    """
    Display a simple numbered menu and return the chosen item.
    Returns None if the user cancels.
    """
    if not items:
        print("No items available.")
        return None

    print(f"\n{title}")
    for idx, name in enumerate(items, start=1):
        print(f"  [{idx}] {name}")

    while True:
        choice = input(
            f"\n{prompt} "
            "(or 'q' to quit): "
        ).strip()

        if choice.lower() == "q":
            return None

        if not choice.isdigit():
            print("Please type a valid number.")
            continue

        idx = int(choice)
        if 1 <= idx <= len(items):
            return items[idx - 1]

        print("Number out of range. Try again.")
