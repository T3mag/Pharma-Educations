import UIKit

final class PharmacyFinishViewController: UIViewController {
    
    private let contentView: PharmacyFinishView
    private let firestoreService: FirestoreServiceProtocol
    private let userService: UserServiceProtocol
    private var didTrackCompletedSimulator = false
    
    init(
        feedbacks: [UserAnswerResponse?],
        customers: [Customer],
        firestoreService: FirestoreServiceProtocol = FirestoreService.shared,
        userService: UserServiceProtocol = UserService.shared
    ) {
        self.contentView = PharmacyFinishView(
            results: PharmacyFinishViewController.makeResults(
                feedbacks: feedbacks,
                customers: customers
            )
        )
        self.firestoreService = firestoreService
        self.userService = userService
        super.init(nibName: nil, bundle: nil)
        setupActions()
    }
    
    override func loadView() {
        view = contentView
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        trackCompletedSimulatorIfNeeded()
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        navigationController?.setNavigationBarHidden(true, animated: animated)
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        navigationController?.setNavigationBarHidden(false, animated: animated)
    }
    
    private func setupActions() {
        contentView.onNewShiftTap = { [weak self] in
            self?.popToStartScreen()
        }
        
        contentView.onScenariosTap = { [weak self] in
            self?.navigationController?.popToRootViewController(animated: true)
        }
    }
    
    private func popToStartScreen() {
        guard let navigationController else { return }
        
        if let startViewController = navigationController.viewControllers.first(where: { $0 is SimulatorStartViewController }) {
            navigationController.popToViewController(startViewController, animated: true)
        } else {
            navigationController.popToRootViewController(animated: true)
        }
    }

    private func trackCompletedSimulatorIfNeeded() {
        guard !didTrackCompletedSimulator else { return }

        let userId = userService.userId
        guard !userId.isEmpty else { return }

        didTrackCompletedSimulator = true

        Task {
            do {
                try await firestoreService.incrementSimulatorsCount(uid: userId)
            } catch {
                print(error)
            }
        }
    }
    
    private static func makeResults(
        feedbacks: [UserAnswerResponse?],
        customers: [Customer]
    ) -> [PharmacyFinishClientResult] {
        customers.enumerated().map { index, customer in
            let feedback = feedbacks.indices.contains(index) ? feedbacks[index] : nil
            
            return PharmacyFinishClientResult(
                title: makeTitle(customer: customer),
                subtitle: makeSubtitle(customer: customer),
                score: feedback?.score ?? 0,
                feedback: feedback?.feedback ?? "Фидбек не получен",
                recommendedAnswer: feedback?.recommendedAnswer ?? "Рекомендованный ответ не получен"
            )
        }
    }
    
    private static func makeTitle(customer: Customer) -> String {
        "\(formattedGender(customer.bio.gender)), \(customer.bio.age)"
    }
    
    private static func makeSubtitle(customer: Customer) -> String {
        if let fact = customer.facts.first, !fact.isEmpty {
            return fact
        }
        
        return customer.bio.context
    }
    
    private static func formattedGender(_ gender: String) -> String {
        guard let firstCharacter = gender.first else { return gender }
        return firstCharacter.uppercased() + gender.dropFirst()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
