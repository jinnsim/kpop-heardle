import SwiftUI

struct PlayerControls: View {
    @Environment(AudioService.self) private var audio

    let game: GameState
    let onPlay: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            if game.finished {
                Text("player.reveal.full")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                Text("Listen: \(durationLabel)")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            Button(action: onPlay) {
                Image(systemName: audio.isPlaying ? "stop.circle.fill" : "play.circle.fill")
                    .font(.system(size: 64))
                    .symbolRenderingMode(.hierarchical)
            }
            .buttonStyle(.plain)

            if let hintKey {
                Text(hintKey)
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

    private var hintKey: LocalizedStringKey? {
        switch game.hintTier {
        case .none: return nil
        case .groupType:
            return "Hint: \(game.targetSong.type.localizedLabel)"
        case .debutYear:
            guard let group = game.targetGroup else { return nil }
            return "Hint: \(group.type.localizedLabel) · debuted \(group.debutYear)"
        case .firstLetter:
            let first = String(game.targetSong.artistEn.prefix(1))
            return "Hint: artist starts with \(first)"
        }
    }
}

extension GroupType {
    var localizedLabel: String {
        switch self {
        case .boyGroup:  return String(localized: "groupType.boy",   comment: "Boy group label")
        case .girlGroup: return String(localized: "groupType.girl",  comment: "Girl group label")
        case .solo:      return String(localized: "groupType.solo",  comment: "Solo artist label")
        case .coed:      return String(localized: "groupType.coed",  comment: "Coed group label")
        }
    }
}
