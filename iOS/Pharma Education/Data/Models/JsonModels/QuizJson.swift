import Foundation

struct QuizRequest: Encodable {
    let topicIds: [String]
    let questionCount: Int
    let optionsPerQuestion: Int
    
    enum CodingKeys: String, CodingKey {
        case topicIds = "topic_ids"
        case questionCount = "question_count"
        case optionsPerQuestion = "options_per_question"
    }
}

struct QuizResponse: Decodable {
    let gameType: String?
    let topic: String
    let title: String
    let questions: [QuizQuestion]
    
    enum CodingKeys: String, CodingKey {
        case gameType = "game_type"
        case topic
        case title
        case questions
    }
}

struct QuizQuestion: Decodable {
    let question: String
    let options: [String]
    let correctAnswer: String
    let explanation: String
    
    enum CodingKeys: String, CodingKey {
        case question
        case options
        case correctAnswer = "correct_answer"
        case explanation
    }
}
