import SwiftUI
import SwiftData

@main
struct KPopHeardleApp: App {
    @State private var catalogService = CatalogService()
    @State private var audioService = AudioService()
    @State private var coordinator: GameCoordinator?

    var body: some Scene {
        WindowGroup {
            Group {
                if let coordinator {
                    ContentView()
                        .environment(catalogService)
                        .environment(audioService)
                        .environment(coordinator)
                } else {
                    ProgressView("Loading…")
                        .task { setupCoordinator() }
                }
            }
            .preferredColorScheme(.dark)
        }
        .modelContainer(for: PuzzleRecord.self)
    }

    @MainActor
    private func setupCoordinator() {
        coordinator = GameCoordinator(
            catalogService: catalogService,
            audioService: audioService
        )
        Task {
            await catalogService.load()
        }
    }
}
