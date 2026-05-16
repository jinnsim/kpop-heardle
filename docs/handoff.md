# Handoff — continuing on Apple Silicon Mac

Bootstrapped on the Intel Mac (macOS 13, Xcode 15.2). Move this entire
folder to the Apple Silicon Mac running macOS Sonoma+ / Xcode 16+ for
production work and App Store submission.

## What's already done

1. Project skeleton + xcodegen spec under `ios/`
2. Phase 1 game loop (home, game view, audio service, autocomplete,
   result view with share, SwiftData puzzle history)
3. Real catalog of 233 4th-gen K-pop songs (`catalog/data/catalog.json`)
4. Schedule picker: today's global + per-group dailies populated
5. GitHub Actions for daily scheduling + weekly catalog refresh
6. App launches and renders the home screen against the real catalog
   in iOS Simulator (iPhone 15, iOS 17.2). See screenshot in commit.

## First steps on the Silicon Mac

1. `git clone` this repo (or copy the folder).
2. Install xcodegen (Homebrew works fine on Sonoma+):
   ```bash
   brew install xcodegen
   ```
3. Regenerate the project (always do this after pulling):
   ```bash
   cd ios && xcodegen generate && open KPopHeardle.xcodeproj
   ```
4. Set the `DEVELOPMENT_TEAM` in `ios/project.yml` to your Apple Developer
   team ID, then regenerate.
5. Pick a real bundle identifier (currently `com.ootssu.kpopheardle`) and
   register the App ID in App Store Connect.

## Build environment caveat (Intel-only)

The reason `xcodegen` couldn't be installed via Homebrew on the Intel Mac:
`xcodegen` requires Xcode 15.3+, which requires macOS Sonoma 14.5+, which
the 2017 MBP can't run. Workaround used here:

```bash
cd /tmp
git clone --depth 1 https://github.com/yonaskolb/XcodeGen.git
cd XcodeGen
git fetch --tags --depth 1
git checkout 2.42.0           # last Swift 5.9-compatible release
swift build -c release
cp .build/release/xcodegen ~/.local/bin/xcodegen
```

You won't need this on the Silicon Mac.

## App Store submission path

1. Bump `MARKETING_VERSION` in `project.yml`.
2. Regenerate xcodeproj.
3. Either use **Xcode Cloud** (configured via the Xcode IDE: Integrate
   → Create Workflow) or `xcodebuild archive` + `xcrun altool` from the
   Silicon Mac.
4. The Intel Mac CANNOT submit — Apple requires Xcode 16+ for new
   submissions as of mid-2025.

## Cloudflare Pages hosting (free tier)

1. Push this repo to GitHub.
2. Cloudflare Pages → Connect to Git → choose this repo.
3. Build settings:
   - Build command: (leave empty)
   - Output directory: `public`
4. Cloudflare gives you `https://<project>.pages.dev`.
5. Update `CatalogService.remoteURL` in
   `ios/KPopHeardle/Services/CatalogService.swift` to the real URL.
6. Regenerate xcodeproj, rebuild.

## GitHub Actions setup

When you push to GitHub:

1. Go to repo settings → Actions → General → Workflow permissions →
   set to "Read and write".
2. The `daily-schedule.yml` workflow will run every day at 00:00 KST
   and commit the new schedule to the repo.
3. The `refresh-catalog.yml` workflow runs Sundays at 03:00 KST and
   pulls in new K-pop singles for the configured groups.
4. Manual triggers also available via the Actions tab.

## What to build next (Phase 1 leftovers)

Most of Phase 1 is now done. Remaining:

1. **GameKit (Game Center) leaderboards** — add the entitlement, register
   leaderboards in App Store Connect, submit scores in `persistResult()`.
   Blocked by needing a real `DEVELOPMENT_TEAM` first.
2. **Translation review** — Phase 1 translations were AI-generated.
   Recommend native review for Thai (particles), Hindi (gender), Filipino
   (code-switching), Korean (honorific level).
3. **App icon polish** — current icon is programmatically generated.
   A designer-made replacement can drop in at the same path.
4. **Real device testing** — especially the AVPlayer clip-bounded
   playback timing on actual hardware vs simulator.

Already shipped in scaffold:
- ✅ App icon (programmatic)
- ✅ 13-locale strings
- ✅ Stats / streak view with histogram
- ✅ Daily local notification + Settings toggle
- ✅ First-launch onboarding
- ✅ Tab navigation (Home / Stats / Settings)

## What to build for Phase 2 (per the design doc)

1. **Lyric reveal after correct guess** — `Genius API` for line lookup,
   highlight Korean line + EN translation.
2. **Friend challenge** — Universal Links carrying a song ID + nonce.
3. **Premium tier** — StoreKit 2 with monthly/yearly subscription.
   Free = global daily only. Premium = all group dailies + practice mode.

## Files you'll touch most often

| File                                             | When |
|--------------------------------------------------|---|
| `catalog/data/groups.yml`                        | Adding/removing K-pop groups |
| `ios/KPopHeardle/Services/CatalogService.swift`  | Changing remote URL |
| `ios/project.yml`                                | Team ID, version, capabilities |
| `ios/KPopHeardle/Models/GameState.swift`         | Tuning hint thresholds, timing |
| `ios/KPopHeardle/Views/HomeView.swift`           | Home-screen layout |

## Useful one-liners

```bash
# Local dev build
cd ios && xcodegen generate && \
  xcodebuild -project KPopHeardle.xcodeproj -scheme KPopHeardle \
  -destination 'platform=iOS Simulator,name=iPhone 15' build

# Install on running simulator
xcrun simctl install booted \
  ~/Library/Developer/Xcode/DerivedData/KPopHeardle-*/Build/Products/Debug-iphonesimulator/KPopHeardle.app
xcrun simctl launch booted com.ootssu.kpopheardle

# Refresh catalog locally
source venv/bin/activate
python catalog/scripts/build_catalog.py \
  --groups catalog/data/groups.yml --out catalog/data/catalog.json
```
