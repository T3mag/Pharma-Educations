import Foundation

protocol QuizViewModelProtocol {
    var onFinal: (() -> Void)? {get set}
    var countQuestions: Int { get }
    var currentQuestions: Int { get }
    
    func proceed(userAnswer: String?) -> GameStep<QuizQuestion, QuizResult>
    func setGameInfo(topics: [String], countQuestions: Int)
    func loadQuizQuestions(completion: @escaping (Result<Void, Error>) -> Void)
}

final class QuizViewModel: QuizViewModelProtocol {
    
    var onFinal: (() -> Void)?
    
    private var topics: [String] = []
    private var questions: [QuizQuestion] = []
    private var gameService: GameServiceProtocol
    private(set) var countQuestions: Int = 0
    private(set) var currentQuestions: Int = 0
    private(set) var countCorrectAnswer: Int = 0
    
    init(gameService: GameServiceProtocol = GameService()) {
        self.gameService = gameService
    }
    
    func setGameInfo(topics: [String], countQuestions: Int) {
        self.topics = topics
        self.countQuestions = countQuestions
    }
    
    func proceed(userAnswer: String? = nil) -> GameStep<QuizQuestion, QuizResult> {
        if let userAnswer {
            checkCorrectAnswer(userAnswer: userAnswer)
            currentQuestions += 1
        }
        
        guard currentQuestions < questions.count else {
            return .final(QuizResult(correctAnswers: countCorrectAnswer,
                          totalQuestions: questions.count))
        }
        
        return .question(questions[currentQuestions])
    }
    
    private func checkCorrectAnswer(userAnswer: String) {
        let correctAnswer = questions[currentQuestions].correctAnswer
        if userAnswer == correctAnswer {
            countCorrectAnswer += 1
        }
    }
    
    func loadQuizQuestions(completion: @escaping (Result<Void, Error>) -> Void) {
        Task {
            do {
                let questons = try await withThrowingTaskGroup(of: [QuizQuestion].self) { group in
                    guard countQuestions > 0, topics != [] else {
                        throw NSError(domain: "Нет информации", code: -1)
                    }
                    var currentQuestion = countQuestions
                    
                    while currentQuestion > 0 {
                        let requestCount = min(currentQuestion, 10)
                        
                        currentQuestion -= requestCount
                        
                        group.addTask { [gameService] in
                            let response = try await gameService.getQuiz(
                                topicIds: self.topics,
                                questionCount: requestCount
                            )
                            return response.questions
                        }
                    }
                    var allQuestions: [QuizQuestion] = []
                    
                    for try await questions in group {
                        allQuestions.append(contentsOf: questions)
                    }
                    
                    return allQuestions
                }
                self.questions = questons
                completion(.success(()))
            } catch {
                completion(.failure(error))
            }
        }
    }
}
