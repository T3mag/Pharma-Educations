import UIKit

final class LoadingView: UIView {
    
    private lazy var backgroundDesign = BackgroundDesignView()
    
    private lazy var topTextStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.spacing = 10
        stackView.alignment = .center
        stackView.distribution = .fill
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var bottomTextStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.spacing = 10
        stackView.alignment = .center
        stackView.distribution = .fill
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var topTitleStackView: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 2
        label.textColor = .black
        label.textAlignment = .center
        label.text = "Умный подход" + "\n" + "к знаниям"
        label.font = UIFont.systemFont(ofSize: 35, weight: .bold)
        return label
    }()
    
    private lazy var topSubtitleStackView: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 2
        label.textColor = .gray
        label.textAlignment = .center
        label.text = "Изучайте лекарства." + "\n" + "Принимайте верные решения."
        label.font = UIFont.systemFont(ofSize: 15, weight: .regular)
        return label
    }()
    
    private lazy var bottomTitleStackView: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 1
        label.textColor = Colors.rose
        label.text = "Pharma App"
        label.font = UIFont.systemFont(ofSize: 50, weight: .bold)
        return label
    }()
    
    private lazy var bottomSubtitleStackView: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 1
        label.textColor = .gray
        label.text = "Обучение. Практика. Уверенность."
        label.font = UIFont.systemFont(ofSize: 15, weight: .regular)
        return label
    }()
    
    private lazy var centerImageView: UIImageView = {
        let image = UIImage(named: "LaunchImage")
        let imageView = UIImageView(image: image)
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.contentMode = .scaleAspectFit
        return imageView
    }()
    
    private lazy var activityIndicator: UIActivityIndicatorView = {
        let indicator = UIActivityIndicatorView(style: .large)
        indicator.color = .gray
        indicator.hidesWhenStopped = true
        indicator.translatesAutoresizingMaskIntoConstraints = false
        return indicator
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    private func setupHierarchy() {
        addSubview(backgroundDesign)
        addSubview(topTextStackView)
        addSubview(centerImageView)
        addSubview(bottomTextStackView)
        addSubview(activityIndicator)
        
        topTextStackView.addArrangedSubview(topTitleStackView)
        topTextStackView.addArrangedSubview(topSubtitleStackView)
        
        bottomTextStackView.addArrangedSubview(bottomTitleStackView)
        bottomTextStackView.addArrangedSubview(bottomSubtitleStackView)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        activityIndicator.startAnimating()
        
        NSLayoutConstraint.activate([
            backgroundDesign.topAnchor.constraint(
                equalTo: topAnchor),
            backgroundDesign.leadingAnchor.constraint(
                equalTo: leadingAnchor),
            backgroundDesign.trailingAnchor.constraint(
                equalTo: trailingAnchor),
            backgroundDesign.bottomAnchor.constraint(
                equalTo: bottomAnchor),

            centerImageView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: 20
            ),
            centerImageView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -20
            ),
            centerImageView.heightAnchor.constraint(
                equalTo: heightAnchor,
                multiplier: 0.4
            ),
            centerImageView.centerYAnchor.constraint(
                equalTo: safeAreaLayoutGuide.centerYAnchor),
            
            activityIndicator.topAnchor.constraint(
                equalTo: safeAreaLayoutGuide.topAnchor,
                constant: 20),
            activityIndicator.centerXAnchor.constraint(
                equalTo: centerXAnchor),
            
            topTextStackView.bottomAnchor.constraint(
                equalTo: centerImageView.topAnchor),
            topTextStackView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor),
            topTextStackView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor),
            
            bottomTextStackView.topAnchor.constraint(
                equalTo: centerImageView.bottomAnchor),
            bottomTextStackView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor),
            bottomTextStackView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor),
            
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
