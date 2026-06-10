import UIKit

final class MatchCardView: UIControl {
    
    var onTap: (() -> Void)?
    var onEndpointPan: ((UIPanGestureRecognizer) -> Void)?
    
    private let side: MatchSide
    private let endpointView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .white
        view.layer.borderWidth = 1
        view.layer.borderColor = UIColor.systemGray4.cgColor
        view.isUserInteractionEnabled = true
        view.addGestureRecognizer(UIPanGestureRecognizer(target: MatchCardView.self, action: #selector(endpointPan(_:))))
        return view
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = UIFont.systemFont(ofSize: 14, weight: .semibold)
        label.textAlignment = .center
        label.textColor = .black
        label.numberOfLines = 0
        return label
    }()
    
    init(side: MatchSide) {
        self.side = side
        super.init(frame: .zero)
        setupLayout()
        addTarget(self, action: #selector(cardTap), for: .touchUpInside)
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        layer.cornerRadius = self.frame.height * 0.2
        endpointView.layer.cornerRadius = endpointView.frame.width / 2
    }
    
    func configure(title: String) {
        titleLabel.text = title
    }
    
    func setSelected(_ isSelected: Bool) {
        layer.borderColor = isSelected ? Colors.rose.cgColor : UIColor.systemGray5.cgColor
        layer.borderWidth = isSelected ? 2 : 1
        backgroundColor = isSelected ? Colors.softPink.withAlphaComponent(0.35) : .white
    }
    
    func setConnected(_ isConnected: Bool) {
        endpointView.backgroundColor = isConnected ? Colors.rose : .white
        endpointView.layer.borderColor = isConnected ? Colors.rose.cgColor : UIColor.systemGray4.cgColor
    }
    
    func endpointCenter(in view: UIView) -> CGPoint {
        convert(endpointView.center, to: view)
    }
    
    private func setupLayout() {
        translatesAutoresizingMaskIntoConstraints = false
        backgroundColor = .white
        layer.borderColor = UIColor.systemGray5.cgColor
        layer.shadowColor = UIColor.black.cgColor
        layer.borderWidth = 1
        layer.shadowOpacity = 0.08
        layer.shadowRadius = 8
        layer.shadowOffset = CGSize(width: 0, height: 4)
        
        addSubview(titleLabel)
        addSubview(endpointView)
        
        let endpointHorizontalConstraint: NSLayoutConstraint
        let titleLeadingConstraint: NSLayoutConstraint
        let titleTrailingConstraint: NSLayoutConstraint
        
        switch side {
        case .left:
            endpointHorizontalConstraint = endpointView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: 8)
            titleLeadingConstraint = titleLabel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 12)
            titleTrailingConstraint = titleLabel.trailingAnchor.constraint(equalTo: endpointView.leadingAnchor, constant: -12)
        case .right:
            endpointHorizontalConstraint = endpointView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: -8)
            titleLeadingConstraint = titleLabel.leadingAnchor.constraint(equalTo: endpointView.trailingAnchor, constant: 12)
            titleTrailingConstraint = titleLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -12)
        }
        
        NSLayoutConstraint.activate([
            heightAnchor.constraint(equalToConstant: 92),
            
            endpointHorizontalConstraint,
            endpointView.centerYAnchor.constraint(
                equalTo: centerYAnchor),
            endpointView.widthAnchor.constraint(
                equalToConstant: 18),
            endpointView.heightAnchor.constraint(
                equalTo: endpointView.widthAnchor),
            
            titleLeadingConstraint,
            titleLabel.centerYAnchor.constraint(equalTo: centerYAnchor),
            titleTrailingConstraint
        ])
    }
    
    @objc
    private func cardTap() {
        onTap?()
    }
    
    @objc
    private func endpointPan(_ gesture: UIPanGestureRecognizer) {
        onEndpointPan?(gesture)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
