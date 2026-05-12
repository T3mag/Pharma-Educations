import Foundation

final class AIAssistentViewModel {
    
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
        print(testMessages)
    }
    
    private func currentTimeStaring() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: Date())
    }
}

