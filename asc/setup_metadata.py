"""
End-to-end ASC metadata setup for K-Pop Heardle.

Idempotent — re-running with the same content is a no-op. Existing
appStoreVersions / localizations are PATCHed rather than re-created.
"""
from __future__ import annotations

import sys
from asc_client import ASCClient, ASCError

APP_ID = "6770101543"
TARGET_VERSION = "1.0"
DEFAULT_LOCALE = "en-US"
EXTRA_LOCALES = ["ko", "ja"]  # additional App Store storefront locales


# ── Content ──────────────────────────────────────────────────────────

COPY = {
    "en-US": {
        "name": "K-Pop Heardle",  # required
        "subtitle": "Guess today's K-pop song",
        "description": (
            "K-Pop Heardle is a daily K-pop song guessing game.\n\n"
            "Each day you get one fresh global puzzle plus a per-group "
            "daily for NewJeans, IVE, LE SSERAFIM, aespa, Stray Kids, "
            "ATEEZ, ENHYPEN, and TXT.\n\n"
            "Listen to a one-second clip. Guess the song. Wrong? You get "
            "two seconds. Then four. Up to six tries before the answer "
            "is revealed.\n\n"
            "Strict mode for serious fans — both the song title AND the "
            "artist must match. Get the artist right but the song wrong? "
            "You earn a hint. After three wrong attempts, the app drops "
            "extra clues: girl group vs boy group vs solo, debut year, "
            "and the artist's first letter.\n\n"
            "Build your streak. Compare attempt distributions over time. "
            "Share your daily result with the classic emoji grid.\n\n"
            "100% on-device. No accounts. No ads. No tracking."
        ),
        "promotionalText": (
            "Daily K-pop guessing for 4th-gen fans. Listen, guess, share."
        ),
        "keywords": "kpop,k-pop,heardle,kpop game,nwjns,kpop quiz,music guess,kpop daily,song guess,bts",
        "marketingUrl": "https://github.com/jinnsim/kpop-heardle",
        "supportUrl": "https://github.com/jinnsim/kpop-heardle/issues",
        "whatsNew": "Initial release.",
    },
    "ko": {
        "name": "K-Pop Heardle",
        "subtitle": "오늘의 K-pop 곡 맞추기",
        "description": (
            "K-Pop Heardle은 매일 한 곡씩 K-pop을 맞추는 데일리 게임입니다.\n\n"
            "매일 전체 그룹 데일리 1곡 + 그룹별(뉴진스/아이브/르세라핌/에스파/"
            "스트레이키즈/에이티즈/엔하이픈/투바투) 데일리가 제공됩니다.\n\n"
            "1초만 듣고 맞춰보세요. 틀리면 2초, 그 다음은 4초... 6번 안에 "
            "정답을 맞춰야 합니다.\n\n"
            "엄격 모드 — 곡명과 아티스트 둘 다 정답이어야 성공. 아티스트만 "
            "맞추면 부분 정답 힌트로 표시됩니다. 3번 실패 시 그룹 타입, 4번엔 "
            "데뷔년도, 5번엔 아티스트 첫 글자까지 단계별 힌트가 공개됩니다.\n\n"
            "스트릭을 쌓아보세요. 시도 분포 그래프로 본인 실력을 시각화하고, "
            "Wordle 스타일 이모지 그리드로 결과를 공유할 수 있어요.\n\n"
            "100% 온디바이스. 회원가입 없음. 광고 없음. 트래킹 없음."
        ),
        "promotionalText": (
            "4세대 K-pop 팬을 위한 데일리 노래 맞추기. 듣고, 맞추고, 공유하세요."
        ),
        "keywords": "케이팝,kpop,히어들,뉴진스,아이브,르세라핌,에스파,데일리,노래맞추기,퀴즈",
        "marketingUrl": "https://github.com/jinnsim/kpop-heardle",
        "supportUrl": "https://github.com/jinnsim/kpop-heardle/issues",
        "whatsNew": "첫 출시.",
    },
    "ja": {
        "name": "K-Pop Heardle",
        "subtitle": "今日のK-POPを当てよう",
        "description": (
            "K-Pop Heardle は毎日 K-POP を 1 曲ずつ当てるデイリーゲームです。\n\n"
            "毎日、全グループ対象のデイリー 1 曲＋グループ別（NewJeans, IVE, "
            "LE SSERAFIM, aespa, Stray Kids, ATEEZ, ENHYPEN, TXT）のデイリーが "
            "用意されています。\n\n"
            "最初は 1 秒だけ。間違えると 2 秒、次は 4 秒…全 6 回以内に当てましょう。\n\n"
            "厳格モード — 曲名とアーティスト名の両方が正解で成功。アーティスト "
            "だけ合っていれば部分正解のヒントが付きます。3 回間違えるとグループ "
            "タイプ、4 回でデビュー年、5 回でアーティスト名の頭文字までヒントが "
            "段階的に開示されます。\n\n"
            "連勝を積み重ね、回答分布グラフで実力を可視化。Wordle スタイルの "
            "絵文字グリッドで結果をシェアできます。\n\n"
            "100% オンデバイス。アカウント登録なし。広告なし。トラッキングなし。"
        ),
        "promotionalText": (
            "4 世代 K-POP ファン向けのデイリー曲当て。聴いて、当てて、シェアしよう。"
        ),
        "keywords": "ケーポップ,kpop,ヒアドル,NewJeans,IVE,デイリー,曲当て,クイズ,音楽",
        "marketingUrl": "https://github.com/jinnsim/kpop-heardle",
        "supportUrl": "https://github.com/jinnsim/kpop-heardle/issues",
        "whatsNew": "初回リリース。",
    },
}

