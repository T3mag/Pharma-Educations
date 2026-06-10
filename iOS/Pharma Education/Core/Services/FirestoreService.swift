import FirebaseFirestore

protocol FirestoreServiceProtocol {
    static var shared: FirestoreServiceProtocol { get }
    var onUpgradeUserInfo: (() -> Void)? { get set }
    func addUser(registrationUserInfo: UserInfoFirestoreItem) async throws
    func getUSerInfo(uid: String) async throws -> UserInfoFirestoreItem
    func incrementRequestCount(uid: String) async throws
    func incrementGamesCount(uid: String) async throws
    func incrementSimulatorsCount(uid: String) async throws
}

final class FirestoreService: FirestoreServiceProtocol {
    static let shared: FirestoreServiceProtocol = FirestoreService()
    
    var onUpgradeUserInfo: (() -> Void)?
    
    func addUser(registrationUserInfo: UserInfoFirestoreItem) async throws {
        
        guard let uid = registrationUserInfo.uid else {
            throw NSError(domain: "FirestoreService/addUser", code: -1)
        }
        
        try await Firestore.firestore()
            .collection("users")
            .document(uid)
            .setData(registrationUserInfo.dictionary)
            
    }
    
    func getUSerInfo(uid: String) async throws -> UserInfoFirestoreItem {
        let doc = try await Firestore.firestore()
            .collection("users")
            .document(uid)
            .getDocument()
        
        guard let data = doc.data() else {
            throw NSError(domain: "FirestoreService/getUserInfo", code: -1)
        }
        
        return UserInfoFirestoreItem(
            uid: data["uid"] as? String ?? uid,
            email: data["email"] as? String ?? "",
            fullName: data["fullName"] as? String ?? "",
            countGames: intValue(from: data["countGames"]),
            countSimulators: intValue(from: data["countSimulators"]),
            countRequests: intValue(from: data["countRequests"]),
            daysRunning: intValue(from: data["daysRunning"]),
            currentLevel: intValue(from: data["currentLevel"]),
            currentExp: intValue(from: data["currentExp"])
        )
    }
    
    private func intValue(from value: Any?) -> Int {
        if let int = value as? Int {
            return int
        }
        
        if let number = value as? NSNumber {
            return number.intValue
        }
        
        return 0
    }
    
    func incrementRequestCount(uid: String) async throws {
        try await Firestore.firestore()
            .collection("users")
            .document(uid)
            .updateData([
                "countRequests": FieldValue.increment(Int64(1))
            ])
        await MainActor.run {
            onUpgradeUserInfo?()
        }
    }

    func incrementGamesCount(uid: String) async throws {
        try await Firestore.firestore()
            .collection("users")
            .document(uid)
            .updateData([
                "countGames": FieldValue.increment(Int64(1))
            ])
        await MainActor.run {
            onUpgradeUserInfo?()
        }
    }

    func incrementSimulatorsCount(uid: String) async throws {
        try await Firestore.firestore()
            .collection("users")
            .document(uid)
            .updateData([
                "countSimulators": FieldValue.increment(Int64(1))
            ])
        await MainActor.run {
            onUpgradeUserInfo?()
        }
    }
}
