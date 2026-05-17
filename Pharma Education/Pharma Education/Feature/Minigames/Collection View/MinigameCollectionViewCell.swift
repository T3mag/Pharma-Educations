import UIKit

final class  MinigameCollectionViewCell: UICollectionViewCell {
    
    static let reuseIdentifier = "MinigameCollectionViewCell"
    
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
        label.numberOfLines = 1
        label.textAlignment = .left
        label.font = MinigameFonts.CollectionCell.titleFont
        return label
    }()
    
    private let minigameSubtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.numberOfLines = 2
        label.textAlignment = .left
        label.font = MinigameFonts.CollectionCell.subtitleFont
        return label
    }()
    
    private let startButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = Colors.lightRose
        button.layer.cornerRadius = MinigameConstants.CollectionCell.buttonSize / 2
        button.setImage(UIImage(systemName: "paperplane.fill"), for: .normal)
        button.tintColor = .white
        button.clipsToBounds = true
        return button
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupLayout()
    }
    
    func configure(item: MinigameItem) {
        miniGameImageView.image = UIImage(named: item.imageName)
        minigameTitleLabel.text = item.title
        minigameSubtitleLabel.text = item.subtitle
    }
    
    private func setupLayout() {
        backgroundColor = .white
        let cornerRadius = bounds.width * MinigameConstants.CollectionCell.percentageOfCornerRounding
        
        contentView.layer.cornerRadius = cornerRadius
        contentView.layer.masksToBounds = true
        
        layer.cornerRadius = cornerRadius
        layer.masksToBounds = false
        
        contentView.addSubview(miniGameImageView)
        contentView.addSubview(minigameTitleLabel)
        contentView.addSubview(minigameSubtitleLabel)
        contentView.addSubview(startButton)
        
        NSLayoutConstraint.activate([
            
            miniGameImageView.topAnchor.constraint(
                equalTo: contentView.topAnchor,
                constant: MinigameConstants.CollectionCell.indentsFromContentView - 10),
            miniGameImageView.centerXAnchor.constraint(
                equalTo: contentView.centerXAnchor),
            miniGameImageView.heightAnchor.constraint(
                equalTo: contentView.heightAnchor,
                multiplier: 0.6),
            miniGameImageView.widthAnchor.constraint(
                lessThanOrEqualTo: contentView.widthAnchor,
                multiplier: 0.4),
            
            minigameTitleLabel.topAnchor.constraint(
                equalTo: miniGameImageView.bottomAnchor,
                constant: MinigameConstants.CollectionCell.spacingBetwewnImageAndTitle),
            minigameTitleLabel.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor,
                constant: MinigameConstants.CollectionCell.indentsFromContentView),
            minigameTitleLabel.trailingAnchor.constraint(
                equalTo: startButton.leadingAnchor,
                constant: -MinigameConstants.CollectionCell.indentsFromContentView),
            
            minigameSubtitleLabel.topAnchor.constraint(
                equalTo: minigameTitleLabel.bottomAnchor,
                constant: MinigameConstants.CollectionCell.spacingBetweenTitleAndSubtitle),
            minigameSubtitleLabel.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor,
                constant: MinigameConstants.CollectionCell.indentsFromContentView),
            minigameSubtitleLabel.trailingAnchor.constraint(
                equalTo: startButton.leadingAnchor,
                constant: -MinigameConstants.CollectionCell.indentsFromContentView),
            minigameSubtitleLabel.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -MinigameConstants.CollectionCell.indentsFromContentView),
            
            startButton.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -MinigameConstants.CollectionCell.indentsFromContentView),
            startButton.trailingAnchor.constraint(
                equalTo: contentView.trailingAnchor,
                constant: -MinigameConstants.CollectionCell.indentsFromContentView),
            startButton.widthAnchor.constraint(
                equalToConstant: MinigameConstants.CollectionCell.buttonSize),
            startButton.heightAnchor.constraint(
                equalToConstant: MinigameConstants.CollectionCell.buttonSize)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
