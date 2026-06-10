import UIKit

final class  MinigameCollectionViewCell: UICollectionViewCell {
    
    private(set) var miniGameType: MiniGamesType?
    static let reuseIdentifier = "MinigameCollectionViewCell"
    
    private let textStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = MinigameConstants.MiniGameCell.spacingBetweenTitleAndSubtitle
        return stackView
    }()
    
    private let miniGameImageView: UIImageView = {
        let imageView = UIImageView()
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.contentMode = .scaleAspectFit
        imageView.clipsToBounds = true
        return imageView
    }()
    
    private let minigameTitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.numberOfLines = 0
        label.textAlignment = .left
        label.font = MinigameFonts.MiniGameCell.titleFont
        return label
    }()
    
    private let minigameSubtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.numberOfLines = 0
        label.textAlignment = .left
        label.font = MinigameFonts.MiniGameCell.subtitleFont
        return label
    }()
    
    private let startButton: UIButton = {
        let button = UIButton()
        let image = UIImage(systemName: "paperplane.fill")?
            .withConfiguration(UIImage.SymbolConfiguration(
                pointSize: MinigameConstants.MiniGameCell.buttonSize * 0.4))
        
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = Colors.lightRose
        button.layer.cornerRadius = MinigameConstants.MiniGameCell.buttonSize / 2
        button.setImage(image, for: .normal)
        button.tintColor = .white
        button.clipsToBounds = true
        return button
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    func configure(item: MinigameItem) {
        miniGameType = item.type
        miniGameImageView.image = UIImage(named: item.imageName)
        minigameTitleLabel.text = item.title
        minigameSubtitleLabel.text = item.subtitle
    }
    
    private func setupHierarchy() {
        contentView.addSubview(miniGameImageView)
        contentView.addSubview(textStackView)
        contentView.addSubview(startButton)
        
        textStackView.addArrangedSubview(minigameTitleLabel)
        textStackView.addArrangedSubview(minigameSubtitleLabel)
    }
    
    private func setupLayout() {
        backgroundColor = .white
        let cornerRadius = bounds.width * MinigameConstants.MiniGameCell.percentageOfCornerRounding
        
        contentView.layer.cornerRadius = cornerRadius
        contentView.layer.masksToBounds = true
        
        layer.cornerRadius = cornerRadius
        layer.masksToBounds = false
        
        NSLayoutConstraint.activate([
            
            miniGameImageView.topAnchor.constraint(
                equalTo: contentView.topAnchor),
            miniGameImageView.centerXAnchor.constraint(
                equalTo: contentView.centerXAnchor),
            miniGameImageView.heightAnchor.constraint(
                lessThanOrEqualTo: contentView.heightAnchor,
                multiplier: 0.5),
            
            textStackView.topAnchor.constraint(
                equalTo: miniGameImageView.bottomAnchor,
                constant: MinigameConstants.MiniGameCell.spacingBetwewnImageAndTitle),
            textStackView.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor,
                constant: MinigameConstants.MiniGameCell.indentsFromContentView),
            textStackView.trailingAnchor.constraint(
                equalTo: startButton.leadingAnchor,
                constant: -MinigameConstants.MiniGameCell.indentsFromContentView),
            textStackView.bottomAnchor.constraint(
                lessThanOrEqualTo: contentView.bottomAnchor,
                constant: -MinigameConstants.MiniGameCell.indentsFromContentView),
            
            startButton.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -MinigameConstants.MiniGameCell.indentsFromContentView),
            startButton.trailingAnchor.constraint(
                equalTo: contentView.trailingAnchor,
                constant: -MinigameConstants.MiniGameCell.indentsFromContentView),
            startButton.widthAnchor.constraint(
                equalToConstant: MinigameConstants.MiniGameCell.buttonSize),
            startButton.heightAnchor.constraint(
                equalToConstant: MinigameConstants.MiniGameCell.buttonSize)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
