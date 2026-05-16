import Foundation
import SwiftData

/// Resolves "today's song" for each mode and creates GameState instances.
@MainActor
@Observable
final class GameCoordinator {
    let catalogService: CatalogService
    let audioService: AudioService

    /// Today's date string, "YYYY-MM-DD" in user's local timezone.
    /// Uses Gregorian calendar + POSIX locale so non-Gregorian locales
    /// (Thai/Buddhist, Japanese imperial, etc.) still produce keys
    /// matching the schedule JSON.
    var todayString: String {
        Self.scheduleFormatter.string(from: Date())
    }

    private static let scheduleFormatter: DateFormatter = {
        let f = DateFormatter()
        f.calendar = Calendar(identifier: .gregorian)
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    init(catalogService: CatalogService, audioService: AudioService) {
        self.catalogService = catalogService
        self.audioService = audioService
    }

    func globalDailyGame() -> GameState? {
        guard let catalog = catalogService.catalog,
              let songId = catalog.schedule.globalSongId(for: todayString),
              let song = catalog.song(id: songId) else { return nil }
        let group = catalog.group(id: song.groupId)
        return GameState(mode: .globalDaily(date: todayString),
                         targetSong: song,
                         targetGroup: group)
    }

    func groupDailyGame(groupId: String) -> GameState? {
        guard let catalog = catalogService.catalog,
              let songId = catalog.schedule.groupSongId(groupId: groupId, date: todayString),
              let song = catalog.song(id: songId) else { return nil }
        let group = catalog.group(id: groupId)
        return GameState(mode: .groupDaily(groupId: groupId, date: todayString),
                         targetSong: song,
                         targetGroup: group)
    }

    /// Returns groups that currently have a scheduled song for today.
    func activeGroupDailies() -> [ArtistGroup] {
        guard let catalog = catalogService.catalog else { return [] }
        let today = todayString
        return catalog.groups.filter { group in
            catalog.schedule.groupSongId(groupId: group.id, date: today) != nil
        }
    }

    /// Filters catalog songs for the autocomplete in a given game mode.
    /// Group dailies only autocomplete against that group's songs to keep input tight.
    func autocompleteUniverse(for mode: GameMode) -> [Song] {
        guard let catalog = catalogService.catalog else { return [] }
        switch mode {
        case .globalDaily:
            return catalog.songs
        case .groupDaily(let groupId, _):
            return catalog.songs.filter { $0.groupId == groupId }
        }
    }
}
