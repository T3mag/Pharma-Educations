import UIKit

final class PharmacyClientProfileView: UIView {
    
    private lazy var titleIconView = makeIconView(systemName: "person", pointSize: 32)
    
    private lazy var titleLabel: UILabel = makeLabel(
        text: "Профиль клиента",
        font: UIFont.systemFont(ofSize: 20, weight: .bold),
        color: .black
    )
    
    private lazy var detailsView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .white
        view.layer.borderWidth = 1
        view.layer.borderColor = UIColor.systemGray5.cgColor
        view.clipsToBounds = true
        return view
    }()
    
    private lazy var contentStackView: UIStackView = {
        let stackView = UIStackView(arrangedSubviews: [topSectionsStackView, horizontalDividerView, knownFactsStackView])
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.spacing = 18
        return stackView
    }()
    
    private lazy var topSectionsStackView: UIStackView = {
        let stackView = UIStackView(arrangedSubviews: [clientInfoStackView, verticalDividerView, clientReplicaStackView])
        stackView.axis = .horizontal
        stackView.alignment = .top
        stackView.spacing = 18
        return stackView
    }()
    
    private lazy var clientInfoStackView: UIStackView = makeSectionStackView(spacing: 10)
    private lazy var clientReplicaStackView: UIStackView = makeSectionStackView(spacing: 12)
    private lazy var knownFactsStackView: UIStackView = makeSectionStackView(spacing: 8)
    
    private lazy var verticalDividerView: UIView = {
        let view = UIView()
        view.backgroundColor = UIColor.systemGray4
        return view
    }()
    
    private lazy var horizontalDividerView: UIView = {
        let view = UIView()
        view.backgroundColor = UIColor.systemGray5
        return view
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupAppearance()
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        layer.cornerRadius = frame.height * 0.05
        detailsView.layer.cornerRadius = detailsView.frame.height * 0.05
    }
    
    private func setupAppearance() {
        backgroundColor = .white
        clipsToBounds = true
    }
    
    private func setupHierarchy() {
        addSubview(titleIconView)
        addSubview(titleLabel)
        addSubview(detailsView)
        detailsView.addSubview(contentStackView)
    }
    
    private func setupLayout() {
        NSLayoutConstraint.activate([
            titleIconView.topAnchor.constraint(equalTo: topAnchor, constant: 24),
            titleIconView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 24),
            titleIconView.widthAnchor.constraint(equalToConstant: 34),
            titleIconView.heightAnchor.constraint(equalToConstant: 34),
            
            titleLabel.centerYAnchor.constraint(equalTo: titleIconView.centerYAnchor),
            titleLabel.leadingAnchor.constraint(equalTo: titleIconView.trailingAnchor, constant: 14),
            titleLabel.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -24),
            
            detailsView.topAnchor.constraint(equalTo: titleIconView.bottomAnchor, constant: 18),
            detailsView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            detailsView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            detailsView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -22),
            
            contentStackView.topAnchor.constraint(equalTo: detailsView.topAnchor, constant: 20),
            contentStackView.leadingAnchor.constraint(equalTo: detailsView.leadingAnchor, constant: 20),
            contentStackView.trailingAnchor.constraint(equalTo: detailsView.trailingAnchor, constant: -20),
            contentStackView.bottomAnchor.constraint(equalTo: detailsView.bottomAnchor, constant: -18),
            
            topSectionsStackView.heightAnchor.constraint(greaterThanOrEqualToConstant: 180),
            clientInfoStackView.widthAnchor.constraint(equalTo: clientReplicaStackView.widthAnchor, multiplier: 1.2),
            verticalDividerView.widthAnchor.constraint(equalToConstant: 1),
            verticalDividerView.heightAnchor.constraint(equalTo: topSectionsStackView.heightAnchor),
            horizontalDividerView.heightAnchor.constraint(equalToConstant: 1)
        ])
    }
    
    func configureDefaultClientInfo(customer: Customer) {
        clientInfoStackView.removeArrangedSubviews()
        clientReplicaStackView.removeArrangedSubviews()
        knownFactsStackView.removeArrangedSubviews()
        
        clientInfoStackView.addArrangedSubview(
            makeInfoRow(
                iconName: "calendar",
                title: "Возраст:",
                value: "\(customer.bio.age)"))
        clientInfoStackView.addArrangedSubview(
            makeInfoRow(iconName: "figure.dress.line.vertical.figure",
                        title: "Пол:",
                        value: "\(customer.bio.gender)"))
        clientInfoStackView.addArrangedSubview(
            makeInfoRow(iconName: "list.clipboard",
                        title: "Контекст:",
                        value: "\(customer.bio.context)"
                       ))
        clientReplicaStackView.addArrangedSubview(
            makeIconTitleRow(
                iconName: "bubble.left",
                title: "Реплика клиента"))
        clientReplicaStackView.addArrangedSubview(
            makeReplicaLabel(
                text: "\(customer.request)"))
        clientReplicaStackView.addArrangedSubview(
            makeFlexibleSpacer())
        
        knownFactsStackView.addArrangedSubview(
            makeIconTitleRow(iconName: "list.clipboard",
                             title: "Известные факты"))
        for fact in customer.facts {
            knownFactsStackView.addArrangedSubview(
                makeFactLabel("\(fact)"))
        }
        knownFactsStackView.addArrangedSubview(
            makeFlexibleSpacer())
    }
    
    private func makeSectionStackView(spacing: CGFloat) -> UIStackView {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = spacing
        return stackView
    }
    
    private func makeInfoRow(iconName: String, title: String, value: String) -> UIView {
        let iconView = makeIconView(systemName: iconName, pointSize: 24)
        let titleLabel = makeLabel(text: title, font: UIFont.systemFont(ofSize: 17, weight: .bold), color: .black)
        let valueLabel = makeLabel(text: value, font: UIFont.systemFont(ofSize: 17, weight: .regular), color: .darkGray)
        titleLabel.setContentCompressionResistancePriority(.required, for: .vertical)
        valueLabel.setContentCompressionResistancePriority(.required, for: .vertical)
        
        let textStackView = UIStackView(arrangedSubviews: [titleLabel, valueLabel])
        textStackView.axis = .vertical
        textStackView.spacing = 4
        textStackView.setContentCompressionResistancePriority(.required, for: .vertical)
        
        let stackView = UIStackView(arrangedSubviews: [iconView, textStackView])
        stackView.axis = .horizontal
        stackView.alignment = .top
        stackView.spacing = 12
        
        NSLayoutConstraint.activate([
            iconView.widthAnchor.constraint(equalToConstant: 26),
            iconView.heightAnchor.constraint(equalToConstant: 26)
        ])
        
        return stackView
    }
    
    private func makeIconTitleRow(iconName: String, title: String) -> UIView {
        let iconView = makeIconView(systemName: iconName, pointSize: 24)
        let titleLabel = makeLabel(text: title, font: UIFont.systemFont(ofSize: 17, weight: .bold), color: .black)
        
        let stackView = UIStackView(arrangedSubviews: [iconView, titleLabel])
        stackView.axis = .horizontal
        stackView.alignment = .center
        stackView.spacing = 12
        stackView.setContentHuggingPriority(.required, for: .vertical)
        stackView.setContentCompressionResistancePriority(.required, for: .vertical)
        
        NSLayoutConstraint.activate([
            iconView.widthAnchor.constraint(equalToConstant: 26),
            iconView.heightAnchor.constraint(equalToConstant: 26)
        ])
        
        return stackView
    }
    
    private func makeReplicaLabel(text: String) -> UILabel {
        let label = makeLabel(
            text: text,
            font: UIFont.italicSystemFont(ofSize: 17),
            color: .darkGray
        )
        label.textAlignment = .center
        label.setContentHuggingPriority(.required, for: .vertical)
        label.setContentCompressionResistancePriority(.required, for: .vertical)
        return label
    }
    
    private func makeFlexibleSpacer() -> UIView {
        let view = UIView()
        view.setContentHuggingPriority(.defaultLow, for: .vertical)
        view.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        return view
    }
    
    private func makeFactLabel(_ text: String) -> UILabel {
        let label = makeLabel(text: "•  \(text)", font: UIFont.systemFont(ofSize: 16, weight: .regular), color: .darkGray)
        let attributedString = NSMutableAttributedString(string: "•  \(text)")
        attributedString.addAttribute(.foregroundColor, value: Colors.rose, range: NSRange(location: 0, length: 1))
        attributedString.addAttribute(.foregroundColor, value: UIColor.darkGray, range: NSRange(location: 3, length: text.count))
        label.attributedText = attributedString
        label.setContentHuggingPriority(.required, for: .vertical)
        label.setContentCompressionResistancePriority(.required, for: .vertical)
        return label
    }
    
    private func makeIconView(systemName: String, pointSize: CGFloat) -> UIImageView {
        let configuration = UIImage.SymbolConfiguration(pointSize: pointSize, weight: .regular)
        let imageView = UIImageView(image: UIImage(systemName: systemName, withConfiguration: configuration))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = Colors.rose
        imageView.contentMode = .scaleAspectFit
        return imageView
    }
    
    private func makeLabel(text: String, font: UIFont, color: UIColor) -> UILabel {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = text
        label.textColor = color
        label.font = font
        label.numberOfLines = 0
        return label
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}

private extension UIStackView {
    func removeArrangedSubviews() {
        arrangedSubviews.forEach { view in
            removeArrangedSubview(view)
            view.removeFromSuperview()
        }
    }
}
