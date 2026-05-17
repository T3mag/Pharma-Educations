import Foundation

protocol RegistrationViewModelProtocol {
    var onError: ((String) -> Void)? {get set}
    var onSuccess: (() -> Void)? {get set}
    func register(email: String, password: String, confirmPassword: String, fullName: String)
}

final class RegistrationViewModel: RegistrationViewModelProtocol {
    private let authService: AuthServiceProtocol
    var onError: ((String) -> Void)?
    var onSuccess: (() -> Void)?
    
    init(authService: AuthServiceProtocol = AuthService()) {
        self.authService = authService
    }
    
    func register(email: String,
                  password: String,
                  confirmPassword: String,
                  fullName: String) {
        
        guard !email.isEmpty, !password.isEmpty, !confirmPassword.isEmpty,
              !fullName.isEmpty else {
            onError?(Texts.Errors.emptyString)
            return
        }
        
        guard checkValidEmail(email) else {
            onError?(Texts.Errors.invalidEmail)
            return
        }
        
        guard passwordMatch(password, confirmPassword) else {
            onError?(Texts.Errors.invalidEmail)
            return
        }
        
        authService.register(email: email, password: password) { result in
            switch result {
            case .success:
                self.onSuccess?()
            case .failure(let error):
                self.onError?(error.localizedDescription)
            }
        }
    }
    
    
    private func checkValidEmail(_ email: String) -> Bool {
        let email = email.trimmingCharacters(in: .whitespacesAndNewlines)
        let patern = RegistrationTexts.emailPattern
        return email.range(of: patern, options: .regularExpression) != nil
    }
    
    private func passwordMatch(_ password: String, _ confirmPassword: String) -> Bool {
        password == confirmPassword
    }
}
