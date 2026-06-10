import Foundation
import Alamofire

protocol AIAssistantServiceProtocol {
    func sendMessage(_ message: String) async throws -> ChatResponse
}

final class AIAssistantService: AIAssistantServiceProtocol {
    
    func sendMessage(_ message: String) async throws -> ChatResponse {
        let parameters = [
            "message": message
        ]
        
        let data = try await AF.request(
            Config.urlChat,
            method: .post,
            parameters: parameters,
            encoder: JSONParameterEncoder.default,
            headers: ["Content-Type": "application/json"]
        )
        .serializingData()
        .value
        
        return try JSONDecoder().decode(ChatResponse.self, from: data)
    }
    
    
}
