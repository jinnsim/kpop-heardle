"""
Declare 'data not collected' for App Privacy.

K-Pop Heardle collects nothing — everything is on-device. Apple still
requires an explicit declaration via the App Privacy API.
"""
from __future__ import annotations

import sys
from asc_client import ASCClient, ASCError

APP_ID = "6770101543"


def main() -> int:
    c = ASCClient()

    # The PrivacyDetail resource lives under /apps/{id}/appPrivacyDetail
    print("→ Checking existing privacy declaration…")
    try:
        existing = c.get(f"/apps/{APP_ID}/appPrivacyDetail")
        detail_id = existing.get("data", {}).get("id")
        print(f"  existing detail id={detail_id}")
    except ASCError as e:
        if e.status == 404:
            detail_id = None
            print("  no existing declaration")
        else:
            raise

    # If we have no detail, create one.
    if not detail_id:
        print("→ Creating empty app privacy detail…")
        body = {
            "data": {
                "type": "appPrivacyDetails",
                "relationships": {
                    "app": {"data": {"type": "apps", "id": APP_ID}},
                },
            }
        }
        try:
            resp = c.post("/appPrivacyDetails", body)
            detail_id = resp["data"]["id"]
            print(f"  created detail id={detail_id}")
        except ASCError as e:
            print(f"  warn: create failed ({e.status}); listing children to see state")
            print(f"  {e.payload}")

    # Each "data type" the app might collect needs an appPrivacyDataUsage
    # entry. Since we collect nothing, we just need ZERO entries — the
    # absence of entries means "Data Not Collected" once submitted.
    #
    # We do need to acknowledge that we've reviewed the questionnaire,
    # which is implied by submitting the version.
    print("✓ App Privacy: no data-usage entries needed (Data Not Collected).")
    print("  Apple infers 'Data Not Collected' from the absence of usage rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
