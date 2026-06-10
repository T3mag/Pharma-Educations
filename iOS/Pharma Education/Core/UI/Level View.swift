import UIKit

final class LevelView: UIView {
    
    private lazy var topStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.distribution = .fillEqually
        return stackView
    }()
    
    private lazy var levelLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textAlignment = .left
        label.textColor = .black
        label.text = Texts.LevelView.level + " " + "1"
        label.font = Fonts.LevelView.levelFont
        return label
    }()
    
    private lazy var amountOfExperienceLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textAlignment = .right
        label.textColor = .gray
        label.text = Texts.LevelView.exp + " " + "2.400 / 3.000"
        label.font = Fonts.LevelView.expFont
        return label
    }()
    
    private lazy var progressBarView: UIProgressView = {
        let progressView = UIProgressView(progressViewStyle: .default)
        progressView.translatesAutoresizingMaskIntoConstraints = false
        progressView.progress = 0
        progressView.progressTintColor = Colors.rose
        progressView.trackTintColor = .white
        progressView.transform = CGAffineTransform(scaleX: 1, y: 3)
        return progressView
    }()
    
    private lazy var motivationLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textAlignment = .left
        label.textColor = .gray
        label.text = Texts.LevelView.motivation
        label.font = Fonts.LevelView.motivationFont
        return label
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        layer.cornerRadius = bounds.height * Constants.levelView.percentageOfCurdling
    }
    
    func changeLevelViewInfo(currentLevel: Int, currentExp: Int, maxExpOnLevel: Int) {
        levelLabel.text = Texts.LevelView.level + " " + "\(currentLevel)"
        amountOfExperienceLabel.text = Texts.LevelView.exp + " " + "\(currentExp) / \(maxExpOnLevel)"
        progressBarView.progress = Float(Float(currentExp) / Float(maxExpOnLevel))
    }
    
    private func setupHierarchy() {
        addSubview(topStackView)
        topStackView.addArrangedSubview(levelLabel)
        topStackView.addArrangedSubview(amountOfExperienceLabel)
        
        addSubview(progressBarView)
        addSubview(motivationLabel)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.softPink
        
        NSLayoutConstraint.activate([
            topStackView.topAnchor.constraint(
                equalTo: topAnchor,
                constant: Constants.levelView.indentsFromSafeArea),
            topStackView.leadingAnchor.constraint(
                equalTo: leadingAnchor,
                constant: Constants.levelView.indentsFromSafeArea),
            topStackView.trailingAnchor.constraint(
                equalTo: trailingAnchor,
                constant: -Constants.levelView.indentsFromSafeArea),
            
            progressBarView.topAnchor.constraint(
                equalTo: topStackView.bottomAnchor,
                constant: Constants.levelView.intervalBetweenView),
            progressBarView.leadingAnchor.constraint(
                equalTo: leadingAnchor,
                constant: Constants.levelView.indentsFromSafeArea),
            progressBarView.trailingAnchor.constraint(
                equalTo: trailingAnchor,
                constant: -Constants.levelView.indentsFromSafeArea),
            
            motivationLabel.topAnchor.constraint(
                equalTo: progressBarView.bottomAnchor,
                constant: Constants.levelView.intervalBetweenView),
            motivationLabel.leadingAnchor.constraint(
                equalTo: leadingAnchor,
                constant: Constants.levelView.indentsFromSafeArea),
            motivationLabel.trailingAnchor.constraint(
                equalTo: trailingAnchor,
                constant: -Constants.levelView.indentsFromSafeArea),
            motivationLabel.bottomAnchor.constraint(
                equalTo: bottomAnchor,
                constant: -Constants.levelView.indentsFromSafeArea)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
}

