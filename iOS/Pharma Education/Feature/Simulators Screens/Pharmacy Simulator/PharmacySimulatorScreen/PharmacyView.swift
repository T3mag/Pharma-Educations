import UIKit

final class PharmacyView: UIView {
    
    var onConfirmTap: ((String) -> Void)?
    
    private let backgroundDesignView: BackgroundDesignView = {
        let view = BackgroundDesignView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var backgroundImageView: UIImageView = {
        let imageView = UIImageView(image: UIImage(named: "pharmacy_background"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.contentMode = .scaleAspectFill
        imageView.clipsToBounds = true
        return imageView
    }()
    
    private lazy var scrollView: UIScrollView = {
        let scrollView = UIScrollView()
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        scrollView.showsVerticalScrollIndicator = false
        scrollView.keyboardDismissMode = .interactive
        return scrollView
    }()
    
    private lazy var contentView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 15
        return stackView
    }()
    
    private lazy var timerContainerView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private let timerView = PharmacyTimerView()
    private let clientCounterView = PharmacyClientCounterView()
    private let clientProfileView = PharmacyClientProfileView()
    private let answerInputView = PharmacyAnswerInputView()
    
    private lazy var confirmButton: UIButton = {
        let button = UIButton(type: .system)
        button.backgroundColor = Colors.blackRose
        button.setTitle("Следующий клиент", for: .normal)
        button.setTitleColor(.white, for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 24, weight: .bold)
        button.addTarget(self, action: #selector(confirmButtonTapped), for: .touchUpInside)
        return button
    }()
    
    func configure(
        customer: Customer,
        currentClient: Int,
        totalClients: Int,
        animated: Bool
    ) {
        let updates = { [self] in
            clientCounterView.configure(
                currentClient: currentClient,
                totalClients: totalClients
            )
            clientProfileView.configureDefaultClientInfo(customer: customer)
        }
        
        guard animated else {
            updates()
            return
        }
        
        animateClientUpdate(updates: updates)
    }
    
    func configureTimer(time: String) {
        timerView.configure(time: time)
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
        setupPriorities()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        confirmButton.layer.cornerRadius = confirmButton.bounds.height * 0.2
    }
    
    private func setupHierarchy() {
        addSubview(backgroundImageView)
        addSubview(backgroundDesignView)
        addSubview(scrollView)
        
        scrollView.addSubview(contentView)
        contentView.addSubview(rootStackView)
        
        rootStackView.addArrangedSubview(timerContainerView)
        timerContainerView.addSubview(timerView)
        timerContainerView.addSubview(clientCounterView)
        rootStackView.addArrangedSubview(clientProfileView)
        rootStackView.addArrangedSubview(answerInputView)
        rootStackView.addArrangedSubview(confirmButton)
    }
    
    private func setupPriorities() {
        clientProfileView.setContentHuggingPriority(.required, for: .vertical)
        clientProfileView.setContentCompressionResistancePriority(.required, for: .vertical)
        
        answerInputView.setContentHuggingPriority(.defaultLow, for: .vertical)
        answerInputView.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
    }
    
    private func animateClientUpdate(updates: @escaping () -> Void) {
        let animatedViews = [clientCounterView, clientProfileView]
        
        UIView.animate(
            withDuration: 0.16,
            delay: 0,
            options: [.curveEaseInOut, .beginFromCurrentState]
        ) {
            animatedViews.forEach {
                $0.alpha = 0
                $0.transform = CGAffineTransform(translationX: -12, y: 0)
            }
        } completion: { _ in
            updates()
            animatedViews.forEach {
                $0.transform = CGAffineTransform(translationX: 12, y: 0)
            }
            
            UIView.animate(
                withDuration: 0.22,
                delay: 0,
                options: [.curveEaseOut, .beginFromCurrentState]
            ) {
                animatedViews.forEach {
                    $0.alpha = 1
                    $0.transform = .identity
                }
            }
        }
    }
    
    private func setupLayout() {
        backgroundColor = .white
        
        NSLayoutConstraint.activate([
            backgroundImageView.topAnchor.constraint(equalTo: topAnchor),
            backgroundImageView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundImageView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundImageView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
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
            contentView.heightAnchor.constraint(greaterThanOrEqualTo: scrollView.frameLayoutGuide.heightAnchor),
            
            rootStackView.topAnchor.constraint(equalTo: contentView.safeAreaLayoutGuide.topAnchor, constant: 20),
            rootStackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            rootStackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            rootStackView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20),
            
            timerContainerView.heightAnchor.constraint(equalToConstant: 56),
            
            timerView.topAnchor.constraint(equalTo: timerContainerView.topAnchor),
            timerView.leadingAnchor.constraint(equalTo: timerContainerView.leadingAnchor),
            timerView.bottomAnchor.constraint(equalTo: timerContainerView.bottomAnchor),
            timerView.widthAnchor.constraint(equalToConstant: 126),
            
            clientCounterView.topAnchor.constraint(equalTo: timerContainerView.topAnchor),
            clientCounterView.leadingAnchor.constraint(equalTo: timerView.trailingAnchor, constant: 12),
            clientCounterView.bottomAnchor.constraint(equalTo: timerContainerView.bottomAnchor),
            clientCounterView.widthAnchor.constraint(equalToConstant: 112),
            clientCounterView.trailingAnchor.constraint(lessThanOrEqualTo: timerContainerView.trailingAnchor),
            
            answerInputView.heightAnchor.constraint(greaterThanOrEqualToConstant: 160),
            confirmButton.heightAnchor.constraint(equalToConstant: 68)
        ])
    }
    
    @objc private func confirmButtonTapped() {
        let answerText = answerInputView.answerText
        answerInputView.clearAnswer()
        onConfirmTap?(answerText)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
