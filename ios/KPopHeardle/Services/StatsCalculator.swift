import Foundation

/// Pure-function aggregator for PuzzleRecord history.
/// Owned by views via SwiftData @Query; nothing here mutates state.
struct StatsCalculator {
    let records: [PuzzleRecord]

    // MARK: - Scope

    /// Records limited to the global daily mode.
    var globalRecords: [PuzzleRecord] {
        records.filter { $0.modeKind == "global" }
    }

    /// Records for a specific group daily.
    func groupRecords(groupId: String) -> [PuzzleRecord] {
        records.filter { $0.modeKind == "group" && $0.groupId == groupId }
    }

    // MARK: - Per-scope metrics

    /// Total puzzles played in this scope.
    static func played(_ scope: [PuzzleRecord]) -> Int { scope.count }

    /// Puzzles won.
    static func won(_ scope: [PuzzleRecord]) -> Int {
        scope.filter(\.won).count
    }

    /// Win rate as 0…1 (0 if nothing played yet).
    static func winRate(_ scope: [PuzzleRecord]) -> Double {
        let total = scope.count
        guard total > 0 else { return 0 }
        return Double(won(scope)) / Double(total)
    }

    /// Histogram of attempts used on winning plays, indexed 1...6.
    /// Index 0 is unused so the view loop matches the displayed "1..6" label.
    static func attemptHistogram(_ scope: [PuzzleRecord]) -> [Int] {
        var buckets = Array(repeating: 0, count: 7)  // 0..6, only 1..6 matter
        for record in scope where record.won {
            let idx = max(1, min(6, record.attemptsUsed))
            buckets[idx] += 1
        }
        return buckets
    }

    /// Lost (failed at attempt 6) count.
    static func lossCount(_ scope: [PuzzleRecord]) -> Int {
        scope.filter { !$0.won }.count
    }

    // MARK: - Streaks

    /// Current consecutive-day win streak ending today (or yesterday).
    /// Counts only WIN days; a loss day breaks the streak; a missing day
    /// breaks the streak unless it's today (so a streak persists until
    /// midnight on the day you skip).
    static func currentStreak(_ scope: [PuzzleRecord], today: Date = Date()) -> Int {
        let winDates = scope.filter(\.won).compactMap { parseDate($0.date) }
        guard !winDates.isEmpty else { return 0 }
        let winSet = Set(winDates.map { startOfDay($0) })
        let calendar = Calendar(identifier: .gregorian)

        var streak = 0
        var cursor = startOfDay(today)

        // If the user hasn't played today yet, the streak is whatever it was
        // up to yesterday.
        if !winSet.contains(cursor) {
            if let yesterday = calendar.date(byAdding: .day, value: -1, to: cursor) {
                cursor = yesterday
            } else {
                return 0
            }
        }

        while winSet.contains(cursor) {
            streak += 1
            guard let prev = calendar.date(byAdding: .day, value: -1, to: cursor) else { break }
            cursor = prev
        }
        return streak
    }

    /// All-time longest consecutive-day win streak.
    static func longestStreak(_ scope: [PuzzleRecord]) -> Int {
        let winDates = scope.filter(\.won).compactMap { parseDate($0.date) }
        guard !winDates.isEmpty else { return 0 }
        let sorted = winDates.map { startOfDay($0) }.sorted()
        let calendar = Calendar(identifier: .gregorian)

        var longest = 1
        var current = 1
        for i in 1..<sorted.count {
            let prev = sorted[i - 1]
            let day = sorted[i]
            if let expected = calendar.date(byAdding: .day, value: 1, to: prev),
               calendar.isDate(day, inSameDayAs: expected) {
                current += 1
                longest = max(longest, current)
            } else if !calendar.isDate(day, inSameDayAs: prev) {
                current = 1
            }
        }
        return longest
    }

    // MARK: - Helpers

    /// Parses YYYY-MM-DD into a Date at local midnight. Returns nil on bad input.
    static func parseDate(_ raw: String) -> Date? {
        Self.dayFormatter.date(from: raw)
    }

    private static let dayFormatter: DateFormatter = {
        let f = DateFormatter()
        f.calendar = Calendar(identifier: .gregorian)
        f.locale = Locale(identifier: "en_US_POSIX")
        f.timeZone = TimeZone.current
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    static func startOfDay(_ date: Date) -> Date {
        Calendar(identifier: .gregorian).startOfDay(for: date)
    }
}
