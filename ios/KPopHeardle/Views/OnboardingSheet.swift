import SwiftUI

struct OnboardingSheet: View {
    let onDone: () -> Void
    @State private var page = 0

    private let totalPages = 3

    var body: some View {
        VStack {
            TabView(selection: $page) {
                OnboardingPage(
                    systemImage: "play.circle.fill",
                    title: Text("onboarding.p1.title"),
                    bodyText: Text("onboarding.p1.body"),
                    accent: Color(hex: "#7C3AED") ?? .purple
                )
                .tag(0)

                OnboardingPage(
                    systemImage: "magnifyingglass.circle.fill",
                    title: Text("onboarding.p2.title"),
                    bodyText: Text("onboarding.p2.body"),
                    accent: Color(hex: "#E94B7B") ?? .pink
                )
                .tag(1)

                OnboardingPage(
                    systemImage: "bell.badge.fill",
                    title: Text("onboarding.p3.title"),
                    bodyText: Text("onboarding.p3.body"),
                    accent: Color(hex: "#FF9F66") ?? .orange
                )
                .tag(2)
            }
            .tabViewStyle(.page)
            .indexViewStyle(.page(backgroundDisplayMode: .always))

            Button(action: handlePrimary) {
                Text(page < totalPages - 1 ? "onboarding.next" : "onboarding.start")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .padding(.horizontal, 24)
            .padding(.bottom, 24)
        }
    }

    private func handlePrimary() {
        if page < totalPages - 1 {
            withAnimation { page += 1 }
        } else {
            onDone()
        }
    }
}

private struct OnboardingPage: View {
    let systemImage: String
    let title: Text
    let bodyText: Text
    let accent: Color

    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: systemImage)
                .font(.system(size: 96))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(accent)
            title
                .font(.title.bold())
                .multilineTextAlignment(.center)
            bodyText
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            Spacer()
        }
    }
}
