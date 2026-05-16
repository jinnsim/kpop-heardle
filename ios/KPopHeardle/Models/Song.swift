import Foundation

struct Song: Codable, Identifiable, Hashable {
    let id: String
    let itunesId: String
    let titleEn: String
    let titleKr: String?
    let artistEn: String
    let artistKr: String?
    let groupId: String
    let releaseDate: String
    let type: GroupType
    let previewUrl: String
    let artworkUrl: String?

    var displayTitle: String { titleEn }
    var displayArtist: String { artistEn }

    /// User-visible combined label for autocomplete.
    var searchLabel: String { "\(artistEn) — \(titleEn)" }

    /// All strings that the autocomplete should match against, lowercased.
    var searchTokens: [String] {
        [titleEn, titleKr, artistEn, artistKr]
            .compactMap { $0?.lowercased() }
    }
}

enum GroupType: String, Codable {
    case boyGroup = "boy_group"
    case girlGroup = "girl_group"
    case solo = "solo"
    case coed = "coed"
}
