
import Foundation
internal import Combine
import Dispatch

protocol AccountViewModelProtocol {
    var updateUserInfo: ((UserInfoFirestoreItem) -> Void)? { get set }
    var onStatsUpdate: (() -> Void)? { get set }
    
    var stats: [AccountStatistics] { get }
    var settings: [AccountStatistics] { get }
    
    func logout()
}

final class AccountViewModel: AccountViewModelProtocol {
    
    private var currentUserInfo: UserInfoFirestoreItem?
    private let authService: AuthServiceProtocol
    private let userService: UserServiceProtocol
    private var cancellables = Set<AnyCancellable>()
    
    var stats: [AccountStatistics] = [
        AccountStatistics(title: "Дней без пропусков", icon: "flame.fill", accessory: .value("0 дней")),
        AccountStatistics(title: "Кол-во игр", icon: "gamecontroller.fill", accessory: .value("0")),
        AccountStatistics(title: "Кол-во симуляторов", icon: "cross.case.fill", accessory: .value("0")),
        AccountStatistics(title: "Кол-во запросов", icon: "bubble.left.and.bubble.right.fill", accessory: .value("0")),
        AccountStatistics(title: "Достижения", icon: "rosette", accessory: .chevron)
    ]
    
    var settings: [AccountStatistics] = [
        AccountStatistics(title: "Светлая/тёмная тема", icon: "circle.lefthalf.filled", accessory: .switch),
        AccountStatistics(title: "Включить уведомления", icon: "bell.fill", accessory: .switch),
        AccountStatistics(title: "Настроить язык", icon: "globe", accessory: .chevron)
    ]
    
    var updateUserInfo: ((UserInfoFirestoreItem) -> Void)? {
        didSet {
            if let currentUserInfo {
                updateUserInfo?(currentUserInfo)
            }
        }
    }
    var onStatsUpdate: (() -> Void)?
    
    init(authService: AuthServiceProtocol = AuthService.shared,
         userService: UserServiceProtocol = UserService.shared) {
        self.authService = authService
        self.userService = userService
        
        observeUserInfo()
    }
    
    private func observeUserInfo() {
        userService.userInfoPublisher
            .compactMap { $0 }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] data in
                self?.currentUserInfo = data
                self?.updateStats()
                print(data)
            }
            .store(in: &cancellables)
    }
    
    private func updateStats() {
        guard let userInfo = currentUserInfo else {
            return
        }
        stats[0].accessory = .value("\(userInfo.daysRunning)")
        stats[1].accessory = .value("\(userInfo.countGames)")
        stats[2].accessory = .value("\(userInfo.countSimulators)")
        stats[3].accessory = .value("\(userInfo.countRequests)")
        
        onStatsUpdate?()
    }
    
    func logout() {
        try? authService.logout()
    }
}
