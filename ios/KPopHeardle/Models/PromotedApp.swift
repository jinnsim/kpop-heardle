import Foundation

/// Owner's other apps that we cross-promote inside K-Pop Heardle.
/// Apple allows cross-promotion of apps published by the same developer.
struct PromotedApp: Identifiable {
    let id: String
    let appStoreId: String
    let nameKey: LocalizedStringResource
    let taglineKey: LocalizedStringResource
    let iconAssetName: String?

    var appStoreURL: URL {
        URL(string: "https://apps.apple.com/app/id\(appStoreId)")!
    }

    static let biasly = PromotedApp(
        id: "biasly",
        appStoreId: "6762536099",
        nameKey: "promo.biasly.name",
        taglineKey: "promo.biasly.tagline",
        iconAssetName: nil   // App Store icon fetched lazily via iTunes Lookup
    )

    static let all: [PromotedApp] = [biasly]
}
