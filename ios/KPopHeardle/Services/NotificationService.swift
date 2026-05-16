import Foundation
import UserNotifications
import Observation

/// Schedules and manages the daily reminder local notification.
/// 100% on-device — no server, no APNs token.
@MainActor
@Observable
final class NotificationService {

    enum AuthorizationStatus {
        case unknown
        case denied
        case granted
        case provisional
    }

    static let dailyReminderId = "com.ootssu.kpopheardle.dailyReminder"

    /// User preference (persisted in UserDefaults). When true, we keep the
    /// daily reminder scheduled; when false we remove it.
    var remindersEnabled: Bool {
        didSet {
            UserDefaults.standard.set(remindersEnabled, forKey: Self.prefKey)
            Task { await syncSchedule() }
        }
    }

    private(set) var authorization: AuthorizationStatus = .unknown
    private static let prefKey = "kph.remindersEnabled"

    init() {
        // Default: ON. The user can flip it off in Settings.
        if UserDefaults.standard.object(forKey: Self.prefKey) == nil {
            UserDefaults.standard.set(true, forKey: Self.prefKey)
        }
        self.remindersEnabled = UserDefaults.standard.bool(forKey: Self.prefKey)
    }

    func refreshAuthorizationStatus() async {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        authorization = Self.translate(settings.authorizationStatus)
    }

    /// Prompt the system permission sheet (no-op if already determined).
    /// Returns the resulting status.
    @discardableResult
    func requestAuthorization() async -> AuthorizationStatus {
        let center = UNUserNotificationCenter.current()
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])
            authorization = granted ? .granted : .denied
        } catch {
            authorization = .denied
        }
        await syncSchedule()
        return authorization
    }

    /// Adds or removes the daily reminder depending on `remindersEnabled`
    /// and `authorization`. Idempotent.
    func syncSchedule() async {
        let center = UNUserNotificationCenter.current()
        center.removePendingNotificationRequests(withIdentifiers: [Self.dailyReminderId])

        // Provisional permission is silent-only on iOS but still delivers,
        // so schedule for both .granted and .provisional.
        let canSchedule = authorization == .granted || authorization == .provisional
        guard remindersEnabled, canSchedule else { return }

        let content = UNMutableNotificationContent()
        content.title = String(localized: "notif.daily.title",
                               comment: "Title of the daily reminder notification.")
        content.body  = String(localized: "notif.daily.body",
                               comment: "Body of the daily reminder notification.")
        content.sound = .default
        content.threadIdentifier = "daily"

        // Fire at 00:05 local time every day so the new puzzle is fresh.
        var trigger = DateComponents()
        trigger.hour = 0
        trigger.minute = 5
        let request = UNNotificationRequest(
            identifier: Self.dailyReminderId,
            content: content,
            trigger: UNCalendarNotificationTrigger(dateMatching: trigger, repeats: true)
        )

        do {
            try await center.add(request)
        } catch {
            // Don't crash the app over a failed schedule; log and continue.
            print("notification schedule failed: \(error)")
        }
    }

    private static func translate(_ raw: UNAuthorizationStatus) -> AuthorizationStatus {
        switch raw {
        case .notDetermined: return .unknown
        case .denied, .ephemeral: return .denied
        case .authorized: return .granted
        case .provisional: return .provisional
        @unknown default: return .unknown
        }
    }
}
