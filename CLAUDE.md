# Claude / AI agent context

This file is auto-loaded by Claude Code when working in this repo.
Read it before doing anything in this codebase.

## What this project is

K-Pop Heardle: daily K-pop song guessing game for iOS. Plays the first
1s → 2s → 4s → 7s → 11s → 16s of an iTunes preview clip. Players guess
song + artist via a single autocomplete search bar (strict mode — both
must match).

Owner: Jung Soon Shin (jinnsim@gmail.com). Part of an ~22-app indie iOS
portfolio at https://ootssu.com/apps/.

## Read these first

In order, before making changes:

1. `README.md` — what each top-level directory does, how to build
2. `docs/handoff.md` — how to continue on another machine, what to do
   for App Store submission, full Phase 1 leftover list and Phase 2 plan
3. `docs/decisions.md` — design decisions and *why* (don't re-litigate
   without reason)
4. `docs/session-log.md` — what changed and when

## Hard constraints (don't break these)

- **Audio source is iTunes Search API ONLY.** Not Spotify Web API, not
  YouTube embeds, not user-uploaded clips, not third-party hosting.
  Reason: K-pop labels (HYBE, SM, JYP, YG) are aggressive about IP and
  a takedown would put the owner's other 22 apps at risk because they
  share the developer account.
- **30-second preview clip is the maximum playback.** Do not implement
  full-song playback unless integrating MusicKit with an explicit
  Apple Music subscription gate.
- **Catalog `version` field uses `datetime.now(timezone.utc)`**, not
  the deprecated `datetime.utcnow()`. Python 3.12+ warns about utcnow.
- **iOS deployment target is 17.0.** Required for SwiftData. Drop only
  with the owner's explicit go-ahead.
- **Schedule is deterministic per date+mode.** See
  `catalog/scripts/schedule_picker.py:deterministic_pick`. Same date
  always picks the same song. Do not introduce randomness without
  preserving this property — share-result reproducibility depends on it.
- **GameCoordinator is intentionally NOT `@MainActor`.** Methods are
  pure reads of the immutable catalog and need to be callable from
  SwiftUI view bodies without `await`. Don't re-add the isolation
  without restructuring the call sites.

## Architecture at a glance

```
ios/KPopHeardle/
├── App/             # @main entry, root navigation
├── Models/          # Codable data structures + @Model (SwiftData)
├── Services/        # CatalogService, AudioService, GameCoordinator,
│                    # Autocomplete (pure-function utility)
├── Views/           # SwiftUI views
└── Resources/       # Assets.xcassets + bundled catalog.json fallback

catalog/
├── scripts/         # Python build/schedule/merge tools
└── data/
    ├── groups.yml   # source of truth for which groups to include
    └── catalog.json # generated; committed to git as source of truth

.github/workflows/   # daily-schedule.yml, refresh-catalog.yml
public/              # Cloudflare Pages output (mirror of catalog.json)
```

## Build / test commands

Single source of truth in `README.md`. Quick reference:

```bash
# Regenerate Xcode project (always after pulling)
cd ios && xcodegen generate

# Build for simulator
xcodebuild -project ios/KPopHeardle.xcodeproj -scheme KPopHeardle \
  -destination 'platform=iOS Simulator,name=iPhone 15,OS=17.2' build

# Refresh catalog from iTunes
source venv/bin/activate
python catalog/scripts/build_catalog.py \
  --groups catalog/data/groups.yml --out catalog/data/catalog.json

# Pick today's daily
python catalog/scripts/schedule_picker.py --catalog catalog/data/catalog.json
```

## When picking up work

1. Read `docs/session-log.md` (last entry) to know what was last touched.
2. Run the build to confirm the repo compiles on this machine before
   editing anything.
3. If the build fails: do NOT delete or rewrite anything. The repo
   compiled at commit `699b2b3`. Compare against that.
4. Check `docs/handoff.md` "Phase 1 leftovers" for the next task.
5. Always update `docs/session-log.md` when you make non-trivial changes.

## Things this codebase intentionally does NOT have (yet)

These were deferred to Phase 2+. Don't add them unprompted:

- Lyric display / Korean learning layer
- Friend challenge / Universal Links
- StoreKit / subscriptions / paywall
- Choreo mode / MV-based modes (legally too risky)
- "Unlimited practice" mode (dilutes the daily ritual)
- Custom backend (Cloudflare Pages static JSON + GameKit covers everything)
- Sign in with Apple (deferred until multi-device sync becomes a real need)

## When you finish a session

Append a dated entry to `docs/session-log.md`. Format:

```markdown
## 2026-MM-DD — <one-line summary>

**Changes:**
- bullet
- bullet

**State after session:**
- bullet

**Next:**
- bullet
```

This is how the *next* Claude session knows what's loaded into git but
not yet implemented, what was attempted but abandoned, and what the
owner explicitly approved/rejected.
