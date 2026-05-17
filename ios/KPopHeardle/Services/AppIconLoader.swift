import Foundation
import SwiftUI

/// Lightweight loader that fetches an App Store app's icon via the
/// iTunes Lookup API (same backend we already use for previews). Result
/// is cached in memory for the app lifetime — small payload (~50 KB)
/// so no disk cache.
@MainActor
@Observable
final class AppIconLoader {
    private var cache: [String: URL] = [:]
    private var inflight: Set<String> = []

    /// Returns the cached URL synchronously if available, else nil and
    /// kicks off a background fetch. View should re-render when cache
    /// updates.
    func iconURL(appStoreId: String) -> URL? {
        if let cached = cache[appStoreId] { return cached }
        if !inflight.contains(appStoreId) {
            inflight.insert(appStoreId)
            Task { await fetch(appStoreId: appStoreId) }
        }
        return nil
    }

    private func fetch(appStoreId: String) async {
        defer { inflight.remove(appStoreId) }
        let urlStr = "https://itunes.apple.com/lookup?id=\(appStoreId)&entity=software"
        guard let url = URL(string: urlStr) else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            struct Response: Decodable {
                let results: [Result]
                struct Result: Decodable {
                    let artworkUrl512: URL?
                    let artworkUrl100: URL?
                }
            }
            let response = try JSONDecoder().decode(Response.self, from: data)
            if let result = response.results.first,
               let artwork = result.artworkUrl512 ?? result.artworkUrl100 {
                cache[appStoreId] = artwork
            }
        } catch {
            // Silent failure — promo card will show fallback icon.
        }
    }
}
