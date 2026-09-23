"""
Two-signal NEET PG26 result checker:

1. PRIMARY (higher confidence): watches whether
   https://results.natboard.edu.in/neetpg/index goes from "not found" to
   actually loading. This is NBE's real results-portal address (reused
   across past cycles), and it isn't bot-blocked -- it's just inactive
   until the current cycle's result goes live.

2. BACKUP (lower confidence): watches nbe.edu.in, an older mirror page,
   for ANY change. Caveat: its NEET-PG listing hasn't been updated since
   2022, so it may never reflect the 2026 result at all. Kept only as a
   free extra check, not something to rely on alone.

Sends a phone notification via ntfy.sh either way, but labels which
signal fired so you know how much to trust it.

SETUP -- edit this one line before use:
"""
NTFY_TOPIC = "drshubham-neetpg26-7q2m"   # the same one you set in the ntfy app

RESULTS_URL = "https://results.natboard.edu.in/neetpg/index"
NBE_URL = "https://nbe.edu.in"
NATBOARD_URL = "https://natboard.edu.in/index"
PARINAM_URL = "https://natboard.edu.in/parinam/neetpg/index"
STATUS_FILE = "last_status.txt"
STATE_FILE = "last_seen.txt"
STATE_FILE_NATBOARD = "last_seen_natboard.txt"
STATE_FILE_PARINAM = "last_seen_parinam.txt"

import requests
import os
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def normalize(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def notify(message, click_url=None):
    headers = {"Title": "NEET PG26 result alert".encode("utf-8")}
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


def check_results_portal():
    """Returns (changed, status) for the real results-portal URL."""
    try:
        resp = requests.get(RESULTS_URL, timeout=20, headers=HEADERS, allow_redirects=True)
        status = str(resp.status_code)
    except Exception as e:
        status = f"error:{e}"

    previous = None
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, encoding="utf-8") as f:
            previous = f.read().strip()

    changed = previous is not None and status != previous

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write(status)

    return changed, status, previous


def check_nbe_page():
    """Returns True if the nbe.edu.in mirror page's text changed."""
    resp = requests.get(NBE_URL, timeout=30, headers=HEADERS)
    resp.raise_for_status()
    current = normalize(resp.text)

    previous = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            previous = f.read()

    changed = previous is not None and current != previous

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(current)

    return changed


def check_natboard_index():
    """Returns True if natboard.edu.in/index's text changed. Note: this page
    loaded stale (2022-dated) content when last checked, so a change here is
    a decent sign something moved, but isn't guaranteed to mean much."""
    resp = requests.get(NATBOARD_URL, timeout=30, headers=HEADERS)
    resp.raise_for_status()
    current = normalize(resp.text)

    previous = None
    if os.path.exists(STATE_FILE_NATBOARD):
        with open(STATE_FILE_NATBOARD, encoding="utf-8") as f:
            previous = f.read()

    changed = previous is not None and current != previous

    with open(STATE_FILE_NATBOARD, "w", encoding="utf-8") as f:
        f.write(current)

    return changed


def check_parinam_page():
    """Returns True if natboard.edu.in/parinam/neetpg/index's text changed.
    NOTE: this URL is confirmed blocked by bot detection (403) as of the
    last check -- this function is expected to raise on most/all runs
    until NBE's protection changes, which is outside our control. Kept
    only in case that ever changes; do not expect this to fire."""
    resp = requests.get(PARINAM_URL, timeout=30, headers=HEADERS)
    resp.raise_for_status()
    current = normalize(resp.text)

    previous = None
    if os.path.exists(STATE_FILE_PARINAM):
        with open(STATE_FILE_PARINAM, encoding="utf-8") as f:
            previous = f.read()

    changed = previous is not None and current != previous

    with open(STATE_FILE_PARINAM, "w", encoding="utf-8") as f:
        f.write(current)

    return changed


def main():
    if "PASTE_YOUR" in NTFY_TOPIC:
        raise SystemExit("Set NTFY_TOPIC at the top of this script first.")

    # --- Primary signal ---
    results_changed, status, prev_status = check_results_portal()
    if results_changed:
        notify(
            f"HIGH CONFIDENCE: results.natboard.edu.in/neetpg/index changed "
            f"({prev_status} -> {status}). Check now!",
            click_url=RESULTS_URL,
        )
        print(f"Primary signal fired: {prev_status} -> {status}")
    else:
        print(f"Primary check: no change (status {status}).")

    # --- Backup signal 1: nbe.edu.in ---
    try:
        if check_nbe_page():
            notify(
                "Lower confidence: nbe.edu.in changed. May or may not be "
                "about NEET PG26 -- worth a manual look.",
                click_url=NBE_URL,
            )
            print("Backup signal fired: nbe.edu.in changed.")
        else:
            print("Backup check: no change on nbe.edu.in.")
    except Exception as e:
        print(f"Backup check failed (non-fatal): {e}")

    # --- Backup signal 2: natboard.edu.in/index ---
    try:
        if check_natboard_index():
            notify(
                "Lower confidence: natboard.edu.in/index changed. Worth a "
                "manual look.",
                click_url=NATBOARD_URL,
            )
            print("Backup signal fired: natboard.edu.in/index changed.")
        else:
            print("Backup check: no change on natboard.edu.in/index.")
    except Exception as e:
        print(f"Backup check failed (non-fatal): {e}")

    # --- Backup signal 3: natboard.edu.in/parinam/neetpg/index ---
    # Expected to fail with 403 (bot detection) most/every run -- see docstring.
    try:
        if check_parinam_page():
            notify(
                "natboard.edu.in/parinam/neetpg/index changed (and actually "
                "loaded this time) -- check now!",
                click_url=PARINAM_URL,
            )
            print("Backup signal fired: parinam page changed.")
        else:
            print("Backup check: parinam page loaded, no change.")
    except Exception as e:
        print(f"Parinam check failed as expected (non-fatal): {e}")


if __name__ == "__main__":
    main()
