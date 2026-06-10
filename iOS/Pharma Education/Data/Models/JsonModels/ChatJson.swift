
struct ChatResponse: Decodable {
    let message: String
    let answer: String
    
    enum CodingKeys: String, CodingKey {
        case message = "message"
        case answer = "answer"
    }
}
