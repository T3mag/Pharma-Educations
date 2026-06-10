import UIKit

final class FlashcardViewController: UIViewController {
    
    private let loadingView: LoadingView = .init(frame: .zero)
    private let contentView = FlashcardView(frame: .zero)
    private let viewmodel: FlashcardViewModelProtocol
    
    init(viewmodel: FlashcardViewModelProtocol = FlashcardViewModel(), topics: [String], countQuestion: Int) {
        self.viewmodel = viewmodel
        self.viewmodel.setGameInfo(topics: topics, countQuestions: countQuestion)
        super.init(nibName: nil, bundle: nil)
        setupActions()
    }
    
    override func loadView() {
        setupViews()
    }
    
    private func setupViews() {
        view = loadingView
        
        viewmodel.loadFlashcards { [weak self] result in
            switch result {
            case .success(_):
                self?.proceedQuestion(userAnswerIsCorrect: nil)
                self?.view = self?.contentView
            case .failure(_):
                self?.navigationController?.popViewController(animated: true)
            }
        }
    }
    
    private func setupActions() {
        contentView.onUserAnswer = {[weak self] bool in
            self?.proceedQuestion(userAnswerIsCorrect: bool)
        }
    }
    
    private func proceedQuestion(userAnswerIsCorrect: Bool?) {
        switch viewmodel.proceed(userAnswers: userAnswerIsCorrect) {
        case .question(let flashcard):
            contentView.configure(frontText: flashcard.front,
                                  frontTitle: flashcard.frontTitle,
                                  backText: flashcard.back,
                                  backTitle: flashcard.backTitle,
                                  currentCard: viewmodel.currentQuestions,
                                  totalCards: viewmodel.countQuestions)
        case .final(let result):
            guard var viewControllers = navigationController?.viewControllers else { return }

            let summaryVC = SummaryViewController(countCorrectAnswers: result.correctAnswers, countQuestions: result.totalQuestions)
            viewControllers.removeLast()
            viewControllers.append(summaryVC)

            navigationController?.setViewControllers(viewControllers, animated: true)
        }
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        navigationController?.setNavigationBarHidden(true, animated: animated)
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        navigationController?.setNavigationBarHidden(false, animated: animated)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
