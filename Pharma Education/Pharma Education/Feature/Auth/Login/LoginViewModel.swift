import Foundation

final class LoginViewModel {
    private let authService: AuthServiceProtocol
    var onError: ((String) -> Void)?
    var onSuccess: (() -> Void)?
    
    init(authService: AuthServiceProtocol) {
        self.authService = authService
    }
    
    func auth(email: String, password: String) {
        guard !email.isEmpty, !password.isEmpty else {
            onError?(Texts.Errors.emptyString)
            return
        }
        
        authService.login(email: email, password: password) { result in
            switch result {
            case .success:
                self.onSuccess?()
            case .failure(let error):
                self.onError?(error.localizedDescription)
            }
        }
    }
    
}
