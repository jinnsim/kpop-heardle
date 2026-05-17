import SwiftUI

/// Cross-promote card. Tapping opens the App Store via the system browser.
@MainActor
struct PromoCard: View {
    @Environment(AppIconLoader.self) private var iconLoader

    let app: PromotedApp
    var compact: Bool = false

    var body: some View {
        Link(destination: app.appStoreURL) {
            HStack(spacing: 12) {
                iconView
                    .frame(width: compact ? 44 : 56, height: compact ? 44 : 56)
                    .clipShape(RoundedRectangle(cornerRadius: compact ? 10 : 12,
                                                style: .continuous))

                VStack(alignment: .leading, spacing: 2) {
                    Text(app.nameKey)
                        .font(compact ? .subheadline.weight(.semibold) : .headline)
                        .foregroundStyle(.primary)
                    Text(app.taglineKey)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }

                Spacer()

                Text("promo.get")
                    .font(.caption.bold())
                    .padding(.horizontal, 12)
                    .padding(.vertical, 5)
                    .background(Color.accentColor.opacity(0.15))
                    .foregroundStyle(Color.accentColor)
                    .clipShape(Capsule())
            }
            .padding(compact ? 10 : 12)
            .background(Color.gray.opacity(0.10))
            .clipShape(RoundedRectangle(cornerRadius: compact ? 12 : 14,
                                        style: .continuous))
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private var iconView: some View {
        if let url = iconLoader.iconURL(appStoreId: app.appStoreId) {
            AsyncImage(url: url) { image in
                image.resizable().scaledToFill()
            } placeholder: {
                placeholderIcon
            }
        } else {
            placeholderIcon
        }
    }

    private var placeholderIcon: some View {
        ZStack {
            LinearGradient(
                colors: [Color.purple, Color.pink],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            Image(systemName: "app.fill")
                .foregroundStyle(.white.opacity(0.6))
                .font(.system(size: 24))
        }
    }
}
