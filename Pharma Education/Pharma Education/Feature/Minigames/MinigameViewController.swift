//
//  MinigameViewController.swift
//  Pharma Education
//
//  Created by Артур Миннушин on 13.05.2026.
//

import UIKit

class MinigameViewController: UIViewController {
    
    private let contentView: MinigameView = .init(frame: .zero)
    private let collectonViewHandler = MinigameCollectionViewHandller(with: MinigameViewModel.testGames)

    override func viewDidLoad() {
        super.viewDidLoad()

        contentView.setupCollectionView(
            dataSources: collectonViewHandler,
            delegate: collectonViewHandler)
    }
    
    override func loadView() {
        view = contentView
    }

}
