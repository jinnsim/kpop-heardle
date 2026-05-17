"""
Final submission step. Selects the latest VALID build, uploads
screenshot(s), and creates a Review Submission.

Run after setup_metadata.py, setup_classification.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import requests
from asc_client import ASCClient, ASCError

APP_ID = "6770101543"
TARGET_VERSION = "1.0"

# Display-type → local screenshot directory mapping.
# We upload whatever exists; missing dirs are skipped silently.
SCREENSHOT_SETS = [
    # 6.7" iPhone (iPhone 14/15 Pro Max @ 1290×2796).
    # Apple still accepts 6.7" for submission even after the 6.9" was
    # added — they auto-scale up if no 6.9" provided.
    ("APP_IPHONE_67", Path(__file__).parent / "screenshots"),

    # 12.9" iPad Pro (3rd gen and later, @ 2048×2732).
    ("APP_IPAD_PRO_3GEN_129", Path(__file__).parent / "screenshots-ipad"),
]


# ── Helpers ──────────────────────────────────────────────────────────

def latest_valid_build(c: ASCClient, app_id: str) -> dict:
    resp = c.get(
        "/builds",
        **{
            "filter[app]": app_id,
            "filter[processingState]": "VALID",
            "sort": "-uploadedDate",
            "limit": "5",
        },
    )
    for b in resp.get("data", []):
        if b["attributes"].get("processingState") == "VALID":
            return b
    raise RuntimeError("No VALID build found.")


def get_version(c: ASCClient, app_id: str, version_string: str) -> dict:
    resp = c.get(f"/apps/{app_id}/appStoreVersions",
                 **{"filter[versionString]": version_string})
    for v in resp.get("data", []):
        if v["attributes"]["versionString"] == version_string:
            return v
    raise RuntimeError(f"No app store version {version_string}")


def promote_build_to_app_store_eligible(c: ASCClient, build_id: str) -> None:
    """Xcode Cloud's default audience is INTERNAL_ONLY (TestFlight only).
    Promote to APP_STORE_ELIGIBLE so the build can be attached to an
    App Store version. Idempotent if already eligible."""
    body = {
        "data": {
            "type": "builds",
            "id": build_id,
            "attributes": {"buildAudienceType": "APP_STORE_ELIGIBLE"},
        }
    }
    try:
        c.patch(f"/builds/{build_id}", body)
        print(f"  promoted build {build_id} → APP_STORE_ELIGIBLE")
    except ASCError as e:
        if e.status == 409 and "already" in str(e.payload).lower():
            print(f"  already APP_STORE_ELIGIBLE")
        else:
            raise


def attach_build_to_version(c: ASCClient, version_id: str, build_id: str) -> None:
    body = {"data": {"type": "builds", "id": build_id}}
    c.patch(f"/appStoreVersions/{version_id}/relationships/build", body)
    print(f"  attached build {build_id} → version {version_id}")


def get_en_us_localization(c: ASCClient, version_id: str) -> dict:
    resp = c.get(f"/appStoreVersions/{version_id}/appStoreVersionLocalizations")
    for loc in resp["data"]:
        if loc["attributes"]["locale"] == "en-US":
            return loc
    raise RuntimeError("en-US localization missing — run setup_metadata.py first")


def get_or_create_screenshot_set(c: ASCClient, loc_id: str, display_type: str) -> dict:
    resp = c.get(f"/appStoreVersionLocalizations/{loc_id}/appScreenshotSets")
    for s in resp.get("data", []):
        if s["attributes"]["screenshotDisplayType"] == display_type:
            return s
    print(f"  creating screenshot set for {display_type}…")
    body = {
        "data": {
            "type": "appScreenshotSets",
            "attributes": {"screenshotDisplayType": display_type},
            "relationships": {
                "appStoreVersionLocalization": {
                    "data": {"type": "appStoreVersionLocalizations", "id": loc_id}
                }
            },
        }
    }
    return c.post("/appScreenshotSets", body)["data"]


def existing_screenshot_filenames(c: ASCClient, set_id: str) -> set[str]:
    resp = c.get(f"/appScreenshotSets/{set_id}/appScreenshots")
    return {s["attributes"]["fileName"] for s in resp.get("data", [])}


def upload_screenshot(c: ASCClient, set_id: str, file_path: Path) -> None:
    size = file_path.stat().st_size

    # 1. Reserve the asset
    print(f"  reserving {file_path.name} ({size} bytes)…")
    body = {
        "data": {
            "type": "appScreenshots",
            "attributes": {
                "fileSize": size,
                "fileName": file_path.name,
            },
            "relationships": {
                "appScreenshotSet": {
                    "data": {"type": "appScreenshotSets", "id": set_id}
                }
            },
        }
    }
    reservation = c.post("/appScreenshots", body)["data"]
    asset_id = reservation["id"]
    operations = reservation["attributes"]["uploadOperations"]

    # 2. Run each upload operation (usually a single PUT)
    file_bytes = file_path.read_bytes()
    for op in operations:
        method = op["method"]
        url = op["url"]
        headers = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}
        offset = op["offset"]
        length = op["length"]
        chunk = file_bytes[offset:offset + length]
        r = requests.request(method, url, headers=headers, data=chunk, timeout=120)
        if r.status_code >= 400:
            raise RuntimeError(f"upload {method} {url} → {r.status_code} {r.text[:300]}")

    # 3. Finalize with MD5 checksum + uploaded=true
    checksum = hashlib.md5(file_bytes).hexdigest()
    patch_body = {
        "data": {
            "type": "appScreenshots",
            "id": asset_id,
            "attributes": {
                "uploaded": True,
                "sourceFileChecksum": checksum,
            },
        }
    }
    c.patch(f"/appScreenshots/{asset_id}", patch_body)
    print(f"    ✓ {file_path.name} uploaded")


def create_review_submission(c: ASCClient, app_id: str, version_id: str) -> str:
    # 1. Create the review submission for the app + platform
    print("  creating review submission…")
    sub_body = {
        "data": {
            "type": "reviewSubmissions",
            "attributes": {"platform": "IOS"},
            "relationships": {
                "app": {"data": {"type": "apps", "id": app_id}},
            },
        }
    }
    try:
        submission = c.post("/reviewSubmissions", sub_body)["data"]
    except ASCError as e:
        # If one already exists in editable state, fetch it
        if e.status == 409:
            resp = c.get("/reviewSubmissions",
                         **{"filter[app]": app_id, "filter[platform]": "IOS",
                            "filter[state]": "READY_FOR_REVIEW,WAITING_FOR_REVIEW,IN_REVIEW,COMPLETING,UNRESOLVED_ISSUES,CANCELING"})
            submission = next(iter(resp.get("data", [])), None)
            if not submission:
                raise
            print(f"  reusing existing submission {submission['id']}")
        else:
            raise
    sub_id = submission["id"]

    # 2. Attach the AppStoreVersion as a submission item
    print(f"  attaching version {version_id} to submission {sub_id}…")
    item_body = {
        "data": {
            "type": "reviewSubmissionItems",
            "relationships": {
                "reviewSubmission": {
                    "data": {"type": "reviewSubmissions", "id": sub_id}
                },
                "appStoreVersion": {
                    "data": {"type": "appStoreVersions", "id": version_id}
                },
            },
        }
    }
    try:
        c.post("/reviewSubmissionItems", item_body)
    except ASCError as e:
        if e.status == 409:
            print("  (already attached)")
        else:
            raise

    # 3. Submit
    print("  submitting…")
    submit_body = {
        "data": {
            "type": "reviewSubmissions",
            "id": sub_id,
            "attributes": {"submitted": True},
        }
    }
    c.patch(f"/reviewSubmissions/{sub_id}", submit_body)
    return sub_id


# ── Main ─────────────────────────────────────────────────────────────

def main() -> int:
    c = ASCClient()

    print("→ Finding latest VALID build…")
    build = latest_valid_build(c, APP_ID)
    a = build["attributes"]
    print(f"  build {a['version']} (id={build['id']}) uploaded {a['uploadedDate']}")

    print("→ Fetching AppStoreVersion 1.0…")
    version = get_version(c, APP_ID, TARGET_VERSION)
    print(f"  version id={version['id']} state={version['attributes']['appStoreState']}")

    print("→ Promoting build to App Store eligible…")
    promote_build_to_app_store_eligible(c, build["id"])

    print("→ Attaching build to version…")
    attach_build_to_version(c, version["id"], build["id"])

    print("→ Uploading screenshots…")
    loc = get_en_us_localization(c, version["id"])
    for display_type, src_dir in SCREENSHOT_SETS:
        files = sorted(src_dir.glob("*.png")) if src_dir.exists() else []
        if not files:
            print(f"  ({display_type}) no files in {src_dir} — skipping")
            continue
        print(f"  ({display_type}) {len(files)} file(s) from {src_dir.name}/")
        screenshot_set = get_or_create_screenshot_set(c, loc["id"], display_type)
        existing = existing_screenshot_filenames(c, screenshot_set["id"])
        for fp in files:
            if fp.name in existing:
                print(f"    skip (already present): {fp.name}")
                continue
            upload_screenshot(c, screenshot_set["id"], fp)

    print("→ Creating review submission…")
    sub_id = create_review_submission(c, APP_ID, version["id"])
    print(f"✓ Submitted! Review submission id={sub_id}")
    print("  Watch progress in App Store Connect → App Review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
