
import UIKit

final class AIAssistentMessageTableViewCell: UITableViewCell {
    
    static let reuseIdentifire = "AIAssistentMesageCell"
    
    private var leadingConstraint: NSLayoutConstraint?
    private var trailingConstraint: NSLayoutConstraint?
    
    private lazy var typingIndicatorView = TypingIndicatorView()
    
    private lazy var bubbleView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.clipsToBounds = true
        view.layer.cornerRadius = AIAssistentConstants.MessageCell.backgroundViewCornerRadius
        return view
    }()
    
    private lazy var messageLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 0
        return label
    }()
    
    private lazy var timeLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textAlignment = .right
        return label
    }()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupUI()
    }
    
    func configure(with message: ChatMessage) {
        
        messageLabel.text = message.text
        timeLabel.text = message.time
        
        leadingConstraint?.isActive = false
        trailingConstraint?.isActive = false
        
        messageLabel.isHidden = true
        timeLabel.isHidden = true
        typingIndicatorView.isHidden = true
        
        backgroundColor = .clear
        contentView.backgroundColor = .clear
        
        if message.isUserMessage {
            bubbleView.backgroundColor = Colors.rose
            messageLabel.textColor = .white
            timeLabel.textColor = .white
            
            trailingConstraint?.isActive = true
            messageLabel.isHidden = false
            timeLabel.isHidden = false
            
            typingIndicatorView.removeFromSuperview()
        } else {
            bubbleView.backgroundColor = .white
            messageLabel.textColor = .black
            timeLabel.textColor = .black
            leadingConstraint?.isActive = true
            
            if message.text == "" && message.time == "" {
                typingIndicatorView.isHidden = false
            } else {
                typingIndicatorView.removeFromSuperview()
                messageLabel.isHidden = false
                timeLabel.isHidden = false
            }
        }
    }
    
    private func setupUI() {
        selectionStyle = .none
        backgroundColor = .clear
        
        contentView.addSubview(bubbleView)
        bubbleView.addSubview(typingIndicatorView)
        bubbleView.addSubview(messageLabel)
        bubbleView.addSubview(timeLabel)
        
        leadingConstraint = bubbleView.leadingAnchor.constraint(
            equalTo: contentView.leadingAnchor,
            constant: AIAssistentConstants.MessageCell.backgroundIndents)
        trailingConstraint = bubbleView.trailingAnchor.constraint(
            equalTo: contentView.trailingAnchor,
            constant: -AIAssistentConstants.MessageCell.backgroundIndents)
        
        NSLayoutConstraint.activate([
            bubbleView.topAnchor.constraint(
                equalTo: contentView.topAnchor,
                constant: AIAssistentConstants.MessageCell.backgroundIndents),
            bubbleView.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -AIAssistentConstants.MessageCell.backgroundIndents),
            bubbleView.widthAnchor.constraint(
                lessThanOrEqualTo: contentView.widthAnchor,
                multiplier: AIAssistentConstants.MessageCell.backgroundViewMaxWidthMultiplier),
            bubbleView.widthAnchor.constraint(
                greaterThanOrEqualTo: contentView.widthAnchor,
                multiplier: AIAssistentConstants.MessageCell.backgroundViewMinWidthMultiplier),
        ])
        
        NSLayoutConstraint.activate([
            typingIndicatorView.topAnchor.constraint(
                equalTo: bubbleView.topAnchor,
                constant: AIAssistentConstants.MessageCell.typingIndents),
            typingIndicatorView.bottomAnchor.constraint(
                equalTo: bubbleView.bottomAnchor,
                constant: -AIAssistentConstants.MessageCell.typingIndents),
            typingIndicatorView.centerXAnchor.constraint(
                equalTo: bubbleView.centerXAnchor),
            typingIndicatorView.widthAnchor.constraint(
                lessThanOrEqualTo: bubbleView.widthAnchor,
                multiplier: 0.9),
        ])
        
        NSLayoutConstraint.activate([
            messageLabel.topAnchor.constraint(
                equalTo: bubbleView.topAnchor,
                constant: AIAssistentConstants.MessageCell.labelIndents),
            messageLabel.leadingAnchor.constraint(
                equalTo: bubbleView.leadingAnchor,
                constant: AIAssistentConstants.MessageCell.labelIndents),
            messageLabel.trailingAnchor.constraint(
                equalTo: bubbleView.trailingAnchor,
                constant: -AIAssistentConstants.MessageCell.labelIndents),
            messageLabel.bottomAnchor.constraint(
                equalTo: timeLabel.topAnchor,
                constant: -AIAssistentConstants.MessageCell.labelIndents),
            timeLabel.trailingAnchor.constraint(
                equalTo: bubbleView.trailingAnchor,
                constant: -AIAssistentConstants.MessageCell.labelIndents),
            timeLabel.bottomAnchor.constraint(
                equalTo: bubbleView.bottomAnchor,
                constant: -AIAssistentConstants.MessageCell.labelIndents),
            timeLabel.leadingAnchor.constraint(
                equalTo: messageLabel.leadingAnchor)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
