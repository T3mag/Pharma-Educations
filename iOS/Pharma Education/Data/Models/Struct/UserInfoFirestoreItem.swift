import FirebaseFirestore

struct UserInfoFirestoreItem {
    var uid: String?
    var email: String
    var fullName: String
    var createdAt: FieldValue = FieldValue.serverTimestamp()
    var countGames: Int = 0
    var countSimulators: Int = 0
    var countRequests: Int = 0
    var daysRunning: Int = 0
    var currentLevel: Int = 0
    var currentExp: Int = 0
    
    var dictionary: [String: Any] {
        [
            "uid": uid ?? "",
            "email": email,
            "fullName": fullName,
            "createdAt": createdAt,
            "countGames": countGames,
            "countSimulators": countSimulators,
            "countRequests": countRequests,
            "daysRunning": daysRunning,
            "currentLevel": currentLevel,
            "currentExp": currentExp
        ]
    }
    func withUserId(_ userId: String) -> UserInfoFirestoreItem {
        UserInfoFirestoreItem(uid: userId,
                             email: email,
                             fullName: fullName
        )
    }
}
