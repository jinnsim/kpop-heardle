from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(relative_path: str, module_name: str):
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


merge_schedule = load_module("catalog/scripts/merge_schedule.py", "merge_schedule")
schedule_picker = load_module("catalog/scripts/schedule_picker.py", "schedule_picker")


def run_merge_schedule(prev_path: Path, next_path: Path, monkeypatch) -> dict:
    monkeypatch.setattr(
        "sys.argv",
        [
            "merge_schedule.py",
            "--prev",
            str(prev_path),
            "--next",
            str(next_path),
        ],
    )

    assert merge_schedule.main() == 0
    return json.loads(next_path.read_text())


def test_merge_schedule_populates_missing_schedule_and_drops_unknown_song_ids(tmp_path, monkeypatch) -> None:
    prev_path = tmp_path / "prev.json"
    next_path = tmp_path / "next.json"

    prev_path.write_text(json.dumps({
        "schedule": {
            "global": {
                "2026-05-27": "song-1",
                "2026-05-28": "missing-song",
            },
            "groups": {
                "aespa": {
                    "2026-05-27": "song-2",
                    "2026-05-28": "missing-song",
                },
                "ive": {
                    "2026-05-27": "missing-song",
                },
            },
        },
    }))
    next_path.write_text(json.dumps({
        "songs": [
            {"id": "song-1", "groupId": "aespa"},
            {"id": "song-2", "groupId": "aespa"},
            {"id": "song-3", "groupId": "aespa"},
        ] + [
            {"id": f"aespa-fill-{idx}", "groupId": "aespa"} for idx in range(17)
        ],
        "groups": [
            {"id": "aespa", "dailyEligible": True},
            {"id": "ive", "dailyEligible": True},
        ],
    }))

    merged = run_merge_schedule(prev_path, next_path, monkeypatch)
    assert merged["schedule"] == {
        "global": {"2026-05-27": "song-1"},
        "groups": {"aespa": {"2026-05-27": "song-2"}},
        "comeback": {},   # H-05 로 생긴 키 — prev 에 없으면 빈 채로 유지된다
    }


def test_schedule_picker_skips_non_daily_eligible_groups() -> None:
    catalog = {
        "songs": [
            {"id": f"aespa-{idx}", "groupId": "aespa"} for idx in range(25)
        ] + [
            {"id": f"heize-{idx}", "groupId": "heize"} for idx in range(25)
        ],
        "groups": [
            {"id": "aespa", "dailyEligible": True},
            {"id": "heize", "dailyEligible": False},
        ],
    }
    schedule = {"global": {}, "groups": {}}

    schedule_picker.populate_one_day(catalog, schedule, "2026-06-01", verbose=False)

    assert "2026-06-01" in schedule["global"]
    assert "aespa" in schedule["groups"]
    assert "2026-06-01" in schedule["groups"]["aespa"]
    assert "heize" not in schedule["groups"]


def test_merge_schedule_removes_stale_prepopulated_next_schedule_entries(tmp_path, monkeypatch) -> None:
    prev_path = tmp_path / "prev.json"
    next_path = tmp_path / "next.json"

    prev_path.write_text(json.dumps({
        "schedule": {
            "global": {"2026-05-27": "song-1"},
            "groups": {"aespa": {"2026-05-27": "song-2"}},
        },
    }))
    next_path.write_text(json.dumps({
        "songs": [
            {"id": "song-1", "groupId": "aespa"},
            {"id": "song-2", "groupId": "aespa"},
        ] + [
            {"id": f"aespa-fill-{idx}", "groupId": "aespa"} for idx in range(18)
        ],
        "groups": [
            {"id": "aespa", "dailyEligible": True},
        ],
        "schedule": {
            "global": {"2099-01-01": "stale-next-song"},
            "groups": {"legacy": {"2099-01-01": "stale-next-song"}},
        },
    }))

    merged = run_merge_schedule(prev_path, next_path, monkeypatch)

    assert merged["schedule"] == {
        "global": {"2026-05-27": "song-1"},
        "groups": {"aespa": {"2026-05-27": "song-2"}},
        "comeback": {},   # H-05 로 생긴 키 — prev 에 없으면 빈 채로 유지된다
    }


def test_merge_schedule_drops_groups_that_are_no_longer_daily_eligible(tmp_path, monkeypatch) -> None:
    prev_path = tmp_path / "prev.json"
    next_path = tmp_path / "next.json"

    prev_path.write_text(json.dumps({
        "schedule": {
            "global": {"2026-05-27": "song-1"},
            "groups": {
                "newjeans": {"2026-05-27": "song-1"},
                "aespa": {"2026-05-27": "song-2"},
            },
        },
    }))
    next_path.write_text(json.dumps({
        "songs": (
            [{"id": "song-1", "groupId": "newjeans"} for _ in range(19)]
            + [{"id": "song-2", "groupId": "aespa"} for _ in range(20)]
        ),
        "groups": [
            {"id": "newjeans", "dailyEligible": True},
            {"id": "aespa", "dailyEligible": True},
        ],
    }))

    merged = run_merge_schedule(prev_path, next_path, monkeypatch)

    assert merged["schedule"] == {
        "global": {"2026-05-27": "song-1"},
        "groups": {"aespa": {"2026-05-27": "song-2"}},
        "comeback": {},   # H-05 로 생긴 키 — prev 에 없으면 빈 채로 유지된다
    }


