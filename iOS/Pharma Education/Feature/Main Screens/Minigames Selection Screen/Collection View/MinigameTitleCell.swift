
import UIKit

final class MinigameTitleCollectionViewCell: UICollectionViewCell {
    
    static let reuseIdentifier = "MinigameTitleCollectionViewCell"
    
    private lazy var titleStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = MinigameConstants.TitleCell.spacingStackview
        return stackView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.numberOfLines = 1
        label.textAlignment = .left
        label.text = MinigameTexts.TitleCell.title
        label.font = MinigameFonts.TitleCell.titleFont
        return label
    }()
    
    private lazy var subtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.numberOfLines = 2
        label.textAlignment = .left
        label.text = MinigameTexts.TitleCell.subtitle
        label.font = MinigameFonts.TitleCell.subtitleFont
        return label
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    private func setupHierarchy() {
        addSubview(titleStackView)
        
        titleStackView.addArrangedSubview(titleLabel)
        titleStackView.addArrangedSubview(subtitleLabel)
    }
    
    private func setupLayout() {
        backgroundColor = .clear
        isUserInteractionEnabled = false
        
        NSLayoutConstraint.activate([            
            titleStackView.centerYAnchor.constraint(equalTo: centerYAnchor),
            titleStackView.leadingAnchor.constraint(equalTo: leadingAnchor),
            titleStackView.trailingAnchor.constraint(equalTo: trailingAnchor)
            
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
