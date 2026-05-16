# K-Pop Heardle

Daily K-pop song guessing game (Heardle-style) for iOS. Plays the first
1s → 2s → 4s → 7s → 11s → 16s of an iTunes preview clip and asks the player
to guess the song + artist.

Targets 4th-gen and newer K-pop (NewJeans, IVE, LE SSERAFIM, aespa,
Stray Kids, ATEEZ, ENHYPEN, TXT to start).

## Project layout

```
ios/                  iOS app (SwiftUI, iOS 17+, Xcode 15.2-compatible)
  project.yml         xcodegen spec
  KPopHeardle/        sources, regenerate xcodeproj with `xcodegen`
catalog/
  scripts/            Python tools (catalog build, daily picker, schedule merge)
  data/groups.yml     which K-pop groups are in scope
  data/catalog.json   generated catalog + schedule (in-repo source of truth)
public/catalog.json   mirror served by Cloudflare Pages (CDN for the iOS app)
.github/workflows/    GitHub Actions:
                        - daily-schedule.yml  (picks tomorrow's songs nightly)
                        - refresh-catalog.yml (weekly iTunes refresh)
```

## iOS app — local build

Requires Xcode 15.2+ and the bundled `xcodegen` build (see "Toolchain notes").

```bash
cd ios
~/.local/bin/xcodegen generate
open KPopHeardle.xcodeproj
# or:
xcodebuild -project KPopHeardle.xcodeproj -scheme KPopHeardle \
  -destination 'platform=iOS Simulator,name=iPhone 15,OS=17.2' \
  -configuration Debug build
```

The app falls back to `Resources/catalog.json` (bundled) when the remote
catalog is unreachable, so it works offline on first launch.

## Catalog operations

```bash
# Refresh tracks from iTunes (run after editing groups.yml)
python catalog/scripts/build_catalog.py \
  --groups catalog/data/groups.yml \
  --out catalog/data/catalog.json \
  --max-per-group 40

# Pick today's global + per-group dailies (in-place)
python catalog/scripts/schedule_picker.py \
  --catalog catalog/data/catalog.json

# (Run on Sundays) Rebuild + preserve prior schedule
python catalog/scripts/build_catalog.py ... --out catalog/data/catalog.json
python catalog/scripts/merge_schedule.py \
  --prev catalog/data/catalog.prev.json \
  --next catalog/data/catalog.json
```

## Hosting

- GitHub repo holds `catalog/data/catalog.json` as source of truth.
- Cloudflare Pages should be wired to publish `public/` (just `catalog.json`).
- The iOS app fetches `https://kpop-heardle.pages.dev/catalog.json`.
  (Change `CatalogService.remoteURL` once the real subdomain is set.)

## Toolchain notes

- This repo was bootstrapped on macOS 13 / Xcode 15.2 (Intel Mac).
  Homebrew refused to install `xcodegen` because it wants Xcode 15.3+.
  Workaround: build xcodegen 2.42.0 from source — see
  `docs/handoff.md` for the exact commands.
- App Store submission requires Xcode 16+ which needs macOS Sonoma+.
  Build/test here, submit from the Apple Silicon Mac.

## Status (2026-05-17)

Phase 1 scaffolding complete:
- [x] Home screen renders today's global + per-group dailies with group colors
- [x] Audio playback service (clip-bounded AVPlayer)
- [x] Guess input with autocomplete over scoped song universe
- [x] Game state machine (6 attempts, partial credit for artist match,
      progressive hints at 3/4/5 wrong)
- [x] Result view with Wordle-style emoji share + Apple Music deep link
- [x] SwiftData persistence for completed puzzles
- [x] Catalog builder + scheduler running on real iTunes data (233 songs, 8 groups)

Phase 1 still to do:
- [ ] Stats / streak screen
- [ ] GameKit Game Center wiring (entitlement + leaderboard registration)
- [ ] App icon + launch screen artwork
- [ ] Localized strings (en/ko/ja)
- [ ] Real Apple Developer team in `project.yml` (currently blank)
- [ ] Cloudflare Pages domain registered + remote URL updated

See `docs/handoff.md` for picking this up on the Apple Silicon machine.
