#!/usr/bin/env python3
"""
Build / refresh the K-Pop Heardle catalog by querying iTunes Search API.

Usage:
    python build_catalog.py --groups groups.yml --out catalog.json

Reads a groups.yml describing which K-pop groups to include and how many
top songs per group. For each group it queries iTunes Search API, filters
out lives/remixes/inst/OST tracks, dedupes by song title, and writes a
catalog JSON in the shape the iOS app expects.
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
import yaml

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

ITUNES_SEARCH = "https://itunes.apple.com/search"

# Reject tracks whose title matches any of these. Word boundaries and
# common punctuation variants are handled by the regex below.
REJECT_PATTERNS = [
    r"\binst(rumental)?\b",
    r"\blive\b",
    r"\bremix(es)?\b",
    r"\bacoustic\b",
    r"\bkaraoke\b",
    r"\bost\b",
    r"\b(japanese|jp|chinese|cn|english|en|korean|kr)\s*(ver(sion|\.)?)\b",
    r"\b(japanese|jp|chinese|cn|english|en|korean|kr)\s*-?ver",
    r"-\s*(japanese|jp|chinese|cn|english|en|korean|kr)\s*version\s*-",
    r"\binterlude\b",
    r"\bdemo\b",
    r"\b(radio|extended|club|dance)\s*(edit|mix|version)\b",
    r"\bsped\s*up\b",
    r"\bslowed\b",
    r"\bnightcore\b",
    r"\bremaster(ed)?\b",
    r"\bremix\s*version\b",
    r"\bprologue\b|\bepilogue\b",
    r"\bskit\b",
    r"\binst\.?\b",
    # mashups / collab "X / Y" titles
    r"\s/\s",
]
REJECT_RE = re.compile("|".join(REJECT_PATTERNS), re.IGNORECASE)

# `allowOst` 시드는 OST 거절만 건너뛴다. 패턴을 하나만 빼서 두 번째 정규식을 만들어
# 두면, REJECT_PATTERNS 가 늘어나도 이 분기가 저절로 따라온다.
OST_PATTERN = r"\bost\b"
OST_RE = re.compile(OST_PATTERN, re.IGNORECASE)
REJECT_RE_NO_OST = re.compile(
    "|".join(p for p in REJECT_PATTERNS if p != OST_PATTERN), re.IGNORECASE
)
assert OST_PATTERN in REJECT_PATTERNS, "OST 패턴 이름이 바뀌었다 — allowOst 분기가 죽는다"


def canonical_dedupe_key(title: str) -> str:
    """
    Normalize a track title so near-duplicates collapse to the same key:
    - Unicode NFKC (e.g. fullwidth → ASCII)
    - Casefold (locale-independent lowercase)
    - Smart-quote / apostrophe variants → straight
    - Strip everything that isn't a letter or digit
    """
    nfkc = unicodedata.normalize("NFKC", title)
    quote_map = str.maketrans({
        "‘": "'", "’": "'", "ʼ": "'", "ʻ": "'",
        "“": '"', "”": '"',
        "–": "-", "—": "-",
        "´": "'", "`": "'",
    })
    flat = nfkc.translate(quote_map).casefold()
    return re.sub(r"[^a-z0-9]+", "", flat)


def itunes_search(term: str, limit: int = 50, country: str = "us") -> list[dict]:
    """Hit iTunes Search API for `term` and return song results."""
    params = {
        "term": term,
        "entity": "song",
        "limit": limit,
        "country": country,
        "media": "music",
    }
    url = f"{ITUNES_SEARCH}?{urllib.parse.urlencode(params)}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=15, context=_SSL_CTX) as resp:
                payload = json.load(resp)
            return payload.get("results", [])
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 3:
                raise
            wait = 5 * (attempt + 1)
            print(f"  iTunes 429, retrying in {wait}s…", file=sys.stderr)
            time.sleep(wait)
    return []


def normalize_title(raw: str) -> str:
    cleaned = re.sub(r"\s*\([^)]*\)", "", raw)
    cleaned = re.sub(r"\s*\[[^\]]*\]", "", cleaned)
    return cleaned.strip()


# 협업 표기를 나누는 구분자. ⚠️ **" x " 를 넣으면 안 된다** — "TOMORROW X TOGETHER"
# 가 세 조각으로 갈려 그 그룹의 곡을 전부 버린다. 실제 아티스트 이름에 X 가 들어가는
# 경우가 K-pop 에 흔하다.
CREDIT_SPLIT_RE = re.compile(
    r"\s*(?:&|,|;|/|\bfeat\.?\b|\bfeaturing\b|\bwith\b|\bvs\.?\b)\s*",
    re.IGNORECASE,
)


def _norm_artist(name: str) -> str:
    """비교용 정규화 — NFKC, casefold, 공백 축약."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", name)).strip().casefold()


