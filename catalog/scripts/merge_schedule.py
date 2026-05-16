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
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prev", required=True)
    parser.add_argument("--next", required=True)
    args = parser.parse_args()

    prev = json.loads(Path(args.prev).read_text())
    nxt = json.loads(Path(args.next).read_text())

    valid_ids = {s["id"] for s in nxt["songs"]}
    schedule = nxt.setdefault("schedule", {"global": {}, "groups": {}})

    prev_global = prev.get("schedule", {}).get("global", {})
    for date, sid in prev_global.items():
        if sid in valid_ids:
            schedule["global"][date] = sid

    prev_groups = prev.get("schedule", {}).get("groups", {})
    for gid, group_sched in prev_groups.items():
        kept = {d: sid for d, sid in group_sched.items() if sid in valid_ids}
        if kept:
            schedule["groups"][gid] = kept

    Path(args.next).write_text(json.dumps(nxt, indent=2, ensure_ascii=False))
    print(
        f"merged schedule: global={len(schedule['global'])}, "
        f"groups={sum(len(v) for v in schedule['groups'].values())}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
