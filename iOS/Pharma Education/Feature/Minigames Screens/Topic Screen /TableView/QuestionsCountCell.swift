
import UIKit

final class QuestionsCountCell: UITableViewCell {
    
    static let reuseIdentifier = "QuestionsCountCell"
    
    var onValueChanged: ((Int) -> Void)?
    
    private var value: Int = 1 {
        didSet {
            countLabel.text = "\(value)"
            stepper.value = Double(value)
            onValueChanged?(value)
        }
    }
    
    private lazy var containerView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .white
        view.layer.cornerRadius = 16
        return view
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Количество вопросов"
        label.font = .systemFont(ofSize: 16, weight: .semibold)
        label.textColor = .label
        return label
    }()
    
    private lazy var subtitleLabel: UILabel = {
        let label = UILabel()
        label.text = "Выберите от 1 до 100"
        label.font = .systemFont(ofSize: 13, weight: .regular)
        label.textColor = .secondaryLabel
        return label
    }()
    
    private lazy var countLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "1"
        label.font = .systemFont(ofSize: 24, weight: .bold)
        label.textColor = .label
        label.textAlignment = .center
        label.backgroundColor = UIColor.systemGray6
        label.layer.cornerRadius = 12
        label.clipsToBounds = true
        return label
    }()
    
    private lazy var stepper: UIStepper = {
        let stepper = UIStepper()
        stepper.minimumValue = 1
        stepper.maximumValue = 100
        stepper.value = 1
        stepper.stepValue = 1
        stepper.addTarget(self, action: #selector(stepperChanged), for: .valueChanged)
        return stepper
    }()
    
    private lazy var textStackView: UIStackView = {
        let stackView = UIStackView(arrangedSubviews: [titleLabel, subtitleLabel])
        stackView.axis = .vertical
        stackView.spacing = 4
        return stackView
    }()
    
    private lazy var controlStackView: UIStackView = {
        let stackView = UIStackView(arrangedSubviews: [countLabel, stepper])
        stackView.axis = .horizontal
        stackView.alignment = .center
        stackView.spacing = 12
        return stackView
    }()
    
    private lazy var mainStackView: UIStackView = {
        let stackView = UIStackView(arrangedSubviews: [textStackView, controlStackView])
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.alignment = .center
        stackView.distribution = .fill
        stackView.spacing = 16
        return stackView
    }()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupLayout()
        setupAppearance()
    }
    
    override func prepareForReuse() {
        super.prepareForReuse()
        onValueChanged = nil
    }
    
    func configure(value: Int) {
        self.value = min(max(value, 1), 100)
    }
    
    @objc private func stepperChanged() {
        value = Int(stepper.value)
    }
    
    private func setupAppearance() {
        backgroundColor = .clear
        selectionStyle = .none
        contentView.backgroundColor = .clear
    }
    
    private func setupLayout() {
        contentView.addSubview(containerView)
        containerView.addSubview(mainStackView)
        
        NSLayoutConstraint.activate([
            containerView.topAnchor.constraint(
                equalTo: contentView.topAnchor),
            containerView.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor),
            containerView.trailingAnchor.constraint(
                equalTo: contentView.trailingAnchor),
            containerView.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor),
            
            mainStackView.topAnchor.constraint(
                equalTo: containerView.topAnchor,
                constant: 16),
            mainStackView.leadingAnchor.constraint(
                equalTo: containerView.leadingAnchor,
                constant: 16),
            mainStackView.trailingAnchor.constraint(
                equalTo: containerView.trailingAnchor,
                constant: -16),
            mainStackView.bottomAnchor.constraint(
                equalTo: containerView.bottomAnchor,
                constant: -16),
            
            countLabel.widthAnchor.constraint(equalToConstant: 56),
            countLabel.heightAnchor.constraint(equalToConstant: 44)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
