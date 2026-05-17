
protocol MinigameViewModelProtocol {
    var testGames: [MinigameItem] { get }
}

final class MinigameViewModel: MinigameViewModelProtocol {
    var testGames: [MinigameItem] = [
        MinigameItem(imageName: "Quizzes", title: "Викторины", subtitle: "Проверьте свои знания с помощью коротких викторин."),
        MinigameItem(imageName: "MatchGames", title: "Матчевая игра", subtitle: "Сопоставьте лекарства с их применением и эффектами."),
        MinigameItem(imageName: "FlashCards", title: "Карточки", subtitle: "Повторите ключевые понятия с помощью интерактивных карточек."),
        MinigameItem(imageName: "FindError", title: "Найдите ошибку", subtitle: "Выявляйте ошибки в рецептах."),
        MinigameItem(imageName: "DrugMemory", title: "Память о лекарствах", subtitle: "Улучшите память, сопоставляя пары."),
        MinigameItem(imageName: "Time Challenge", title: "Вызов времени", subtitle: "Отвечайте на вопросы на время.")
    ]
    
}
