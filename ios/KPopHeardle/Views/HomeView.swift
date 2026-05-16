import SwiftUI

struct HomeView: View {
    @Environment(GameCoordinator.self) private var coordinator

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                if coordinator.globalDailyGame() != nil {
                    NavigationLink(value: GameRoute.global) {
                        DailyCard(
                            title: Text("home.global.title"),
                            subtitle: Text("home.global.subtitle"),
                            colorHex: "#7C3AED"
                        )
                    }
                    .buttonStyle(.plain)
                } else {
                    DailyCard(
                        title: Text("home.global.none.title"),
                        subtitle: Text("home.global.none.subtitle"),
                        colorHex: "#666666"
                    )
                }

                ForEach(coordinator.activeGroupDailies()) { group in
                    NavigationLink(value: GameRoute.group(group.id)) {
                        DailyCard(
                            title: Text(verbatim: group.nameEn),
                            subtitle: Text("home.group.subtitle"),
                            colorHex: group.colorHex
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding()
        }
        .navigationDestination(for: GameRoute.self) { route in
            switch route {
            case .global:
                if let game = coordinator.globalDailyGame() {
                    GameView(game: game)
                }
            case .group(let groupId):
                if let game = coordinator.groupDailyGame(groupId: groupId) {
                    GameView(game: game)
                }
            }
        }
    }
}

enum GameRoute: Hashable {
    case global
    case group(String)
}

struct DailyCard: View {
    let title: Text
    let subtitle: Text
    let colorHex: String

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                subtitle
                    .textCase(.uppercase)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.7))
                title
                    .font(.title2.bold())
                    .foregroundStyle(.white)
            }
            Spacer()
            Image(systemName: "play.circle.fill")
                .font(.system(size: 32))
                .foregroundStyle(.white.opacity(0.9))
        }
        .padding(20)
        .frame(maxWidth: .infinity, minHeight: 100)
        .background(
            LinearGradient(
                colors: [
                    Color(hex: colorHex) ?? .pink,
                    (Color(hex: colorHex) ?? .pink).opacity(0.6)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}
