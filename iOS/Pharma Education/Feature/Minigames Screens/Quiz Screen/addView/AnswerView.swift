
import UIKit

final class AnswerView: UIView {
    
    var onCheckTap: (() -> Void)?
    private(set) var isChecked = false
    
    private(set) lazy var answerLabel: UILabel = {
        let label = UILabel()
        label.numberOfLines = 0
        label.font = UIFont.systemFont(ofSize: 15, weight: .semibold)
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        return label
    }()
    
    private lazy var checkboxButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.tintColor = .systemGray2
        button.setImage(UIImage(systemName: "circle"), for: .normal)
        button.addTarget(self, action: #selector(configureCheckBox), for: .touchUpInside)
        return button
    }()
    
    func configureTitle(title: String) {
        answerLabel.text = title
    }
    func setCheck(_ isCheked: Bool) {
        self.isChecked = isCheked
        
        let imageName = isChecked ? "checkmark.circle.fill" : "circle"
        checkboxButton.setImage(UIImage(systemName: imageName), for: .normal)
        checkboxButton.tintColor = isChecked ? Colors.rose : .systemGray2
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupLayout()
    }
    
    override func layoutSubviews() {
        clipsToBounds = true
        layer.cornerRadius = frame.height * 0.4
    }
    
    private func setupLayout() {
        backgroundColor = .white
        addSubview(answerLabel)
        addSubview(checkboxButton)
        
        NSLayoutConstraint.activate([
            checkboxButton.topAnchor.constraint(equalTo: topAnchor, constant: 20),
            checkboxButton.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 20),
            checkboxButton.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -20),
            checkboxButton.widthAnchor.constraint(equalToConstant: 40),
            checkboxButton.heightAnchor.constraint(equalToConstant: 40),
            
            answerLabel.centerYAnchor.constraint(equalTo: checkboxButton.centerYAnchor),
            answerLabel.leadingAnchor.constraint(equalTo: checkboxButton.trailingAnchor, constant: 20),
            answerLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -20)
        ])
    }
    @objc
    private func configureCheckBox() {
        onCheckTap?()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
}
