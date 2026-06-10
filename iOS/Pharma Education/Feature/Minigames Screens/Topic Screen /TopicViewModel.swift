
import Foundation

protocol TopicViewModelProtocol {
    var topics: [TopicNode] { get }
    var onTopicsLoaded: (() -> Void)? { get set }
    var onError: ((String) -> Void)? { get set }
    
    func loadTopics()
}

final class TopicViewModel: TopicViewModelProtocol {
    private let gameService: GameService
    
    var topics: [TopicNode] = []
    var onTopicsLoaded: (() -> Void)?
    var onError: ((String) -> Void)?
    
    init(gameService: GameService = GameService()) {
        self.gameService = gameService
    }
    
    func loadTopics() {
        Task {
            do {
                let response  = try await gameService.getTopic()
                
                await MainActor.run {
                    self.topics = response.topics
                    self.onTopicsLoaded?()
                }
            } catch {
                onError?(error.localizedDescription)
            }
        }
    }
}
