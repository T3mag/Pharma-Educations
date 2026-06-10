
import UIKit

final class AIAssistantViewController: UIViewController {
    
    private let contentView: AIAssistantView = .init(frame: .zero)
    private var tableViewHandler: AIAssistantTableViewHandler
    private var viewModel: AIAssistantViewModelProtocol
    
    init(
        tableViewHandler: AIAssistantTableViewHandler = AIAssistantTableViewHandler(),
         viewModel: AIAssistantViewModelProtocol = AIAssistantViewModel()
    ) {
        self.tableViewHandler = tableViewHandler
        self.viewModel = viewModel
        
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        navigationController?.isNavigationBarHidden = true
        setupActions()
        contentView.setupTableView(datesource: tableViewHandler,
                                   delegate: tableViewHandler)
        contentView.reloadTableView()
    }
    
    override func loadView() {
        view = contentView
    }
    
    private func setupActions() {
        contentView.onSendTap = { [weak self] message in
            self?.viewModel.sendMessage(message: message)
        }
        
        viewModel.onMessageAdd = { [weak self] indexPath in
            self?.tableViewHandler.updateMessages(messages: self?.viewModel.testMessages ?? [])
            self?.contentView.updateTableView(indexPath: indexPath)
        }
        
        viewModel.onMessageUpdate = {[weak self] in
            self?.tableViewHandler.updateMessages(messages: self?.viewModel.testMessages ?? [])
            self?.contentView.reloadTableView()
        }
    }

}
