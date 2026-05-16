# Design decisions and rationale

Every entry here was discussed and approved by the owner during
brainstorming. Don't re-litigate without a strong new reason.

---

## D1 — Concept choice: K-pop Heardle

**Decision:** Build a Heardle-style daily K-pop song guessing game.

**Why:** Picked from a scored list of 12 ideas. Heardle wins on:
- Strong fit with the owner's existing biasly (K-pop learning) app's
  audience and marketing channels.
- Mobile-native iOS gap exists (most K-pop Heardles are web-only).
- AI-friendly content pipeline (iTunes API + auto curation).

**Alternatives rejected:** Lab result interpreter (build cost too high
for a hobby project), GLP-1 companion (too far from owner's existing
portfolio strengths).

---

## D2 — Audio source: iTunes Search API

**Decision:** Use Apple's free `https://itunes.apple.com/search` endpoint
with the 30-second preview clips returned in `previewUrl`.

**Why:** It's the only path that's *both* legal and doesn't require user
auth. Spotify's Web API preview clips were the model used by the
original Heardle, but Spotify shut down Heardle in 2023 over licensing.
K-pop labels are particularly aggressive about IP enforcement, and a
takedown would risk the owner's 22-app developer account.

**Alternatives rejected:**
- Spotify Web API — Spotify has shown they'll kill this use case.
- Direct licensing — impossible for an indie game.
- Apple Music MusicKit full playback — requires user's active Apple Music
  subscription, narrows the addressable market too much.
- Self-hosted previews / YouTube embeds — illegal.

---

## D3 — Strict mode (song + artist both required)

**Decision:** A guess is correct only when both the song title and the
artist match. Artist-only matches show as `🎯 artist correct` partial
credit (in the attempt indicator and in the share emoji as 🟧).

**Why:** Targets the hardcore K-pop fan demographic. Distinguishes the
app from casual web Heardles. Owner explicitly chose "엄격 모드".

---

## D4 — Single autocomplete input field

**Decision:** One search field that matches against any of `titleEn`,
`titleKr`, `artistEn`, `artistKr` (lowercased substring). Returns top
8 suggestions ranked by prefix match count.

**Why:** Korean ↔ English ↔ romanized transliteration ("NewJeans" vs
"뉴진스" vs "newjeans") would break free-text fuzzy matching. Two-step
input (artist → song) added too many clicks and leaked information.
Owner chose single-field autocomplete.

---

## D5 — Attempt structure: classic Heardle timings

**Decision:** 6 attempts at 1s → 2s → 4s → 7s → 11s → 16s. After all
attempts used or on win, reveal full 30s preview.

**Why:** Matches the mental model players already have from Heardle and
its clones. The owner's stated goal is "do K-pop Heardle done well on
mobile", not "reinvent the timing curve".

---

## D6 — Daily structure: global daily + per-group dailies

**Decision:** One puzzle/day shared by all players ("global daily"), plus
separate daily puzzles for each group that has ≥20 songs in the catalog
(initially: NewJeans, IVE, LE SSERAFIM, aespa, Stray Kids, ATEEZ,
ENHYPEN, TXT). No unlimited practice mode.

**Why:** Global daily preserves the Wordle "everyone is talking about
the same puzzle" social loop. Per-group dailies give fans of specific
groups extra engagement without diluting the shared experience.
Unlimited practice would kill the daily ritual that drives retention.

Owner picked "추천방향으로 자율진행" — this was the recommended option.

---

## D7 — Catalog scope: 4th gen + new gen (2018-present)

**Decision:** Initial catalog covers groups debuted from 2018 onward.

**Why:** Owner explicitly chose this scope. Smaller catalog = higher
install skin per song. Z-gen / late-Millennial K-pop fans are the
global core audience. Older gen groups (2nd, 3rd) can be added later as
a "Throwback" mode if there's demand.

---

## D8 — Differentiation: portfolio cross-promote, not feature gimmicks

**Decision:** Don't try to differentiate with multiple game modes
(Lyric, Choreo, Heardle hybrid) in Phase 1. Differentiation comes from:
- Mobile-native quality (most competition is web-only)
- Per-group dailies (most competition is single-mode)
- Cross-promotion to/from biasly (Phase 2)
- GameKit leaderboards
- Polish

**Why:** Owner confirmed biasly has no reusable lyrics infrastructure,
so the "K-pop Heardle + Korean learning" hybrid is a Phase 2 task. Trying
to ship that hybrid in Phase 1 would 3x the build time.

---

## D9 — Backend: serverless (static JSON + GameKit)

**Decision:** No custom backend in Phase 1.
- Catalog and schedule live as `catalog.json` in this git repo.
- Cloudflare Pages mirrors `public/catalog.json` for the iOS app to fetch.
- iOS app bundles a copy as offline fallback.
- Leaderboards: Apple's GameKit (free, no own server).
- Daily reminders: `UserNotifications` local scheduling.
- Stats: local SwiftData; optional CloudKit later for multi-device sync.

**Why:** Owner's explicit operational ask: "버튼만 하나 누르고 싶은데"
(I want to press just one button). Total ongoing cost: $0/month. Total
ongoing operator effort: ~30 min/quarter to add new K-pop releases to
`groups.yml`.

---

## D10 — Curation: automated via GitHub Actions

**Decision:**
- `daily-schedule.yml` runs nightly at 00:00 KST, picks tomorrow's
  global + per-group dailies via `schedule_picker.py`, commits the
  result.
- `refresh-catalog.yml` runs Sundays at 03:00 KST, pulls in any new
  releases via `build_catalog.py` and preserves the existing schedule
  via `merge_schedule.py`.
- Selection algorithm: deterministic from `hash(date+mode)`, with a
  90-day no-repeat window.

**Why:** Owner's stated zero-touch goal. Deterministic seeding means a
schedule never silently changes — if today's pick was X, it stays X
forever in the committed schedule.

---

## D11 — Visual direction: dark mode, group-color accents

**Decision:** Dark mode default. Each group has an accent color (defined
in `groups.yml` under `color`) used as the gradient on its daily card.
Wordle-style minimal layout. Apple Music / Threads tonality.

**Why:** K-pop fan demographic skews younger and dark-mode preferring.
"Cute K-pop maximalism" is what fans get from official label apps;
this app is the *clean* alternative. Apple's design review tends to
favor restrained design too.

---

## D12 — Build environment: Intel Mac scaffold, Silicon Mac for ship

**Decision:** Phase 1 scaffolding built on the owner's Intel Mac
(macOS 13 / Xcode 15.2). Ongoing development + App Store submission
will happen on the owner's Apple Silicon Mac.

**Why:** Intel Mac can run Xcode 15.2 (iOS 17.2 SDK) which is enough
to scaffold and test. But App Store submission requires Xcode 16+,
which requires macOS Sonoma 14.5+, which the 2017 MBP can't run. Owner
already has a Silicon Mac at home — moving the repo over is one git
push away.

---

## What's intentionally undecided

These need owner input before implementing:

- **Pricing model.** Owner deferred: "수익 모델은 나중에, 게임부터".
  Default placeholder plan in `docs/handoff.md` is freemium
  (free = global daily only, premium = group dailies + practice mode)
  but this is not yet approved.
- **App icon / branding.** No designer engaged yet. The `AppIcon.appiconset`
  has the Contents.json but no PNG.
- **Localization scope.** Tentative en/ko/ja for Phase 1 per the design,
  but no translations have been started.
