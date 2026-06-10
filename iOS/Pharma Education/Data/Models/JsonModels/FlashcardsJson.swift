struct FlashcardsRequest: Encodable {
    let topicIds: [String]
    let flashcardsCount: Int
    
    enum CodingKeys: String, CodingKey {
        case topicIds = "topic_ids"
        case flashcardsCount = "card_count"
    }
}

struct FlashcardsResponse: Decodable {
    let gameType: String?
    let topic: String
    let title: String
    let cards: [Flashcard]
    
    enum CodingKeys: String, CodingKey {
        case gameType = "game_type"
        case topic
        case title
        case cards
    }
}

struct Flashcard: Decodable {
    let frontTitle: String
    let front: String
    let backTitle: String
    let back: String
    
    enum CodingKeys: String, CodingKey {
        case frontTitle = "front_title"
        case front
        case backTitle = "back_title"
        case back
    }
}
