import Foundation
import UIKit

protocol AIAssistantViewModelProtocol {
    var testMessages: [ChatMessage] { get set }
    var onMessageAdd: ((IndexPath) -> Void)? { get set }
    var onMessageUpdate: (() -> Void)? { get set }
    
    func sendMessage(message: String)
}

final class AIAssistantViewModel: AIAssistantViewModelProtocol {
    
    private var updatedMessageFlag = false
    private var firestoreService: FirestoreServiceProtocol
    private var userService: UserServiceProtocol
    var onMessageUpdate: (() -> Void)?
    var onMessageAdd: ((IndexPath) -> Void)?
    var testMessages: [ChatMessage] = [] {
        didSet {
            let indexPath = IndexPath(row: testMessages.count, section: 0)
            if updatedMessageFlag {
                onMessageUpdate?()
            } else {
                onMessageAdd?(indexPath)
            }
        }
    }
    
    init(firestoreService: FirestoreServiceProtocol = FirestoreService.shared,
         userService: UserServiceProtocol = UserService.shared) {
        self.firestoreService = firestoreService
        self.userService = userService
    }
    
    func sendMessage(message: String) {
        let userMessage = ChatMessage(
            text: message,
            time: currentTimeString(),
            isUserMessage: true
        )
        
        let botMessage = ChatMessage(
            text: "", time: "", isUserMessage: false
        )
        
        Task {
            try await firestoreService.incrementRequestCount(uid: userService.userId)
        }
        testMessages.append(userMessage)
        testMessages.append(botMessage)
        
        
        Task {
            do {
                let response = try await AIAssistantService().sendMessage(message)
                
                let botMessage = ChatMessage(
                    text: response.answer,
                    time: currentTimeString(),
                    isUserMessage: false
                )
                updatedMessageFlag = true
                
                guard !self.testMessages.isEmpty else {
                    return
                }
                self.testMessages[self.testMessages.count - 1] = botMessage
            } catch {
                let errorMessage = ChatMessage(
                    text: error.localizedDescription,
                    time: currentTimeString(),
                    isUserMessage: false
                )
                self.testMessages.append(errorMessage)
            }
        }
        updatedMessageFlag = false
        
    }
    
    private func currentTimeString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: Date())
    }
}

