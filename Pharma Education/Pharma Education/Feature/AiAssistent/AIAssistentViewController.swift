
import UIKit

final class AIAssistentViewController: UIViewController {
    
    private let contentView: AIAssistentView = .init(frame: .zero)
    private var tableViewHandler: AIAssistentTableViewHandller
    private let viewModel: AIAssistentViewModelProtocol
    
    init(tableViewHandler: AIAssistentTableViewHandller = AIAssistentTableViewHandller(),
         viewModel: AIAssistentViewModelProtocol = AIAssistentViewModel()
    ) {
        self.tableViewHandler = tableViewHandler
        self.viewModel = viewModel
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
        viewModel.onMessagesChangeed = { [weak self] in
            self?.tableViewHandler.updateMessages(messages: self?.viewModel.testMessages ?? [])
            self?.contentView.reloadTableView()
        }
    }

}
