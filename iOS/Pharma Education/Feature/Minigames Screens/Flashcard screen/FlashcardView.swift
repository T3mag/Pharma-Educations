import UIKit

final class FlashcardView: UIView {
    
    var onUserAnswer: ((Bool) -> Void)?
    
    private var isFlipped = false
    private var frontText = ""
    private var backText = ""
    
    private let backgroundDesignView = BackgroundDesignView()
    private let flashcardCardView = FlashcardCardView()
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 20
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var titleStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = 10
        return stackView
    }()
    
    private lazy var progressStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 12
        return stackView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Карточки"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 30, weight: .bold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var subTitleLabel: UILabel = {
        let label = UILabel()
        label.text = "Изучайте препараты по карточкам"
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
    
    private lazy var modeContainerView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.isUserInteractionEnabled = false
        return view
    }()
    
    private lazy var modeBadgeView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = Colors.lavenderBlush.withAlphaComponent(0.85)
        view.isUserInteractionEnabled = false
        return view
    }()
    
    private lazy var modeImageView: UIImageView = {
        let imageView = UIImageView(image: UIImage(systemName: "arrow.left.arrow.right"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = Colors.rose
        imageView.contentMode = .scaleAspectFit
        return imageView
    }()
    
    private lazy var modeLabel: UILabel = {
        let label = UILabel()
        label.text = "Препарат ↔ Противопоказание"
        label.textColor = Colors.rose
        label.font = UIFont.systemFont(ofSize: 16, weight: .semibold)
        label.numberOfLines = 1
        return label
    }()
    
    private lazy var modeStackView: UIStackView = {
        let stackView = UIStackView(arrangedSubviews: [modeImageView, modeLabel])
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.alignment = .center
        stackView.spacing = 12
        return stackView
    }()
    
    private lazy var buttonsStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.alignment = .fill
        stackView.distribution = .fillEqually
        stackView.spacing = 20
        return stackView
    }()
    
    private lazy var unknownButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Не знаю", for: .normal)
        button.setTitleColor(Colors.rose, for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 18, weight: .bold)
        button.backgroundColor = .white
        button.layer.borderColor = Colors.rose.cgColor
        button.addTarget(self, action: #selector(unknownButtonTapped), for: .touchUpInside)
        return button
    }()
    
    private lazy var knownButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Знаю", for: .normal)
        button.setTitleColor(.white, for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 18, weight: .bold)
        button.backgroundColor = Colors.blackRose
        button.addTarget(self, action: #selector(knownButtonTapped), for: .touchUpInside)
        return button
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
        setupBindings()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        modeBadgeView.layer.cornerRadius = modeBadgeView.frame.height / 2
        unknownButton.layer.cornerRadius = unknownButton.frame.height * 0.22
        knownButton.layer.cornerRadius = knownButton.frame.height * 0.22
    }
    
    func configure(frontText: String, frontTitle: String, backText: String, backTitle: String, currentCard: Int, totalCards: Int) {
        self.frontText = frontText
        self.backText = backText
        isFlipped = false
        flashcardCardView.configure(title: frontText, hint: "Нажмите, чтобы перевернуть")
        modeLabel.text = "\(frontTitle) ↔ \(backTitle)"
        countQuestionsLabel.text = "Карточка \(currentCard + 1) из \(totalCards)"
        progressBarView.progress = Float(currentCard + 1) / Float(totalCards)
    }
    
    private func setupHierarchy() {
        addSubview(backgroundDesignView)
        addSubview(rootStackView)
        addSubview(buttonsStackView)
        
        rootStackView.addArrangedSubview(titleStackView)
        rootStackView.addArrangedSubview(progressStackView)
        rootStackView.addArrangedSubview(modeContainerView)
        modeContainerView.addSubview(modeBadgeView)
        modeBadgeView.addSubview(modeStackView)
        rootStackView.addArrangedSubview(flashcardCardView)
        
        titleStackView.addArrangedSubview(titleLabel)
        titleStackView.addArrangedSubview(subTitleLabel)
        progressStackView.addArrangedSubview(countQuestionsLabel)
        progressStackView.addArrangedSubview(progressBarView)
        
        buttonsStackView.addArrangedSubview(unknownButton)
        buttonsStackView.addArrangedSubview(knownButton)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            backgroundDesignView.topAnchor.constraint(equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            rootStackView.topAnchor.constraint(equalTo: safeAreaLayoutGuide.topAnchor, constant: 28),
            rootStackView.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor, constant: 24),
            rootStackView.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor, constant: -24),
            rootStackView.bottomAnchor.constraint(lessThanOrEqualTo: buttonsStackView.topAnchor, constant: -22),
            
            modeContainerView.heightAnchor.constraint(equalToConstant: 54),
            
            modeBadgeView.centerXAnchor.constraint(equalTo: modeContainerView.centerXAnchor),
            modeBadgeView.topAnchor.constraint(equalTo: modeContainerView.topAnchor),
            modeBadgeView.bottomAnchor.constraint(equalTo: modeContainerView.bottomAnchor),
            modeBadgeView.leadingAnchor.constraint(greaterThanOrEqualTo: modeContainerView.leadingAnchor),
            modeBadgeView.trailingAnchor.constraint(lessThanOrEqualTo: modeContainerView.trailingAnchor),
            
            modeStackView.topAnchor.constraint(equalTo: modeBadgeView.topAnchor, constant: 12),
            modeStackView.leadingAnchor.constraint(equalTo: modeBadgeView.leadingAnchor, constant: 18),
            modeStackView.trailingAnchor.constraint(equalTo: modeBadgeView.trailingAnchor, constant: -18),
            modeStackView.bottomAnchor.constraint(equalTo: modeBadgeView.bottomAnchor, constant: -12),
            
            modeImageView.widthAnchor.constraint(equalToConstant: 24),
            modeImageView.heightAnchor.constraint(equalToConstant: 24),
            
            flashcardCardView.heightAnchor.constraint(greaterThanOrEqualToConstant: 360),
            
            buttonsStackView.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor, constant: 24),
            buttonsStackView.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor, constant: -24),
            buttonsStackView.bottomAnchor.constraint(equalTo: safeAreaLayoutGuide.bottomAnchor, constant: -24),
            buttonsStackView.heightAnchor.constraint(equalToConstant: 60)
        ])
    }
    
    private func setupBindings() {
        flashcardCardView.onTap = { [weak self] in
            self?.flipCard()
        }
    }
    
    private func flipCard() {
        isFlipped.toggle()
        let nextText = isFlipped ? backText : frontText
        let nextHint = isFlipped ? "Нажмите, чтобы вернуться" : "Нажмите, чтобы перевернуть"
        flashcardCardView.flip(to: nextText, hint: nextHint)
    }
    
    @objc private func unknownButtonTapped() {
        onUserAnswer?(false)
    }
    
    @objc private func knownButtonTapped() {
        onUserAnswer?(true)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
