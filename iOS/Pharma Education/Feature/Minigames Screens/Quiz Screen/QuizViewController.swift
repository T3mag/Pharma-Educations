
import UIKit

final class QuizViewController: UIViewController {
    
    private let loadingView: LoadingView = .init(frame: .zero)
    private let contentView: QuizView = .init(frame: .zero)
    private var viewmodel: QuizViewModelProtocol
    
    override func loadView() {
        setupViews()
    }
    
    init(viewmodel: QuizViewModelProtocol = QuizViewModel(), topics: [String], countQuestion: Int) {
        self.viewmodel = viewmodel
        self.viewmodel.setGameInfo(topics: topics, countQuestions: countQuestion)
        super.init(nibName: nil, bundle: nil)
        setupBindings()
    }
    
    private func setupBindings() {
        contentView.onNextTap = { [weak self] answer in
            self?.proceedQuestion(userAnswer: answer)
        }
    }
    
    private func setupViews() {
        view = loadingView
        
        viewmodel.loadQuizQuestions { [weak self] result in
            switch result {
            case .success(_):
                self?.proceedQuestion(userAnswer: nil)
                self?.view = self?.contentView
            case .failure(_):
                self?.navigationController?.popViewController(animated: true)
            }
        }
        
    }
    
    private func proceedQuestion(userAnswer: String?) {
        switch viewmodel.proceed(userAnswer: userAnswer) {
        case .question(let quizQuestion):
            contentView.configure(question: quizQuestion,
                                  currentQuestion: viewmodel.currentQuestions,
                                  totalQuestions: viewmodel.countQuestions)
        case .final(let result):
            guard var viewControllers = navigationController?.viewControllers else { return }

            let summaryVC = SummaryViewController(countCorrectAnswers: result.correctAnswers, countQuestions: result.totalQuestions)
            viewControllers.removeLast()
            viewControllers.append(summaryVC)

            navigationController?.setViewControllers(viewControllers, animated: true)
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
