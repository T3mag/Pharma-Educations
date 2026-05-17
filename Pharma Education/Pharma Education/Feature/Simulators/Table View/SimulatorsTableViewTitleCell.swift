
import UIKit

final class SimulatorsTableViewTitleCell: UITableViewCell {
    static let reuseIdentifire = "SimulatorsTableViewTitleCell"
    
    private lazy var topStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = SimulatorsConstatnts.TitleCell.topStackViewSpacing
        return stackView
    }()
    
    private lazy var titleTextField: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.text = SimulatorsTexts.TitleCell.title
        label.font = SimulatorsFonts.TitleCell.titleFont
        return label
    }()
    
    private lazy var subTitleTextFiled: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.numberOfLines = 2
        label.text = SimulatorsTexts.TitleCell.subtitile
        label.font = SimulatorsFonts.TitleCell.subbtitleFont
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
                constant: -SimulatorsConstatnts.TitleCell.indentsFromSafeArea)
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
