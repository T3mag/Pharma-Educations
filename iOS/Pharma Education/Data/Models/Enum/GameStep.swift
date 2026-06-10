
enum GameStep<Question, Result> {
    case question(Question)
    case final(Result)
}

struct QuizResult {
    let correctAnswers: Int
    let totalQuestions: Int
}

struct MatchResult {
    let procentCorrectAnswers: Double
}
