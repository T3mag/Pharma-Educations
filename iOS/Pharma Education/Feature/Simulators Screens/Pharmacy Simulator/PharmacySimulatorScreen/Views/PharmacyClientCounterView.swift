import UIKit

final class PharmacyClientCounterView: UIView {
    
    private lazy var iconView: UIImageView = {
        let imageView = UIImageView(image: UIImage(systemName: "person.2"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = Colors.rose
        imageView.contentMode = .scaleAspectFit
        return imageView
    }()
    
    private lazy var counterLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "3/10"
        label.textColor = .darkGray
        label.font = UIFont.systemFont(ofSize: 17, weight: .semibold)
        return label
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupAppearance()
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        layer.cornerRadius = bounds.height * 0.2
    }
    
    func configure(currentClient: Int, totalClients: Int) {
        counterLabel.text = "\(currentClient)/\(totalClients)"
    }
    
    private func setupAppearance() {
        translatesAutoresizingMaskIntoConstraints = false
        backgroundColor = .white
        clipsToBounds = true
    }
    
    private func setupHierarchy() {
        addSubview(iconView)
        addSubview(counterLabel)
    }
    
    private func setupLayout() {
        NSLayoutConstraint.activate([
            iconView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 18),
            iconView.centerYAnchor.constraint(equalTo: centerYAnchor),
            iconView.widthAnchor.constraint(equalToConstant: 20),
            iconView.heightAnchor.constraint(equalToConstant: 20),
            
            counterLabel.leadingAnchor.constraint(equalTo: iconView.trailingAnchor, constant: 10),
            counterLabel.centerYAnchor.constraint(equalTo: centerYAnchor),
            counterLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -18)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
