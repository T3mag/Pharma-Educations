
import UIKit

final class QuizView: UIView {
    
    var onNextTap: ((_ answer: String) -> Void)?
    private var answerViews: [AnswerView] = []
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 30
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var titleStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = 10
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var progresStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 10
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var quizStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 15
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private let backgroundDesignView = BackgroundDesignView()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Викторина"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 30, weight: .bold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var subTitleLabel: UILabel = {
        let label = UILabel()
        label.text = "Выберите правильный ответ"
        label.textColor = .gray
        label.font = UIFont.systemFont(ofSize: 15, weight: .semibold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var countQuestionsLabel: UILabel = {
        let label = UILabel()
        label.textColor = Colors.rose
        label.font = UIFont.systemFont(ofSize: 13, weight: .semibold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var progressBarView: UIProgressView = {
        let progressView = UIProgressView(progressViewStyle: .default)
        progressView.translatesAutoresizingMaskIntoConstraints = false
        progressView.progressTintColor = Colors.rose
        progressView.trackTintColor = Colors.softPink
        progressView.transform = CGAffineTransform(scaleX: 1, y: 3)
        return progressView
    }()
    
    private lazy var nextButton: UIButton = {
        let button = UIButton()
        button.setTitle("Продолжить", for: .normal)
        button.backgroundColor = Colors.blackRose
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(nextButtonTap), for: .touchUpInside)
        return button
    }()
    
    private lazy var questionView: QuestionView = {
        let view = QuestionView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        
        nextButton.layer.cornerRadius = nextButton.frame.height * 0.2
        nextButton.clipsToBounds = true
    }
    
    func configure(question: QuizQuestion, currentQuestion: Int, totalQuestions: Int) {
        questionView.setupText(text: question.question)
        
        answerViews.forEach { answerView in
            quizStackView.removeArrangedSubview(answerView)
            answerView.removeFromSuperview()
        }

        answerViews.removeAll()
        
        for answer in question.options {
            let view = AnswerView()
            view.translatesAutoresizingMaskIntoConstraints = false
            view.configureTitle(title: answer)
            
            view.onCheckTap = { [weak self, weak view] in
                guard let self, let selectedView = view else { return }
                
                self.answerViews.forEach { view in
                    view.setCheck(view == selectedView)
                }
            }
            answerViews.append(view)
            quizStackView.addArrangedSubview(view)
        }
        
        countQuestionsLabel.text = "Вопрос \(currentQuestion + 1) из \(totalQuestions)"
        progressBarView.progress = Float(currentQuestion + 1) / Float(totalQuestions)
        
    }
    
    private func setupHierarchy() {
        addSubview(backgroundDesignView)
        addSubview(rootStackView)
        addSubview(nextButton)
        
        rootStackView.addArrangedSubview(titleStackView)
        rootStackView.addArrangedSubview(progresStackView)
        rootStackView.addArrangedSubview(quizStackView)
        
        titleStackView.addArrangedSubview(titleLabel)
        titleStackView.addArrangedSubview(subTitleLabel)
        progresStackView.addArrangedSubview(countQuestionsLabel)
        progresStackView.addArrangedSubview(progressBarView)
        quizStackView.addArrangedSubview(questionView)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            backgroundDesignView.topAnchor.constraint(equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            rootStackView.topAnchor.constraint(equalTo: safeAreaLayoutGuide.topAnchor, constant: 20),
            rootStackView.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor, constant: 20),
            rootStackView.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor, constant: -20),
            rootStackView.bottomAnchor.constraint(lessThanOrEqualTo: nextButton.topAnchor, constant: 20),
            
            nextButton.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor, constant: 20),
            nextButton.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor, constant: -20),
            nextButton.bottomAnchor.constraint(equalTo: safeAreaLayoutGuide.bottomAnchor, constant: -20),
            nextButton.heightAnchor.constraint(equalToConstant: 70)
        ])
    }
    
    @objc
    private func nextButtonTap() {
        for view in answerViews {
            if view.isChecked {
                onNextTap?(view.answerLabel.text ?? "")
            }
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}

