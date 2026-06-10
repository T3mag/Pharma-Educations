
import UIKit

final class AIAssistantMessageTableViewCell: UITableViewCell {
    
    static let reuseIdentifier = "AIAssistantMessageCell"
    
    private var leadingConstraint: NSLayoutConstraint?
    private var trailingConstraint: NSLayoutConstraint?
    
    private lazy var typingIndicatorView = TypingIndicatorView()
    
    private lazy var bubbleView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.clipsToBounds = true
        view.layer.cornerRadius = AIAssistantConstants.MessageCell.backgroundViewCornerRadius
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
            constant: AIAssistantConstants.MessageCell.backgroundIndents)
        trailingConstraint = bubbleView.trailingAnchor.constraint(
            equalTo: contentView.trailingAnchor,
            constant: -AIAssistantConstants.MessageCell.backgroundIndents)
        
        NSLayoutConstraint.activate([
            bubbleView.topAnchor.constraint(
                equalTo: contentView.topAnchor,
                constant: AIAssistantConstants.MessageCell.backgroundIndents),
            bubbleView.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -AIAssistantConstants.MessageCell.backgroundIndents),
            bubbleView.widthAnchor.constraint(
                lessThanOrEqualTo: contentView.widthAnchor,
                multiplier: AIAssistantConstants.MessageCell.backgroundViewMaxWidthMultiplier),
            bubbleView.widthAnchor.constraint(
                greaterThanOrEqualTo: contentView.widthAnchor,
                multiplier: AIAssistantConstants.MessageCell.backgroundViewMinWidthMultiplier),
        ])
        
        NSLayoutConstraint.activate([
            typingIndicatorView.topAnchor.constraint(
                equalTo: bubbleView.topAnchor,
                constant: AIAssistantConstants.MessageCell.typingIndents),
            typingIndicatorView.bottomAnchor.constraint(
                equalTo: bubbleView.bottomAnchor,
                constant: -AIAssistantConstants.MessageCell.typingIndents),
            typingIndicatorView.centerXAnchor.constraint(
                equalTo: bubbleView.centerXAnchor),
            typingIndicatorView.widthAnchor.constraint(
                lessThanOrEqualTo: bubbleView.widthAnchor,
                multiplier: 0.9),
        ])
        
        NSLayoutConstraint.activate([
            messageLabel.topAnchor.constraint(
                equalTo: bubbleView.topAnchor,
                constant: AIAssistantConstants.MessageCell.labelIndents),
            messageLabel.leadingAnchor.constraint(
                equalTo: bubbleView.leadingAnchor,
                constant: AIAssistantConstants.MessageCell.labelIndents),
            messageLabel.trailingAnchor.constraint(
                equalTo: bubbleView.trailingAnchor,
                constant: -AIAssistantConstants.MessageCell.labelIndents),
            messageLabel.bottomAnchor.constraint(
                equalTo: timeLabel.topAnchor,
                constant: -AIAssistantConstants.MessageCell.labelIndents),
            timeLabel.trailingAnchor.constraint(
                equalTo: bubbleView.trailingAnchor,
                constant: -AIAssistantConstants.MessageCell.labelIndents),
            timeLabel.bottomAnchor.constraint(
                equalTo: bubbleView.bottomAnchor,
                constant: -AIAssistantConstants.MessageCell.labelIndents),
            timeLabel.leadingAnchor.constraint(
                equalTo: messageLabel.leadingAnchor)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
