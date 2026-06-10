import UIKit

final class SummaryViewController: UIViewController {
    private let contentView: SummaryView = .init(frame: .zero)
    private var viewModel: SummaryViewModelProtocol
    private let firestoreService: FirestoreServiceProtocol
    private let userService: UserServiceProtocol
    private var didTrackCompletedGame = false
    
    override func loadView() {
        view = contentView
        navigationController?.setNavigationBarHidden(true, animated: false)
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        trackCompletedGameIfNeeded()
    }
    
    init(
        viewModel: SummaryViewModelProtocol = SummaryViewModel(),
        firestoreService: FirestoreServiceProtocol = FirestoreService.shared,
        userService: UserServiceProtocol = UserService.shared,
        countCorrectAnswers: Int,
        countQuestions: Int
    ) {
        self.viewModel = viewModel
        self.firestoreService = firestoreService
        self.userService = userService
        super.init(nibName: nil, bundle: nil)
        let motivation = self.viewModel.getMotivationFromCount(correctAnswers: countCorrectAnswers,
                                     totalAnswers: countQuestions)
        contentView.configureInfoInCount(correctQuestions: countCorrectAnswers,
                                  totalQuesitions: countQuestions,
                                  motivation: motivation)
        setupActions()
    }
    
    init(
        viewModel: SummaryViewModelProtocol = SummaryViewModel(),
        firestoreService: FirestoreServiceProtocol = FirestoreService.shared,
        userService: UserServiceProtocol = UserService.shared,
        procentCorrectAnswers: Double
    ) {
        self.viewModel = viewModel
        self.firestoreService = firestoreService
        self.userService = userService
        super.init(nibName: nil, bundle: nil)
        let motivation = self.viewModel.getMotivationFromProcent(procentCorrectAnswer: procentCorrectAnswers)
        contentView.configureInfoInProcent(procentCorrectQuestions: procentCorrectAnswers,
                                           motivation: motivation)
        setupActions()
    }
    
    private func setupActions() {
        contentView.onExitTap = { [weak self] in
            self?.navigationController?.popToRootViewController(animated: true)
        }
        contentView.onRepeatTap = { [weak self] in
            self?.navigationController?.popViewController(animated: true)
        }
    }

    private func trackCompletedGameIfNeeded() {
        guard !didTrackCompletedGame else { return }

        let userId = userService.userId
        guard !userId.isEmpty else { return }

        didTrackCompletedGame = true

        Task {
            do {
                try await firestoreService.incrementGamesCount(uid: userId)
            } catch {
                print(error)
            }
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
