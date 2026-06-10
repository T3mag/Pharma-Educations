import Foundation
import FirebaseAuth

protocol AuthServiceProtocol {
    func register(
        registrationUserInfo: UserInfoFirestoreItem,
        password: String,
        completion: @escaping(Result<Void, Error>) -> Void)
    func login(email: String, password: String, completion: @escaping (Result<User, Error>) -> Void)
    func logout() throws
}

final class AuthService: AuthServiceProtocol {
    
    static let shared = AuthService()
    
    func register(registrationUserInfo: UserInfoFirestoreItem, password: String,
                  completion: @escaping(Result<Void, Error>) -> Void) {
        Auth.auth().createUser(withEmail: registrationUserInfo.email, password: password) { (result, error) in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let user = result?.user else {
                completion(.failure(NSError(domain: "AuthService", code: -1)))
                return
            }
            let info = registrationUserInfo.withUserId(user.uid)
            
            Task{
                do {
                    try await FirestoreService().addUser(registrationUserInfo: info)
                    completion(.success(()))
                } catch {
                    completion(.failure(error))
                }
            }
        }
    }
    
    func login(email: String, password: String, completion: @escaping(Result<User, Error>) -> Void) {
        Auth.auth().signIn(withEmail: email, password: password) { (result, error) in
            if let error = error {
                completion(.failure(error))
                return
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




