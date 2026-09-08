#!/usr/bin/env python3
"""
After rebuilding the catalog, transfer the previous schedule into the new
catalog so that already-published daily picks keep pointing to the same songs.

Drops schedule entries whose song no longer exists in the new catalog.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

MIN_SONGS_FOR_GROUP_DAILY = 20


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prev", required=True)
    parser.add_argument("--next", required=True)
    args = parser.parse_args()

    prev = json.loads(Path(args.prev).read_text())
    nxt = json.loads(Path(args.next).read_text())

    valid_ids = {s["id"] for s in nxt["songs"]}
    song_counts = Counter(
        s["groupId"]
        for s in nxt["songs"]
        if s.get("groupId")
    )
    eligible_group_ids = {
        group["id"]
        for group in nxt.get("groups", [])
        if group.get("dailyEligible", True)
        and song_counts.get(group["id"], 0) >= MIN_SONGS_FOR_GROUP_DAILY
    }
    schedule = {"global": {}, "groups": {}, "comeback": {}}

    # comeback 도 이제 서버 일정이다 — 곡이 사라지면 그 날짜를 버린다.
    # ⚠️ 옛 카탈로그에는 이 키가 없다. 없다고 죽으면 파이프라인이 멈춘다.
    for date, sid in prev.get("schedule", {}).get("comeback", {}).items():
        if sid in valid_ids:
            schedule["comeback"][date] = sid

    prev_global = prev.get("schedule", {}).get("global", {})
    for date, sid in prev_global.items():
        if sid in valid_ids:
            schedule["global"][date] = sid

    prev_groups = prev.get("schedule", {}).get("groups", {})
    for gid, group_sched in prev_groups.items():
        if gid not in eligible_group_ids:
            continue
        kept = {d: sid for d, sid in group_sched.items() if sid in valid_ids}
        if kept:
            schedule["groups"][gid] = kept

    nxt["schedule"] = schedule

    Path(args.next).write_text(json.dumps(nxt, indent=2, ensure_ascii=False))
    print(
        f"merged schedule: global={len(schedule['global'])}, "
        f"comeback={len(schedule['comeback'])}, "
        f"groups={sum(len(v) for v in schedule['groups'].values())}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
