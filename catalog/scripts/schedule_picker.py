#!/usr/bin/env python3
"""
Pick today's global daily + per-group daily songs and update catalog.json.

Designed to run from GitHub Actions on a cron. Avoids repeating any song
within the last 90 days per mode. Falls back to a deterministic pick if
the catalog is too small.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

NO_REPEAT_DAYS = 90


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def deterministic_pick(date_str: str, mode: str, candidates: list[dict]) -> dict:
    seed = hashlib.sha256(f"{mode}-{date_str}".encode()).hexdigest()
    rng = random.Random(int(seed[:16], 16))
    return rng.choice(candidates)


def recent_song_ids(schedule_mode: dict[str, str], today: date) -> set[str]:
    """Songs scheduled within the last NO_REPEAT_DAYS days."""
    cutoff = today - timedelta(days=NO_REPEAT_DAYS)
    return {
        song_id
        for date_str, song_id in schedule_mode.items()
        if parse_date(date_str) >= cutoff
    }


def pick_for_mode(
    today_str: str,
    songs: list[dict],
    existing_schedule: dict[str, str],
    mode_label: str,
) -> str | None:
    if not songs:
        return None
    today = parse_date(today_str)
    recent = recent_song_ids(existing_schedule, today)
    candidates = [s for s in songs if s["id"] not in recent]
    pool = candidates if candidates else songs
    pick = deterministic_pick(today_str, mode_label, pool)
    return pick["id"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True, help="path to catalog.json (in-place edit)")
    parser.add_argument("--date", default=None, help="override date for testing (YYYY-MM-DD)")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    catalog = json.loads(catalog_path.read_text())

    today_str = args.date or date.today().isoformat()
    schedule = catalog.setdefault("schedule", {"global": {}, "groups": {}})

    # Global daily
    if today_str not in schedule["global"]:
        global_pick = pick_for_mode(
            today_str, catalog["songs"], schedule["global"], "global"
        )
        if global_pick:
            schedule["global"][today_str] = global_pick
            print(f"global daily: {global_pick}", file=sys.stderr)

    # Per-group dailies (only for groups with >= 20 songs)
    for group in catalog["groups"]:
        gid = group["id"]
        group_songs = [s for s in catalog["songs"] if s["groupId"] == gid]
        if len(group_songs) < 20:
            continue
        group_schedule = schedule["groups"].setdefault(gid, {})
        if today_str in group_schedule:
            continue
        pick = pick_for_mode(today_str, group_songs, group_schedule, gid)
        if pick:
            group_schedule[today_str] = pick
            print(f"[{gid}] daily: {pick}", file=sys.stderr)

    catalog["version"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
