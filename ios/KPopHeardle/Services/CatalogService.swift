import Foundation

/// Loads the central catalog JSON. Tries remote (Cloudflare Pages),
/// falls back to a bundled copy when offline or unreachable.
@Observable
final class CatalogService {
    private(set) var catalog: Catalog?
    private(set) var loadError: String?
    private(set) var isLoading: Bool = false

    /// Hard-coded for now; move to a build config once a real domain is registered.
    static let remoteURL = URL(string: "https://kpop-heardle.pages.dev/catalog.json")!
    static let bundledFilename = "catalog"   // catalog.json in main bundle

    func load() async {
        isLoading = true
        defer { isLoading = false }

        if let remote = await fetchRemote() {
            catalog = remote
            return
        }
        if let bundled = loadBundled() {
            catalog = bundled
            return
        }
        loadError = "No catalog available (remote failed, no bundled copy)."
    }

    private func fetchRemote() async -> Catalog? {
        do {
            var request = URLRequest(url: Self.remoteURL)
            request.timeoutInterval = 10
            request.cachePolicy = .reloadIgnoringLocalCacheData
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
                return nil
            }
            return try JSONDecoder().decode(Catalog.self, from: data)
        } catch {
            return nil
        }
    }

    private func loadBundled() -> Catalog? {
        guard let url = Bundle.main.url(forResource: Self.bundledFilename, withExtension: "json"),
              let data = try? Data(contentsOf: url) else {
            return nil
        }
        return try? JSONDecoder().decode(Catalog.self, from: data)
    }
}
