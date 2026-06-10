import UIKit

final class PharmacyTimerView: UIView {
    
    private lazy var iconView: UIImageView = {
        let imageView = UIImageView(image: UIImage(systemName: "clock"))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = Colors.rose
        imageView.contentMode = .scaleAspectFit
        return imageView
    }()
    
    private lazy var timerLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "09:42"
        label.textColor = .darkGray
        label.font = UIFont.systemFont(ofSize: 17, weight: .medium)
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
        clipsToBounds = true
        layer.cornerRadius = bounds.height * 0.2
    }
    
    func configure(time: String) {
        timerLabel.text = time
    }
    
    private func setupAppearance() {
        translatesAutoresizingMaskIntoConstraints = false
        backgroundColor = .white
    }
    
    private func setupHierarchy() {
        addSubview(iconView)
        addSubview(timerLabel)
    }
    
    private func setupLayout() {
        NSLayoutConstraint.activate([
            iconView.leadingAnchor.constraint(
                equalTo: leadingAnchor,
                constant: 20),
            iconView.centerYAnchor.constraint(
                equalTo: centerYAnchor),
            iconView.widthAnchor.constraint(
                equalToConstant: 20),
            iconView.heightAnchor.constraint(
                equalToConstant: 20),
            
            timerLabel.leadingAnchor.constraint(
                equalTo: iconView.trailingAnchor,
                constant: 12),
            timerLabel.centerYAnchor.constraint(
                equalTo: centerYAnchor),
            timerLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -18)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