# 뒤에 붙는 한정 괄호만 떼어낸다 — "JENNIE (from BLACKPINK)" 는 Jennie 의 곡이다.
# ⚠️ **앞의 괄호는 떼면 안 된다.** "(G)I-DLE" 은 괄호가 이름의 일부다.
TRAILING_PAREN_RE = re.compile(r"\s*\([^()]*\)\s*$")


def artist_matches_seed(artist_name: str, seed_query: str) -> bool:
    """
    트랙의 아티스트가 이 시드의 것인지 판정한다.

    예전에는 **부분 문자열**로 봤다(`seed.lower() in artist.lower()`). 짧은 시드가
    남의 곡을 대량으로 끌어왔다 — 2026-09-08 실측(iTunes 61시드)에서 시드 `cortis`
    가 이탈리아 오페라 가수 "Marcello Cortis" 를 41곡, `babymonster` 가 홍콩 가수
    "Babymonster An" 을 20곡 넘게, `tws` 가 가스펠 그룹 "The Worshipers TWS" 를
    29곡 끌어오고 있었다. `ive` 는 "Oliver Anthony Music"("Ive Got to Get Sober")
    과 "5ive" 까지 통과시켰다.

    반대로 구분자로 무조건 쪼개면 진짜 곡을 잃는다. 실측으로 확인한 세 형태를 살린다:

      · 협업을 X 로 적는 표기 — "Coldplay X BTS"
        ⚠️ 그런데 " x " 를 항상 구분자로 쓰면 **"TOMORROW X TOGETHER" 가 깨진다.**
        그래서 **시드 자신에 x 토큰이 없을 때만** x 로 쪼갠다.
      · 공식 서브유닛의 하이픈 접미 — "EXO-K", "SUPER JUNIOR-K.R.Y."
      · 뒤에 붙는 한정 괄호 — "JENNIE (from BLACKPINK)"

    한 가지는 **일부러 거절한다.** "JENNIE (from BLACKPINK)" 는 `blackpink` 시드에서
    빠진다 — `jennie` 시드가 따로 있으므로 그 곡은 거기에 속한다. 양쪽에 넣으면
    같은 곡이 두 시드의 정답이 된다.
    """
    seed = _norm_artist(seed_query)
    if not seed:
        return False
    full = _norm_artist(artist_name)

    candidates = {full, TRAILING_PAREN_RE.sub("", full)}
    for c in list(candidates):
        candidates.update(p for p in CREDIT_SPLIT_RE.split(c) if p)
        # 시드에 x 토큰이 없을 때만 x 를 구분자로 본다(TOMORROW X TOGETHER 보호).
        if not re.search(r"(?:^|\s)x(?:\s|$)", seed):
            candidates.update(p for p in re.split(r"(?:^|\s)x(?:\s|$)", c) if p)

    for c in candidates:
        c = _norm_artist(c)
        if not c:
            continue
        if c == seed:
            return True
        # 공식 서브유닛: 시드 이름에 하이픈 접미가 붙은 형태. 공백 접미는 보지 않는다
        # ("Babymonster An" 이 BABYMONSTER 로 통과하면 안 된다).
        if c.startswith(seed + "-"):
            return True
    return False


def is_track_keepable(track: dict, group_artist: str, allow_ost: bool = False) -> bool:
    name = track.get("trackName") or ""
    if REJECT_RE.search(name):
        # OST 시드는 제목에 OST 가 들어간 곡이 **목적**이다. 그 시드에서만 OST 거절을
        # 건너뛴다 — 나머지 거절 사유(inst/live/remix …)는 그대로 적용한다.
        if not (allow_ost and _rejected_only_by_ost(name)):
            return False
    if not track.get("previewUrl"):
        return False
    return artist_matches_seed(track.get("artistName") or "", group_artist)


def _rejected_only_by_ost(name: str) -> bool:
    """OST 패턴을 뺀 나머지로는 거절되지 않는가."""
    return OST_RE.search(name) is not None and REJECT_RE_NO_OST.search(name) is None


