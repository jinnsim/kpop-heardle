import Foundation

/// Heardle attempt timing — number of seconds revealed per attempt.
enum HeardleAttempts {
    static let clipDurations: [TimeInterval] = [1, 2, 4, 7, 11, 16]
    static let maxAttempts = clipDurations.count
}

enum GuessOutcome: Equatable {
    case correct
    case artistOnly      // 🎯 artist correct, song wrong
    case sameAgency      // soft hint (later, not Phase 1 required)
    case wrong
    case skipped
}

struct Guess: Identifiable, Equatable {
    let id = UUID()
    let songId: String?   // nil if skipped
    let outcome: GuessOutcome
    let typedLabel: String

    var revealedAt: Date = Date()
}

enum HintTier {
    case none
    case groupType   // after 3 wrong: boy/girl/solo
    case debutYear   // after 4 wrong: year
    case firstLetter // after 5 wrong: artist first letter
}

/// In-flight game state for one puzzle (global daily or one group daily).
@Observable
final class GameState {
    let mode: GameMode
    let targetSong: Song
    let targetGroup: ArtistGroup?

    private(set) var guesses: [Guess] = []
    private(set) var finished: Bool = false
    private(set) var won: Bool = false

    init(mode: GameMode, targetSong: Song, targetGroup: ArtistGroup?) {
        self.mode = mode
        self.targetSong = targetSong
        self.targetGroup = targetGroup
    }

    var currentAttemptIndex: Int { guesses.count }
    var attemptsRemaining: Int { HeardleAttempts.maxAttempts - guesses.count }
    var currentClipDuration: TimeInterval {
        let idx = min(currentAttemptIndex, HeardleAttempts.maxAttempts - 1)
        return HeardleAttempts.clipDurations[idx]
    }

    var revealedClipDuration: TimeInterval {
        // After finish (win or lose), reveal full preview (30s).
        if finished { return 30 }
        let idx = max(currentAttemptIndex - 1, 0)
        return HeardleAttempts.clipDurations[idx]
    }

    var hintTier: HintTier {
        let wrongCount = guesses.filter { $0.outcome != .correct }.count
        switch wrongCount {
        case 5...: return .firstLetter
        case 4: return .debutYear
        case 3: return .groupType
        default: return .none
        }
    }

    /// Returns the resulting outcome.
    @discardableResult
    func submit(guessedSong: Song?) -> GuessOutcome {
        guard !finished else { return .wrong }

        let outcome: GuessOutcome
        let label: String

        if let guessed = guessedSong {
            label = guessed.searchLabel
            if guessed.id == targetSong.id {
                outcome = .correct
            } else if guessed.artistEn.lowercased() == targetSong.artistEn.lowercased() {
                outcome = .artistOnly
            } else {
                outcome = .wrong
            }
        } else {
            label = "(skipped)"
            outcome = .skipped
        }

        guesses.append(Guess(songId: guessedSong?.id, outcome: outcome, typedLabel: label))

        if outcome == .correct {
            finished = true
            won = true
        } else if guesses.count >= HeardleAttempts.maxAttempts {
            finished = true
            won = false
        }

        return outcome
    }
}

enum GameMode: Hashable {
    case globalDaily(date: String)
    case groupDaily(groupId: String, date: String)

    var displayName: String {
        switch self {
        case .globalDaily: return "Daily"
        case .groupDaily(let groupId, _): return "\(groupId.capitalized) Daily"
        }
    }
}
