#!/usr/bin/env python3
"""
Pick today's (or many future days') global daily + per-group daily
songs and update catalog.json.

Designed to run from GitHub Actions on a cron, but also supports bulk
pre-population (--days N) so the bundled catalog can ship with months
of playable content offline.

Date math uses KST (Asia/Seoul); within KST picks are deterministic per
date+mode so the catalog reproduces exactly if re-run.

Anti-repeat:
 - Prefer songs not scheduled in the last 90 days.
 - If exhausted (catalog smaller than the window), fall back to the
   least-recently-used song so the rotation stays fair instead of
   re-picking whatever the hash happens to land on.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
NO_REPEAT_DAYS = 90
MIN_SONGS_FOR_GROUP_DAILY = 20
# "New Releases"(comeback) 풀 크기. 클라이언트의 옛 상수와 같은 값이라 서버가
# 정하기 시작한 뒤에도 같은 성격의 퍼즐이 나온다.
COMEBACK_POOL_SIZE = 40


def today_in_kst() -> date:
    return datetime.now(KST).date()


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def deterministic_pick(date_str: str, mode: str, candidates: list[dict]) -> dict:
    seed = hashlib.sha256(f"{mode}-{date_str}".encode()).hexdigest()
    rng = random.Random(int(seed[:16], 16))
    return rng.choice(candidates)


def recent_song_ids(schedule_mode: dict[str, str], today: date) -> set[str]:
    cutoff = today - timedelta(days=NO_REPEAT_DAYS)
    return {
        song_id
        for date_str, song_id in schedule_mode.items()
        if parse_date(date_str) >= cutoff
    }


def last_used_dates(schedule_mode: dict[str, str]) -> dict[str, date]:
    out: dict[str, date] = {}
    for date_str, song_id in schedule_mode.items():
        d = parse_date(date_str)
        if song_id not in out or d > out[song_id]:
            out[song_id] = d
    return out


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
    fresh = [s for s in songs if s["id"] not in recent]
    if fresh:
        return deterministic_pick(today_str, mode_label, fresh)["id"]

    last_used = last_used_dates(existing_schedule)
    sentinel = date(1970, 1, 1)
    def lru_key(song: dict) -> tuple[date, str]:
        return (last_used.get(song["id"], sentinel), song["id"])
    songs_sorted = sorted(songs, key=lru_key)
    oldest_date = lru_key(songs_sorted[0])[0]
    oldest = [s for s in songs_sorted if lru_key(s)[0] == oldest_date]
    return deterministic_pick(today_str, mode_label + ":lru", oldest)["id"]


def comeback_pool(songs: list[dict], limit: int = COMEBACK_POOL_SIZE) -> list[dict]:
    """가장 최근에 발매된 `limit` 곡, 최신 우선.

    `releaseDate` 는 "YYYY-MM-DD" 라 문자열 정렬이 곧 시간 정렬이다. 같은 날짜는
    `id` 로 갈라 순서를 고정한다 — 클라이언트 구현과 같은 규칙이다.
    발매일이 없는 곡은 뺀다(정렬이 무의미하고 "신곡" 도 아니다).
    """
    dated = [s for s in songs if s.get("releaseDate")]
    dated.sort(key=lambda s: (s["releaseDate"], [-ord(c) for c in s["id"]]), reverse=True)
    return dated[:limit]


def populate_one_day(catalog: dict, schedule: dict, today_str: str, verbose: bool = True) -> None:
    if today_str not in schedule["global"]:
        global_pick = pick_for_mode(
            today_str, catalog["songs"], schedule["global"], "global"
        )
        if global_pick:
            schedule["global"][today_str] = global_pick
            if verbose:
                print(f"{today_str} global: {global_pick}", file=sys.stderr)

    # ⚠️ comeback 은 **서버가 정해야 한다.** 예전에는 클라이언트가 자기 카탈로그의
    # 최근 40곡에서 골랐는데, 그 풀이 갱신마다 바뀌어 **기기마다 정답이 달랐다**
    # (09-07 → 09-08 갱신에서 40곡 중 13곡 교체, 5개 날짜 정답 전부 불일치).
    comeback_schedule = schedule.setdefault("comeback", {})
    if today_str not in comeback_schedule:
        pool = comeback_pool(catalog["songs"])
        comeback_pick = pick_for_mode(today_str, pool, comeback_schedule, "comeback")
        if comeback_pick:
            comeback_schedule[today_str] = comeback_pick
            if verbose:
                print(f"{today_str} comeback: {comeback_pick}", file=sys.stderr)

    for group in catalog["groups"]:
        gid = group["id"]
        if not group.get("dailyEligible", True):
            continue
        group_songs = [s for s in catalog["songs"] if s["groupId"] == gid]
        if len(group_songs) < MIN_SONGS_FOR_GROUP_DAILY:
            continue
        group_schedule = schedule["groups"].setdefault(gid, {})
        if today_str in group_schedule:
            continue
        pick = pick_for_mode(today_str, group_songs, group_schedule, gid)
        if pick:
            group_schedule[today_str] = pick
            if verbose:
                print(f"{today_str} [{gid}]: {pick}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True, help="path to catalog.json (in-place edit)")
    parser.add_argument("--date", default=None,
                        help="start date (YYYY-MM-DD, KST); defaults to today KST")
    parser.add_argument("--days", type=int, default=1,
                        help="bulk-populate N consecutive days starting at --date")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    catalog = json.loads(catalog_path.read_text())

    start_date = parse_date(args.date) if args.date else today_in_kst()
    schedule = catalog.setdefault("schedule", {"global": {}, "groups": {}, "comeback": {}})
    schedule.setdefault("comeback", {})   # 옛 카탈로그에는 키가 없다

    verbose = args.days <= 10  # spamming logs for 90-day bulk is unhelpful
    for offset in range(args.days):
        target = start_date + timedelta(days=offset)
        populate_one_day(catalog, schedule, target.isoformat(), verbose=verbose)

    if not verbose:
        last = (start_date + timedelta(days=args.days - 1)).isoformat()
        print(
            f"populated global: {len(schedule['global'])} days through {last}",
            file=sys.stderr,
        )
        for gid, gs in schedule["groups"].items():
            print(f"  [{gid}]: {len(gs)} days", file=sys.stderr)

    catalog["version"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