# --- H-05 "New Releases" 를 서버 일정으로 옮긴다 -------------------------------
#
# comeback(New Releases) 정답은 클라이언트가 **카탈로그의 최근 40곡 풀**에서
# 골랐다. 풀은 카탈로그가 갱신될 때마다 바뀌므로 **기기마다 정답이 달랐다** —
# 09-07 판본과 09-08 판본으로 실측하니 40곡 중 13곡이 교체되고 테스트한 5개
# 날짜의 정답이 전부 갈렸다. 공유 그리드를 비교할 수 없고, 친구가 올린 결과의
# 퍼즐을 내가 풀 수도 없다. global·group 데일리처럼 **서버가 정한다.**

def _comeback_catalog(n: int = 60) -> dict:
    # releaseDate 가 최신인 순서대로 song-00 … song-(n-1)
    return {
        "songs": [
            {"id": f"song-{idx:02d}", "groupId": "aespa",
             "releaseDate": f"2026-{(12 - idx // 28):02d}-{28 - idx % 28:02d}"}
            for idx in range(n)
        ],
        "groups": [{"id": "aespa", "dailyEligible": True}],
    }


def test_schedule_picker_populates_comeback() -> None:
    catalog = _comeback_catalog()
    schedule = {"global": {}, "groups": {}}

    schedule_picker.populate_one_day(catalog, schedule, "2026-06-01", verbose=False)

    assert "2026-06-01" in schedule["comeback"]
    picked = schedule["comeback"]["2026-06-01"]
    pool = {s["id"] for s in schedule_picker.comeback_pool(catalog["songs"])}
    assert picked in pool, "최근 발매 풀 안에서 골라야 한다"


def test_comeback_pool_is_the_freshest_songs_only() -> None:
    catalog = _comeback_catalog(n=60)
    pool = schedule_picker.comeback_pool(catalog["songs"])
    assert len(pool) == schedule_picker.COMEBACK_POOL_SIZE
    assert [s["id"] for s in pool] == [f"song-{i:02d}" for i in range(40)]


def test_comeback_ignores_songs_without_a_release_date() -> None:
    songs = [{"id": "dated", "groupId": "g", "releaseDate": "2026-01-01"},
             {"id": "undated", "groupId": "g", "releaseDate": ""}]
    assert [s["id"] for s in schedule_picker.comeback_pool(songs)] == ["dated"]


def test_comeback_does_not_repeat_within_the_no_repeat_window() -> None:
    catalog = _comeback_catalog()
    schedule = {"global": {}, "groups": {}, "comeback": {}}
    for offset in range(20):
        day = f"2026-06-{offset + 1:02d}"
        schedule_picker.populate_one_day(catalog, schedule, day, verbose=False)
    picks = list(schedule["comeback"].values())
    assert len(picks) == 20
    assert len(set(picks)) == 20, "90일 창 안에서는 같은 곡이 다시 나오면 안 된다"


def test_merge_schedule_carries_comeback_and_drops_removed_songs(tmp_path, monkeypatch) -> None:
    prev_path = tmp_path / "prev.json"
    next_path = tmp_path / "next.json"
    prev_path.write_text(json.dumps({
        "schedule": {
            "global": {},
            "groups": {},
            "comeback": {"2026-05-27": "song-1", "2026-05-28": "missing-song"},
        },
    }))
    next_path.write_text(json.dumps({
        "songs": [{"id": "song-1", "groupId": "aespa", "releaseDate": "2026-05-01"}],
        "groups": [{"id": "aespa", "dailyEligible": True}],
    }))

    merged = run_merge_schedule(prev_path, next_path, monkeypatch)
    assert merged["schedule"]["comeback"] == {"2026-05-27": "song-1"}


def test_merge_schedule_keeps_comeback_key_even_when_prev_lacks_it(tmp_path, monkeypatch) -> None:
    """옛 카탈로그에서 올라올 때 키가 없다고 죽으면 파이프라인이 멈춘다."""
    prev_path = tmp_path / "prev.json"
    next_path = tmp_path / "next.json"
    prev_path.write_text(json.dumps({"schedule": {"global": {}, "groups": {}}}))
    next_path.write_text(json.dumps({
        "songs": [{"id": "song-1", "groupId": "aespa", "releaseDate": "2026-05-01"}],
        "groups": [{"id": "aespa", "dailyEligible": True}],
    }))

    merged = run_merge_schedule(prev_path, next_path, monkeypatch)
    assert merged["schedule"]["comeback"] == {}
