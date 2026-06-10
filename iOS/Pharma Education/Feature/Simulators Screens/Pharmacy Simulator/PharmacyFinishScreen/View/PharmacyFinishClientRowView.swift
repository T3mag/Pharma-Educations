import UIKit

final class PharmacyFinishClientRowView: UIView {
    
    private let result: PharmacyFinishClientResult
    private let isLast: Bool
    
    private lazy var contentStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.spacing = 0
        return stackView
    }()
    
    private lazy var headerView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var iconContainerView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = Colors.softPink
        view.layer.cornerRadius = 24
        view.clipsToBounds = true
        return view
    }()
    
    private lazy var iconView: UIImageView = {
        let imageView = UIImageView(image: UIImage(systemName: "person.fill"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = Colors.blackRose
        imageView.contentMode = .scaleAspectFit
        return imageView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = result.title
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 19, weight: .semibold)
        label.numberOfLines = 0
        return label
    }()
    
    private lazy var subtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = result.subtitle
        label.textColor = .darkGray
        label.font = UIFont.systemFont(ofSize: 16, weight: .regular)
        label.numberOfLines = 0
        return label
    }()
    
    private lazy var scoreLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "\(result.score)"
        label.textColor = Colors.blackRose
        label.font = UIFont.systemFont(ofSize: 28, weight: .bold)
        label.textAlignment = .right
        label.setContentHuggingPriority(.required, for: .horizontal)
        label.setContentCompressionResistancePriority(.required, for: .horizontal)
        return label
    }()
    
    private lazy var chevronView: UIImageView = {
        let imageView = UIImageView(image: UIImage(systemName: "chevron.down"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = .systemGray3
        imageView.contentMode = .scaleAspectFit
        imageView.setContentHuggingPriority(.required, for: .horizontal)
        imageView.setContentCompressionResistancePriority(.required, for: .horizontal)
        return imageView
    }()
    
    private lazy var detailStackView: UIStackView = {
        let stackView = UIStackView(arrangedSubviews: [
            makeDetailLabel(title: "Фидбек", text: result.feedback),
            makeDetailLabel(title: "Рекомендованный ответ", text: result.recommendedAnswer)
        ])
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.spacing = 12
        stackView.isHidden = true
        stackView.alpha = 0
        return stackView
    }()
    
    private lazy var separatorView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .systemGray5
        view.isHidden = isLast
        return view
    }()
    
    init(result: PharmacyFinishClientResult, isLast: Bool) {
        self.result = result
        self.isLast = isLast
        super.init(frame: .zero)
        setupAppearance()
        setupHierarchy()
        setupLayout()
    }
    
    private func setupAppearance() {
        translatesAutoresizingMaskIntoConstraints = false
        backgroundColor = .white.withAlphaComponent(0.48)
        isUserInteractionEnabled = true
        addGestureRecognizer(UITapGestureRecognizer(target: self, action: #selector(rowTapped)))
    }
    
    private func setupHierarchy() {
        addSubview(contentStackView)
        addSubview(separatorView)
        contentStackView.addArrangedSubview(headerView)
        contentStackView.addArrangedSubview(detailStackView)
        
        headerView.addSubview(iconContainerView)
        iconContainerView.addSubview(iconView)
        headerView.addSubview(titleLabel)
        headerView.addSubview(subtitleLabel)
        headerView.addSubview(scoreLabel)
        headerView.addSubview(chevronView)
    }
    
    private func setupLayout() {
        NSLayoutConstraint.activate([
            contentStackView.topAnchor.constraint(equalTo: topAnchor),
            contentStackView.leadingAnchor.constraint(equalTo: leadingAnchor),
            contentStackView.trailingAnchor.constraint(equalTo: trailingAnchor),
            contentStackView.bottomAnchor.constraint(equalTo: separatorView.topAnchor),
            
            headerView.heightAnchor.constraint(greaterThanOrEqualToConstant: 78),
            
            iconContainerView.leadingAnchor.constraint(equalTo: headerView.leadingAnchor, constant: 12),
            iconContainerView.topAnchor.constraint(equalTo: headerView.topAnchor, constant: 15),
            iconContainerView.widthAnchor.constraint(equalToConstant: 48),
            iconContainerView.heightAnchor.constraint(equalToConstant: 48),
            
            iconView.centerXAnchor.constraint(equalTo: iconContainerView.centerXAnchor),
            iconView.centerYAnchor.constraint(equalTo: iconContainerView.centerYAnchor),
            iconView.widthAnchor.constraint(equalToConstant: 28),
            iconView.heightAnchor.constraint(equalToConstant: 28),
            
            titleLabel.leadingAnchor.constraint(equalTo: iconContainerView.trailingAnchor, constant: 16),
            titleLabel.topAnchor.constraint(equalTo: headerView.topAnchor, constant: 17),
            titleLabel.trailingAnchor.constraint(lessThanOrEqualTo: scoreLabel.leadingAnchor, constant: -12),
            
            subtitleLabel.leadingAnchor.constraint(equalTo: titleLabel.leadingAnchor),
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 8),
            subtitleLabel.trailingAnchor.constraint(equalTo: headerView.trailingAnchor, constant: -18),
            subtitleLabel.bottomAnchor.constraint(equalTo: headerView.bottomAnchor, constant: -16),
            
            scoreLabel.firstBaselineAnchor.constraint(equalTo: titleLabel.firstBaselineAnchor),
            scoreLabel.trailingAnchor.constraint(equalTo: chevronView.leadingAnchor, constant: -14),
            scoreLabel.widthAnchor.constraint(equalToConstant: 48),
            
            chevronView.trailingAnchor.constraint(equalTo: headerView.trailingAnchor, constant: -18),
            chevronView.centerYAnchor.constraint(equalTo: scoreLabel.centerYAnchor),
            chevronView.widthAnchor.constraint(equalToConstant: 18),
            chevronView.heightAnchor.constraint(equalToConstant: 18),
            
            detailStackView.leadingAnchor.constraint(equalTo: contentStackView.leadingAnchor, constant: 24),
            detailStackView.trailingAnchor.constraint(equalTo: contentStackView.trailingAnchor, constant: -22),
            
            separatorView.leadingAnchor.constraint(equalTo: leadingAnchor),
            separatorView.trailingAnchor.constraint(equalTo: trailingAnchor),
            separatorView.bottomAnchor.constraint(equalTo: bottomAnchor),
            separatorView.heightAnchor.constraint(equalToConstant: 1)
        ])
    }
    
    private func makeDetailLabel(title: String, text: String) -> UILabel {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 0
        label.textColor = .darkGray
        label.font = UIFont.systemFont(ofSize: 15, weight: .regular)
        
        let attributedText = NSMutableAttributedString(
            string: "\(title):\n",
            attributes: [
                .font: UIFont.systemFont(ofSize: 15, weight: .bold),
                .foregroundColor: UIColor.black
            ]
        )
        attributedText.append(NSAttributedString(
            string: text,
            attributes: [
                .font: UIFont.systemFont(ofSize: 15, weight: .regular),
                .foregroundColor: UIColor.darkGray
            ]
        ))
        label.attributedText = attributedText
        return label
    }
    
    @objc private func rowTapped() {
        let shouldExpand = detailStackView.isHidden
        if shouldExpand {
            detailStackView.isHidden = false
        }
        
        UIView.animate(
            withDuration: 0.24,
            delay: 0,
            options: [.curveEaseInOut, .beginFromCurrentState]
        ) {
            self.detailStackView.alpha = shouldExpand ? 1 : 0
            self.chevronView.transform = shouldExpand ? CGAffineTransform(rotationAngle: .pi) : .identity
            self.superview?.superview?.layoutIfNeeded()
        } completion: { _ in
            if !shouldExpand {
                self.detailStackView.isHidden = true
            }
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
