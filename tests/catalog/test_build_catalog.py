from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(relative_path: str, module_name: str):
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


build_catalog = load_module("catalog/scripts/build_catalog.py", "build_catalog")


def test_build_for_group_filters_and_dedupes_tracks(monkeypatch) -> None:
    raw_tracks = [
        {
            "trackId": 101,
            "trackName": "Supernova",
            "artistName": "aespa",
            "releaseDate": "2024-05-13T00:00:00Z",
            "previewUrl": "https://example.com/101.m4a",
            "artworkUrl100": "https://example.com/101.jpg",
        },
        {
            "trackId": 102,
            "trackName": "Supernova (English Ver.)",
            "artistName": "aespa",
            "releaseDate": "2024-05-14T00:00:00Z",
            "previewUrl": "https://example.com/102.m4a",
            "artworkUrl100": "https://example.com/102.jpg",
        },
        {
            "trackId": 103,
            "trackName": "Better Things (Live)",
            "artistName": "aespa",
            "releaseDate": "2024-01-01T00:00:00Z",
            "previewUrl": "https://example.com/103.m4a",
            "artworkUrl100": "https://example.com/103.jpg",
        },
        {
            "trackId": 104,
            "trackName": "Drama",
            "artistName": "aespa",
            "releaseDate": "2023-11-10T00:00:00Z",
            "previewUrl": None,
            "artworkUrl100": "https://example.com/104.jpg",
        },
        {
            "trackId": 105,
            "trackName": "Drama",
            "artistName": "Various Artists",
            "releaseDate": "2023-11-10T00:00:00Z",
            "previewUrl": "https://example.com/105.m4a",
            "artworkUrl100": "https://example.com/105.jpg",
        },
        {
            "trackId": 106,
            "trackName": "Black Mamba",
            "artistName": "aespa",
            "releaseDate": "2020-11-17T00:00:00Z",
            "previewUrl": "https://example.com/106.m4a",
            "artworkUrl100": "https://example.com/106.jpg",
        },
        {
            "trackId": 107,
            "trackName": "Black   Mamba",
            "artistName": "aespa",
            "releaseDate": "2020-11-18T00:00:00Z",
            "previewUrl": "https://example.com/107.m4a",
            "artworkUrl100": "https://example.com/107.jpg",
        },
    ]

    monkeypatch.setattr(build_catalog, "itunes_search", lambda *args, **kwargs: raw_tracks)

    songs = build_catalog.build_for_group(
        "aespa",
        {"query": "aespa", "nameEn": "aespa", "type": "girl_group"},
        max_songs=10,
    )

    assert [song["titleEn"] for song in songs] == ["Supernova", "Black   Mamba"]
    assert songs[0]["itunesId"] == "101"
    assert songs[1]["itunesId"] == "107"
    assert all(song["groupId"] == "aespa" for song in songs)
    assert songs[0]["contentKind"] == "group"
    assert songs[0]["dailyEligible"] is True
    assert songs[0]["artistNameMode"] == "group"
    assert songs[0]["allowOst"] is False
    assert songs[0]["seedArtistEn"] == "aespa"


def test_build_for_group_supports_track_artist_and_explicit_ost_opt_in(monkeypatch) -> None:
    raw_tracks = [
        {
            "trackId": 201,
            "trackName": "You, Clouds, Rain",
            "artistName": "HEIZE",
            "releaseDate": "2017-06-26T00:00:00Z",
            "previewUrl": "https://example.com/201.m4a",
            "artworkUrl100": "https://example.com/201.jpg",
        },
        {
            "trackId": 202,
            "trackName": "Future OST Part.1",
            "artistName": "HEIZE & Punch",
            "releaseDate": "2020-03-28T00:00:00Z",
            "previewUrl": "https://example.com/202.m4a",
            "artworkUrl100": "https://example.com/202.jpg",
        },
    ]

    monkeypatch.setattr(build_catalog, "itunes_search", lambda *args, **kwargs: raw_tracks)

    default_songs = build_catalog.build_for_group(
        "heize",
        {
            "query": "HEIZE",
            "nameEn": "HEIZE",
            "type": "solo",
        },
        max_songs=10,
    )
    configured_songs = build_catalog.build_for_group(
        "ost_heize",
        {
            "query": "HEIZE",
            "nameEn": "K-Drama OST Picks",
            "nameKr": "드라마 OST 픽",
            "type": "solo",
            "contentKind": "ost_seed",
            "dailyEligible": False,
            "allowOst": True,
            "artistNameMode": "track",
        },
        max_songs=10,
    )

    assert [song["titleEn"] for song in default_songs] == ["You, Clouds, Rain"]

    assert [song["titleEn"] for song in configured_songs] == [
        "Future OST Part.1",
        "You, Clouds, Rain",
    ]
    assert configured_songs[0]["artistEn"] == "HEIZE & Punch"
    assert configured_songs[0]["seedArtistEn"] == "K-Drama OST Picks"
    assert configured_songs[0]["artistKr"] is None
    assert configured_songs[0]["contentKind"] == "ost_seed"
    assert configured_songs[0]["dailyEligible"] is False
    assert configured_songs[0]["artistNameMode"] == "track"
    assert configured_songs[0]["allowOst"] is True


