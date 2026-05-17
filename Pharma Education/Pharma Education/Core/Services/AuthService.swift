import Foundation
import FirebaseAuth

protocol AuthServiceProtocol {
    func register(email: String, password: String, completion: @escaping (Result<User, Error>) -> Void)
    func login(email: String, password: String, completion: @escaping (Result<User, Error>) -> Void)
    func logout() throws
}

final class AuthService: AuthServiceProtocol {
    static let shared = AuthService()
    
    func register(email: String, password: String, completion: @escaping(Result<User, Error>) -> Void) {
        Auth.auth().createUser(withEmail: email, password: password) { (result, error) in
            if let error = error {
                completion(.failure(error))
            }
            
            guard let user = result?.user else {
                completion(.failure(NSError(domain: "AuthService", code: -1)))
                return
            }
            
            completion(.success(user))
        }
    }
    
    func login(email: String, password: String, completion: @escaping(Result<User, Error>) -> Void) {
        Auth.auth().signIn(withEmail: email, password: password) { (result, error) in
            if let error = error {
                completion(.failure(error))
            }
            
            guard let user = result?.user else {
                completion(.failure(NSError(domain: "AuthService", code: -1)))
                return
            }
            
            completion(.success(user))
        }
    }
    
    func logout() throws {
        try Auth.auth().signOut()
    }
}




