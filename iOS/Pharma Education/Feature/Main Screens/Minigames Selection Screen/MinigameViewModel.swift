
protocol MinigameViewModelProtocol {
    var testGames: [MinigameItem] { get }
}

final class MinigameViewModel: MinigameViewModelProtocol {
    var testGames: [MinigameItem] = [
        MinigameItem(type: .quiz,
                    imageName: "Quizzes",
                     title: "Викторины",
                     subtitle: "Проверьте свои знания с помощью коротких викторин."),
        MinigameItem(type: .match,
                     imageName: "MatchGames",
                     title: "Матчевая игра",
                     subtitle: "Сопоставьте лекарства с их применением и эффектами."),
        MinigameItem(type: .flashcards,
                     imageName: "FlashCards",
                     title: "Карточки",
                     subtitle: "Повторите ключевые понятия с помощью интерактивных карточек.")
    ]
    
}
