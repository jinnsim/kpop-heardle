import SwiftUI

struct ContentView: View {
    @Environment(CatalogService.self) private var catalog
    @Environment(GameCoordinator.self) private var coordinator

    var body: some View {
        NavigationStack {
            Group {
                if catalog.isLoading {
                    ProgressView("loading.catalog")
                } else if catalog.loadError != nil {
                    VStack(spacing: 12) {
                        Text("catalog.unavailable.title")
                            .font(.headline)
                        Text("catalog.unavailable.body")
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
            .navigationTitle("home.title")
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
