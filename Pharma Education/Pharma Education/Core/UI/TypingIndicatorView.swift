import UIKit

final class TypingIndicatorView: UIView {
    
    private lazy var dots: [UIView] = [UIView(), UIView(), UIView()]
    
    private lazy var stackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.spacing = 6
        stackView.alignment = .center
        return stackView
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        configureUI()
        startAnimation()
    }
    
    private func configureUI() {
        translatesAutoresizingMaskIntoConstraints = false
        addSubview(stackView)
        
        dots.forEach { view in
            view.translatesAutoresizingMaskIntoConstraints = false
            view.backgroundColor = .gray
            stackView.addArrangedSubview(view)
            
            NSLayoutConstraint.activate([
                view.heightAnchor.constraint(equalToConstant: 12),
                view.widthAnchor.constraint(equalToConstant: 12)
            ])
            
            view.layer.cornerRadius = 12 / 2
        }
        
        NSLayoutConstraint.activate([
            stackView.topAnchor.constraint(equalTo: topAnchor),
            stackView.leadingAnchor.constraint(equalTo: leadingAnchor),
            stackView.trailingAnchor.constraint(equalTo: trailingAnchor),
            stackView.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
    }
    
    func startAnimation() {
        for(index, dot) in dots.enumerated() {
            UIView.animate(
                withDuration: 0.6,
                delay: Double(index) * 0.2,
                options: [.repeat, .autoreverse],
                animations: {
                    dot.alpha = 0.2
                }
            )
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
}
