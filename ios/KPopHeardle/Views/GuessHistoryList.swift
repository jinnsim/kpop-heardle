import SwiftUI

struct GuessHistoryList: View {
    let game: GameState

    var body: some View {
        VStack(spacing: 6) {
            ForEach(game.guesses) { guess in
                HStack {
                    Circle()
                        .fill(color(for: guess.outcome))
                        .frame(width: 10, height: 10)
                    Text(verbatim: guess.typedLabel)
                        .font(.subheadline)
                        .foregroundStyle(.primary)
                        .lineLimit(1)
                    Spacer()
                    if guess.outcome == .artistOnly {
                        Text("guess.artistMatched")
                            .font(.caption2)
                            .foregroundStyle(.orange)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.gray.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
            }
        }
        .padding(.horizontal)
    }

    private func color(for outcome: GuessOutcome) -> Color {
        switch outcome {
        case .correct: return .green
        case .artistOnly: return .orange
        case .sameAgency: return .yellow
        case .skipped: return .gray
        case .wrong: return .red.opacity(0.8)
        }
    }
}
