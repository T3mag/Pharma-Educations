import UIKit

final class LoginViewController: UIViewController {
    private let contentView: LoginView = .init(frame: .zero)
    
    override func loadView() {
        view = contentView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupActions()
    }
    
    private func setupActions() {
        contentView.onLoginTap = { [weak self] in
            print("hello")
        }
        
        contentView.onRegisterTap = { [weak self] in
            let registrationVC = RegistrationViewController()
            self?.navigationController?.pushViewController(registrationVC, animated: true)
        }
    }

}