# Hosted privacy URL set via app-level (separate from version localizations).
PRIVACY_POLICY_URL = "https://jinnsim.github.io/kpop-heardle/privacy"


# ── Helpers ──────────────────────────────────────────────────────────

def get_or_create_app_store_version(c: ASCClient, app_id: str, version_string: str) -> dict:
    """Return the editable app store version (creates if missing)."""
    # GET_COLLECTION isn't allowed on /appStoreVersions; use the
    # app→versions relationship endpoint instead and filter client-side.
    resp = c.get(f"/apps/{app_id}/appStoreVersions",
                 **{"filter[versionString]": version_string})
    for v in resp.get("data", []):
        if v["attributes"]["versionString"] == version_string:
            print(f"  found existing app store version {version_string} id={v['id']} "
                  f"state={v['attributes'].get('appStoreState')}")
            return v

    # Create new
    print(f"  creating app store version {version_string}…")
    body = {
        "data": {
            "type": "appStoreVersions",
            "attributes": {
                "platform": "IOS",
                "versionString": version_string,
            },
            "relationships": {
                "app": {"data": {"type": "apps", "id": app_id}},
            },
        }
    }
    return c.post("/appStoreVersions", body)["data"]


def get_or_create_version_localization(c: ASCClient,
                                       version_id: str,
                                       locale: str) -> dict:
    resp = c.get(f"/appStoreVersions/{version_id}/appStoreVersionLocalizations")
    for loc in resp.get("data", []):
        if loc["attributes"]["locale"] == locale:
            return loc
    print(f"    creating localization {locale}…")
    body = {
        "data": {
            "type": "appStoreVersionLocalizations",
            "attributes": {"locale": locale},
            "relationships": {
                "appStoreVersion": {
                    "data": {"type": "appStoreVersions", "id": version_id}
                }
            },
        }
    }
    return c.post("/appStoreVersionLocalizations", body)["data"]


