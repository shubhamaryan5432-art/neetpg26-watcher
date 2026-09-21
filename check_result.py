"""
Checks nbe.edu.in (a mirror of NBEMS's site that isn't behind bot-detection,
unlike natboard.edu.in) for ANY change, and pushes a phone notification via
ntfy.sh when it changes. This watches the whole page, not just NEET-PG, so an
unrelated update elsewhere on the page could occasionally trigger a false
alert -- that's an acceptable trade-off for not missing the real one.

SETUP -- edit this one line before use:
"""
NTFY_TOPIC = "drshubham-neetpg26-7q2m"   # the same one you set in the ntfy app

MONITOR_URL = "https://nbe.edu.in"
STATE_FILE = "last_seen.txt"

import requests
import os
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def normalize(html):
    """Strip tags to rough visible text and collapse whitespace, so trivial
    formatting-only changes (extra spaces, etc.) don't look like real diffs."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def notify(message, click_url=None):
    headers = {"Title": "NBE site changed".encode("utf-8")}
    if click_url:
        headers["Click"] = click_url
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=15,
        )
    except Exception as e:
        print(f"ntfy notify failed: {e}")


def main():
    if "PASTE_YOUR" in NTFY_TOPIC:
        raise SystemExit("Set NTFY_TOPIC at the top of this script first.")

    resp = requests.get(MONITOR_URL, timeout=30, headers=HEADERS)
    resp.raise_for_status()
    current = normalize(resp.text)

    previous = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            previous = f.read()

    if previous is None:
        # First-ever run: nothing to compare against yet, just save the
        # baseline. Do NOT notify -- there's no real "change" on run 1.
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(current)
        print("Baseline saved on first run. Nothing to compare yet.")
        return

    if current != previous:
        notify(
            "nbe.edu.in changed -- check if NEET PG26 result is out.",
            click_url=MONITOR_URL,
        )
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(current)
        print("Change detected, notification sent.")
    else:
        print("No change detected this run.")


if __name__ == "__main__":
    main()
