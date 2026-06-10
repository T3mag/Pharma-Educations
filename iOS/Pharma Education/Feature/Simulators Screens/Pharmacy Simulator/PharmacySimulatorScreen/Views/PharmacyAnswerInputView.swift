import UIKit

final class PharmacyAnswerInputView: UIView {
    
    var answerText: String {
        answerTextView.text
    }
    
    func clearAnswer() {
        answerTextView.text = nil
    }
    
    private lazy var titleIconView: UIImageView = {
        let configuration = UIImage.SymbolConfiguration(pointSize: 20, weight: .regular)
        let imageView = UIImageView(image: UIImage(systemName: "bubble.left", withConfiguration: configuration))
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.tintColor = Colors.rose
        imageView.contentMode = .scaleAspectFit
        return imageView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "Введите ответ"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 20, weight: .bold)
        return label
    }()
    
    private lazy var answerTextView: UITextView = {
        let textView = UITextView()
        textView.translatesAutoresizingMaskIntoConstraints = false
        textView.backgroundColor = .white
        textView.layer.borderWidth = 1.2
        textView.layer.borderColor = Colors.rose.cgColor
        textView.textColor = .gray
        textView.clipsToBounds = true
        textView.font = UIFont.systemFont(ofSize: 18, weight: .regular)
        textView.textContainerInset = UIEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)
        return textView
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        
        layer.cornerRadius = bounds.height * 0.1
        answerTextView.layer.cornerRadius = answerTextView.bounds.height * 0.15
        answerTextView.clipsToBounds = true
    }
    
    private func setupHierarchy() {
        addSubview(titleIconView)
        addSubview(titleLabel)
        addSubview(answerTextView)
    }
    
    private func setupLayout() {
        backgroundColor = .white
        clipsToBounds = true
        
        NSLayoutConstraint.activate([
            titleIconView.topAnchor.constraint(equalTo: topAnchor, constant: 24),
            titleIconView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 24),
            titleIconView.widthAnchor.constraint(equalToConstant: 24),
            titleIconView.heightAnchor.constraint(equalToConstant: 24),
            
            titleLabel.centerYAnchor.constraint(equalTo: titleIconView.centerYAnchor),
            titleLabel.leadingAnchor.constraint(equalTo: titleIconView.trailingAnchor, constant: 14),
            titleLabel.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -24),
            
            answerTextView.topAnchor.constraint(equalTo: titleIconView.bottomAnchor, constant: 16),
            answerTextView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            answerTextView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            answerTextView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
