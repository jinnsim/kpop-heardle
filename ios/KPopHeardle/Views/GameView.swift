import SwiftUI
import SwiftData

struct GameView: View {
    @Environment(AudioService.self) private var audio
    @Environment(GameCoordinator.self) private var coordinator
    @Environment(\.modelContext) private var modelContext

    @State var game: GameState
    @State private var query = ""
    @State private var lastOutcome: GuessOutcome?
    @State private var showResult = false

    private var autocomplete: [Song] {
        Autocomplete.filter(query, in: coordinator.autocompleteUniverse(for: game.mode))
    }

    var body: some View {
        VStack(spacing: 16) {
            AttemptIndicatorRow(game: game)

            PlayerControls(
                game: game,
                onPlay: playCurrentClip
            )

            GuessHistoryList(game: game)

            if !game.finished {
                GuessInputView(
                    query: $query,
                    suggestions: autocomplete,
                    onPick: handlePick,
                    onSkip: { handlePick(nil) }
                )
            } else {
                Button {
                    showResult = true
                } label: {
                    Label("View Result", systemImage: "trophy.fill")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .padding(.horizontal)
            }

            Spacer(minLength: 0)
        }
        .navigationTitle(game.mode.displayName)
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if let url = URL(string: game.targetSong.previewUrl) {
                audio.prepare(previewURL: url)
            }
        }
        .onDisappear {
            audio.stop()
        }
        .sheet(isPresented: $showResult) {
            ResultView(game: game)
        }
        .onChange(of: game.finished) { _, finished in
            if finished {
                persistResult()
                showResult = true
            }
        }
    }

    private func handlePick(_ song: Song?) {
        lastOutcome = game.submit(guessedSong: song)
        query = ""
        if !game.finished {
            playCurrentClip()
        }
    }

    private func playCurrentClip() {
        audio.playClip(duration: game.revealedClipDuration > 0 ? game.revealedClipDuration : game.currentClipDuration)
    }

    private func persistResult() {
        let key = PuzzleRecord.makeKey(mode: game.mode)
        let descriptor = FetchDescriptor<PuzzleRecord>(predicate: #Predicate { $0.key == key })
        let existing = (try? modelContext.fetch(descriptor))?.first
        if existing != nil { return }

        let (kind, groupId, date): (String, String?, String) = {
            switch game.mode {
            case .globalDaily(let date): return ("global", nil, date)
            case .groupDaily(let groupId, let date): return ("group", groupId, date)
            }
        }()

        let record = PuzzleRecord(
            key: key,
            modeKind: kind,
            groupId: groupId,
            date: date,
            songId: game.targetSong.id,
            attemptsUsed: game.guesses.count,
            won: game.won
        )
        modelContext.insert(record)
        try? modelContext.save()
    }
}
