import SwiftUI

struct ContentView: View {
    @Environment(CatalogService.self) private var catalog
    @Environment(GameCoordinator.self) private var coordinator

    var body: some View {
        NavigationStack {
            Group {
                if catalog.isLoading {
                    ProgressView("Loading today's K-Pop…")
                } else if let error = catalog.loadError {
                    VStack(spacing: 12) {
                        Text("Catalog unavailable")
                            .font(.headline)
                        Text(error)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 32)
                    }
                } else if catalog.catalog != nil {
                    HomeView()
                } else {
                    ProgressView()
                }
            }
            .navigationTitle("K-Pop Heardle")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

#Preview {
    ContentView()
        .environment(CatalogService())
        .environment(AudioService())
        .environment(GameCoordinator(catalogService: CatalogService(), audioService: AudioService()))
}