def build_for_group(group_id: str, group_cfg: dict, max_songs: int) -> list[dict]:
    artist_query = group_cfg["query"]
    raw = itunes_search(artist_query, limit=200, country=group_cfg.get("country", "us"))

    # 시드 종류. 기본은 정식 그룹이고 데일리에 쓸 수 있다. `unit`(유닛)·`ost_seed`
    # (드라마 OST 모음) 처럼 데일리 정답으로 쓰면 공정하지 않은 시드는 설정에서
    # dailyEligible=false 로 내린다 — 판정을 앱이 아니라 카탈로그가 들고 있어야
    # 두 플랫폼이 같은 정답을 만든다.
    content_kind = group_cfg.get("contentKind", "group")
    daily_eligible = bool(group_cfg.get("dailyEligible", True))
    allow_ost = bool(group_cfg.get("allowOst", False))
    # "group": 시드의 표시 이름을 쓴다. "track": 트랙에 적힌 실제 아티스트를 쓴다
    # (OST 모음처럼 한 시드 안에 여러 아티스트가 섞이는 경우).
    artist_name_mode = group_cfg.get("artistNameMode", "group")

    # keepers keyed by canonical dedupe key; on collision the newer release wins
    keepers: dict[str, dict] = {}

    for track in raw:
        if not is_track_keepable(track, artist_query, allow_ost=allow_ost):
            continue
        title = normalize_title(track["trackName"])
        key = canonical_dedupe_key(title)
        if not key:
            continue  # title was all punctuation / non-Latin after stripping

        entry = {
            "id": f"{group_id}-{track['trackId']}",
            "itunesId": str(track["trackId"]),
            "titleEn": title,
            "titleKr": None,
            "artistEn": (
                (track.get("artistName") or group_cfg["nameEn"])
                if artist_name_mode == "track" else group_cfg["nameEn"]
            ),
            # artistNameMode="track" 이면 트랙마다 아티스트가 달라 시드의 한국어
            # 이름을 붙일 수 없다 — 붙이면 다른 사람 이름이 한국어로 찍힌다.
            "artistKr": None if artist_name_mode == "track" else group_cfg.get("nameKr"),
            # 시드의 표시 이름. artistEn 이 트랙 아티스트로 바뀌어도 어느 시드에서
            # 왔는지 남아야 큐레이션을 되짚을 수 있다.
            "seedArtistEn": group_cfg["nameEn"],
            "contentKind": content_kind,
            "dailyEligible": daily_eligible,
            "artistNameMode": artist_name_mode,
            "allowOst": allow_ost,
            "groupId": group_id,
            "releaseDate": (track.get("releaseDate") or "")[:10],
            "type": group_cfg.get("type", "girl_group"),
            "previewUrl": track["previewUrl"],
            "artworkUrl": track.get("artworkUrl100"),
        }

        existing = keepers.get(key)
        if existing is None or entry["releaseDate"] > existing["releaseDate"]:
            keepers[key] = entry

    sorted_songs = sorted(
        keepers.values(),
        key=lambda s: s.get("releaseDate") or "",
        reverse=True,
    )
    return sorted_songs[:max_songs]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", required=True, help="path to groups.yml")
    parser.add_argument("--out", required=True, help="path to write catalog.json")
    parser.add_argument(
        "--max-per-group", type=int, default=40,
        help="max songs per group after filtering"
    )
    args = parser.parse_args()

    with open(args.groups) as fp:
        groups_cfg = yaml.safe_load(fp)

    all_songs: list[dict] = []
    groups: list[dict] = []

    for group_id, cfg in groups_cfg["groups"].items():
        print(f"[{group_id}] fetching…", file=sys.stderr)
        songs = build_for_group(group_id, cfg, args.max_per_group)
        print(f"[{group_id}]   kept {len(songs)} tracks", file=sys.stderr)
        all_songs.extend(songs)
        groups.append({
            "id": group_id,
            "name_en": cfg["nameEn"],
            "name_kr": cfg.get("nameKr"),
            "debut_year": cfg.get("debutYear", 0),
            "agency": cfg.get("agency"),
            "color": cfg.get("color", "#FF6B9D"),
            "type": cfg.get("type", "girl_group"),
        })
        time.sleep(0.5)  # be polite to iTunes API

    catalog = {
        "version": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schedule": {"global": {}, "groups": {}},
        "songs": all_songs,
        "groups": groups,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    print(f"wrote {len(all_songs)} songs across {len(groups)} groups to {out_path}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
