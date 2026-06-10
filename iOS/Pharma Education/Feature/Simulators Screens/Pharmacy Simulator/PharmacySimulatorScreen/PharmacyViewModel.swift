import Foundation

protocol PharmacyViewModelProtocol {
    var feedbackResponses: [UserAnswerResponse?] { get }
    var customers: [Customer] { get }
    var currentClientNumber: Int { get }
    var totalClientsCount: Int { get }
    
    func configureCustomersCount(_ count: Int)
    func loadCustomers(completion: @escaping (Result<Void, Error>) -> Void)
    func proceed(userAnswer: String?) -> GameStep<Customer, QuizResult>
    func proceedAfterTimeout() -> GameStep<Customer, QuizResult>
    func waitForFeedbackResponses() async -> [UserAnswerResponse?]
}

final class PharmacyViewModel: PharmacyViewModelProtocol {
    
    private var gameService: GameServiceProtocol
    private(set) var customers: [Customer] = []
    private var countCustommers: Int = 2
    private(set) var currentCustommers: Int = 0
    private(set) var feedbackResponses: [UserAnswerResponse?] = []
    private var feedbackTasks: [Task<UserAnswerResponse?, Never>] = []
    
    var currentClientNumber: Int {
        guard !customers.isEmpty else { return 0 }
        return min(currentCustommers + 1, customers.count)
    }
    
    var totalClientsCount: Int {
        customers.count
    }
    
    init(gameService: GameServiceProtocol = GameService()) {
        self.gameService = gameService
    }
    
    func configureCustomersCount(_ count: Int) {
        countCustommers = max(1, count)
    }
    
    func proceed(userAnswer: String?) -> GameStep<Customer, QuizResult> {
        if let userAnswer {
            guard currentCustommers < customers.count else {
                return makeFinalResult()
            }
            
            let customer = customers[currentCustommers]
            requestFeedback(
                scenarioId: customer.scenarioId,
                userAnswer: userAnswer
            )
            currentCustommers += 1
        }
        
        guard currentCustommers < customers.count else {
            return makeFinalResult()
        }
        
        return .question(customers[currentCustommers])
    }

    func proceedAfterTimeout() -> GameStep<Customer, QuizResult> {
        guard currentCustommers < customers.count else {
            return makeFinalResult()
        }

        feedbackResponses.append(nil)
        currentCustommers += 1

        guard currentCustommers < customers.count else {
            return makeFinalResult()
        }

        return .question(customers[currentCustommers])
    }
    
    private func requestFeedback(scenarioId: String, userAnswer: String) {
        let feedbackIndex = feedbackResponses.count
        feedbackResponses.append(nil)
        
        let task: Task<UserAnswerResponse?, Never> = Task { [weak self, gameService] in
            do {
                let response = try await gameService.getFeedbackByUserAnswer(
                    scenarioId: scenarioId,
                    userAnswer: userAnswer
                )
                
                await MainActor.run {
                    self?.feedbackResponses[feedbackIndex] = response
                }
                
                return response
            } catch {
                print(error)
                return nil
            }
        }
        
        feedbackTasks.append(task)
    }
    
    func waitForFeedbackResponses() async -> [UserAnswerResponse?] {
        for task in feedbackTasks {
            _ = await task.value
        }
        
        return feedbackResponses
    }
    
    private func makeFinalResult() -> GameStep<Customer, QuizResult> {
        .final(QuizResult(
            correctAnswers: 0,
            totalQuestions: feedbackResponses.count
        ))
    }
    
    func loadCustomers(completion: @escaping (Result<Void, Error>) -> Void) {
        Task{
            do {
                let customers = try await withThrowingTaskGroup(of: [Customer].self) { group in
                    guard countCustommers > 0 else {
                        throw NSError(domain: "Нет информации", code: -1)
                    }
                    var currentQuestion = countCustommers
                    
                    while currentQuestion > 0 {
                        let requestCount = min(currentQuestion, 10)
                        
                        currentQuestion -= requestCount
                        
                        group.addTask { [gameService] in
                            let response = try await gameService.getCustomers(customersCount: requestCount)
                            return response.customers
                        }
                    }
                    var allQuestions: [Customer] = []
                    
                    for try await questions in group {
                        allQuestions.append(contentsOf: questions)
                    }
                    
                    return allQuestions
                }
                self.customers = customers
                completion(.success(()))
            } catch {
                completion(.failure(error))
            }
        }
    }
}
