"""
Checks an NBEMS page for new PDF links (e.g. the NEET PG26 result notice),
downloads any new relevant PDF it finds, and sends a phone notification via ntfy.sh.

SETUP — edit these two lines before use:
"""
MONITOR_URL = "https://natboard.edu.in/parinam/neetpg/index"
NTFY_TOPIC = "drshubham-neetpg26-7q2m"   # e.g. shubham-neetpg26-xk93

# Only notify about new PDF links whose URL or link text contains ALL of these
# (case-insensitive). Loosen this list if it misses the real notice, tighten it
# if it fires on unrelated PDFs.
REQUIRED_KEYWORDS = ["neet"]

import requests
import json
import os
import re
from urllib.parse import urljoin

STATE_FILE = "seen_pdfs.json"
DOWNLOAD_DIR = "downloads"


def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2, ensure_ascii=False)


def notify(message, click_url=None):
    headers = {"Title": "NEET PG26 result alert".encode("utf-8")}
    if click_url:
        headers["Click"] = click_url
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=5,
        )
    except Exception as e:
        print(f"ntfy notify failed: {e}")


def main():
    if "PASTE_THE_EXACT" in MONITOR_URL:
        raise SystemExit("Set MONITOR_URL at the top of this script first.")

    headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://natboard.edu.in/parinam/neetpg/index",
    }
    resp.raise_for_status()
    html = resp.text

    # Grab every href ending in .pdf, resolved to an absolute URL.
    raw_links = re.findall(r'href=[\'"]([^\'"]+\.pdf)[\'"]', html, re.IGNORECASE)
    pdf_links = {urljoin(MONITOR_URL, link) for link in raw_links}

    seen = load_seen()
    new_links = pdf_links - seen

    relevant_new = [
        link for link in new_links
        if all(k.lower() in link.lower() for k in REQUIRED_KEYWORDS)
    ]

    for link in relevant_new:
        fname = os.path.join(DOWNLOAD_DIR, os.path.basename(link.split("?")[0]))
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        try:
            headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://natboard.edu.in/",
            }
            pdf_resp.raise_for_status()
            with open(fname, "wb") as f:
                f.write(pdf_resp.content)
            notify(f"New PDF downloaded: {os.path.basename(fname)}", click_url=link)
            print(f"Downloaded {link} -> {fname}")
        except Exception as e:
            notify(f"New PDF link found (download failed): {link}", click_url=link)
            print(f"Failed to download {link}: {e}")

    # Mark ALL currently-seen pdf links as seen, whether or not they matched
    # the keyword filter, so unrelated PDFs don't keep re-triggering checks.
    seen |= pdf_links
    save_seen(seen)

    if not relevant_new:
        print("No new relevant PDF found this run.")


if __name__ == "__main__":
    main()
