//
//  Background Design.swift
//  Pharma Education
//
//  Created by Артур Миннушин on 11.05.2026.
//

import UIKit

final class BackgroundDesignView: UIView {
    
    private let firstBottomCircleSize = Constants.BackgroundDesign.bigBottomCircleSize
    private let secondBottomCircleSize = Constants.BackgroundDesign.litleBottomCircleSize
    private let firstTopCircleSize = Constants.BackgroundDesign.bigTopCircleSize
    private let secondTopCircleSize = Constants.BackgroundDesign.litleTopCircleSize
    
    private lazy var firstBottomCircle: UIView = {
        let view = UIView()
        view.layer.cornerRadius = firstBottomCircleSize / 2
        view.backgroundColor = Colors.lightRose
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var secondBottomCircle: UIView = {
        let view = UIView()
        view.layer.cornerRadius = secondBottomCircleSize / 2
        view.backgroundColor = Colors.rose
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var firstTopCircle: UIView = {
        let view = UIView()
        view.layer.cornerRadius = firstTopCircleSize / 2
        view.backgroundColor = Colors.lightRose
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var secondTopCircle: UIView = {
        let view = UIView()
        view.layer.cornerRadius = secondTopCircleSize / 2
        view.backgroundColor = Colors.blackRose
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        translatesAutoresizingMaskIntoConstraints = false
        configure()
        isUserInteractionEnabled = false
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func configure() {
        
        addSubview(firstBottomCircle)
        addSubview(secondBottomCircle)
        addSubview(firstTopCircle)
        addSubview(secondTopCircle)
        
        NSLayoutConstraint.activate([
            firstBottomCircle.heightAnchor.constraint(equalToConstant: firstBottomCircleSize),
            firstBottomCircle.widthAnchor.constraint(equalToConstant: firstBottomCircleSize),
            firstBottomCircle.bottomAnchor.constraint(equalTo: bottomAnchor, constant: firstBottomCircleSize / 1.5),
            firstBottomCircle.leadingAnchor.constraint(equalTo: leadingAnchor, constant: -firstBottomCircleSize / 4),
            
            secondBottomCircle.heightAnchor.constraint(equalToConstant: secondBottomCircleSize),
            secondBottomCircle.widthAnchor.constraint(equalToConstant: secondBottomCircleSize),
            secondBottomCircle.bottomAnchor.constraint(equalTo: bottomAnchor, constant: secondBottomCircleSize / 1.5),
            secondBottomCircle.trailingAnchor.constraint(equalTo: trailingAnchor, constant: secondBottomCircleSize / 2)
        ])
        
        NSLayoutConstraint.activate([
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
