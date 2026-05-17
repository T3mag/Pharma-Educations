
import UIKit

final class AiAssistentView: UIView {
    
    var onSendTap: ((String) -> Void)?
    
    private lazy var backgroundDesignView: UIView = BackgroundDesignView()
    
    private lazy var messagesTableView: UITableView = {
        let tableView = UITableView(frame: .zero, style: .plain)
        tableView.translatesAutoresizingMaskIntoConstraints = false
        tableView.backgroundColor = .none
        tableView.separatorStyle = .none
        tableView.showsVerticalScrollIndicator = false
        tableView.register(AIAssistentMessageTableViewCell.self,
                           forCellReuseIdentifier: AIAssistentMessageTableViewCell.reuseIdentifire)
        tableView.register(AIAssistentTitleTableViewCell.self,
                           forCellReuseIdentifier: AIAssistentTitleTableViewCell.reuseIdentifire)
        return tableView
    }()
    
    private lazy var messageInputTextField: UITextField = {
        let textField = UITextField()
        let buttonSize = AIAssistentConstants.General.heightTextField * AIAssistentConstants.General.scaleSearchButtonSize
        let heightTextField = AIAssistentConstants.General.heightTextField
        let rightContainer = UIView(frame: CGRect(
            x: 0,
            y: 0,
            width: buttonSize + 10,
            height: heightTextField)
        )
        
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .white
        textField.autocapitalizationType = .none
        textField.placeholder = AiAssistenConstatnts.GeneralTexts.messegeInputPlaceholder
        textField.layer.cornerRadius = AIAssistentConstants.General.heightTextField * AIAssistentConstants.General.percentageOfCurdling
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.clipsToBounds = true
        
        sendButton.frame = CGRect(
            x: 0,
            y: (heightTextField - buttonSize) / 2,
            width: buttonSize,
            height: buttonSize
        )
        sendButton.layer.cornerRadius = sendButton.frame.height / 2
        sendButton.addTarget(self, action: #selector(sendButtonTapped), for: .touchUpInside)
        rightContainer.addSubview(sendButton)

        textField.rightView = rightContainer
        textField.rightViewMode = .always
        
        return textField
    }()
    
    private lazy var sendButton: UIButton = {
        let button = AuxiliaryUIViews.sendButton
        button.backgroundColor = Colors.rose
        button.addTarget(self, action: #selector(sendButtonTapped), for: .touchUpInside)
        return button
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierhacy()
        setupLayout()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    func setupTableView(datesource: UITableViewDataSource,
                        delegate: UITableViewDelegate) {
        messagesTableView.dataSource = datesource
        messagesTableView.delegate = delegate
    }
    
    func reloadTableView() {
        messagesTableView.reloadData()
    }
    
    func updateTableView(index: Int) {
    }
    
    private func setupHierhacy() {
        addSubview(backgroundDesignView)
        addSubview(messagesTableView)
        addSubview(messageInputTextField)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            backgroundDesignView.topAnchor.constraint(equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(equalTo: bottomAnchor),
        ])
        
        NSLayoutConstraint.activate([
            
            messagesTableView.topAnchor.constraint(
                equalTo: safeAreaLayoutGuide.topAnchor),
            messagesTableView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor),
            messagesTableView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor),
            messagesTableView.bottomAnchor.constraint(
                equalTo: messageInputTextField.topAnchor),
            
            messageInputTextField.bottomAnchor.constraint(
                equalTo: safeAreaLayoutGuide.bottomAnchor,
                constant: -AIAssistentConstants.General.indentsFromSafeArea),
            messageInputTextField.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: AIAssistentConstants.General.indentsFromSafeArea),
            messageInputTextField.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -AIAssistentConstants.General.indentsFromSafeArea),
            messageInputTextField.heightAnchor.constraint(
                equalToConstant: AIAssistentConstants.General.heightTextField)
        ])
    }

    @objc
    private func sendButtonTapped() {
        guard let text = messageInputTextField.text?.trimmingCharacters(in: .whitespacesAndNewlines),
              !text.isEmpty else { return }

        onSendTap?(text)
        messageInputTextField.text = ""
    }
}
