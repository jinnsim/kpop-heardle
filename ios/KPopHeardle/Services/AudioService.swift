import Foundation
import AVFoundation
import Observation

/// Streams an iTunes preview clip and stops at a precise duration.
/// Handles "play first N seconds" for Heardle-style attempts.
@MainActor
@Observable
final class AudioService {
    private var player: AVPlayer?
    private var timeObserver: Any?
    private var endTime: CMTime?

    private(set) var isPlaying: Bool = false
    // Internal diagnostic only; not surfaced to the user yet. If/when
    // exposed, localize at the view boundary via a key.
    private(set) var error: String?

    /// Currently playing song's preview URL, kept so we can resume different durations.
    private var currentURL: URL?

    func prepare(previewURL: URL) {
        if currentURL == previewURL, player != nil { return }
        cleanupPlayer()
        let item = AVPlayerItem(url: previewURL)
        player = AVPlayer(playerItem: item)
        currentURL = previewURL

        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            self.error = "Audio session: \(error.localizedDescription)"
        }
    }

    /// Plays from the beginning of the preview clip for `duration` seconds, then stops.
    func playClip(duration: TimeInterval) {
        guard let player else { return }

        removeTimeObserver()
        let target = CMTime(seconds: duration, preferredTimescale: 600)
        player.seek(to: .zero, toleranceBefore: .zero, toleranceAfter: .zero) { [weak self] _ in
            // Seek completion runs off the main actor; hop back before
            // touching observable state.
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.endTime = target
                self.installTimeObserver()
                player.play()
                self.isPlaying = true
            }
        }
    }

    func stop() {
        player?.pause()
        isPlaying = false
        removeTimeObserver()
    }

    private func installTimeObserver() {
        guard let player else { return }
        let interval = CMTime(seconds: 0.05, preferredTimescale: 600)
        // Periodic observer block runs on .main queue. We still hop into a
        // MainActor task to satisfy Swift concurrency.
        timeObserver = player.addPeriodicTimeObserver(
            forInterval: interval,
            queue: .main
        ) { [weak self] time in
            Task { @MainActor [weak self] in
                guard let self, let end = self.endTime else { return }
                if time >= end { self.stop() }
            }
        }
    }

    private func removeTimeObserver() {
        if let obs = timeObserver, let player {
            player.removeTimeObserver(obs)
        }
        timeObserver = nil
    }

    private func cleanupPlayer() {
        stop()
        player = nil
        currentURL = nil
    }

    /// Deinit is implicitly nonisolated. Avoid touching MainActor state.
    /// AVPlayer's own observer registration is automatically released when
    /// the player is deallocated, so explicit removal here is unnecessary.
    deinit {}
}
