import UIKit

public extension UITextField {
    func configurePasswordToggle() {
        isSecureTextEntry = true

        let button = UIButton(type: .system)
        button.setImage(UIImage(systemName: "eye.slash"), for: .normal)
        button.tintColor = .gray
        button.frame = CGRect(x: 0, y: 0, width: 25, height: 20)
        button.addTarget(self, action: #selector(togglePasswordVisibility), for: .touchUpInside)

        let container = UIView(frame: CGRect(x: 0, y: 0, width: 40, height: 24))
        button.center = CGPoint(x: 16, y: container.bounds.midY)
        container.addSubview(button)
        
        rightView = container
        rightViewMode = .always
    }

    @objc
    private func togglePasswordVisibility() {
        isSecureTextEntry.toggle()

        guard let button = rightView?.subviews.first as? UIButton else { return }
        let imageName = isSecureTextEntry ? "eye.slash" : "eye"
        button.setImage(UIImage(systemName: imageName), for: .normal)
    }
}
