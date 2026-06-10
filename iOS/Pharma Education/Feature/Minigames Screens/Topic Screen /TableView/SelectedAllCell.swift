import UIKit

final class SelectedAllCell: UITableViewCell {
    static let reuseIdentifier = "SelectedAllCell"
    
    var onCheckboxTap: (() -> Void)?
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Выбрать все"
        label.font = UIFont.systemFont(ofSize: 15, weight: .semibold)
        label.textColor = .black
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var checkboxButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.tintColor = Colors.rose
        button.addTarget(self, action: #selector(checkboxTapped), for: .touchUpInside)
        return button
    }()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupLayout()
        configure(isChecked: false)
    }
    
    override func prepareForReuse() {
        super.prepareForReuse()
        onCheckboxTap = nil
    }
    
    func configure(isChecked: Bool) {
        let imageName = isChecked ? "checkmark.square.fill" : "square"
        checkboxButton.setImage(UIImage(systemName: imageName), for: .normal)
        checkboxButton.tintColor = isChecked ? Colors.rose : .systemGray2
    }
    
    private func setupLayout() {
        selectionStyle = .none
        backgroundColor = .clear
        contentView.backgroundColor = .white
        
        contentView.addSubview(checkboxButton)
        contentView.addSubview(titleLabel)
        
        NSLayoutConstraint.activate([
            checkboxButton.widthAnchor.constraint(equalToConstant: 30),
            checkboxButton.heightAnchor.constraint(equalToConstant: 30),
            checkboxButton.trailingAnchor.constraint(
                equalTo: contentView.trailingAnchor,
                constant: -20
            ),
            checkboxButton.topAnchor.constraint(
                equalTo: contentView.topAnchor,
                constant: 10
            ),
            checkboxButton.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -10
            ),
            
            titleLabel.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
            titleLabel.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor,
                constant: 20
            ),
            titleLabel.trailingAnchor.constraint(
                lessThanOrEqualTo: checkboxButton.leadingAnchor,
                constant: -12
            )
        ])
    }
    
    @objc
    private func checkboxTapped() {
        onCheckboxTap?()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
