
import UIKit

final class AccountView: UIView {

    private var statisticsTableViewHeightConstraint: NSLayoutConstraint?
    private var settingsTableViewHeightConstraint: NSLayoutConstraint?

    private lazy var levelView = LevelView()

    private lazy var scrollView: UIScrollView = {
        let scrollView = UIScrollView()
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        scrollView.contentInsetAdjustmentBehavior = .never
        return scrollView
    }()
    
    private lazy var contentView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()

    private var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = Constants.AccountView.intervalBetweenStackViews
        return stackView
    }()
    
    private lazy var infoStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .center
        stackView.spacing = Constants.AccountView.intervalInfoStackView
        return stackView
    }()
    
    private lazy var buttonStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = Constants.AccountView.intervalButtonStackView
        return stackView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.numberOfLines = 1
        label.textAlignment = .center
        label.font = Fonts.AccountView.titleFont
        label.text = Texts.Account.titleText
        return label
    }()
    
    private lazy var profileImageView: UIImageView = {
        let imageView = UIImageView()
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.contentMode = .scaleAspectFill
        imageView.clipsToBounds = true
        imageView.backgroundColor = .secondarySystemBackground
        imageView.backgroundColor = .none
        imageView.image = UIImage(systemName: Texts.Account.profileIcon)
        imageView.layer.cornerRadius = Constants.AccountView.avatarSize / 2
        imageView.tintColor = Colors.rose
        return imageView
    }()
    
    private lazy var nameLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.textAlignment = .center
        label.numberOfLines = Constants.AccountView.textLines
        label.text = Texts.Account.testName
        label.font = Fonts.AccountView.nameFont
        return label
    }()
    
    private lazy var emailLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.textAlignment = .center
        label.numberOfLines = Constants.AccountView.textLines
        label.text = Texts.Account.testBirthday
        label.font = Fonts.AccountView.mailFont
        return label
    }()
    
    private lazy var statisticsTableView: UITableView = {
        let tableView = UITableView(frame: .zero, style: .plain)
        return tableView
    }()
    
    private lazy var settingsTableView: UITableView = {
        let tableView = UITableView(frame: .zero, style: .plain)
        return tableView
    }()
    
    private lazy var exitButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = .secondarySystemBackground
        button.setTitleColor(.white, for: .normal)
        button.setTitle(Texts.Account.textExitButton, for: .normal)
        button.layer.cornerRadius = Constants.AccountView.heightButton * Constants.AccountView.buttonRoundingPercentage
        button.backgroundColor = Colors.rose
        return button
    }()

    func configureStatsTablewViews(
        statsDataSource: UITableViewDataSource,
        statsDelegate: UITableViewDelegate,
        settingsDataSources: UITableViewDataSource,
        settingsDelegate: UITableViewDelegate) {
            
        statisticsTableView.dataSource = statsDataSource
        statisticsTableView.delegate = statsDelegate
        settingsTableView.dataSource = settingsDataSources
        settingsTableView.delegate = settingsDelegate
    }

    func updateTableViewHeights() {
        statisticsTableView.layoutIfNeeded()
        settingsTableView.layoutIfNeeded()

        statisticsTableViewHeightConstraint?.constant = statisticsTableView.contentSize.height
        settingsTableViewHeightConstraint?.constant = settingsTableView.contentSize.height
    }

    func reloadTableViews() {
        statisticsTableView.reloadData()
        settingsTableView.reloadData()
    }

    override init(frame: CGRect) {
        super.init(frame: frame)

        setupTableViews([statisticsTableView, settingsTableView])
        setupHierarchy()
        setupLayout()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush

        statisticsTableViewHeightConstraint = statisticsTableView.heightAnchor.constraint(equalToConstant: 0)
        settingsTableViewHeightConstraint = settingsTableView.heightAnchor.constraint(equalToConstant: 0)

        statisticsTableViewHeightConstraint?.isActive = true
        settingsTableViewHeightConstraint?.isActive = true

        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: safeAreaLayoutGuide.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: safeAreaLayoutGuide.bottomAnchor),

            contentView.topAnchor.constraint(equalTo: scrollView.contentLayoutGuide.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.contentLayoutGuide.bottomAnchor),

            contentView.widthAnchor.constraint(equalTo: scrollView.frameLayoutGuide.widthAnchor),

            rootStackView.topAnchor.constraint(equalTo: contentView.topAnchor,
                                               constant: Constants.AccountView.indentsFromSafeArea),
            rootStackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor,
                                                   constant: Constants.AccountView.indentsFromSafeArea),
            rootStackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor,
                                                    constant: -Constants.AccountView.indentsFromSafeArea),
            rootStackView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor,
                                                  constant: -Constants.AccountView.indentsFromSafeArea)
        ])

        NSLayoutConstraint.activate([
            profileImageView.widthAnchor.constraint(equalToConstant: Constants.AccountView.avatarSize),
            profileImageView.heightAnchor.constraint(equalToConstant: Constants.AccountView.avatarSize),

            exitButton.heightAnchor.constraint(equalToConstant: Constants.AccountView.heightButton)
        ])
    }

    private func setupHierarchy() {
        addSubview(scrollView)
        scrollView.addSubview(contentView)
        contentView.addSubview(rootStackView)

        rootStackView.addArrangedSubview(infoStackView)
        rootStackView.addArrangedSubview(buttonStackView)

        infoStackView.addArrangedSubview(titleLabel)
        infoStackView.addArrangedSubview(profileImageView)
        infoStackView.addArrangedSubview(nameLabel)
        infoStackView.addArrangedSubview(emailLabel)

        buttonStackView.addArrangedSubview(levelView)
        buttonStackView.addArrangedSubview(statisticsTableView)
        buttonStackView.addArrangedSubview(settingsTableView)
        buttonStackView.addArrangedSubview(exitButton)
    }
    
    private func setupTableViews(_ tableViews: [UITableView]) {
        
        for tableView in tableViews {
            tableView.translatesAutoresizingMaskIntoConstraints = false
            tableView.backgroundColor = .white
            tableView.separatorStyle = .none
            tableView.showsVerticalScrollIndicator = false
            tableView.isScrollEnabled = false
            tableView.clipsToBounds = true
            //tableView.rowHeight = Constants.AccountView.cellHeight
            tableView.layer.cornerRadius = Constants.AccountView.tableViewCornerRadius
            tableView.register(AccountTableViewCell.self,
                               forCellReuseIdentifier: AccountTableViewCell.reuseIdentifier)
        }
    }
}
