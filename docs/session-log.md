# Session log

Newest first. Append entries when finishing a non-trivial session so the
next session knows what's in flight.

---

## 2026-05-17 — Generated App Store app icon

**Changes:**
- Added `catalog/scripts/generate_icon.py`, a local Pillow script that
  renders the 1024x1024 K-Pop Heardle icon from the approved gradient,
  equalizer bars, and drop shadow spec.
- Generated
  `ios/KPopHeardle/Resources/Assets.xcassets/AppIcon.appiconset/Icon-1024.png`.
- Updated the app icon `Contents.json` 1024x1024 universal entry to
  reference `Icon-1024.png`.

**State after session:**
- `sips` verifies the PNG as 1024x1024 with `hasAlpha: no`.
- PNG mode is RGB and file size is 63,989 bytes.
- Pillow install from PyPI was blocked by DNS, so the generation command
  used the locally available Python 3.14 Pillow package via `PYTHONPATH`.

**Next:**
- Launch screen artwork remains in the Phase 1 leftover list.

---

## 2026-05-17 — Localization to 13 K-pop fan markets

**Changes:**
- Rewrote all user-facing strings in 8 Swift files to use
  `Text("key")` / `String(localized: "key")` / `LocalizedStringKey`.
  Catalog song titles + artist names stay un-localized (`Text(verbatim:)`).
- Added `ios/KPopHeardle/Resources/Localizable.xcstrings` with 26 keys
  × 13 locales = ~340 translations.
- Registered all 13 locales in `project.yml` `knownRegions`.
- Verified live in iOS Simulator for en, ko, ja, id, th. Screenshots in
  `docs/assets/home-{ko,ja,id,th}.png`.
- **Bug surfaced + fixed:** Thai locale's Buddhist calendar caused
  `todayString` to return "2569-05-17" instead of "2026-05-17", so no
  daily resolved. Fixed `GameCoordinator.scheduleFormatter` to use
  Gregorian + POSIX explicitly. See `docs/decisions.md` D13.
- Updated `docs/decisions.md` with D13 (locale list, AI-translation
  caveat, calendar fix).

**State after session:**
- Build clean on Intel Mac iOS Sim 17.2
- 13 locales registered, 4 screen-tested
- AI translations should be reviewed before launch (especially Thai
  particles, Hindi gender, Filipino code-switching, Korean honorific level)

**Next:**
- App icon (1024×1024 PNG) — see next session
- GameKit, stats view, push notification — see `docs/handoff.md`

---

## 2026-05-17 — Phase 1 scaffold from scratch (Intel Mac, Xcode 15.2)

**Changes:**
- Initialized repo at `/Users/jongjinseok/Documents/kpop-heardle`
- Built `xcodegen` 2.42.0 from source (Homebrew refused due to macOS 13)
  and installed to `~/.local/bin/xcodegen`. Required for any future
  `xcodegen generate` invocation on this Intel Mac.
- Wrote `ios/project.yml` (xcodegen spec) targeting iOS 17, bundle id
  `com.ootssu.kpopheardle`, no team ID yet.
- Wrote all 17 Swift source files (Models / Services / Views / App entry).
  Build clean on iPhone 15 / iOS 17.2 simulator.
- One semi-subtle fix during build: removed `@MainActor` from
  `GameCoordinator` because SwiftUI view bodies were calling its read-only
  methods synchronously. See `CLAUDE.md` constraint section.
- Wrote `catalog/scripts/build_catalog.py` (iTunes Search API → JSON),
  `schedule_picker.py` (deterministic daily picker), `merge_schedule.py`
  (preserves schedule across catalog rebuilds).
- Generated first real catalog: 233 songs across 8 4th-gen groups
  (NewJeans, IVE, LE SSERAFIM, aespa, Stray Kids, ATEEZ, ENHYPEN, TXT).
- Ran scheduler — today (2026-05-17) has a global daily + 8 group dailies
  all populated. Today's global pick is an ATEEZ song.
- Booted iPhone 15 sim, installed `KPopHeardle.app`, launched. Home screen
  renders correctly with real catalog data, group color gradients visible.
- Wrote `daily-schedule.yml` and `refresh-catalog.yml` workflows for
  GitHub Actions. Not yet pushed to GitHub.
- Wrote `README.md`, `docs/handoff.md`, `docs/decisions.md`, `CLAUDE.md`,
  `.gitignore`, this session log.
- Committed as `699b2b3 init: K-pop Heardle Phase 1 scaffold`.

**State after session:**
- Clean working tree on `main` branch
- No git remote set
- App compiles + launches + renders home screen
- Catalog has real data
- Scheduler has populated today's schedule
- Phase 1 leftover list in `docs/handoff.md` is current

**Known gotchas for the next session:**
- `ios/KPopHeardle.xcodeproj/` is in `.gitignore`. After cloning on a
  new machine, must run `cd ios && xcodegen generate` before opening Xcode.
- `requirements.txt` includes `certifi` because Python 3.14 on macOS hit
  SSL cert verification failures on iTunes API. Don't remove certifi —
  the script explicitly uses its CA bundle.
- `DeprecationWarning: datetime.datetime.utcnow()` was hit and fixed in
  both Python scripts. If you see it again, you've reverted the fix.
- Today's global daily on the sim shows correctly because `catalog.json`
  is bundled into the app. The remote URL
  (`https://kpop-heardle.pages.dev/catalog.json`) is a placeholder and
  will return 404 until Cloudflare Pages is wired up.

**Next (highest priority first):**
1. Move repo to Apple Silicon Mac (see `docs/handoff.md` step-by-step)
2. Set `DEVELOPMENT_TEAM` in `project.yml`
3. Register app on App Store Connect
4. Push to GitHub + connect Cloudflare Pages → real catalog URL
5. App icon (1024×1024 PNG)
6. Stats / streak view
7. GameKit leaderboard wiring
8. Daily-reminder local notification
9. Localization (en/ko/ja)

See `docs/handoff.md` for full details on each.
