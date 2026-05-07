import UIKit


enum AuxiliaryUIViews {
    static var leftViewForTextField: UIView {
        UIView(frame: CGRect(x: 0, y: 0, width: 10, height: 0))
    }
    
    static var stackViewContainer: UIView {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }
    
}
