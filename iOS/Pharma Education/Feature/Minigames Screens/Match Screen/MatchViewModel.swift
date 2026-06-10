import Foundation

protocol MatchViewModelProtocol {
    typealias MatchStep = GameStep<(left: [MatchItem], right: [MatchItem]), MatchResult>
    
    var countQuestions: Int { get }
    var currentQuestions: Int { get }
    var currentPercent: Double { get }
    
    func proceed(userAnswers: [String: String]?) -> MatchStep
    func loadMatchQuestions(completion: @escaping (Result<Void, Error>) -> Void)
    func setGameInfo(topics: [String], countQuestions: Int)
}

final class MatchViewModel: MatchViewModelProtocol {
    typealias MatchStep = GameStep<(left: [MatchItem], right: [MatchItem]), MatchResult>
    
    private var taskPercents: [Double] = []
    private var gameService: GameServiceProtocol
    private var topicsId: [String] = []
    private var questions: [MatchTask] = []
    private(set) var countQuestions: Int = 0
    private(set) var currentQuestions: Int = 0
    private(set) var countCorrectAnswer: Int = 0
    var currentPercent: Double {
        guard !taskPercents.isEmpty else { return 0 }

        let sum = taskPercents.reduce(0, +)
        return sum / Double(taskPercents.count)
    }
    
    init(gameService: GameServiceProtocol = GameService()) {
        self.gameService = gameService
    }
    
    func setGameInfo(topics: [String], countQuestions: Int) {
        self.topicsId = topics
        self.countQuestions = countQuestions
    }
    
    func proceed(userAnswers: [String: String]?) -> MatchStep {
        if let userAnswers {
            checkAnswers(userAnswers)
            currentQuestions += 1
        }
        
        guard currentQuestions < questions.count else {
            return .final(MatchResult(procentCorrectAnswers: currentPercent))
        }
        
        let task = questions[currentQuestions]
        
        let leftItems = task.pairs.map {
            MatchItem(id: $0.id, title: $0.left)
        }.shuffled()

        let rightItems = task.pairs.map {
            MatchItem(id: $0.id, title: $0.right)
        }.shuffled()

        return .question((left: leftItems, right: rightItems))
    }
    
    private func checkAnswers(_ userAnswers: [String: String]) {
        guard questions.indices.contains(currentQuestions) else { return }

        let task = questions[currentQuestions]

        var correctCount = 0

        for pair in task.pairs {
            if userAnswers[pair.id] == pair.id {
                correctCount += 1
            }
        }

        let percent = Double(correctCount) / Double(task.pairs.count) * 100
        taskPercents.append(percent)
    }
    
    func loadMatchQuestions(completion: @escaping (Result<Void, Error>) -> Void) {
        Task {
            do {
                let questons = try await withThrowingTaskGroup(of: [MatchTask].self) { group in
                    guard countQuestions > 0, topicsId != [] else {
                        throw NSError(domain: "Нет информации", code: -1)
                    }
                    var currentQuestion = countQuestions
                    
                    while currentQuestion > 0 {
                        let requestCount = min(currentQuestion, 10)
                        
                        currentQuestion -= requestCount
                        
                        group.addTask { [gameService] in
                            let response = try await gameService.getMatch(
                                topicIds: self.topicsId,
                                pairCount: requestCount
                            )
                            return response.tasks
                        }
                    }
                    var allQuestions: [MatchTask] = []
                    
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
