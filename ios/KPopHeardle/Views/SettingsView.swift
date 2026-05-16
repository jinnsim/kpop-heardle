import SwiftUI

struct SettingsView: View {
    @Environment(NotificationService.self) private var notifications
    @Environment(CatalogService.self) private var catalog

    var body: some View {
        NavigationStack {
            Form {
                Section("settings.section.notifications") {
                    @Bindable var notifBindable = notifications
                    Toggle("settings.toggle.dailyReminder", isOn: $notifBindable.remindersEnabled)
                        .onChange(of: notifications.remindersEnabled) { _, newValue in
                            if newValue && notifications.authorization == .unknown {
                                Task { await notifications.requestAuthorization() }
                            }
                        }

                    if notifications.authorization == .denied {
                        Label("settings.notifications.denied", systemImage: "exclamationmark.triangle")
                            .font(.footnote)
                            .foregroundStyle(.orange)
                    }
                }

                Section("settings.section.about") {
                    HStack {
                        Text("settings.label.catalogVersion")
                        Spacer()
                        Text(verbatim: catalog.catalog?.version ?? "—")
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                    }
                    HStack {
                        Text("settings.label.songCount")
                        Spacer()
                        Text(verbatim: "\(catalog.catalog?.songs.count ?? 0)")
                            .foregroundStyle(.secondary)
                    }
                    HStack {
                        Text("settings.label.groupCount")
                        Spacer()
                        Text(verbatim: "\(catalog.catalog?.groups.count ?? 0)")
                            .foregroundStyle(.secondary)
                    }
                    HStack {
                        Text("settings.label.appVersion")
                        Spacer()
                        Text(verbatim: Self.appVersionString)
                            .foregroundStyle(.secondary)
                    }
                }

                Section("settings.section.attribution") {
                    Text("settings.attribution.body")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("settings.title")
            .navigationBarTitleDisplayMode(.large)
            .task {
                await notifications.refreshAuthorizationStatus()
            }
        }
    }

    private static var appVersionString: String {
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "?"
        let build = Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "?"
        return "\(version) (\(build))"
    }
}
