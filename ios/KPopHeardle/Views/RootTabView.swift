import SwiftUI

struct RootTabView: View {
    @Environment(CatalogService.self) private var catalog

    var body: some View {
        TabView {
            ContentView()
                .tabItem {
                    Label("tab.home", systemImage: "house.fill")
                }

            StatsView()
                .tabItem {
                    Label("tab.stats", systemImage: "chart.bar.fill")
                }

            SettingsView()
                .tabItem {
                    Label("tab.settings", systemImage: "gearshape.fill")
                }
        }
    }
}
