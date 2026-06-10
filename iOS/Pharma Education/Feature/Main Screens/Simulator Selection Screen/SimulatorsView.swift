
import UIKit

final class SimulatorsView: UIView {
    
    private lazy var backgroundDesign = BackgroundDesignView()
    
    private lazy var tableView: UITableView = {
        let tableView = UITableView(frame: .zero, style: .grouped)
        tableView.translatesAutoresizingMaskIntoConstraints = false
        tableView.backgroundColor = .clear
        tableView.separatorStyle = .none
        tableView.showsVerticalScrollIndicator = false
        tableView.register(
            SimulatorsTableViewGameCell.self,
            forCellReuseIdentifier: SimulatorsTableViewGameCell.reuseIdentifier)
        tableView.register(
            SimulatorsTableViewTitleCell.self,
            forCellReuseIdentifier: SimulatorsTableViewTitleCell.reuseIdentifier)
        return tableView
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupLayout()
    }
    
    func setupTableView(
        dataSoutce: UITableViewDataSource,
        delegate: UITableViewDelegate)
    {
        tableView.dataSource = dataSoutce
        tableView.delegate = delegate
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        addSubview(backgroundDesign)
        addSubview(tableView)

        NSLayoutConstraint.activate([
            backgroundDesign.topAnchor.constraint(
                equalTo: topAnchor),
            backgroundDesign.leadingAnchor.constraint(
                equalTo: leadingAnchor),
            backgroundDesign.trailingAnchor.constraint(
                equalTo: trailingAnchor),
            backgroundDesign.bottomAnchor.constraint(
                equalTo: bottomAnchor)
        ])
        
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(
                equalTo: topAnchor),
            tableView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: SimulatorsConstants.General.indentsFromSaveArea),
            tableView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -SimulatorsConstants.General.indentsFromSaveArea),
            tableView.bottomAnchor.constraint(
                equalTo: safeAreaLayoutGuide.bottomAnchor,
                constant: -SimulatorsConstants.General.indentsFromSaveArea)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
}

