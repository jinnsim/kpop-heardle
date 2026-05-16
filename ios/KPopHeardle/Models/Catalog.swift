import Foundation

/// Top-level JSON shape fetched from Cloudflare Pages.
struct Catalog: Codable {
    let version: String
    let schedule: Schedule
    let songs: [Song]
    let groups: [ArtistGroup]

    func song(id: String) -> Song? {
        songs.first { $0.id == id }
    }

    func group(id: String) -> ArtistGroup? {
        groups.first { $0.id == id }
    }
}

struct Schedule: Codable {
    /// Date string "YYYY-MM-DD" → song id, for the global daily.
    let global: [String: String]
    /// group_id → (date → song id).
    let groups: [String: [String: String]]

    func globalSongId(for date: String) -> String? {
        global[date]
    }

    func groupSongId(groupId: String, date: String) -> String? {
        groups[groupId]?[date]
    }
}
