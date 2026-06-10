import Foundation
protocol FlashcardViewModelProtocol {
    var currentQuestions: Int { get }
    var countQuestions: Int { get }
    
    func proceed(userAnswers: Bool?) -> GameStep<Flashcard, QuizResult>
    func setGameInfo(topics: [String], countQuestions: Int)
    func loadFlashcards(completion: @escaping (Result<Void, Error>) -> Void)
}

final class FlashcardViewModel: FlashcardViewModelProtocol {
    
    private var gameService: GameServiceProtocol
    private var questions: [Flashcard] = []
    private var topicsId: [String] = []
    private(set) var countQuestions: Int = 0
    private(set) var currentQuestions: Int = 0
    private(set) var countCorrectAnswer: Int = 0
    
    func setGameInfo(topics: [String], countQuestions: Int) {
        self.topicsId = topics
        self.countQuestions = countQuestions
    }
    
    init(gameService: GameServiceProtocol = GameService()) {
        self.gameService = gameService
    }
    
    func proceed(userAnswers: Bool?) -> GameStep<Flashcard, QuizResult> {
        if let userAnswers {
            if userAnswers {
                countCorrectAnswer += 1
            }
            currentQuestions += 1
        }
        
        guard currentQuestions < questions.count else {
            return .final(QuizResult(correctAnswers: countCorrectAnswer,
                                     totalQuestions: countQuestions))
        }
        
        let task = questions[currentQuestions]

        return .question(task)
    }
    
    func loadFlashcards(completion: @escaping (Result<Void, Error>) -> Void) {
        Task {
            do {
                let questons = try await withThrowingTaskGroup(of: [Flashcard].self) { group in
                    guard countQuestions > 0, topicsId != [] else {
                        throw NSError(domain: "Нет информации", code: -1)
                    }
                    var currentQuestion = countQuestions
                    
                    while currentQuestion > 0 {
                        let requestCount = min(currentQuestion, 10)
                        
                        currentQuestion -= requestCount
                        
                        group.addTask { [gameService] in
                            let response = try await gameService.getFlashCards(
                                topicIds: self.topicsId,
                                cardsCount: requestCount
                            )
                            return response.cards
                        }
                    }
                    var allQuestions: [Flashcard] = []
                    
                    for try await questions in group {
                        allQuestions.append(contentsOf: questions)
                    }
                    
                    return allQuestions
                }
                self.questions = questons
                completion(.success(()))
            } catch {
                print(error)
                completion(.failure(error))
            }
        }
    }
}
