
import UIKit

final class RegistrationViewController: UIViewController {
    private let contentView: RegistartionView = .init(frame: .zero)
    
    override func loadView() {
        view = contentView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupActions()
    }
    
    private func setupActions() {
        
        contentView.onRegisterTap = { [weak self] in
            print("hi")
        }
    }

}