def update_version_localization(c: ASCClient,
                                loc_id: str,
                                copy: dict,
                                include_whats_new: bool = True) -> None:
    attrs = {
        "description":      copy["description"],
        "keywords":         copy["keywords"],
        "promotionalText":  copy["promotionalText"],
        "marketingUrl":     copy["marketingUrl"],
        "supportUrl":       copy["supportUrl"],
    }
    if include_whats_new:
        attrs["whatsNew"] = copy["whatsNew"]
    body = {
        "data": {
            "type": "appStoreVersionLocalizations",
            "id": loc_id,
            "attributes": attrs,
        }
    }
    c.patch(f"/appStoreVersionLocalizations/{loc_id}", body)


def get_or_create_app_info_localization(c: ASCClient,
                                        app_info_id: str,
                                        locale: str,
                                        name: str,
                                        subtitle: str | None,
                                        privacy_policy_url: str) -> None:
    resp = c.get(f"/appInfos/{app_info_id}/appInfoLocalizations")
    existing = next(
        (l for l in resp.get("data", []) if l["attributes"]["locale"] == locale),
        None,
    )
    attrs = {
        "name": name,
        "subtitle": subtitle,
        "privacyPolicyUrl": privacy_policy_url,
    }
    if existing:
        body = {"data": {"type": "appInfoLocalizations",
                         "id": existing["id"],
                         "attributes": attrs}}
        c.patch(f"/appInfoLocalizations/{existing['id']}", body)
    else:
        print(f"    creating app info localization {locale}…")
        body = {
            "data": {
                "type": "appInfoLocalizations",
                "attributes": {"locale": locale, **attrs},
                "relationships": {
                    "appInfo": {"data": {"type": "appInfos", "id": app_info_id}}
                },
            }
        }
        c.post("/appInfoLocalizations", body)


def latest_editable_app_info(c: ASCClient, app_id: str) -> dict:
    """Most ASC apps have multiple AppInfo records (one per state).
    The editable one is in PREPARE_FOR_SUBMISSION or similar."""
    resp = c.get(f"/apps/{app_id}/appInfos")
    # Prefer one in editable state
    editable_states = {"PREPARE_FOR_SUBMISSION", "REJECTED", "DEVELOPER_REJECTED"}
    for info in resp["data"]:
        if info["attributes"].get("state") in editable_states:
            return info
    return resp["data"][0]


# ── Main ─────────────────────────────────────────────────────────────

def main() -> int:
    c = ASCClient()

    print("→ Fetching app…")
    app = c.get(f"/apps/{APP_ID}")["data"]
    print(f"  app: {app['attributes']['name']} ({app['attributes']['bundleId']})")

    print("→ Resolving editable AppInfo…")
    app_info = latest_editable_app_info(c, APP_ID)
    print(f"  appInfo id={app_info['id']} state={app_info['attributes'].get('state')}")

    print("→ Setting AppInfo per-locale name + subtitle + privacy URL…")
    for loc, copy in [(DEFAULT_LOCALE, COPY["en-US"])] + [
        ({"ko": "ko", "ja": "ja"}[l], COPY[l]) for l in EXTRA_LOCALES
    ]:
        print(f"  → {loc}")
        get_or_create_app_info_localization(
            c, app_info["id"], loc,
            name=copy["name"],
            subtitle=copy["subtitle"],
            privacy_policy_url=PRIVACY_POLICY_URL,
        )

    print("→ Resolving editable AppStoreVersion (1.0)…")
    version = get_or_create_app_store_version(c, APP_ID, TARGET_VERSION)

    # whatsNew is only valid for updates (not the first version).
    is_first_version = TARGET_VERSION == "1.0"
    include_whats_new = not is_first_version

    print("→ Writing per-locale version metadata (description/keywords/etc)…")
    for loc_key, copy in [(DEFAULT_LOCALE, COPY["en-US"])] + [
        ({"ko": "ko", "ja": "ja"}[l], COPY[l]) for l in EXTRA_LOCALES
    ]:
        print(f"  → {loc_key}")
        loc = get_or_create_version_localization(c, version["id"], loc_key)
        update_version_localization(c, loc["id"], copy,
                                    include_whats_new=include_whats_new)

    print("✓ Metadata setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
