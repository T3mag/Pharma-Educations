import UIKit

final class MatchViewController: UIViewController {
    
    private let loadingView: LoadingView = .init(frame: .zero)
    private let contentView: MatchView = .init(frame: .zero)
    private let viewmodel: MatchViewModelProtocol
    
    init(viewmodel: MatchViewModelProtocol = MatchViewModel(), topics: [String], countQuestion: Int) {
        self.viewmodel = viewmodel
        self.viewmodel.setGameInfo(topics: topics, countQuestions: countQuestion)
        super.init(nibName: nil, bundle: nil)
        setupBindings()
    }
    
    override func loadView() {
        setupViews()
    }
    
    private func setupBindings() {
        contentView.onNextTap = { [weak self] answers in
            self?.proceedQuestion(userAnswer: answers)
        }
    }
    
    private func setupViews() {
        view = loadingView
        
        viewmodel.loadMatchQuestions { [weak self] result in
            switch result {
            case .success(_):
                self?.proceedQuestion(userAnswer: nil)
                self?.view = self?.contentView
            case .failure(_):
                self?.navigationController?.popViewController(animated: true)
            }
        }
    }
    
    private func proceedQuestion(userAnswer: [String: String]?) {
        switch viewmodel.proceed(userAnswers: userAnswer) {
        case .question(let quizQuestion):
            contentView.configure(
                currentQuestion: viewmodel.currentQuestions,
                totalQuestions: viewmodel.countQuestions,
                cards: quizQuestion)
            
        case .final(let result):
            guard var viewControllers = navigationController?.viewControllers else { return }
            
            let summaryVC = SummaryViewController(procentCorrectAnswers: result.procentCorrectAnswers)
            viewControllers.removeLast()
            viewControllers.append(summaryVC)
            
            navigationController?.setViewControllers(viewControllers, animated: true)
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
