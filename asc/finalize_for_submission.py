"""
Patch the last few required fields that surface only when submitting:
- App.contentRightsDeclaration
- AppStoreVersion.copyright
- AppStoreVersion's appStoreReviewDetail (reviewer contact info)
"""
from __future__ import annotations

import sys
from asc_client import ASCClient, ASCError

APP_ID = "6770101543"
TARGET_VERSION = "1.0"
COPYRIGHT = "© 2026 Jung Soon Shin"

# Reviewer contact — Apple uses these only if they need to ask questions
# or if a demo account is needed. Game has no auth, so demo creds blank.
REVIEW_CONTACT = {
    "contactFirstName": "Jung Soon",
    "contactLastName": "Shin",
    "contactPhone": "+82-10-0000-0000",   # placeholder; replace with real
    "contactEmail": "jinnsim@gmail.com",
    "demoAccountName": "",
    "demoAccountPassword": "",
    "demoAccountRequired": False,
    "notes": (
        "K-Pop Heardle is a daily song-guessing game. No account is "
        "required. To test: open the app, tap any 'Today's Daily' or "
        "group card, press the play button, then start typing an artist "
        "or song name into the search field. The autocomplete shows "
        "Artist — Song entries; tap one to submit a guess. After a win "
        "or six failed attempts the result sheet appears with Apple "
        "Music deep-link and share. All audio is from Apple's public "
        "iTunes Search API (30-second previews)."
    ),
}


def get_version(c: ASCClient) -> dict:
    resp = c.get(f"/apps/{APP_ID}/appStoreVersions",
                 **{"filter[versionString]": TARGET_VERSION})
    return next(v for v in resp["data"]
                if v["attributes"]["versionString"] == TARGET_VERSION)


def set_content_rights(c: ASCClient) -> None:
    body = {
        "data": {
            "type": "apps",
            "id": APP_ID,
            "attributes": {
                # Audio previews come from third-party labels (via Apple's
                # public iTunes API). We have the rights through that API
                # to use 30-second previews in our app.
                "contentRightsDeclaration": "USES_THIRD_PARTY_CONTENT",
            },
        }
    }
    c.patch(f"/apps/{APP_ID}", body)
    print("  set contentRightsDeclaration=USES_THIRD_PARTY_CONTENT")


def set_copyright(c: ASCClient, version_id: str) -> None:
    body = {
        "data": {
            "type": "appStoreVersions",
            "id": version_id,
            "attributes": {"copyright": COPYRIGHT},
        }
    }
    c.patch(f"/appStoreVersions/{version_id}", body)
    print(f"  set copyright='{COPYRIGHT}'")


def get_or_create_review_detail(c: ASCClient, version_id: str) -> str:
    try:
        resp = c.get(f"/appStoreVersions/{version_id}/appStoreReviewDetail")
        existing = resp.get("data")
        if existing:
            print(f"  review detail already exists id={existing['id']}, updating…")
            body = {
                "data": {
                    "type": "appStoreReviewDetails",
                    "id": existing["id"],
                    "attributes": REVIEW_CONTACT,
                }
            }
            c.patch(f"/appStoreReviewDetails/{existing['id']}", body)
            return existing["id"]
    except ASCError as e:
        if e.status != 404:
            raise

    print("  creating review detail…")
    body = {
        "data": {
            "type": "appStoreReviewDetails",
            "attributes": REVIEW_CONTACT,
            "relationships": {
                "appStoreVersion": {
                    "data": {"type": "appStoreVersions", "id": version_id}
                }
            },
        }
    }
    resp = c.post("/appStoreReviewDetails", body)
    return resp["data"]["id"]


def main() -> int:
    c = ASCClient()

    print("→ Setting contentRightsDeclaration on app…")
    set_content_rights(c)

    print("→ Fetching version 1.0…")
    version = get_version(c)
    print(f"  version id={version['id']}")

    print("→ Setting copyright on version…")
    set_copyright(c, version["id"])

    print("→ Creating/updating app review detail (contact info)…")
    detail_id = get_or_create_review_detail(c, version["id"])
    print(f"  review detail id={detail_id}")

    print("✓ Finalization complete. Re-run submit_for_review.py to submit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
