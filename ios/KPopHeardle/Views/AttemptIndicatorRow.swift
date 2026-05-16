import SwiftUI

struct AttemptIndicatorRow: View {
    let game: GameState

    var body: some View {
        HStack(spacing: 8) {
            ForEach(0..<HeardleAttempts.maxAttempts, id: \.self) { index in
                Capsule()
                    .fill(color(for: index))
                    .frame(height: 8)
            }
        }
        .padding(.horizontal)
    }

    private func color(for index: Int) -> Color {
        guard index < game.guesses.count else {
            return Color.gray.opacity(0.25)
        }
        let g = game.guesses[index]
        switch g.outcome {
        case .correct: return .green
        case .artistOnly: return .orange
        case .sameAgency: return .yellow
        case .skipped: return .gray
        case .wrong: return .red.opacity(0.7)
        }
    }
}
