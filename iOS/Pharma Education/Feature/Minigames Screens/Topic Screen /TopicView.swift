
import UIKit

final class TopicView: UIView {
    
    var onStartTap: (() -> Void)?
    
    private lazy var backgroundDesignView = BackgroundDesignView()

    private lazy var topicTableView: UITableView = {
        let tableView = UITableView(frame: .zero, style: .insetGrouped)
        tableView.translatesAutoresizingMaskIntoConstraints = false
        tableView.separatorStyle = .none
        tableView.backgroundColor = .clear
        tableView.showsVerticalScrollIndicator = false
        tableView.register(SelectedAllCell.self,
                           forCellReuseIdentifier: SelectedAllCell.reuseIdentifier)
        tableView.register(TopicCell.self,
                           forCellReuseIdentifier: TopicCell.reuseIdentifier)
        tableView.register(QuestionsCountCell.self,
                           forCellReuseIdentifier: QuestionsCountCell.reuseIdentifier)
        return tableView
    }()
    
    private lazy var startButton: StartButtonView = {
        let view = StartButtonView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.isUserInteractionEnabled = true

        let tap = UITapGestureRecognizer(target: self, action: #selector(startButtonTapped))
        view.addGestureRecognizer(tap)
        return view
    }()
    
    func uptdateStartView(countTopics: Int) {
        startButton.confugureButtonInfo(countTopics: countTopics)
        reloadInputViews()
    }
    
    func setupTableView(
        delegate: UITableViewDelegate,
        dataSources: UITableViewDataSource
    ){
        topicTableView.dataSource = dataSources
        topicTableView.delegate = delegate
    }
    
    func reloadTableView() {
        topicTableView.reloadData()
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()

        startButton.layer.cornerRadius = startButton.bounds.height * TopicConstants.General.percentageOfRounding
    }
    
    private func setupHierarchy() {
        addSubview(backgroundDesignView)
        addSubview(topicTableView)
        addSubview(startButton)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            backgroundDesignView.topAnchor.constraint(
                equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(
                equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(
                equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(
                equalTo: bottomAnchor)
        ])
        
        NSLayoutConstraint.activate([
            
            topicTableView.topAnchor.constraint(
                equalTo: topAnchor),
            topicTableView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor),
            topicTableView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor),
            topicTableView.bottomAnchor.constraint(
                equalTo: startButton.topAnchor,
                constant: TopicConstants.General.indentFromSaveArea),
            
            startButton.bottomAnchor.constraint(
                equalTo: safeAreaLayoutGuide.bottomAnchor,
                constant: -TopicConstants.General.indentFromSaveArea),
            startButton.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: TopicConstants.General.indentFromSaveArea),
            startButton.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -TopicConstants.General.indentFromSaveArea),
        ])
    }
    
    @objc
    private func startButtonTapped() {
        onStartTap?()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
