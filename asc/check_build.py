"""
Show all uploaded builds for KPopHeardle with processing state and
export compliance status.
"""
from asc_client import ASCClient

APP_ID = "6770101543"


def main() -> int:
    c = ASCClient()
    params = {
        "filter[app]": APP_ID,
        "sort": "-uploadedDate",
        "limit": "10",
    }
    data = c.get("/builds", **params)["data"]

    print(f"{'Build':<10} {'Version':<10} {'State':<28} {'Compliance':<20}  Uploaded")
    print("-" * 100)
    for build in data:
        a = build["attributes"]
        print(
            f"{a.get('version','?'):<10} "
            f"{a.get('preReleaseVersion',{}).get('attributes',{}).get('version','-') if False else a.get('version','-'):<10} "
            f"{a.get('processingState','?'):<28} "
            f"{a.get('usesNonExemptEncryption','?')!s:<20}  "
            f"{a.get('uploadedDate','?')}"
        )
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
