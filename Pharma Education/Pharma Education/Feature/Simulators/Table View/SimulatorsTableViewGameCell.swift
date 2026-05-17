
import UIKit

final class SimulatorsTableViewGameCell: UITableViewCell {
    
    static let reuseIdentifire = "SimulatorsTableViewGameCell"
    
    private let bubbleView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.clipsToBounds = true
        view.backgroundColor = .white
        return view
    }()
    
    private lazy var titelStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = 10
        return stackView
    }()
    
    private lazy var simulatorImageView: UIImageView = {
        let imageView = UIImageView()
        imageView.translatesAutoresizingMaskIntoConstraints = false
        imageView.contentMode = .scaleAspectFit
        imageView.clipsToBounds = true
        return imageView
    }()
    
    private lazy var simulatorTitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 1
        label.textColor = .black
        label.textAlignment = .left
        label.font = SimulatorsFonts.SimulatorCell.titleFont
        return label
    }()
    
    private lazy var simulatorSubtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 0
        label.textColor = .gray
        label.textAlignment = .left
        label.font = SimulatorsFonts.SimulatorCell.subtitleFont
        return label
    }()
    
    private lazy var startButton: UIButton = {
        let button = UIButton(type: .system)
        let image = UIImage(systemName: "paperplane.fill")?
            .withConfiguration(UIImage.SymbolConfiguration(
                pointSize: SimulatorsConstatnts.SimulatorCell.buttonSize * 0.4))
        
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = Colors.lightRose
        button.layer.cornerRadius = SimulatorsConstatnts.SimulatorCell.buttonSize / 2
        button.setImage(image, for: .normal)
        button.tintColor = .white
        button.clipsToBounds = true
        return button
    }()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupHierarhcy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        let cornerRadiusBubbleView = bubbleView.bounds.height * SimulatorsConstatnts.SimulatorCell.roundingPercentage
        let cornerRadiusImageView = simulatorImageView.bounds.height * SimulatorsConstatnts.SimulatorCell.roundingPercentage
        bubbleView.layer.cornerRadius = cornerRadiusBubbleView
        simulatorImageView.layer.cornerRadius = cornerRadiusImageView
    }
    
    func configure(item: SimulatorItem) {
        simulatorImageView.image = UIImage(named: item.imageName)
        simulatorTitleLabel.text = item.title
        simulatorSubtitleLabel.text = item.subtitle
    }
    
    private func setupHierarhcy() {
        contentView.addSubview(bubbleView)
        bubbleView.addSubview(simulatorImageView)
        bubbleView.addSubview(titelStackView)
        bubbleView.addSubview(startButton)
        
        titelStackView.addArrangedSubview(simulatorTitleLabel)
        titelStackView.addArrangedSubview(simulatorSubtitleLabel)
    }
    
    private func setupLayout() {
        selectionStyle = .none
        backgroundColor = .clear
        
        NSLayoutConstraint.activate([
            bubbleView.topAnchor.constraint(
                equalTo: contentView.topAnchor,
                constant: 10),
            bubbleView.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -10),
            bubbleView.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor),
            bubbleView.trailingAnchor.constraint(
                equalTo: contentView.trailingAnchor)
        ])
        
        NSLayoutConstraint.activate([
            simulatorImageView.topAnchor.constraint(
                equalTo: bubbleView.topAnchor,
                constant: SimulatorsConstatnts.SimulatorCell.indentsFromContentView),
            simulatorImageView.bottomAnchor.constraint(
                equalTo: bubbleView.bottomAnchor,
                constant: -SimulatorsConstatnts.SimulatorCell.indentsFromContentView),
            simulatorImageView.leadingAnchor.constraint(
                equalTo: bubbleView.leadingAnchor,
                constant: SimulatorsConstatnts.SimulatorCell.indentsFromContentView),
            simulatorImageView.heightAnchor.constraint(lessThanOrEqualToConstant: SimulatorsConstatnts.SimulatorCell.heightImageView),
            simulatorImageView.widthAnchor.constraint(equalTo: simulatorImageView.heightAnchor, multiplier: 4/3),
            
            titelStackView.topAnchor.constraint(
                equalTo: simulatorImageView.topAnchor,
                constant: SimulatorsConstatnts.SimulatorCell.indentsFromImageView),
            titelStackView.leadingAnchor.constraint(
                equalTo: simulatorImageView.trailingAnchor,
                constant: SimulatorsConstatnts.SimulatorCell.indentsFromImageView),
            titelStackView.trailingAnchor.constraint(
                equalTo: startButton.leadingAnchor,
                constant: -SimulatorsConstatnts.SimulatorCell.indentsFromContentView),
            
            startButton.bottomAnchor.constraint(
                equalTo: simulatorImageView.bottomAnchor,
                constant: -SimulatorsConstatnts.SimulatorCell.indentsFromImageView),
            startButton.trailingAnchor.constraint(
                equalTo: bubbleView.trailingAnchor,
                constant: -SimulatorsConstatnts.SimulatorCell.indentsFromContentView),
            startButton.heightAnchor.constraint(
                equalToConstant: SimulatorsConstatnts.SimulatorCell.buttonSize),
            startButton.widthAnchor.constraint(
                equalToConstant: SimulatorsConstatnts.SimulatorCell.buttonSize)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    
}
