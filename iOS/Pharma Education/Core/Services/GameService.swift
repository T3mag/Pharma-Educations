import Alamofire
import Foundation

protocol GameServiceProtocol {
    func getTopic() async throws -> TopicsTreeResponse
    
    func getFlashCards(
        topicIds: [String],
        cardsCount: Int)
    async throws -> FlashcardsResponse
    
    func getQuiz(
        topicIds: [String],
        questionCount: Int,
    ) async throws -> QuizResponse
    
    func getMatch(
        topicIds: [String],
        pairCount: Int)
    async throws -> MatchResponse
    
    func getCustomers(
        customersCount: Int
    ) async throws -> PharmacySimulatorResponse
    
    func getFeedbackByUserAnswer(
        scenarioId: String,
        userAnswer: String
    ) async throws -> UserAnswerResponse
}

final class GameService: GameServiceProtocol {
    
    func getTopic() async throws -> TopicsTreeResponse {
        let data = try await AF.request(
            Config.urlTopic,
            method: .get
        )
        .serializingData()
        .value
        
        return try JSONDecoder().decode(TopicsTreeResponse.self, from: data)
    }
    
    func getFeedbackByUserAnswer(scenarioId: String, userAnswer: String) async throws -> UserAnswerResponse {
        let request = UserAnswerRequest(scenarioId: scenarioId, answer: userAnswer)
        let body = try JSONEncoder().encode(request)
        
        let response = await AF.upload(
            body,
            to: Config.PharmacySImulatorUserAnswer,
            method: .post,
            headers: HTTPHeaders(["Content-Type": "application/json"])
        )
        .serializingData()
        .response
        
        try checkStatusCode(response: response)
        
        let data = try response.result.get()
        return try JSONDecoder().decode(UserAnswerResponse.self, from: data)
    }
    
    func getCustomers(customersCount: Int) async throws -> PharmacySimulatorResponse {
        guard customersCount <= 10  else {
            throw NSError(domain: "Ошибка", code: -1)
        }
        
        let request = PharmacySimulatorRequest(customersCount: customersCount)
        let body = try JSONEncoder().encode(request)
        
        let response = await AF.upload(
            body,
            to: Config.PharmacySImulator,
            method: .post,
            headers: HTTPHeaders(["Content-Type": "application/json"])
        )
        .serializingData()
        .response
        
        try checkStatusCode(response: response)
        
        let data = try response.result.get()
        return try JSONDecoder().decode(PharmacySimulatorResponse.self, from: data)
    }
    
    func getFlashCards(
        topicIds: [String],
        cardsCount: Int)
    async throws -> FlashcardsResponse {
        guard cardsCount <= 10  else {
            throw NSError(domain: "Ошибка", code: -1)
        }
        
        let request = FlashcardsRequest(
            topicIds: topicIds,
            flashcardsCount: cardsCount)
        
        let body = try JSONEncoder().encode(request)
        
        let response = await AF.upload(
            body,
            to: Config.flashcards,
            method: .post,
            headers: HTTPHeaders(["Content-Type": "application/json"])
        )
        .serializingData()
        .response
        
        try checkStatusCode(response: response)
        
        let data = try response.result.get()
        return try JSONDecoder().decode(FlashcardsResponse.self, from: data)
    }
    
    func getMatch(
        topicIds: [String],
        pairCount: Int)
    async throws -> MatchResponse {
        guard pairCount <= 10  else {
            throw NSError(domain: "Ошибка", code: -1)
        }
        
        let request = MatchRequest(
            topicIds: topicIds,
            taskCount: pairCount
        )
        
        let body = try JSONEncoder().encode(request)
        let response = await AF.upload(
            body,
            to: Config.matchQuiz,
            method: .post,
            headers: HTTPHeaders(["Content-Type": "application/json"])
        )
        .serializingData()
        .response
        
        try checkStatusCode(response: response)
        
        let data = try response.result.get()
        return try JSONDecoder().decode(MatchResponse.self, from: data)
    }
    
    func getQuiz(
        topicIds: [String],
        questionCount: Int
    ) async throws -> QuizResponse {
        guard questionCount <= 10  else {
            throw NSError(domain: "Ошибка", code: -1)
        }
        let request = QuizRequest(
            topicIds: topicIds,
            questionCount: questionCount,
            optionsPerQuestion: 4
        )
        
        let body = try JSONEncoder().encode(request)
        let response = await AF.upload(
            body,
            to: Config.urlQuiz,
            method: .post,
            headers: HTTPHeaders(["Content-Type": "application/json"])
        )
        .serializingData()
        .response
        
        try checkStatusCode(response: response)
        
        let data = try response.result.get()
        return try JSONDecoder().decode(QuizResponse.self, from: data)
    }
    
    private func checkStatusCode(response: DataResponse<Data, AFError>) throws {
        if let statusCode = response.response?.statusCode,
           !(200...299).contains(statusCode) {
            let message = response.data.flatMap {
                String(data: $0, encoding: .utf8)
            } ?? "Unknown server error"
            
            throw NSError(
                domain: "GameService",
                code: statusCode,
                userInfo: [NSLocalizedDescriptionKey: message]
            )
        }
    }
}
