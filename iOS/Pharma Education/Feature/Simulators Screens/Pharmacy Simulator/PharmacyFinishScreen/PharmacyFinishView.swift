import UIKit

final class PharmacyFinishView: UIView {
    
    var onNewShiftTap: (() -> Void)?
    var onScenariosTap: (() -> Void)?
    
    private let results: [PharmacyFinishClientResult]
    private let averageScore: Int
    
    private lazy var backgroundImageView: UIImageView = {
        let imageView = UIImageView(image: UIImage(named: "pharmacy_background"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.contentMode = .scaleAspectFill
        imageView.clipsToBounds = true
        return imageView
    }()
    
    private let backgroundDesignView = BackgroundDesignView()
    
    private lazy var dimView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = Colors.lavenderBlush.withAlphaComponent(0.34)
        return view
    }()
    
    private lazy var scrollView: UIScrollView = {
        let scrollView = UIScrollView()
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        scrollView.showsVerticalScrollIndicator = false
        return scrollView
    }()
    
    private lazy var contentView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "Смена\nзавершена!"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 42, weight: .bold)
        label.numberOfLines = 0
        return label
    }()
    
    private lazy var subtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "Итоги вашей работы за смену"
        label.textColor = .darkGray
        label.font = UIFont.systemFont(ofSize: 20, weight: .regular)
        return label
    }()
    
    private lazy var ratingView = PharmacyFinishRatingView(score: averageScore)
    private lazy var clientsCardView: UIView = makeCardView(cornerRadius: 22)
    
    private lazy var clientsTitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "Клиенты"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 26, weight: .bold)
        return label
    }()
    
    private lazy var clientsListView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .white.withAlphaComponent(0.72)
        view.layer.borderWidth = 1
        view.layer.borderColor = UIColor.systemGray5.cgColor
        view.layer.cornerRadius = 16
        view.clipsToBounds = true
        return view
    }()
    
    private lazy var clientsStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.spacing = 0
        return stackView
    }()
    
    private lazy var buttonsStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.distribution = .fillEqually
        stackView.spacing = 16
        return stackView
    }()
    
    private lazy var newShiftButton: UIButton = makeActionButton(
        title: "Новая смена",
        backgroundColor: .white,
        titleColor: Colors.blackRose,
        selector: #selector(newShiftButtonTapped)
    )
    
    private lazy var scenariosButton: UIButton = makeActionButton(
        title: "К сценариям",
        backgroundColor: Colors.blackRose,
        titleColor: .white,
        selector: #selector(scenariosButtonTapped)
    )
    
    init(results: [PharmacyFinishClientResult]) {
        self.results = results
        self.averageScore = PharmacyFinishView.calculateAverageScore(results: results)
        super.init(frame: .zero)
        setupHierarchy()
        setupLayout()
        setupClients()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        newShiftButton.layer.cornerRadius = newShiftButton.bounds.height * 0.18
        scenariosButton.layer.cornerRadius = scenariosButton.bounds.height * 0.18
    }
    
    private func setupHierarchy() {
        addSubview(backgroundImageView)
        addSubview(dimView)
        addSubview(backgroundDesignView)
        addSubview(scrollView)
        
        scrollView.addSubview(contentView)
        contentView.addSubview(titleLabel)
        contentView.addSubview(subtitleLabel)
        contentView.addSubview(ratingView)
        contentView.addSubview(clientsCardView)
        contentView.addSubview(buttonsStackView)
        
        clientsCardView.addSubview(clientsTitleLabel)
        clientsCardView.addSubview(clientsListView)
        clientsListView.addSubview(clientsStackView)
        
        buttonsStackView.addArrangedSubview(newShiftButton)
        buttonsStackView.addArrangedSubview(scenariosButton)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            backgroundImageView.topAnchor.constraint(equalTo: topAnchor),
            backgroundImageView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundImageView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundImageView.heightAnchor.constraint(equalTo: heightAnchor, multiplier: 0.48),
            
            dimView.topAnchor.constraint(equalTo: topAnchor),
            dimView.leadingAnchor.constraint(equalTo: leadingAnchor),
            dimView.trailingAnchor.constraint(equalTo: trailingAnchor),
            dimView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            backgroundDesignView.topAnchor.constraint(equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            scrollView.topAnchor.constraint(equalTo: topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            contentView.topAnchor.constraint(equalTo: scrollView.contentLayoutGuide.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.contentLayoutGuide.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.frameLayoutGuide.widthAnchor),
            
            titleLabel.topAnchor.constraint(equalTo: contentView.safeAreaLayoutGuide.topAnchor, constant: 40),
            titleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 24),
            titleLabel.trailingAnchor.constraint(lessThanOrEqualTo: contentView.trailingAnchor, constant: -24),
            
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 18),
            subtitleLabel.leadingAnchor.constraint(equalTo: titleLabel.leadingAnchor),
            subtitleLabel.trailingAnchor.constraint(lessThanOrEqualTo: contentView.trailingAnchor, constant: -24),
            
            ratingView.topAnchor.constraint(equalTo: subtitleLabel.bottomAnchor, constant: 34),
            ratingView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 22),
            ratingView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -22),
            
            clientsCardView.topAnchor.constraint(equalTo: ratingView.bottomAnchor, constant: 28),
            clientsCardView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 22),
            clientsCardView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -22),
            
            clientsTitleLabel.topAnchor.constraint(equalTo: clientsCardView.topAnchor, constant: 22),
            clientsTitleLabel.leadingAnchor.constraint(equalTo: clientsCardView.leadingAnchor, constant: 18),
            clientsTitleLabel.trailingAnchor.constraint(equalTo: clientsCardView.trailingAnchor, constant: -18),
            
            clientsListView.topAnchor.constraint(equalTo: clientsTitleLabel.bottomAnchor, constant: 16),
            clientsListView.leadingAnchor.constraint(equalTo: clientsCardView.leadingAnchor, constant: 14),
            clientsListView.trailingAnchor.constraint(equalTo: clientsCardView.trailingAnchor, constant: -14),
            clientsListView.bottomAnchor.constraint(equalTo: clientsCardView.bottomAnchor, constant: -18),
            
            clientsStackView.topAnchor.constraint(equalTo: clientsListView.topAnchor),
            clientsStackView.leadingAnchor.constraint(equalTo: clientsListView.leadingAnchor),
            clientsStackView.trailingAnchor.constraint(equalTo: clientsListView.trailingAnchor),
            clientsStackView.bottomAnchor.constraint(equalTo: clientsListView.bottomAnchor),
            
            buttonsStackView.topAnchor.constraint(equalTo: clientsCardView.bottomAnchor, constant: 26),
            buttonsStackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 22),
            buttonsStackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -22),
            buttonsStackView.heightAnchor.constraint(equalToConstant: 72),
            buttonsStackView.bottomAnchor.constraint(equalTo: contentView.safeAreaLayoutGuide.bottomAnchor, constant: -22)
        ])
    }
    
    private func setupClients() {
        let displayResults = results.isEmpty ? [PharmacyFinishClientResult(
            title: "Клиент",
            subtitle: "Нет данных",
            score: 0,
            feedback: "Фидбек не получен",
            recommendedAnswer: "Рекомендованный ответ не получен"
        )] : results
        
        displayResults.enumerated().forEach { index, result in
            clientsStackView.addArrangedSubview(
                PharmacyFinishClientRowView(
                    result: result,
                    isLast: index == displayResults.count - 1
                )
            )
        }
    }
    
    private func makeCardView(cornerRadius: CGFloat) -> UIView {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .white.withAlphaComponent(0.96)
        view.layer.cornerRadius = cornerRadius
        view.layer.shadowColor = UIColor.black.cgColor
        view.layer.shadowOpacity = 0.08
        view.layer.shadowRadius = 18
        view.layer.shadowOffset = CGSize(width: 0, height: 8)
        return view
    }
    
    private func makeActionButton(
        title: String,
        backgroundColor: UIColor,
        titleColor: UIColor,
        selector: Selector
    ) -> UIButton {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = backgroundColor
        button.setTitle(title, for: .normal)
        button.setTitleColor(titleColor, for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 21, weight: .bold)
        button.layer.shadowColor = UIColor.black.cgColor
        button.layer.shadowOpacity = 0.08
        button.layer.shadowRadius = 12
        button.layer.shadowOffset = CGSize(width: 0, height: 5)
        button.addTarget(self, action: selector, for: .touchUpInside)
        return button
    }
    
    private static func calculateAverageScore(results: [PharmacyFinishClientResult]) -> Int {
        guard !results.isEmpty else { return 0 }
        let totalScore = results.reduce(0) { $0 + $1.score }
        return totalScore / results.count
    }
    
    @objc private func newShiftButtonTapped() {
        onNewShiftTap?()
    }
    
    @objc private func scenariosButtonTapped() {
        onScenariosTap?()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
