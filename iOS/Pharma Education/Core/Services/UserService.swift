internal import Combine

protocol UserServiceProtocol {
    static var shared : UserServiceProtocol { get }
    var userInfoPublisher: AnyPublisher<UserInfoFirestoreItem?, Never> { get }
    var userId: String {get}
}

final class UserService: UserServiceProtocol {
    
    static let shared: UserServiceProtocol = UserService()
    
    @Published var userInfo: UserInfoFirestoreItem?
    
    private var firestoreService: FirestoreServiceProtocol
    private let sessionManager: SessionManagerProtocol
    private var cancellables = Set<AnyCancellable>()
    
    var userInfoPublisher: AnyPublisher<UserInfoFirestoreItem?, Never> {
        $userInfo.eraseToAnyPublisher()
    }
    
    var userId: String {
        self.userInfo?.uid ?? ""
    }
    
    init(firestoreService: FirestoreServiceProtocol = FirestoreService.shared,
         sessionManager: SessionManagerProtocol = SessionManager.shared) {
        self.firestoreService = firestoreService
        self.sessionManager = sessionManager
        
        observeUser()
        updateUser()
    }
    
    private func observeUser() {
        sessionManager.userIDPublisher
            .sink { [weak self] uid in
                guard let self else { return }

                guard let uid else {
                    Task { @MainActor in
                        self.userInfo = nil
                    }
                    return
                }

                self.uploadUserInfo(uid)
            }
            .store(in: &cancellables)
    }
    
    private func updateUser() {
        firestoreService.onUpgradeUserInfo = { [weak self] in
            guard let uid = self?.userInfo?.uid else {
                return
            }
            
            self?.uploadUserInfo(uid)
        }
    }
    
    private func uploadUserInfo(_ uid: String) {
        Task {
            do {
                let updatedUserInfo = try await firestoreService.getUSerInfo(uid: uid)
                await MainActor.run {
                    self.userInfo = updatedUserInfo
                }
            } catch {
                print(error)
            }
        }
    }
}
