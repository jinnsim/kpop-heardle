import SwiftUI
import SwiftData

@main
@MainActor
struct KPopHeardleApp: App {
    @State private var catalogService = CatalogService()
    @State private var audioService = AudioService()
    @State private var notificationService = NotificationService()
    @State private var iconLoader = AppIconLoader()
    @State private var coordinator: GameCoordinator?
    @AppStorage("kph.onboardingSeen") private var onboardingSeen: Bool = false

    var body: some Scene {
        WindowGroup {
            Group {
                if let coordinator {
                    RootTabView()
                        .environment(catalogService)
                        .environment(audioService)
                        .environment(coordinator)
                        .environment(notificationService)
                        .environment(iconLoader)
                        .sheet(isPresented: .constant(!onboardingSeen)) {
                            OnboardingSheet(onDone: {
                                onboardingSeen = true
                                Task { await notificationService.requestAuthorization() }
                            })
                            .interactiveDismissDisabled()
                        }
                } else {
                    ProgressView("loading.bootstrap")
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
            await notificationService.refreshAuthorizationStatus()
            await notificationService.syncSchedule()
        }
    }
}
