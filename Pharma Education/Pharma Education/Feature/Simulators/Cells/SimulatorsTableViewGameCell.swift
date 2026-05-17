
import UIKit

class SimulatorsTableViewGameCell: UITableViewCell {
    
    static let reuseIdentifire = "SimulatorsTableViewGameCell"
    
    private let buubleView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.clipsToBounds = true
        view.backgroundColor = .white
        view.layer.cornerRadius = 40
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
        return label
    }()
    
    private lazy var simulatorSubtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.numberOfLines = 2
        label.textColor = .gray
        label.textAlignment = .left
        return label
    }()
    
    private lazy var startButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = Colors.lightRose
        button.layer.cornerRadius = SimulatorsConstatnts.GameCell.buttonSize / 2
        button.setImage(UIImage(systemName: "paperplane.fill"), for: .normal)
        button.tintColor = .white
        button.clipsToBounds = true
        return button
    }()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupHierarhcy()
        setupLayout()
    }
    
    func configure(item: SimulatorItem) {
        simulatorImageView.image = UIImage(named: item.imageName)
        simulatorTitleLabel.text = item.title
        simulatorSubtitleLabel.text = item.subtitle
    }
    
    private func setupHierarhcy() {
        contentView.addSubview(buubleView)
        buubleView.addSubview(simulatorImageView)
        buubleView.addSubview(titelStackView)
        buubleView.addSubview(startButton)
        
        titelStackView.addArrangedSubview(simulatorTitleLabel)
        titelStackView.addArrangedSubview(simulatorSubtitleLabel)
    }
    
    private func setupLayout() {
        selectionStyle = .none
        backgroundColor = .clear
        
        NSLayoutConstraint.activate([
            buubleView.topAnchor.constraint(
                equalTo: contentView.topAnchor,
                constant: 10),
            buubleView.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor,
                constant: -10),
            buubleView.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor),
            buubleView.trailingAnchor.constraint(
                equalTo: contentView.trailingAnchor)
        ])
        
        NSLayoutConstraint.activate([
            simulatorImageView.topAnchor.constraint(
                equalTo: buubleView.topAnchor,
                constant: SimulatorsConstatnts.GameCell.indentsFromContentView),
            simulatorImageView.bottomAnchor.constraint(
                equalTo: buubleView.bottomAnchor,
                constant: -SimulatorsConstatnts.GameCell.indentsFromContentView),
            simulatorImageView.leadingAnchor.constraint(
                equalTo: buubleView.leadingAnchor,
                constant: SimulatorsConstatnts.GameCell.indentsFromContentView),
            simulatorImageView.widthAnchor.constraint(
                equalToConstant: SimulatorsConstatnts.GameCell.heightImageView),
            
            titelStackView.topAnchor.constraint(
                equalTo: buubleView.topAnchor,
                constant: SimulatorsConstatnts.GameCell.indentsFromContentView),
            titelStackView.bottomAnchor.constraint(
                equalTo: buubleView.bottomAnchor,
                constant: -SimulatorsConstatnts.GameCell.indentsFromContentView),
            titelStackView.leadingAnchor.constraint(
                equalTo: simulatorImageView.trailingAnchor,
                constant: SimulatorsConstatnts.GameCell.indentsFromContentView),
            titelStackView.trailingAnchor.constraint(
                equalTo: startButton.leadingAnchor,
                constant: -SimulatorsConstatnts.GameCell.indentsFromContentView),
            
            startButton.bottomAnchor.constraint(
                equalTo: buubleView.bottomAnchor,
                constant: -SimulatorsConstatnts.GameCell.indentsFromContentView),
            startButton.trailingAnchor.constraint(
                equalTo: buubleView.trailingAnchor,
                constant: -SimulatorsConstatnts.GameCell.indentsFromContentView),
            startButton.heightAnchor.constraint(
                equalToConstant: SimulatorsConstatnts.GameCell.buttonSize),
            startButton.widthAnchor.constraint(
                equalToConstant: SimulatorsConstatnts.GameCell.buttonSize)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    
}
