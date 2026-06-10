import Foundation

struct MatchRequest: Encodable {
    let topicIds: [String]
    let taskCount: Int
    
    enum CodingKeys: String, CodingKey {
        case topicIds = "topic_ids"
        case taskCount = "task_count"
    }
}

struct MatchResponse: Decodable {
    let gameType: String?
    let topic: String
    let title: String
    let tasks: [MatchTask]
    
    enum CodingKeys: String, CodingKey {
        case gameType = "game_type"
        case topic
        case title
        case tasks
    }
}

struct MatchTask: Decodable {
    let id: String
    let pairs: [MatchPair]
    
    enum CodingKeys: String, CodingKey {
        case id = "task_id"
        case pairs
    }
}

struct MatchPair: Decodable {
    let id: String
    let left: String
    let right: String
    
    enum CodingKeys: String, CodingKey {
        case id = "pair_id"
        case left
        case right
    }
}
