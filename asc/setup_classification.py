"""
Set categories, age rating, pricing, and availability for kpopheardle.

Categories:
  Primary: GAMES / GAMES_TRIVIA   (Heardle is technically trivia)
  Secondary: MUSIC

Age rating:
  4+ — no objectionable content. All questionnaire answers are NONE.

Pricing: Free (tier 0 / USD_0)
Availability: Worldwide (default — no territory restriction needed)
"""
from __future__ import annotations

import sys
from asc_client import ASCClient, ASCError

APP_ID = "6770101543"


def list_categories(c: ASCClient) -> None:
    """One-time discovery helper. Prints available platform + categories."""
    resp = c.get("/appCategories", **{"filter[platforms]": "IOS"})
    for cat in resp.get("data", []):
        a = cat["attributes"]
        print(f"  {cat['id']}  ({a.get('platforms')})")


def latest_editable_app_info(c: ASCClient, app_id: str) -> dict:
    resp = c.get(f"/apps/{app_id}/appInfos")
    for info in resp["data"]:
        if info["attributes"].get("state") in {"PREPARE_FOR_SUBMISSION", "REJECTED", "DEVELOPER_REJECTED"}:
            return info
    return resp["data"][0]


def set_categories(c: ASCClient, app_info_id: str,
                   primary_id: str, primary_sub_one_id: str | None = None,
                   secondary_id: str | None = None) -> None:
    attrs: dict = {}
    rels: dict = {
        "primaryCategory": {"data": {"type": "appCategories", "id": primary_id}},
    }
    if primary_sub_one_id:
        rels["primarySubcategoryOne"] = {
            "data": {"type": "appCategories", "id": primary_sub_one_id}
        }
    if secondary_id:
        rels["secondaryCategory"] = {
            "data": {"type": "appCategories", "id": secondary_id}
        }
    body = {
        "data": {
            "type": "appInfos",
            "id": app_info_id,
            "relationships": rels,
        }
    }
    c.patch(f"/appInfos/{app_info_id}", body)
    print(f"  categories set: primary={primary_id} "
          f"sub1={primary_sub_one_id} secondary={secondary_id}")


def set_age_rating_4plus(c: ASCClient, app_info_id: str) -> None:
    """Submit a "no objectionable content" age-rating declaration."""
    # All answers default to NONE means rating is 4+.
    # Check if a declaration already exists.
    existing = c.get(f"/appInfos/{app_info_id}/ageRatingDeclaration")
    declaration_id = existing.get("data", {}).get("id")

    # Apple's age rating questionnaire — all NONE / False for a clean
    # 4+ rating. K-Pop Heardle has no objectionable content of any kind.
    attrs = {
        # ── Frequency-based content questions (NONE / INFREQUENT_OR_MILD / FREQUENT_OR_INTENSE)
        "alcoholTobaccoOrDrugUseOrReferences": "NONE",
        "contests": "NONE",
        "gamblingSimulated": "NONE",
        "medicalOrTreatmentInformation": "NONE",
        "profanityOrCrudeHumor": "NONE",
        "sexualContentGraphicAndNudity": "NONE",
        "sexualContentOrNudity": "NONE",
        "horrorOrFearThemes": "NONE",
        "matureOrSuggestiveThemes": "NONE",
        "violenceCartoonOrFantasy": "NONE",
        "violenceRealistic": "NONE",
        "violenceRealisticProlongedGraphicOrSadistic": "NONE",
        "gunsOrOtherWeapons": "NONE",
        # ── Boolean questions
        "unrestrictedWebAccess": False,
        "gambling": False,
        "lootBox": False,
        "advertising": False,
        "messagingAndChat": False,
        "parentalControls": False,
        "healthOrWellnessTopics": False,
        "ageAssurance": False,
        "userGeneratedContent": False,
        "ageRatingOverride": "NONE",
        "kidsAgeBand": None,
    }
    if declaration_id:
        body = {"data": {"type": "ageRatingDeclarations",
                         "id": declaration_id,
                         "attributes": attrs}}
        c.patch(f"/ageRatingDeclarations/{declaration_id}", body)
        print(f"  age rating updated (4+, all 'NONE')")
    else:
        # Create a fresh declaration linked to the app info
        body = {
            "data": {
                "type": "ageRatingDeclarations",
                "attributes": attrs,
                "relationships": {
                    "appInfo": {"data": {"type": "appInfos", "id": app_info_id}}
                },
            }
        }
        c.post("/ageRatingDeclarations", body)
        print(f"  age rating created (4+)")


def set_pricing_free(c: ASCClient, app_id: str) -> None:
    """Set app to free tier. Uses the v1 appPriceSchedules endpoint."""
    # Look up the FREE price point id (customerPrice == 0.0 in USA).
    resp = c.get(f"/apps/{app_id}/appPricePoints",
                 **{"filter[territory]": "USA", "limit": "1"})
    free_pp_id = resp["data"][0]["id"]
    print(f"  USA free price point: {free_pp_id}")
    body = {
        "data": {
            "type": "appPriceSchedules",
            "relationships": {
                "app": {"data": {"type": "apps", "id": app_id}},
                "baseTerritory": {"data": {"type": "territories", "id": "USA"}},
                "manualPrices": {
                    "data": [{"type": "appPrices", "id": "${price1}"}],
                },
            },
        },
        "included": [
            {
                "type": "appPrices",
                "id": "${price1}",
                "attributes": {"startDate": None},
                "relationships": {
                    "appPricePoint": {
                        "data": {
                            "type": "appPricePoints",
                            "id": free_pp_id,
                        },
                    },
                },
            },
        ],
    }
    try:
        c.post("/appPriceSchedules", body)
        print("  pricing set to FREE")
    except ASCError as e:
        # Already set or otherwise — log and continue
        print(f"  pricing skipped: {e}")


def main() -> int:
    c = ASCClient()

    print("→ Resolving editable AppInfo…")
    app_info = latest_editable_app_info(c, APP_ID)
    print(f"  appInfo id={app_info['id']}")

    print("→ Setting categories (Games/Trivia + Music)…")
    set_categories(
        c, app_info["id"],
        primary_id="GAMES",
        primary_sub_one_id="GAMES_TRIVIA",
        secondary_id="MUSIC",
    )

    print("→ Setting age rating to 4+…")
    set_age_rating_4plus(c, app_info["id"])

    print("→ Setting pricing to FREE…")
    set_pricing_free(c, APP_ID)

    print("✓ Classification complete.")
    print("  Note: availability (territories) defaults to all available regions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
