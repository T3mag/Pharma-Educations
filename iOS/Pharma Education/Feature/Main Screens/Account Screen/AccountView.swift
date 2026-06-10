
import UIKit

final class AccountView: UIView {
    
    var onLogoutTap: (() -> Void)?
    
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
        stackView.spacing = AccountConstants.General.intervalBetweenStackViews
        return stackView
    }()
    
    private lazy var infoStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .center
        stackView.spacing = AccountConstants.General.intervalInfoStackView
        return stackView
    }()
    
    private lazy var buttonStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = AccountConstants.General.intervalButtonStackView
        return stackView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.numberOfLines = 1
        label.textAlignment = .center
        label.font = AccountFonts.General.titleFont
        label.text = AccountTexts.General.titleText
        return label
    }()
    
    private lazy var profileImageView: UIImageView = {
        let imageView = UIImageView()
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.contentMode = .scaleAspectFill
        imageView.clipsToBounds = true
        imageView.backgroundColor = .secondarySystemBackground
        imageView.backgroundColor = .none
        imageView.image = UIImage(systemName: AccountTexts.General.profileIcon)
        imageView.layer.cornerRadius = AccountConstants.General.avatarSize / 2
        imageView.tintColor = Colors.rose
        return imageView
    }()
    
    private lazy var nameLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.textAlignment = .center
        label.numberOfLines = AccountConstants.General.textLines
        label.text = AccountTexts.General.testName
        label.font = AccountFonts.General.nameFont
        return label
    }()
    
    private lazy var emailLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.textAlignment = .center
        label.numberOfLines = AccountConstants.General.textLines
        label.text = AccountTexts.General.testBirthday
        label.font = AccountFonts.General.mailFont
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
        button.setTitle(AccountTexts.General.textExitButton, for: .normal)
        button.titleLabel?.font = AccountFonts.General.logoutButtonFont
        button.layer.cornerRadius = AccountConstants.General.heightButton * AccountConstants.General.buttonRoundingPercentage
        button.backgroundColor = Colors.rose
        button.addTarget(self, action: #selector(logoutTap), for: .touchUpInside)
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
    
    func updateInfo(info: UserInfoFirestoreItem) {
        nameLabel.text = info.fullName
        emailLabel.text = info.email
        
        levelView.changeLevelViewInfo(
            currentLevel: info.currentLevel,
            currentExp: info.currentExp,
            maxExpOnLevel: 100)
    }

    override init(frame: CGRect) {
        super.init(frame: frame)

        setupTableViews([statisticsTableView, settingsTableView])
        setupHierarchy()
        setupLayout()
    }

    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush

        statisticsTableViewHeightConstraint = statisticsTableView.heightAnchor.constraint(equalToConstant: 0)
        settingsTableViewHeightConstraint = settingsTableView.heightAnchor.constraint(equalToConstant: 0)

        statisticsTableViewHeightConstraint?.isActive = true
        settingsTableViewHeightConstraint?.isActive = true

        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(
                equalTo: topAnchor),
            scrollView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor),
            scrollView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor),
            scrollView.bottomAnchor.constraint(
                equalTo: bottomAnchor),

            contentView.topAnchor.constraint(
                equalTo: scrollView.contentLayoutGuide.topAnchor,
                constant: AccountConstants.General.topIndentForStackView),
            contentView.leadingAnchor.constraint(
                equalTo: scrollView.contentLayoutGuide.leadingAnchor),
            contentView.trailingAnchor.constraint(
                equalTo: scrollView.contentLayoutGuide.trailingAnchor),
            contentView.bottomAnchor.constraint(
                equalTo: scrollView.contentLayoutGuide.bottomAnchor,
                constant: -AccountConstants.General.bottomIndentForStackView),
            contentView.widthAnchor.constraint(
                equalTo: scrollView.frameLayoutGuide.widthAnchor),

            rootStackView.topAnchor.constraint(
                equalTo: contentView.topAnchor,
                constant: AccountConstants.General.indentsFromSafeArea),
            rootStackView.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor,
                constant: AccountConstants.General.indentsFromSafeArea),
            rootStackView.trailingAnchor.constraint(
                equalTo: contentView.trailingAnchor,
                constant: -AccountConstants.General.indentsFromSafeArea),
            rootStackView.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -AccountConstants.General.indentsFromSafeArea)
        ])

        NSLayoutConstraint.activate([
            profileImageView.widthAnchor.constraint(
                equalToConstant: AccountConstants.General.avatarSize),
            profileImageView.heightAnchor.constraint(
                equalToConstant: AccountConstants.General.avatarSize),
            exitButton.heightAnchor.constraint(
                equalToConstant: AccountConstants.General.heightButton)
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
            tableView.layer.cornerRadius = AccountConstants.General.tableViewCornerRadius
            tableView.register(AccountTableViewCell.self,
                               forCellReuseIdentifier: AccountTableViewCell.reuseIdentifier)
        }
    }
    
    @objc
    private func logoutTap() {
        onLogoutTap?()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

}
