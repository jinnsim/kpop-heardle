import SwiftUI

struct ResultView: View {
    let game: GameState

    var body: some View {
        VStack(spacing: 16) {
            Text(game.won ? "🎉" : "💔")
                .font(.system(size: 64))

            Text(game.won ? "result.won" : "result.lost")
                .font(.title2.bold())

            VStack(spacing: 4) {
                Text(verbatim: game.targetSong.titleEn)
                    .font(.title3.bold())
                Text(verbatim: game.targetSong.artistEn)
                    .foregroundStyle(.secondary)
            }
            .padding(.top, 8)

            HStack(spacing: 4) {
                ForEach(0..<HeardleAttempts.maxAttempts, id: \.self) { i in
                    Text(emoji(for: i))
                }
            }
            .font(.title2)
            .padding(.top, 8)

            Text(verbatim: shareText)
                .font(.footnote.monospaced())
                .padding(12)
                .background(Color.gray.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))

            ShareLink(item: shareText) {
                Label("result.share", systemImage: "square.and.arrow.up")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)

            if let appleMusicURL = appleMusicURL {
                Link(destination: appleMusicURL) {
                    Label("result.openAppleMusic", systemImage: "music.note")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }
        }
        .padding(24)
        .presentationDetents([.medium, .large])
    }

    private func emoji(for index: Int) -> String {
        guard index < game.guesses.count else { return "⬜" }
        switch game.guesses[index].outcome {
        case .correct: return "🟩"
        case .artistOnly: return "🟧"
        case .sameAgency: return "🟨"
        case .skipped: return "⬛"
        case .wrong: return "🟥"
        }
    }

    private var shareText: String {
        let title: String
        switch game.mode {
        case .globalDaily(let date): title = "K-Pop Heardle • \(date)"
        case .groupDaily(let groupId, let date): title = "K-Pop Heardle [\(groupId)] • \(date)"
        }
        let emojis = (0..<HeardleAttempts.maxAttempts).map { emoji(for: $0) }.joined()
        let attempts = game.won ? "\(game.guesses.count)/6" : "X/6"
        return "\(title)\n\(emojis)  \(attempts)"
    }

    private var appleMusicURL: URL? {
        URL(string: "https://music.apple.com/song/\(game.targetSong.itunesId)")
    }
}
