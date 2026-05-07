
import UIKit

final class ChatView: UIView {
    
    var onSendTap: ((String) -> Void)?

    private lazy var sendButton: UIButton = {
        let button = AuxiliaryUIViews.sendButton
        button.addTarget(self, action: #selector(sendButtonTapped), for: .touchUpInside)
        return button
    }()
    
    private lazy var messagesTableView: UITableView = {
        let tableView = UITableView()
        tableView.translatesAutoresizingMaskIntoConstraints = false
        return tableView
    }()
    
    private lazy var centreTextLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = Texts.ChatWithAi.centerText
        label.font = Fonts.ChatAI.title
        label.textColor = .black
        label.textAlignment = .center
        label.numberOfLines = 0
        return label
    }()
    
    private lazy var messageInputTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.placeholder = Texts.ChatWithAi.messegeInputPlaceholder
        textField.backgroundColor = .secondarySystemBackground
        textField.layer.cornerRadius = Constants.Chat.heightTextField * 0.3
        textField.autocapitalizationType = .none
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.clipsToBounds = true

        let rightContainer = UIView(frame: CGRect(
            x: 0,
            y: 0,
            width: Constants.Chat.heightTextField * Constants.Chat.scaleSearchButtonSize + 10,
            height: Constants.Chat.heightTextField)
        )
        sendButton.frame = CGRect(
            x: 0,
            y: (Constants.Chat.heightTextField - 32) / 2,
            width: Constants.Chat.heightTextField * Constants.Chat.scaleSearchButtonSize,
            height: Constants.Chat.heightTextField * Constants.Chat.scaleSearchButtonSize
        )
        rightContainer.addSubview(sendButton)

        textField.rightView = rightContainer
        textField.rightViewMode = .always
        
        return textField
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierhacy()
        setupLayout()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setupHierhacy() {
        addSubview(messagesTableView)
        addSubview(centreTextLabel)
        addSubview(messageInputTextField)
    }
    
    private func setupLayout() {
        backgroundColor = .systemBackground
        
        NSLayoutConstraint.activate([
            messageInputTextField.bottomAnchor.constraint(
                equalTo: safeAreaLayoutGuide.bottomAnchor,
                constant: -Constants.Chat.indentsFromSafeArea),
            messageInputTextField.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: Constants.Chat.indentsFromSafeArea),
            messageInputTextField.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -Constants.Chat.indentsFromSafeArea),
            messageInputTextField.heightAnchor.constraint(
                equalToConstant: Constants.Chat.heightTextField),
            
            centreTextLabel.topAnchor.constraint(
                equalTo: safeAreaLayoutGuide.topAnchor,
                constant: Constants.Chat.indentsFromSafeArea),
            centreTextLabel.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: Constants.Chat.indentsFromSafeArea),
            centreTextLabel.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -Constants.Chat.indentsFromSafeArea)
        ])
    }

    @objc
    private func sendButtonTapped() {
        guard let text = messageInputTextField.text?.trimmingCharacters(in: .whitespacesAndNewlines),
              !text.isEmpty else { return }

        onSendTap?(text)
    }
}
