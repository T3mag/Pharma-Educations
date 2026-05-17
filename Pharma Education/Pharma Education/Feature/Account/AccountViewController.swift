
import UIKit

final class AccountViewController: UIViewController {
    private let contentView: AccountView = .init(frame: .zero)
    private var viewModel: AccountViewModelProtocol
    
    private let statsHandler: AccountTableHandler
    private let settingsHandler: AccountTableHandler
    
    init(viewModel: AccountViewModelProtocol = AccountViewModel()) {
        self.viewModel = viewModel
        self.statsHandler = AccountTableHandler(items: viewModel.stats)
        self.settingsHandler = AccountTableHandler(items: viewModel.settings)
        super.init(nibName: nil, bundle: nil)
    }
    
    override func loadView() {
        view = contentView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        setupActions()
        setupTableView()
        reloadContetnt()
    }
    
    private func setupActions() {
        contentView.onLogoutTap = {[weak self] in
            self?.navigationController?.popViewController(animated: true)
        }
    }
    
    private func setupTableView() {
        contentView.configureStatsTablewViews(
            statsDataSource: statsHandler,
            statsDelegate: statsHandler,
            settingsDataSources: settingsHandler,
            settingsDelegate: settingsHandler)
    }
    
    private func reloadContetnt() {
        contentView.reloadTableViews()
        contentView.updateTableViewHeights()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}

