import UIKit

final class MotivationsView: UIView {
    
    private lazy var stackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .center
        stackView.spacing = 7
        return stackView
    }()
    
    private lazy var imageContainerView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()

    private lazy var imageBackgroundCircleView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .clear
        view.layer.borderColor = Colors.softPink.cgColor
        view.layer.borderWidth = 2
        return view
    }()
    
    private lazy var starImageView: UIImageView = {
        let imageView = UIImageView()
        let image = UIImage(systemName: "star")
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = Colors.rose
        imageView.image = image
        return imageView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 18, weight: .semibold)
        label.text = "Отличная работа!"
        return label
    }()
    
    private lazy var subTitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.font = UIFont.systemFont(ofSize: 15, weight: .regular)
        label.text = "Продолжайте изучение препоратов"
        return label
    }()
    
    func configure(motivation: (titleString: String, subtitleString: String)) {
        titleLabel.text = motivation.titleString
        subTitleLabel.text = motivation.subtitleString
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        imageBackgroundCircleView.layer.cornerRadius = imageBackgroundCircleView.frame.width / 2
    }
    
    private func setupHierarchy() {
        addSubview(stackView)
        
        stackView.addArrangedSubview(imageContainerView)
        stackView.addArrangedSubview(titleLabel)
        stackView.addArrangedSubview(subTitleLabel)
        
        imageContainerView.addSubview(imageBackgroundCircleView)
        imageContainerView.addSubview(starImageView)
    }
    
    private func setupLayout() {
        backgroundColor = .clear
        
        NSLayoutConstraint.activate([
            stackView.topAnchor.constraint(equalTo: topAnchor),
            stackView.leadingAnchor.constraint(equalTo: leadingAnchor),
            stackView.trailingAnchor.constraint(equalTo: trailingAnchor),
            stackView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            imageBackgroundCircleView.centerXAnchor.constraint(equalTo: imageContainerView.centerXAnchor),
            imageBackgroundCircleView.centerYAnchor.constraint(equalTo: imageContainerView.centerYAnchor),
            imageBackgroundCircleView.widthAnchor.constraint(equalToConstant: 40),
            imageBackgroundCircleView.heightAnchor.constraint(equalTo: imageBackgroundCircleView.widthAnchor),
            imageContainerView.heightAnchor.constraint(equalTo: imageBackgroundCircleView.heightAnchor),

            starImageView.centerXAnchor.constraint(equalTo: imageContainerView.centerXAnchor),
            starImageView.centerYAnchor.constraint(equalTo: imageContainerView.centerYAnchor),
            starImageView.widthAnchor.constraint(equalToConstant: 30),
            starImageView.heightAnchor.constraint(equalToConstant: 30)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
}
