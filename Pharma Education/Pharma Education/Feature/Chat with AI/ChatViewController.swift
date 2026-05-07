//
//  ChatViewController.swift
//  Pharma Education
//
//  Created by Артур Миннушин on 07.05.2026.
//

import UIKit

class ChatViewController: UIViewController {
    
    private let customView: ChatView = .init(frame: .zero)

    override func viewDidLoad() {
        super.viewDidLoad()
    }
    
    override func loadView() {
        view = customView
    }

}
