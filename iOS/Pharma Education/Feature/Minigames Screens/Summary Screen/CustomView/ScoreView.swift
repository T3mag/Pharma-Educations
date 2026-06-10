import UIKit

final class ScoreView: UIView {
    private lazy var stackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .center
        stackView.spacing = 10
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
        view.backgroundColor = Colors.softPink
        return view
    }()
    
    private lazy var checkmarkImageView: UIImageView = {
        let imageView = UIImageView()
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = Colors.rose
        let image = UIImage(systemName: "checkmark.circle")
        imageView.image = image
        return imageView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.textAlignment = .center
        label.font = UIFont.systemFont(ofSize: 15, weight: .semibold)
        label.text = "Правильных ответов"
        return label
    }()
    
    private lazy var subTitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.textAlignment = .center
        label.font = UIFont.systemFont(ofSize: 30, weight: .bold)
        label.text = "8 из 10"
        return label
    }()
    
    func configureInfoInCount(correctQuestions: Int, totalQuesitions: Int) {
        subTitleLabel.text = "\(correctQuestions) из \(totalQuesitions)"
    }
    
    func configureInfoInProcent(procentCorrectQuestions: Double) {
        subTitleLabel.text = "\(procentCorrectQuestions)% из 100%"
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupLayout()
    }
    
    override func layoutSubviews() {
        imageBackgroundCircleView.layer.cornerRadius = imageBackgroundCircleView.frame.width / 2
        layer.cornerRadius = frame.height * 0.2
    }
    
    private func setupLayout() {
        backgroundColor = .white
        addSubview(stackView)
        
        stackView.addArrangedSubview(imageContainerView)
        stackView.addArrangedSubview(titleLabel)
        stackView.addArrangedSubview(subTitleLabel)
        
        imageContainerView.addSubview(imageBackgroundCircleView)
        imageContainerView.addSubview(checkmarkImageView)
        
        NSLayoutConstraint.activate([
            stackView.topAnchor.constraint(equalTo: topAnchor, constant: 20),
            stackView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -20),
            stackView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -20),
            stackView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 20),

            imageBackgroundCircleView.centerXAnchor.constraint(equalTo: imageContainerView.centerXAnchor),
            imageBackgroundCircleView.centerYAnchor.constraint(equalTo: imageContainerView.centerYAnchor),
            imageBackgroundCircleView.widthAnchor.constraint(equalToConstant: 60),
            imageBackgroundCircleView.heightAnchor.constraint(equalTo: imageBackgroundCircleView.widthAnchor),
            imageContainerView.heightAnchor.constraint(equalTo: imageBackgroundCircleView.heightAnchor),

            checkmarkImageView.centerXAnchor.constraint(equalTo: imageContainerView.centerXAnchor),
            checkmarkImageView.centerYAnchor.constraint(equalTo: imageContainerView.centerYAnchor),
            checkmarkImageView.widthAnchor.constraint(equalToConstant: 40),
            checkmarkImageView.heightAnchor.constraint(equalToConstant: 40)
        ])
        
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
