import SwiftUI

struct PlayerControls: View {
    @Environment(AudioService.self) private var audio

    let game: GameState
    let onPlay: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Text(game.finished ? "Reveal: 30s" : "Listen: \(durationLabel)")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Button(action: onPlay) {
                Image(systemName: audio.isPlaying ? "stop.circle.fill" : "play.circle.fill")
                    .font(.system(size: 64))
                    .symbolRenderingMode(.hierarchical)
            }
            .buttonStyle(.plain)

            if let hintText {
                Text(hintText)
                    .font(.caption)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color.orange.opacity(0.15))
                    .foregroundStyle(.orange)
                    .clipShape(Capsule())
            }
        }
        .padding(.vertical, 8)
    }

    private var durationLabel: String {
        let dur = game.currentClipDuration
        return dur == floor(dur) ? "\(Int(dur))s" : String(format: "%.1fs", dur)
    }

    private var hintText: String? {
        switch game.hintTier {
        case .none: return nil
        case .groupType:
            return "Hint: \(game.targetSong.type.label)"
        case .debutYear:
            guard let group = game.targetGroup else { return nil }
            return "Hint: \(group.type.label) · debuted \(group.debutYear)"
        case .firstLetter:
            let first = game.targetSong.artistEn.prefix(1)
            return "Hint: artist starts with \(first)"
        }
    }
}

private extension GroupType {
    var label: String {
        switch self {
        case .boyGroup: return "Boy Group"
        case .girlGroup: return "Girl Group"
        case .solo: return "Solo Artist"
        case .coed: return "Coed Group"
        }
    }
}
