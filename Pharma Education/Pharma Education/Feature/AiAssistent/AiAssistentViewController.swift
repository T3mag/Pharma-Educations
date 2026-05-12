
import UIKit

class AiAssistentViewController: UIViewController {
    
    private let contentView: AiAssistentView = .init(frame: .zero)
    private var tableViewHandler: AiAssistentTableViewHandller
    private let viewModel = AIAssistentViewModel()
    
    init() {
        tableViewHandler = AiAssistentTableViewHandller(with: viewModel.testMessages)
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
        viewModel.onMessagesChangeed = { [weak self] in
            self?.tableViewHandler.updateMessages(messages: self?.viewModel.testMessages ?? [])
            self?.contentView.reloadTableView()
        }
    }

}
