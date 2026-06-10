import UIKit

final class SimulatorStartViewController: UIViewController {
    
    private let contentView = SimulatorStartView(frame: .zero)
    
    override func loadView() {
        view = contentView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupActions()
    }
    
    private func setupActions() {
        contentView.onStartTap = { [weak self] clientsCount, minutesPerClient in
            let viewController = PharmacyViewController(
                timeInMinutes: minutesPerClient,
                countCustomers: clientsCount
            )
            self?.navigationController?.pushViewController(viewController, animated: true)
        }
    }
}
