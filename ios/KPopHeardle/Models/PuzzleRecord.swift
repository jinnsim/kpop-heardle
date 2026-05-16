import Foundation
import SwiftData

/// Persisted history of one completed puzzle (global or group daily).
@Model
final class PuzzleRecord {
    @Attribute(.unique) var key: String   // "global:2026-05-17" or "group:newjeans:2026-05-17"
    var modeKind: String                  // "global" or "group"
    var groupId: String?                  // for group daily
    var date: String                      // "YYYY-MM-DD"
    var songId: String
    var attemptsUsed: Int                 // 1..6, or 6 if lost
    var won: Bool
    var completedAt: Date

    init(
        key: String,
        modeKind: String,
        groupId: String?,
        date: String,
        songId: String,
        attemptsUsed: Int,
        won: Bool,
        completedAt: Date = Date()
    ) {
        self.key = key
        self.modeKind = modeKind
        self.groupId = groupId
        self.date = date
        self.songId = songId
        self.attemptsUsed = attemptsUsed
        self.won = won
        self.completedAt = completedAt
    }

    static func makeKey(mode: GameMode) -> String {
        switch mode {
        case .globalDaily(let date):
            return "global:\(date)"
        case .groupDaily(let groupId, let date):
            return "group:\(groupId):\(date)"
        }
    }
}
