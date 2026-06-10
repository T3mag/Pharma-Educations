
protocol SummaryViewModelProtocol {
    typealias Motivation = (titleString: String, subtitleString: String)
    
    func getMotivationFromProcent(procentCorrectAnswer: Double) -> Motivation
    func getMotivationFromCount(correctAnswers: Int, totalAnswers: Int) -> Motivation
}

final class SummaryViewModel: SummaryViewModelProtocol {
    typealias Motivation = (titleString: String, subtitleString: String)
    
    func getMotivationFromProcent(procentCorrectAnswer: Double) -> Motivation {
        let percentageOfCorrect = procentCorrectAnswer / Double(100)
        
        return getMotivation(percentageOfCorrect: percentageOfCorrect)
    }
    
    func getMotivationFromCount(correctAnswers: Int, totalAnswers: Int) -> Motivation {
        let percentageOfCorrect = Double(correctAnswers) / Double(totalAnswers)
        
        return getMotivation(percentageOfCorrect: percentageOfCorrect)
    }
    
    func getMotivation(percentageOfCorrect: Double) -> Motivation {
        var title = ""
        var subTitle = ""
        
        if percentageOfCorrect > 0.85 {
            title = "Отлично"
            subTitle = "Ты большой молодец! Старайся в том же духе"
        } else if percentageOfCorrect > 0.7 {
            title = "Хорошо"
            subTitle = "Супер! Но тебе есть куда рости!"
        } else if percentageOfCorrect > 0.56 {
            title = "Не плохо"
            subTitle = "Подножми и все получится :)"
        } else {
            title = "Не очень"
            subTitle = "Мы знаем, что ты можешь гораздо больше!"
        }
        
        return (titleString: title, subtitleString: subTitle)
    }
}
