import UIKit

enum Texts {
    enum LevelView {
        static let level = "Уровень"
        static let exp = "XP"
        static let motivation = "Занимайся больше и улучшай свой уровень!"
    }
    
    enum Errors {
        static let unknownError = "Что-то пошло не так, попробуйте позже"
        static let emptyString = "Поля не должны быть пустыми"
        static let invalidEmail = "Некорректный email"
        static let passwordNoMatched = "Пароли не совпадают"
    }
    
    enum TabBar {
        static let simulatorTitle = "Симуляторы"
        static let simulatorIcon = "cross.case"
        static let selectedeSimulatorIcon = "cross.case.fill"
        
        static let gamesAndTestsTitle = "Игры и тесты"
        static let gamesAndTestsIcon = "checklist"
        static let selectedGamesAndTestsIcon = "checklist"
        
        static let chatWithAiTitile = "AI ассистент"
        static let chatWithAIIcon = "bubble.left.and.bubble.right"
        static let selectedChatWithAiIcon = "bubble.left.and.bubble.right.fill"
        
        static let accountTitle = "Аккаунт"
        static let accountIcon = "person.crop.circle"
        static let selectedAccountIcon = "person.crop.circle.fill"
        
    }
}

