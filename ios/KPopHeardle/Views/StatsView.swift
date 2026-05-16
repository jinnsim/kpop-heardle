import SwiftUI
import SwiftData

@MainActor
struct StatsView: View {
    @Query(sort: \PuzzleRecord.completedAt, order: .reverse) private var records: [PuzzleRecord]
    @Environment(CatalogService.self) private var catalog

    private var calc: StatsCalculator { StatsCalculator(records: records) }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    if records.isEmpty {
                        EmptyStatsCard()
                    } else {
                        ScopeStatsBlock(title: Text("stats.scope.global"),
                                        scope: calc.globalRecords)

                        ForEach(activeGroups, id: \.id) { group in
                            ScopeStatsBlock(
                                title: Text("stats.scope.group \(group.nameEn)"),
                                scope: calc.groupRecords(groupId: group.id),
                                accent: group.accentColor
                            )
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("stats.title")
            .navigationBarTitleDisplayMode(.large)
        }
    }

    private var activeGroups: [ArtistGroup] {
        guard let cat = catalog.catalog else { return [] }
        let groupsWithHistory = Set(
            records.filter { $0.modeKind == "group" }.compactMap { $0.groupId }
        )
        return cat.groups.filter { groupsWithHistory.contains($0.id) }
    }
}

// MARK: - Sub-views

private struct ScopeStatsBlock: View {
    let title: Text
    let scope: [PuzzleRecord]
    var accent: Color = .accentColor

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            title
                .font(.headline)
                .foregroundStyle(accent)

            ScopeNumbersGrid(scope: scope)

            AttemptDistributionChart(scope: scope, accent: accent)
        }
        .padding(16)
        .background(Color.gray.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}

private struct ScopeNumbersGrid: View {
    let scope: [PuzzleRecord]

    var body: some View {
        let streak = StatsCalculator.currentStreak(scope)
        HStack(spacing: 12) {
            NumberCell(value: "\(StatsCalculator.played(scope))",
                       label: Text("stats.label.played"))
            NumberCell(value: "\(Int(StatsCalculator.winRate(scope) * 100))%",
                       label: Text("stats.label.winRate"))
            NumberCell(value: "\(streak)",
                       label: Text("stats.label.currentStreak"),
                       trailingEmoji: streak >= 3 ? "🔥" : nil)
            NumberCell(value: "\(StatsCalculator.longestStreak(scope))",
                       label: Text("stats.label.longestStreak"))
        }
    }
}

private struct NumberCell: View {
    let value: String
    let label: Text
    var trailingEmoji: String? = nil

    var body: some View {
        VStack(spacing: 4) {
            HStack(spacing: 4) {
                Text(verbatim: value).font(.title2.bold())
                if let emoji = trailingEmoji {
                    Text(verbatim: emoji).font(.title3)
                }
            }
            label
                .font(.caption2)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .lineLimit(2)
                .minimumScaleFactor(0.7)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
        .background(Color.gray.opacity(0.10))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

private struct AttemptDistributionChart: View {
    let scope: [PuzzleRecord]
    let accent: Color

    private var histogram: [Int] { StatsCalculator.attemptHistogram(scope) }
    private var losses: Int { StatsCalculator.lossCount(scope) }
    private var maxCount: Int {
        max(histogram[1...].max() ?? 0, losses, 1)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("stats.distribution.title")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.secondary)

            VStack(spacing: 4) {
                ForEach(1...6, id: \.self) { attempts in
                    BarRow(label: "\(attempts)",
                           count: histogram[attempts],
                           maxCount: maxCount,
                           color: accent)
                }
                BarRow(label: "X",
                       count: losses,
                       maxCount: maxCount,
                       color: .red.opacity(0.7))
            }
        }
    }
}

private struct BarRow: View {
    let label: String
    let count: Int
    let maxCount: Int
    let color: Color

    var body: some View {
        HStack(spacing: 8) {
            Text(verbatim: label)
                .font(.caption.monospacedDigit())
                .frame(width: 16, alignment: .trailing)
                .foregroundStyle(.secondary)

            GeometryReader { proxy in
                let fullWidth = proxy.size.width
                let ratio = maxCount > 0 ? CGFloat(count) / CGFloat(maxCount) : 0
                let barWidth = max(28, fullWidth * ratio)
                HStack {
                    RoundedRectangle(cornerRadius: 4, style: .continuous)
                        .fill(color.opacity(count == 0 ? 0.2 : 0.85))
                        .frame(width: barWidth)
                        .overlay(
                            Text(verbatim: "\(count)")
                                .font(.caption2.bold())
                                .foregroundStyle(.white)
                                .padding(.trailing, 8),
                            alignment: .trailing
                        )
                    Spacer(minLength: 0)
                }
            }
            .frame(height: 18)
        }
    }
}

private struct EmptyStatsCard: View {
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "chart.bar.xaxis")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("stats.empty.title")
                .font(.headline)
            Text("stats.empty.subtitle")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(32)
        .frame(maxWidth: .infinity)
        .background(Color.gray.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}
