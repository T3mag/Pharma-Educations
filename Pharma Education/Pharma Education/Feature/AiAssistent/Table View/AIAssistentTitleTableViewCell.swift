import UIKit

final class AIAssistentTitleTableViewCell: UITableViewCell {
    
    static let reuseIdentifire = "AIAssistentTitleCell"
    
    private lazy var topStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .center
        stackView.spacing = AIAssistentConstants.TitleCell.topStackViewSpacing
        return stackView
    }()
    
    private lazy var titleTextField: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = AIAssistenTexts.TitleCell.title
        label.font = AIAssistentFonts.TitleCell.titleFont
        label.textColor = .black
        label.textAlignment = .center
        return label
    }()
    
    private lazy var subTitleTextFiled: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.textAlignment = .center
        label.text = AIAssistenTexts.TitleCell.subtitile
        label.font = AIAssistentFonts.TitleCell.subbtitleFont
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
                constant: -AIAssistentConstants.TitleCell.indentsFromSafeArea)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}


