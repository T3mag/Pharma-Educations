import UIKit

final class PharmacyFinishRatingView: UIView {
    
    private let score: Int
    
    private lazy var ratingIconView: UIView = makeRatingIconView()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.text = "Общий рейтинг работы"
        label.textColor = .darkGray
        label.font = UIFont.systemFont(ofSize: 20, weight: .regular)
        return label
    }()
    
    private lazy var scoreLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.attributedText = makeScoreText(score: score)
        return label
    }()
    
    private lazy var progressTrackView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = Colors.softPink.withAlphaComponent(0.56)
        view.layer.cornerRadius = 5
        view.clipsToBounds = true
        return view
    }()
    
    private lazy var progressFillView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = Colors.blackRose
        view.layer.cornerRadius = 5
        view.clipsToBounds = true
        return view
    }()
    
    init(score: Int) {
        self.score = max(0, min(score, 100))
        super.init(frame: .zero)
        setupAppearance()
        setupHierarchy()
        setupLayout()
    }
    
    private func setupAppearance() {
        translatesAutoresizingMaskIntoConstraints = false
        backgroundColor = .white.withAlphaComponent(0.96)
        layer.cornerRadius = 28
        layer.shadowColor = UIColor.black.cgColor
        layer.shadowOpacity = 0.08
        layer.shadowRadius = 18
        layer.shadowOffset = CGSize(width: 0, height: 8)
    }
    
    private func setupHierarchy() {
        addSubview(ratingIconView)
        addSubview(titleLabel)
        addSubview(scoreLabel)
        addSubview(progressTrackView)
        progressTrackView.addSubview(progressFillView)
    }
    
    private func setupLayout() {
        let progressWidthMultiplier = max(0.04, CGFloat(score) / 100)
        
        NSLayoutConstraint.activate([
            ratingIconView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 24),
            ratingIconView.topAnchor.constraint(greaterThanOrEqualTo: topAnchor, constant: 24),
            ratingIconView.centerYAnchor.constraint(equalTo: centerYAnchor),
            ratingIconView.widthAnchor.constraint(equalToConstant: 106),
            ratingIconView.heightAnchor.constraint(equalToConstant: 106),
            
            titleLabel.leadingAnchor.constraint(equalTo: ratingIconView.trailingAnchor, constant: 24),
            titleLabel.topAnchor.constraint(equalTo: topAnchor, constant: 34),
            titleLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -24),
            
            scoreLabel.leadingAnchor.constraint(equalTo: titleLabel.leadingAnchor),
            scoreLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 8),
            scoreLabel.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -24),
            
            progressTrackView.leadingAnchor.constraint(equalTo: titleLabel.leadingAnchor),
            progressTrackView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -38),
            progressTrackView.topAnchor.constraint(equalTo: scoreLabel.bottomAnchor, constant: 8),
            progressTrackView.heightAnchor.constraint(equalToConstant: 10),
            progressTrackView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -34),
            
            progressFillView.topAnchor.constraint(equalTo: progressTrackView.topAnchor),
            progressFillView.leadingAnchor.constraint(equalTo: progressTrackView.leadingAnchor),
            progressFillView.bottomAnchor.constraint(equalTo: progressTrackView.bottomAnchor),
            progressFillView.widthAnchor.constraint(equalTo: progressTrackView.widthAnchor, multiplier: progressWidthMultiplier)
        ])
    }
    
    private func makeRatingIconView() -> UIView {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = Colors.softPink.withAlphaComponent(0.4)
        view.layer.borderColor = Colors.lightRose.cgColor
        view.layer.borderWidth = 8
        view.layer.cornerRadius = 53
        view.clipsToBounds = true
        
        let iconView = UIImageView(image: UIImage(systemName: "star.fill"))
        iconView.translatesAutoresizingMaskIntoConstraints = false
        iconView.tintColor = Colors.blackRose
        iconView.contentMode = .scaleAspectFit
        
        view.addSubview(iconView)
        NSLayoutConstraint.activate([
            iconView.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            iconView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            iconView.widthAnchor.constraint(equalToConstant: 46),
            iconView.heightAnchor.constraint(equalToConstant: 46)
        ])
        
        return view
    }
    
    private func makeScoreText(score: Int) -> NSAttributedString {
        let text = NSMutableAttributedString(
            string: "\(score)",
            attributes: [
                .font: UIFont.systemFont(ofSize: 54, weight: .bold),
                .foregroundColor: Colors.blackRose
            ]
        )
        text.append(NSAttributedString(
            string: " / 100",
            attributes: [
                .font: UIFont.systemFont(ofSize: 28, weight: .semibold),
                .foregroundColor: Colors.blackRose
            ]
        ))
        return text
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
