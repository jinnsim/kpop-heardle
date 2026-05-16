import Foundation
import SwiftUI

struct ArtistGroup: Codable, Identifiable, Hashable {
    let id: String
    let nameEn: String
    let nameKr: String?
    let debutYear: Int
    let agency: String?
    let colorHex: String
    let type: GroupType

    enum CodingKeys: String, CodingKey {
        case id
        case nameEn = "name_en"
        case nameKr = "name_kr"
        case debutYear = "debut_year"
        case agency
        case colorHex = "color"
        case type
    }

    var accentColor: Color {
        Color(hex: colorHex) ?? .pink
    }
}

extension Color {
    init?(hex: String) {
        let cleaned = hex.replacingOccurrences(of: "#", with: "")
        guard cleaned.count == 6, let value = UInt32(cleaned, radix: 16) else {
            return nil
        }
        let r = Double((value & 0xFF0000) >> 16) / 255.0
        let g = Double((value & 0x00FF00) >> 8) / 255.0
        let b = Double(value & 0x0000FF) / 255.0
        self = Color(red: r, green: g, blue: b)
    }
}
