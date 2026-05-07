import UIKit


enum AuxiliaryUIViews {
    static var leftViewForTextField: UIView {
        UIView(frame: CGRect(x: 0, y: 0, width: 10, height: 0))
    }
    
    static var sendButton: UIButton {
        let button = UIButton(type: .system)
        button.frame = CGRect(x: 0, y: 0, width: 32, height: 32)
        button.backgroundColor = .tertiarySystemBackground
        button.layer.cornerRadius = 16
        button.clipsToBounds = true
        button.tintColor = .label
        button.setImage(UIImage(systemName: "arrow.up"), for: .normal)
        return button
    }
    
    static var stackViewContainer: UIView {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }
    
}
