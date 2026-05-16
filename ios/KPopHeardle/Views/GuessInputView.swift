import SwiftUI

struct GuessInputView: View {
    @Binding var query: String
    let suggestions: [Song]
    let onPick: (Song) -> Void
    let onSkip: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("guess.search.placeholder", text: $query)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
            }
            .padding(12)
            .background(Color.gray.opacity(0.15))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

            if !suggestions.isEmpty {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(suggestions.prefix(6)) { song in
                        Button {
                            onPick(song)
                        } label: {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(verbatim: song.titleEn)
                                    .font(.body)
                                    .foregroundStyle(.primary)
                                Text(verbatim: song.artistEn)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.vertical, 10)
                            .padding(.horizontal, 12)
                        }
                        Divider()
                    }
                }
                .background(Color.gray.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            }

            Button(role: .destructive, action: onSkip) {
                Label("guess.skip", systemImage: "forward.fill")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
            .controlSize(.regular)
        }
        .padding(.horizontal)
    }
}