def test_build_for_group_rejects_ambiguous_short_query_contamination(monkeypatch) -> None:
    raw_tracks = [
        {
            "trackId": 301,
            "trackName": "Fighting",
            "artistName": "BSS",
            "releaseDate": "2023-02-06T00:00:00Z",
            "previewUrl": "https://example.com/301.m4a",
            "artworkUrl100": "https://example.com/301.jpg",
        },
        {
            "trackId": 302,
            "trackName": "Noise Result",
            "artistName": "DJ Noah feat. BSS Choir & Friends",
            "releaseDate": "2024-01-01T00:00:00Z",
            "previewUrl": "https://example.com/302.m4a",
            "artworkUrl100": "https://example.com/302.jpg",
        },
    ]

    monkeypatch.setattr(build_catalog, "itunes_search", lambda *args, **kwargs: raw_tracks)

    songs = build_catalog.build_for_group(
        "bss",
        {
            "query": "BSS",
            "nameEn": "BSS",
            "type": "boy_group",
            "contentKind": "unit",
            "dailyEligible": False,
        },
        max_songs=10,
    )

    assert [song["titleEn"] for song in songs] == ["Fighting"]


def test_build_for_group_accepts_tomorrow_x_together_artist_name(monkeypatch) -> None:
    raw_tracks = [
        {
            "trackId": 401,
            "trackName": "Deja Vu",
            "artistName": "TOMORROW X TOGETHER",
            "releaseDate": "2024-04-01T00:00:00Z",
            "previewUrl": "https://example.com/401.m4a",
            "artworkUrl100": "https://example.com/401.jpg",
        },
        {
            "trackId": 402,
            "trackName": "Noise Result",
            "artistName": "DJ Noah feat. BSS Choir & Friends",
            "releaseDate": "2024-01-01T00:00:00Z",
            "previewUrl": "https://example.com/402.m4a",
            "artworkUrl100": "https://example.com/402.jpg",
        },
    ]

    monkeypatch.setattr(build_catalog, "itunes_search", lambda *args, **kwargs: raw_tracks)

    txt_songs = build_catalog.build_for_group(
        "txt",
        {
            "query": "Tomorrow X Together",
            "nameEn": "TXT",
            "type": "boy_group",
        },
        max_songs=10,
    )
    bss_songs = build_catalog.build_for_group(
        "bss",
        {
            "query": "BSS",
            "nameEn": "BSS",
            "type": "boy_group",
            "contentKind": "unit",
            "dailyEligible": False,
        },
        max_songs=10,
    )

    assert [song["titleEn"] for song in txt_songs] == ["Deja Vu"]
    assert bss_songs == []


# 2026-09-08 iTunes 61시드 실측으로 정한 매칭 경계. 부분 문자열로 보던 예전 규칙이
# 오페라 가수·홍콩 가수·가스펠 그룹을 대량으로 끌어오고 있었다(cortis 41곡,
# babymonster 20+곡, tws 29곡). 반대로 무조건 쪼개면 진짜 곡을 잃는다.
# 여기 사례는 전부 실제 iTunes 응답에서 뽑았다 — 지어낸 것이 없다.

def test_artist_matching_keeps_real_credits() -> None:
    m = build_catalog.artist_matches_seed
    # 협업을 X 로 적는 표기
    assert m("Coldplay X BTS", "BTS") is True
    # 공식 서브유닛의 하이픈 접미
    assert m("EXO-K", "EXO") is True
    assert m("SUPER JUNIOR-K.R.Y.", "Super Junior") is True
    # 뒤에 붙는 한정 괄호
    assert m("JENNIE (from BLACKPINK)", "Jennie") is True
    # 협업 구분자
    assert m("HEIZE & Punch", "HEIZE") is True
    assert m("K/DA, Madison Beer & i-dle", "i-dle") is True
    assert m("BSS", "BSS") is True


def test_artist_matching_rejects_contamination() -> None:
    m = build_catalog.artist_matches_seed
    assert m("DJ Noah feat. BSS Choir & Friends", "BSS") is False
    assert m("Marcello Cortis", "CORTIS") is False          # 이탈리아 오페라 가수
    assert m("Babymonster An", "BABYMONSTER") is False      # 홍콩 가수 — 공백 접미는 거절
    assert m("The Worshipers TWS", "TWS") is False          # 가스펠 그룹
    assert m("Oliver Anthony Music", "IVE") is False        # "Ive Got to Get Sober"
    assert m("5ive", "IVE") is False
    assert m("Flying Izna Drop", "izna") is False
    assert m("Qwer665", "QWER") is False
    assert m("VCHA STUDIO", "VCHA") is False
    assert m("Yena Blue", "YENA") is False


def test_x_is_not_a_separator_when_the_seed_itself_has_x() -> None:
    """⚠️ " x " 를 항상 구분자로 쓰면 TOMORROW X TOGETHER 의 곡을 전부 잃는다."""
    m = build_catalog.artist_matches_seed
    assert m("TOMORROW X TOGETHER", "Tomorrow X Together") is True
    # 시드에 x 가 있으므로 x 로 쪼개지 않는다 → 남의 이름이 통과하지 않는다
    assert m("Coldplay X BTS", "Tomorrow X Together") is False


def test_member_solo_belongs_to_the_member_seed_not_the_group() -> None:
    """멤버 솔로곡을 그룹 시드에도 넣으면 같은 곡이 두 시드의 정답이 된다."""
    m = build_catalog.artist_matches_seed
    assert m("JENNIE (from BLACKPINK)", "Jennie") is True
    assert m("JENNIE (from BLACKPINK)", "BLACKPINK") is False
