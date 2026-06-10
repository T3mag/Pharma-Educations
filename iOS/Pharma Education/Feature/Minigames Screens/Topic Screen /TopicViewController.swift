
import UIKit

class TopicViewController: UIViewController {
    
    private let contentView: TopicView = .init(frame: .zero)
    private var viewModel: TopicViewModelProtocol
    private var tableViewHandller: TopicTableViewHandler
    private var minigameType: MiniGamesType
    
    init(viewModel: TopicViewModelProtocol = TopicViewModel(),
         handler: TopicTableViewHandler = TopicTableViewHandler(), minigameType: MiniGamesType) {
        self.viewModel = viewModel
        self.tableViewHandller = handler
        self.minigameType = minigameType
        super.init(nibName: nil, bundle: nil)
    }
    
    override func loadView() {
        view = contentView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        contentView.setupTableView(delegate: tableViewHandller,
                                  dataSources: tableViewHandller)
        setupBindings()
        viewModel.loadTopics()
    }
    
    override func viewWillAppear(_ animated: Bool) {
        navigationController?.setNavigationBarHidden(false, animated: false)
    }
    
    private func setupBindings() {
        tableViewHandller.onSetTopics = {[weak self] countTopics in
            self?.contentView.uptdateStartView(countTopics: countTopics)
        }
        viewModel.onTopicsLoaded = { [weak self] in
            self?.tableViewHandller.updateTopics(self?.viewModel.topics ?? [])
            self?.contentView.reloadTableView()
        }
        contentView.onStartTap = {[weak self] in
            guard let topics = self?.tableViewHandller.selectedTopicIds,
                  let countQuestions = self?.tableViewHandller.questionsCount else {
                return
            }
            let topicIds = topics
                .filter { !$0.contains(":synthetic:") }
                .sorted()
            
            let vc: UIViewController
            switch self?.minigameType {
            case .quiz:
                vc = QuizViewController(topics: Array(topicIds),
                                        countQuestion: countQuestions)
            case .flashcards:
                vc = FlashcardViewController(topics: Array(topicIds),
                                        countQuestion: countQuestions)
            case .match:
                vc = MatchViewController(topics: Array(topicIds),
                                         countQuestion: countQuestions)
            case .none:
                vc = QuizViewController(topics: Array(topicIds),
                                        countQuestion: countQuestions)
            }
            self?.navigationController?.pushViewController(vc, animated: true)
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
