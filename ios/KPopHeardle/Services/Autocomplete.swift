import Foundation

/// Pure-function autocomplete for the guess input field.
/// Matches user query against the song's titleEn/titleKr/artistEn/artistKr lowercased.
enum Autocomplete {
    static func filter(_ query: String, in songs: [Song], limit: Int = 8) -> [Song] {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !trimmed.isEmpty else { return [] }
        let terms = trimmed.split(separator: " ").map(String.init)

        let scored: [(song: Song, score: Int)] = songs.compactMap { song in
            let haystack = song.searchTokens
            var score = 0
            for term in terms {
                let hit = haystack.contains { $0.contains(term) }
                if !hit { return nil }
                score += haystack.filter { $0.hasPrefix(term) }.count
            }
            return (song, score)
        }

        return scored
            .sorted { $0.score > $1.score }
            .prefix(limit)
            .map(\.song)
    }
}
