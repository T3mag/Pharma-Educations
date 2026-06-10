import FirebaseAuth
internal import Combine

protocol SessionManagerProtocol {
    static var shared: SessionManagerProtocol { get }
    var userPublisher: AnyPublisher<User?, Never> { get }
    var userIDPublisher: AnyPublisher<String?, Never> { get }
    func start()
}

final class SessionManager: ObservableObject, SessionManagerProtocol {
    static let shared: SessionManagerProtocol = SessionManager()
    
    @Published var user: User?
    private var handle: NSObjectProtocol?
    
    var userPublisher: AnyPublisher<User?, Never> {
        $user.eraseToAnyPublisher()
    }
    var userIDPublisher: AnyPublisher<String?, Never> {
        $user
            .map { $0?.uid }
            .eraseToAnyPublisher()
    }
    
    func start() {
        startListening { [weak self] user in
            DispatchQueue.main.async {
                self?.user = user
            }
        }
    }
    
    private func startListening(onChange: @escaping (FirebaseAuth.User?) -> Void) {
        handle = Auth.auth().addStateDidChangeListener({ (auth, user) in
            onChange(user)
        })
    }
    
    private func stopListening() {
        if let handle {
            Auth.auth().removeStateDidChangeListener(handle)
        }
    }
    
    deinit {
        stopListening()
    }
}


