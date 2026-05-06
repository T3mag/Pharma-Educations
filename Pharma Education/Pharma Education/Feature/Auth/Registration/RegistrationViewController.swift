
import UIKit

final class RegistrationViewController: UIViewController {
    private let contentView: RegistartionView = .init(frame: .zero)
    private let viewModel: RegistrationViewModel
    
    init(viewModel: RegistrationViewModel) {
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
        setupBinndings()
    }
    
    private func setupActions() {
        contentView.onRegisterTap = { [weak self] email, password, confirmPassword, surname, name, lastname, birthday in
            self?.viewModel.register(
                email: email,
                password: password,
                confirmPassword: confirmPassword,
                surname: surname,
                name: name,
                lastname: name,
                birthday: birthday
            )
        }
    }
    
    private func setupBinndings() {
        viewModel.onError = { [weak self] message in
            self?.showError(message)
        }
        viewModel.onSuccess = { [weak self] in
            self?.navigationController?.popViewController(animated: true)
        }
    }
    
    private func showError(_ message: String) {
        let alert = UIAlertController(title: "Ошибка", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Ок", style: .default))
        present(alert, animated: true)
        
    }

}
