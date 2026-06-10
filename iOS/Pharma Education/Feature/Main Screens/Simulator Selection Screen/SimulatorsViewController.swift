
import UIKit

final class SimulatorsViewController: UIViewController {

    private var viewModel: SimulatorsViewmodelProtocol
    private let contetntView = SimulatorsView()
    private let tableViewHandler: SimulatorTableViewHandler
    
    init(viewModel: SimulatorsViewmodelProtocol = SimulatorsViewmodel(),
         tableViewHandler: SimulatorTableViewHandler = SimulatorTableViewHandler())
    {
        self.viewModel = viewModel
        self.tableViewHandler = tableViewHandler
        self.tableViewHandler.updateSimulators(items: viewModel.testGames)
        contetntView.setupTableView(dataSoutce: self.tableViewHandler,
                                    delegate: self.tableViewHandler)
        super.init(nibName: nil, bundle: nil)
        setupBindings()
    }
    
    override func loadView() {
        view = contetntView
    }
    
    private func setupBindings() {
        tableViewHandler.onCellTap = { [weak self] _ in
            let viewController = SimulatorStartViewController()
            self?.navigationController?.pushViewController(viewController, animated: true)
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
