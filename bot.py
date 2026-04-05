#!/usr/bin/env python3
"""Strava auto-kudos bot.

Reads your Chrome session cookies and uses them to check your wife's
Strava profile and give kudos to new activities. No browser automation needed.

Usage:
    python3 bot.py           # normal run
    python3 bot.py --dry-run # check for activities without giving kudos
"""

import argparse
import json
import logging
import os
import random
import re
import time
from pathlib import Path

import browser_cookie3
import requests
from dotenv import load_dotenv

load_dotenv()

WIFE_ATHLETE_ID = os.getenv("WIFE_ATHLETE_ID")

BASE_DIR = Path(__file__).parent
KUDOS_HISTORY = BASE_DIR / "kudos_history.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("strava-kudos")


def load_history():
    if KUDOS_HISTORY.exists():
        return set(json.loads(KUDOS_HISTORY.read_text()))
    return set()


def save_history(history):
    KUDOS_HISTORY.write_text(json.dumps(sorted(history), indent=2))


def create_session() -> requests.Session:
    """Create a requests session using Chrome's Strava cookies."""
    cj = browser_cookie3.chrome(domain_name=".strava.com")
    session = requests.Session()
    session.cookies = cj
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    return session


def get_csrf_token(session):
    """Fetch a CSRF token from the dashboard."""
    resp = session.get("https://www.strava.com/dashboard")
    if resp.url.rstrip("/").endswith("/login") or "/session" in resp.url:
        raise RuntimeError(
            "Not logged in. Log into Strava in Chrome and try again."
        )
    match = re.search(r'csrf-token["\s]+content="([^"]+)"', resp.text)
    if not match:
        match = re.search(r'content="([^"]+)"[^>]*name="csrf-token"', resp.text)
    if not match:
        raise RuntimeError("Could not find CSRF token on dashboard")
    return match.group(1)


def find_activities(session):
    """Get recent activity IDs from the wife's profile page."""
    url = f"https://www.strava.com/athletes/{WIFE_ATHLETE_ID}"
    log.info(f"Checking profile: {url}")
    resp = session.get(url)
    resp.raise_for_status()

    # Activities are embedded in JS comments/data on the profile page
    activity_ids = set(re.findall(r"Activity[- ](\d{8,})", resp.text))

    log.info(f"Found {len(activity_ids)} activities on profile")
    return activity_ids


def give_kudos(session, csrf_token, activity_id):
    """Give kudos to an activity via the unofficial endpoint."""
    resp = session.post(
        f"https://www.strava.com/feed/activity/{activity_id}/kudo",
        headers={
            "X-CSRF-Token": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        },
    )
    if resp.status_code == 200:
        log.info(f"Kudos given to activity {activity_id}")
        return True
    else:
        log.warning(f"Kudos failed for {activity_id}: {resp.status_code} {resp.text}")
        return False


def run(dry_run: bool = False):
    history = load_history()
    session = create_session()

    csrf_token = get_csrf_token(session)
    log.info("Logged in successfully")

    activities = find_activities(session)
    new_activities = activities - history

    if not new_activities:
        log.info("No new activities to kudos")
    else:
        log.info(f"{len(new_activities)} new activity(ies) to kudos")
        for activity_id in new_activities:
            if dry_run:
                log.info(f"[DRY RUN] Would kudos activity {activity_id}")
            else:
                give_kudos(session, csrf_token, activity_id)
                history.add(activity_id)
                time.sleep(random.uniform(2, 5))

    save_history(history)
    log.info("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strava auto-kudos bot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check for activities without giving kudos",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run)
