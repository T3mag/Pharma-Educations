import UIKit

final class LoginViewController: UIViewController {
    private let contentView: LoginView = .init(frame: .zero)
    private let viewModel: LoginViewModel
    
    init(viewModel: LoginViewModel) {
        self.viewModel = viewModel
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    override func loadView() {
        view = contentView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupActions()
        setupBindings()
    }
    
    private func setupBindings() {
        viewModel.onError = { [weak self] message in
            self?.showError(message)
        }
        viewModel.onSuccess = { [weak self] in
            print("успех")
        }
    }
    
    private func setupActions() {
        contentView.onLoginTap = { [weak self] email, password in
            let mainTabBarController = MainTabBarController()
            self?.navigationController?.pushViewController(mainTabBarController, animated: true)
            //self?.viewModel.auth(email: email, password: password)
        }
        
        contentView.onRegisterTap = { [weak self] in
            let registrationVM = RegistrationViewModel(authService: AuthService.shared)
            let registrationVC = RegistrationViewController(viewModel: registrationVM)
            self?.navigationController?.pushViewController(registrationVC, animated: true)
        }
    }
    
    private func showError(_ message: String) {
        let alert = UIAlertController(title: "Ошибка", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Ок", style: .default))
        present(alert, animated: true)
        
    }

}
