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


def is_track_keepable(track: dict, group_artist: str) -> bool:
    name = track.get("trackName") or ""
    if REJECT_RE.search(name):
        return False
    if not track.get("previewUrl"):
        return False
    artist = (track.get("artistName") or "").lower()
    if group_artist.lower() not in artist:
        # iTunes sometimes returns collabs that don't match cleanly; allow if
        # the group name appears as substring.
        return False
    return True


def build_for_group(group_id: str, group_cfg: dict, max_songs: int) -> list[dict]:
    artist_query = group_cfg["query"]
    raw = itunes_search(artist_query, limit=200, country=group_cfg.get("country", "us"))

    # keepers keyed by canonical dedupe key; on collision the newer release wins
    keepers: dict[str, dict] = {}

    for track in raw:
        if not is_track_keepable(track, artist_query):
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
            "artistEn": group_cfg["nameEn"],
            "artistKr": group_cfg.get("nameKr"),
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
