
import UIKit

final class StartButtonView: UIView {
    
    private lazy var textStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.spacing = TopicConstants.StartButton.spacingStackView
        stackView.alignment = .leading
        return stackView
    }()
    
    private lazy var graduationcapImageView: UIImageView = {
        let imageView = UIImageView()
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.backgroundColor = .white
        imageView.tintColor = Colors.rose
        imageView.clipsToBounds = true
        imageView.contentMode = .center
        return imageView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "Начать"
        label.textColor = .white
        label.font = UIFont.systemFont(ofSize: 20, weight: .semibold)
        return label
    }()
    
    private lazy var countTopicLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .white
        label.font = UIFont.systemFont(ofSize: 15, weight: .regular)
        return label
    }()
    
    private lazy var chevronImageView: UIImageView = {
        let imageView = UIImageView(image: UIImage(systemName: "chevron.right"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = .white
        return imageView
    }()
    
    func confugureButtonInfo(countTopics: Int) {
        let text = countTopics == 1
                    ? "Выбрана \(countTopics) тема" : countTopics >= 2 && countTopics <= 4
                    ? "Выбрано \(countTopics) темы" : "Выбрано \(countTopics) тем"
        countTopicLabel.text = text
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        let config = UIImage.SymbolConfiguration(
            pointSize: graduationcapImageView.frame.height * TopicConstants.StartButton.imageViewReductionPercentage,
            weight: .light)
        let image = UIImage(
            systemName: "graduationcap",
            withConfiguration: config
        )
        graduationcapImageView.image = image
        graduationcapImageView.layer.cornerRadius = graduationcapImageView.frame.height * 0.5
    }
    
    private func setupHierarchy() {
        addSubview(graduationcapImageView)
        addSubview(textStackView)
        addSubview(chevronImageView)
        
        textStackView.addArrangedSubview(titleLabel)
        textStackView.addArrangedSubview(countTopicLabel)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.rose
        
        NSLayoutConstraint.activate([
            graduationcapImageView.topAnchor.constraint(
                equalTo: topAnchor,
                constant: TopicConstants.StartButton.indentFromBorder),
            graduationcapImageView.bottomAnchor.constraint(
                equalTo: bottomAnchor,
                constant: -TopicConstants.StartButton.indentFromBorder),
            graduationcapImageView.leadingAnchor.constraint(
                equalTo: leadingAnchor,
                constant: TopicConstants.StartButton.indentFromBorder),
            graduationcapImageView.heightAnchor.constraint(
                equalToConstant: TopicConstants.StartButton.graduationcapImageView),
            graduationcapImageView.widthAnchor.constraint(
                equalToConstant: TopicConstants.StartButton.graduationcapImageView),
            
            textStackView.centerYAnchor.constraint(
                equalTo: graduationcapImageView.centerYAnchor),
            textStackView.leadingAnchor.constraint(
                equalTo: graduationcapImageView.trailingAnchor,
                constant: TopicConstants.StartButton.indentFromBorder),
            textStackView.trailingAnchor.constraint(
                lessThanOrEqualTo: chevronImageView.leadingAnchor,
                constant: -TopicConstants.StartButton.indentFromBorder),
            
            chevronImageView.centerYAnchor.constraint(
                equalTo: graduationcapImageView.centerYAnchor),
            chevronImageView.trailingAnchor.constraint(
                equalTo: trailingAnchor,
                constant: -TopicConstants.StartButton.indentFromBorder),
            chevronImageView.heightAnchor.constraint(
                equalToConstant: TopicConstants.StartButton.chevronImageView),
            chevronImageView.widthAnchor.constraint(
                equalToConstant: TopicConstants.StartButton.chevronImageView)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
