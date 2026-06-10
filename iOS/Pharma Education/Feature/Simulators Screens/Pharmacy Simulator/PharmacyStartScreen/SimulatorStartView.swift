import UIKit

final class SimulatorStartView: UIView {
    
    var onStartTap: ((_ clientsCount: Int, _ minutesPerClient: Int) -> Void)?
    
    private var clientCount = 10 {
        didSet {
            clientsCountLabel.text = "\(clientCount)"
        }
    }
    
    private var minutesPerClient = 3 {
        didSet {
            clientTimeLabel.text = "\(minutesPerClient) мин"
        }
    }
    
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
        view.backgroundColor = Colors.lavenderBlush.withAlphaComponent(0.22)
        return view
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "Симулятор\nаптекаря"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 44, weight: .bold)
        label.numberOfLines = 0
        return label
    }()
    
    private lazy var subtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "Настройте смену\nперед началом"
        label.textColor = .darkGray
        label.font = UIFont.systemFont(ofSize: 22, weight: .medium)
        label.numberOfLines = 0
        return label
    }()
    
    private lazy var cardsStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.spacing = 18
        return stackView
    }()
    
    private lazy var clientsCard = makeCardView()
    private lazy var clientTimeCard = makeCardView()
    
    private lazy var clientsCountLabel: UILabel = {
        let label = UILabel()
        label.text = "10"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 34, weight: .regular)
        label.textAlignment = .center
        return label
    }()
    
    private lazy var clientTimeLabel: UILabel = {
        let label = UILabel()
        label.text = "3 мин"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 28, weight: .regular)
        label.textAlignment = .center
        return label
    }()
    
    private lazy var startButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = Colors.blackRose
        button.setTitle("Начать смену", for: .normal)
        button.setTitleColor(.white, for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 26, weight: .bold)
        button.addTarget(self, action: #selector(startButtonTapped), for: .touchUpInside)
        return button
    }()
    
    private lazy var startButtonIconView: UIImageView = {
        let imageView = UIImageView(image: UIImage(systemName: "arrow.right"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = .white
        imageView.contentMode = .scaleAspectFit
        return imageView
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
        setupCards()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        startButton.layer.cornerRadius = startButton.bounds.height * 0.2
    }
    
    private func setupHierarchy() {
        addSubview(backgroundImageView)
        addSubview(dimView)
        addSubview(backgroundDesignView)
        addSubview(titleLabel)
        addSubview(subtitleLabel)
        addSubview(cardsStackView)
        addSubview(startButton)
        
        startButton.addSubview(startButtonIconView)
        cardsStackView.addArrangedSubview(clientsCard)
        cardsStackView.addArrangedSubview(clientTimeCard)
    }
    
    private func setupLayout() {
        NSLayoutConstraint.activate([
            backgroundImageView.topAnchor.constraint(equalTo: topAnchor),
            backgroundImageView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundImageView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundImageView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            dimView.topAnchor.constraint(equalTo: topAnchor),
            dimView.leadingAnchor.constraint(equalTo: leadingAnchor),
            dimView.trailingAnchor.constraint(equalTo: trailingAnchor),
            dimView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            backgroundDesignView.topAnchor.constraint(equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            titleLabel.topAnchor.constraint(equalTo: safeAreaLayoutGuide.topAnchor, constant: 48),
            titleLabel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 28),
            titleLabel.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -28),
            
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 18),
            subtitleLabel.leadingAnchor.constraint(equalTo: titleLabel.leadingAnchor),
            subtitleLabel.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -28),
            
            cardsStackView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 22),
            cardsStackView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -22),
            cardsStackView.bottomAnchor.constraint(equalTo: startButton.topAnchor, constant: -28),
            
            startButton.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 22),
            startButton.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -22),
            startButton.bottomAnchor.constraint(equalTo: safeAreaLayoutGuide.bottomAnchor, constant: -24),
            startButton.heightAnchor.constraint(equalToConstant: 76),
            
            startButtonIconView.centerYAnchor.constraint(equalTo: startButton.centerYAnchor),
            startButtonIconView.trailingAnchor.constraint(equalTo: startButton.trailingAnchor, constant: -28),
            startButtonIconView.widthAnchor.constraint(equalToConstant: 34),
            startButtonIconView.heightAnchor.constraint(equalToConstant: 34)
        ])
    }
    
    private func setupCards() {
        configureCard(clientsCard, title: "Количество клиентов", content: makeClientsCounterView())
        configureCard(clientTimeCard, title: "Время на одного клиента", content: makeClientTimeCounterView())
    }
    
    private func configureCard(_ card: UIView, title: String, content: UIView) {
        let titleLabel = UILabel()
        titleLabel.text = title
        titleLabel.textColor = .black
        titleLabel.font = UIFont.systemFont(ofSize: 23, weight: .bold)
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        
        let stackView = UIStackView(arrangedSubviews: [titleLabel, content])
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.spacing = 20
        
        card.addSubview(stackView)
        
        NSLayoutConstraint.activate([
            stackView.topAnchor.constraint(equalTo: card.topAnchor, constant: 26),
            stackView.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 26),
            stackView.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -26),
            stackView.bottomAnchor.constraint(equalTo: card.bottomAnchor, constant: -26),
            content.heightAnchor.constraint(equalToConstant: 58)
        ])
    }
    
    private func makeCardView() -> UIView {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .white.withAlphaComponent(0.96)
        view.layer.cornerRadius = 28
        view.clipsToBounds = true
        return view
    }
    
    private func makeClientsCounterView() -> UIView {
        makeCounterView(
            valueLabel: clientsCountLabel,
            minusAction: #selector(decreaseClientsCount),
            plusAction: #selector(increaseClientsCount)
        )
    }
    
    private func makeClientTimeCounterView() -> UIView {
        makeCounterView(
            valueLabel: clientTimeLabel,
            minusAction: #selector(decreaseClientTime),
            plusAction: #selector(increaseClientTime)
        )
    }
    
    private func makeCounterView(valueLabel: UILabel, minusAction: Selector, plusAction: Selector) -> UIView {
        let containerView = UIView()
        containerView.translatesAutoresizingMaskIntoConstraints = false
        containerView.backgroundColor = .white.withAlphaComponent(0.72)
        containerView.layer.cornerRadius = 16
        containerView.layer.borderWidth = 1.2
        containerView.layer.borderColor = Colors.softPink.cgColor
        
        let minusButton = makeCounterButton(title: "−", action: minusAction)
        let plusButton = makeCounterButton(title: "+", action: plusAction)
        
        containerView.addSubview(minusButton)
        containerView.addSubview(valueLabel)
        containerView.addSubview(plusButton)
        valueLabel.translatesAutoresizingMaskIntoConstraints = false
        
        NSLayoutConstraint.activate([
            minusButton.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 14),
            minusButton.centerYAnchor.constraint(equalTo: containerView.centerYAnchor),
            minusButton.widthAnchor.constraint(equalToConstant: 52),
            minusButton.heightAnchor.constraint(equalToConstant: 42),
            
            valueLabel.centerXAnchor.constraint(equalTo: containerView.centerXAnchor),
            valueLabel.centerYAnchor.constraint(equalTo: containerView.centerYAnchor),
            valueLabel.leadingAnchor.constraint(greaterThanOrEqualTo: minusButton.trailingAnchor, constant: 12),
            valueLabel.trailingAnchor.constraint(lessThanOrEqualTo: plusButton.leadingAnchor, constant: -12),
            
            plusButton.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -14),
            plusButton.centerYAnchor.constraint(equalTo: containerView.centerYAnchor),
            plusButton.widthAnchor.constraint(equalToConstant: 52),
            plusButton.heightAnchor.constraint(equalToConstant: 42)
        ])
        
        return containerView
    }
    
    private func makeCounterButton(title: String, action: Selector) -> UIButton {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.setTitle(title, for: .normal)
        button.setTitleColor(Colors.rose, for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 34, weight: .regular)
        button.backgroundColor = Colors.softPink.withAlphaComponent(0.55)
        button.layer.cornerRadius = 12
        button.addTarget(self, action: action, for: .touchUpInside)
        return button
    }
    
    @objc private func decreaseClientsCount() {
        clientCount = max(1, clientCount - 1)
    }
    
    @objc private func increaseClientsCount() {
        clientCount = min(100, clientCount + 1)
    }
    
    @objc private func decreaseClientTime() {
        minutesPerClient = max(1, minutesPerClient - 1)
    }
    
    @objc private func increaseClientTime() {
        minutesPerClient = min(60, minutesPerClient + 1)
    }
    
    @objc private func startButtonTapped() {
        onStartTap?(clientCount, minutesPerClient)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
