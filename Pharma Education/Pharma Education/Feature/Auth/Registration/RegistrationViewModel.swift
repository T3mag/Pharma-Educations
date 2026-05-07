import Foundation

final class RegistrationViewModel {
    private let authService: AuthServiceProtocol
    var onError: ((String) -> Void)?
    var onSuccess: (() -> Void)?
    
    init(authService: AuthServiceProtocol) {
        self.authService = authService
    }
    
    func register(email: String,
                  password: String,
                  confirmPassword: String,
                  surname: String,
                  name: String,
                  lastname: String,
                  birthday: String) {
        
        guard !email.isEmpty, !password.isEmpty, !confirmPassword.isEmpty,
              !surname.isEmpty, !name.isEmpty, !birthday.isEmpty else {
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
        let patern = Texts.Registration.emailPattern
        return email.range(of: patern, options: .regularExpression) != nil
    }
    
    private func passwordMatch(_ password: String, _ confirmPassword: String) -> Bool {
        password == confirmPassword
    }
}
