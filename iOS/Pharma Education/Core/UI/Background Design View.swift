import UIKit

final class BackgroundDesignView: UIView {
    
    private let firstBottomCircleSize = Constants.BackgroundDesign.bigBottomCircleSize
    private let secondBottomCircleSize = Constants.BackgroundDesign.litleBottomCircleSize
    private let firstTopCircleSize = Constants.BackgroundDesign.bigTopCircleSize
    private let secondTopCircleSize = Constants.BackgroundDesign.litleTopCircleSize
    
    private lazy var firstBottomCircle = makeCircle(
        size: firstBottomCircleSize,
        color: Colors.lightRose
    )
    
    private lazy var secondBottomCircle = makeCircle(
        size: secondBottomCircleSize,
        color: Colors.rose
    )
    
    private lazy var firstTopCircle = makeCircle(
        size: firstTopCircleSize,
        color: Colors.lightRose
    )
    
    private lazy var secondTopCircle = makeCircle(
        size: secondTopCircleSize,
        color: Colors.blackRose
    )
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        translatesAutoresizingMaskIntoConstraints = false
        isUserInteractionEnabled = false
        setupHierarchy()
        setupLayout()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func makeCircle(size: CGFloat, color: UIColor) -> UIView {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = color
        view.layer.cornerRadius = size / 2
        return view
    }
    
    private func setupHierarchy() {
        addSubview(firstBottomCircle)
        addSubview(secondBottomCircle)
        addSubview(firstTopCircle)
        addSubview(secondTopCircle)
    }
    
    private func setupLayout() {
        NSLayoutConstraint.activate([
            firstBottomCircle.heightAnchor.constraint(equalToConstant: firstBottomCircleSize),
            firstBottomCircle.widthAnchor.constraint(equalToConstant: firstBottomCircleSize),
            firstBottomCircle.bottomAnchor.constraint(equalTo: bottomAnchor, constant: firstBottomCircleSize / 1.3),
            firstBottomCircle.leadingAnchor.constraint(equalTo: leadingAnchor, constant: -firstBottomCircleSize / 4),
            
            secondBottomCircle.heightAnchor.constraint(equalToConstant: secondBottomCircleSize),
            secondBottomCircle.widthAnchor.constraint(equalToConstant: secondBottomCircleSize),
            secondBottomCircle.bottomAnchor.constraint(equalTo: bottomAnchor, constant: secondBottomCircleSize / 1.3),
            secondBottomCircle.trailingAnchor.constraint(equalTo: trailingAnchor, constant: secondBottomCircleSize / 2),
            
            firstTopCircle.heightAnchor.constraint(equalToConstant: firstTopCircleSize),
            firstTopCircle.widthAnchor.constraint(equalToConstant: firstTopCircleSize),
            firstTopCircle.trailingAnchor.constraint(equalTo: trailingAnchor, constant: firstTopCircleSize / 2),
            firstTopCircle.topAnchor.constraint(equalTo: topAnchor, constant: -firstTopCircleSize / 2),
            
            secondTopCircle.heightAnchor.constraint(equalToConstant: secondTopCircleSize),
            secondTopCircle.widthAnchor.constraint(equalToConstant: secondTopCircleSize),
            secondTopCircle.trailingAnchor.constraint(equalTo: trailingAnchor, constant: secondTopCircleSize / 2),
            secondTopCircle.topAnchor.constraint(equalTo: firstTopCircle.bottomAnchor, constant: -firstTopCircleSize / 4)
        ])
    }
}
