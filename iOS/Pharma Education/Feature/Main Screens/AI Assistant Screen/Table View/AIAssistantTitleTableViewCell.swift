import UIKit

final class AIAssistantTitleTableViewCell: UITableViewCell {
    
    static let reuseIdentifier = "AIAssistantTitleCell"
    
    private lazy var topStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .center
        stackView.spacing = AIAssistantConstants.TitleCell.topStackViewSpacing
        return stackView
    }()
    
    private lazy var titleTextField: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = AIAssistantTexts.TitleCell.title
        label.font = AIAssistantFonts.TitleCell.titleFont
        label.textColor = .black
        label.textAlignment = .center
        return label
    }()
    
    private lazy var subTitleTextFiled: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.textAlignment = .center
        label.text = AIAssistantTexts.TitleCell.subtitle
        label.font = AIAssistantFonts.TitleCell.subtitleFont
        return label
    }()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupHierhacy()
        setupLayout()
    }
    
    private func setupHierhacy() {
        addSubview(topStackView)
        
        topStackView.addArrangedSubview(titleTextField)
        topStackView.addArrangedSubview(subTitleTextFiled)
        
    }
    
    private func setupLayout() {
        backgroundColor = .clear
        
        NSLayoutConstraint.activate([
            topStackView.topAnchor.constraint(
                equalTo: topAnchor),
            topStackView.leadingAnchor.constraint(
                equalTo: leadingAnchor),
            topStackView.trailingAnchor.constraint(
                equalTo: trailingAnchor),
            topStackView.bottomAnchor.constraint(
                equalTo: bottomAnchor,
                constant: -AIAssistantConstants.TitleCell.indentsFromSafeArea)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}


