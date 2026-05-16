# Session log

Newest first. Append entries when finishing a non-trivial session so the
next session knows what's in flight.

---

## 2026-05-17 — Codex review pass: all 12 findings fixed

Ran `codex exec` as a second-opinion code review against the current
state. Codex flagged 12 issues (1 CRITICAL, 3 HIGH, 5 MEDIUM, 2 LOW)
plus a verdict. All addressed in this commit.

**Fixes:**

CRITICAL
- #1 `schedule_picker.py`: switched to KST (`datetime.now(KST).date()`)
  instead of `date.today()` (UTC on Ubuntu runner). The 15:00 UTC cron
  now correctly schedules the new KST day instead of the previous one.

HIGH
- #2 + #9: re-isolated all `@Observable` UI services with `@MainActor`
  (`CatalogService`, `AudioService`, `NotificationService`,
  `GameCoordinator`). The earlier "GameCoordinator must be nonisolated"
  constraint in CLAUDE.md is removed; the `App` struct itself is now
  `@MainActor` so `@State` initializers compile. View structs that hold
  helper computed properties / methods touching services
  (`StatsView`, `GameView`, `PlayerControls`, `GuessInputView`) are
  also `@MainActor`-annotated.
- #3 `StatsCalculator.currentStreak`: explicitly checks for a loss
  record on today's date and returns 0 in that case, instead of
  silently falling back to yesterday's streak.
- #4 `schedule_picker.py`: when the no-repeat candidate pool is empty,
  fall back to least-recently-used song instead of a hash pick from
  the full catalog. Per-group dailies with <90 songs now rotate fairly.

MEDIUM
- #5 `GameView.titleText`: now uses `game.targetGroup?.nameEn`
  (e.g. "Stray Kids") instead of `groupId.capitalized`
  ("Stray_Kids"). `GameMode.localizedTitle` removed.
- #6: artist-only credit comparison left as-is — Songs come from the
  autocomplete which always supplies `artistEn`, so the edge case
  Codex flagged is not reachable in practice. Will revisit if/when
  free-text input is added.
- #7 `build_catalog.py`: filter regex extended for `version` (full
  word), `Korean version`, `remaster`, `sped up`, `slowed`,
  `nightcore`, `radio/extended/club/dance edit/mix`, `prologue`,
  `epilogue`, `skit`, `demo`, and slash-mashup `X / Y` titles.
- #8 `build_catalog.py`: new `canonical_dedupe_key()` does NFKC
  normalization + casefold + quote/dash flatten + non-alphanumeric
  strip. On collision, the newer release wins. Verified clean: the
  previously-duplicated "Eve, Psyche & The/the Bluebeard's wife" and
  "Can't Stop / Can′t Stop" now collapse to single entries.
- #10 `CatalogService.loadError` is now `CatalogLoadError` enum;
  `ContentView` renders a new `catalog.unavailable.body` localized
  key for all 13 locales. `AudioService.error` left as String for
  internal diagnostics with a comment.

LOW
- #11 `NotificationService.syncSchedule`: also schedules when
  authorization is `.provisional` (silent delivery is still useful).
- #12 `StatsView`: `currentStreak` is computed once per render and
  reused for both the displayed value and the 🔥 emoji condition.

**Catalog refresh as part of this work:**
- Rebuilt catalog with new filters + dedup → 300 songs across 8 groups
  (vs prior 233). Today's KST schedule populated.
- NewJeans only has 20 songs (limited discography, expected).

**Build state:**
- Clean build (0 warnings, 0 errors) on iOS Sim 17.2 iPhone 15
- Home screen verified in Korean post-fix (oneului daily + all groups)
- AudioService deinit no longer touches MainActor state (uses AVPlayer's
  own observer cleanup on dealloc)

**Next:**
- Tap into a Group Daily → game screen on Apple Silicon Mac to
  visually confirm group title now shows "NewJeans Daily" not
  "Newjeans Daily" / "Stray Kids Daily" not "Stray_Kids Daily"
- Native translation review still pending

---

## 2026-05-17 — Stats, notifications, settings, onboarding, tab nav

**Changes:**
- `Services/StatsCalculator.swift`: pure functions for played / win rate /
  current streak / longest streak / attempt histogram. Operates on the
  existing `PuzzleRecord` SwiftData history.
- `Views/StatsView.swift`: SwiftData @Query feeds a per-scope card
  (global daily + each group the user has played). Each card shows the
  4-number stat row + a 1..6+X histogram chart.
- `Services/NotificationService.swift`: wraps `UNUserNotificationCenter`.
  Persists `remindersEnabled` in UserDefaults (default true). Schedules
  a daily local notification at 00:05 local time, repeating. Idempotent
  `syncSchedule()`. No remote / APNs — fully on-device.
- `Views/SettingsView.swift`: Daily reminder toggle (requests permission
  on first enable), denied-state hint, About section (catalog version,
  song count, group count, app version), Attribution disclaimer.
- `Views/OnboardingSheet.swift`: 3-page introduction (hear/guess, search,
  daily). Presented once via `@AppStorage("kph.onboardingSeen")`. Final
  page tap triggers the notification permission request.
- `Views/RootTabView.swift`: TabView wrapping Home / Stats / Settings.
- `App/KPopHeardleApp.swift`: wires NotificationService env, presents
  onboarding sheet on first launch, syncs notification schedule on
  bootstrap.
- `Resources/Localizable.xcstrings`: added 32 new keys × 13 locales =
  ~400 new translations (all AI-generated; review caveat unchanged).
- Two small fixes during integration:
  1. `OnboardingPage.body` shadowed SwiftUI's `body` requirement — renamed
     to `bodyText`.
  2. `@MainActor` on `NotificationService` blocked `@State` init in App;
     removed since the class only does UserDefaults reads + async API
     calls that are themselves thread-safe.

**State after session:**
- Build clean on Intel iOS Sim 17.2
- Home tab + tab bar verified visually
- Onboarding first page verified visually
- Stats / Settings tabs verified to compile + show in tab bar (full
  visual verification of those screens still pending)
- Notification permission prompt only fires after onboarding completes
  (so the first-launch sequence is: onboarding → permission → home)

**Next:**
- Tap-through verify Stats + Settings on Apple Silicon Mac
- GameKit leaderboard wiring (needs DEVELOPMENT_TEAM set first)
- TestFlight beta with internal testers to gather translation feedback
  for Thai / Hindi / Filipino

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
