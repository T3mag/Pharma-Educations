
import UIKit

final class SummaryView: UIView {
    var onExitTap: (() -> Void)?
    var onRepeatTap: (() -> Void)?
    
    private lazy var bacgroundDesignView = BackgroundDesignView()
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 10
        return stackView
    }()
    
    private lazy var titleStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = 10
        return stackView
    }()
    
    private lazy var buttonStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .horizontal
        stackView.alignment = .fill
        stackView.distribution = .fillEqually
        stackView.spacing = 15
        return stackView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Завершено!"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 40, weight: .bold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var subTitleLabel: UILabel = {
        let label = UILabel()
        label.text = "Вы успешно прошли мини-игру"
        label.textColor = .gray
        label.font = UIFont.systemFont(ofSize: 15, weight: .semibold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var centerImageView: UIImageView = {
        let imageView = UIImageView(image: UIImage(named: "SummaryImage"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.contentMode = .scaleAspectFit
        return imageView
    }()
    
    private lazy var scoreView: ScoreView = {
        let view = ScoreView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var spacerView: UIView = {
        let view = UIView()
        view.setContentHuggingPriority(.defaultLow, for: .vertical)
        view.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        return view
    }()
    
    private lazy var motivationView: MotivationsView = {
        let view = MotivationsView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var returnButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.setTitle("Повторить", for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 18, weight: .bold)
        button.setTitleColor(Colors.rose, for: .normal)
        button.backgroundColor = .white
        button.addTarget(self, action: #selector(repeatTapped), for: .touchUpInside)
        return button
    }()
    
    private lazy var exitButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.setTitle("На главную", for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 18, weight: .bold)
        button.backgroundColor = Colors.rose
        button.addTarget(self, action: #selector(exitTapped), for: .touchUpInside)
        return button
    }()
    
    func configureInfoInCount(correctQuestions: Int,
                       totalQuesitions: Int,
                       motivation: (titleString: String,
                                    subtitleString: String))
    {
        scoreView.configureInfoInCount(correctQuestions: correctQuestions,
                                totalQuesitions: totalQuesitions)
        motivationView.configure(motivation: motivation)
    }
    
    func configureInfoInProcent(procentCorrectQuestions: Double,
                                motivation: (titleString: String,
                                    subtitleString: String))
    {
        scoreView.configureInfoInProcent(procentCorrectQuestions: procentCorrectQuestions)
        motivationView.configure(motivation: motivation)
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        exitButton.layer.cornerRadius = exitButton.frame.height * 0.3
        returnButton.layer.cornerRadius = exitButton.frame.height * 0.3
    }
    
    private func setupHierarchy() {
        addSubview(bacgroundDesignView)
        addSubview(rootStackView)
        
        rootStackView.addArrangedSubview(titleStackView)
        rootStackView.addArrangedSubview(centerImageView)
        rootStackView.addArrangedSubview(scoreView)
        rootStackView.addArrangedSubview(motivationView)
        rootStackView.addArrangedSubview(spacerView)
        rootStackView.addArrangedSubview(buttonStackView)
        
        titleStackView.addArrangedSubview(titleLabel)
        titleStackView.addArrangedSubview(subTitleLabel)
        
        buttonStackView.addArrangedSubview(returnButton)
        buttonStackView.addArrangedSubview(exitButton)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            bacgroundDesignView.topAnchor.constraint(equalTo: topAnchor, constant: 10),
            bacgroundDesignView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 10),
            bacgroundDesignView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -10),
            bacgroundDesignView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -10),
            
            rootStackView.topAnchor.constraint(equalTo: safeAreaLayoutGuide.topAnchor, constant: 20),
            rootStackView.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor, constant: 20),
            rootStackView.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor, constant: -20),
            rootStackView.bottomAnchor.constraint(equalTo: safeAreaLayoutGuide.bottomAnchor, constant: -20),
            
            centerImageView.heightAnchor.constraint(equalToConstant: 250),
            returnButton.heightAnchor.constraint(equalToConstant: 60),
            exitButton.heightAnchor.constraint(equalToConstant: 60)
        ])
    }
    
    @objc
    private func exitTapped() {
        onExitTap?()
    }
    
    @objc
    private func repeatTapped() {
        onRepeatTap?()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
