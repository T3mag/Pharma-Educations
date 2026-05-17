import Foundation

protocol AIAssistentViewModelProtocol {
    var onMessagesChangeed: (() -> Void)? { get set }
    
    func sendMessage(message: String)
}

final class AIAssistentViewModel: AIAssistentViewModelProtocol {
    
    var onMessagesChangeed: (() -> Void)?
    private(set) var testMessages: [ChatMessage] = [] {
        didSet {
            onMessagesChangeed?()
        }
    }
    
    func sendMessage(message: String) {
        let userMessage = ChatMessage(
            text: message,
            time: currentTimeStaring(),
            isUserMessage: true
        )
        
        let botMessage = ChatMessage(
            text: "",
            time: "",
            isUserMessage: false
        )
        
        
        testMessages.append(userMessage)
        testMessages.append(botMessage)
    }
    
    private func currentTimeStaring() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: Date())
    }
}

