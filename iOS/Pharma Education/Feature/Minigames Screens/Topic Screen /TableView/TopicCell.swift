import UIKit

final class TopicCell: UITableViewCell {
    static let reuseIdentifier = "TopicCell"
    
    var onCheckboxTap: (() -> Void)?
    var onChevronTap: (() -> Void)?
    
    private var titleLeadingConstraint: NSLayoutConstraint?
    private var treeDotLeadingConstraint: NSLayoutConstraint?
    private var treeDotWidthConstraint: NSLayoutConstraint?
    private var treeDotHeightConstraint: NSLayoutConstraint?
    
    private lazy var treeLinesView: TreeLinesView = {
        let view = TreeLinesView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.isUserInteractionEnabled = false
        view.backgroundColor = .clear
        return view
    }()
    
    private lazy var treeDotView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = Colors.rose
        view.layer.borderColor = Colors.softPink.cgColor
        return view
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.numberOfLines = 0
        return label
    }()
    
    private lazy var chevronButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.tintColor = Colors.rose
        button.addTarget(self, action: #selector(chevronTapped), for: .touchUpInside)
        return button
    }()
    
    private lazy var checkboxButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(checkboxTapped), for: .touchUpInside)
        return button
    }()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupLayout()
    }
    
    func configure(
        title: String,
        depth: Int,
        hasChildren: Bool,
        isExpanded: Bool,
        isChecked: Bool,
        isLastChild: Bool,
        parentLevels: [Int]
    ) {
        setupDotView(depth: depth, hasChildren: hasChildren)
        titleLabel.text = title
        titleLabel.font = depth == 0
            ? .systemFont(ofSize: 17, weight: .bold)
            : .systemFont(ofSize: 16, weight: .regular)
        
        titleLabel.textColor = depth > 1 ? .darkGray : .black
        
        let indent = CGFloat(depth * 34)
        titleLeadingConstraint?.constant = indent + 56
        
        chevronButton.isHidden = !hasChildren
        chevronButton.setImage(
            UIImage(systemName: isExpanded ? "chevron.up" : "chevron.down"),
            for: .normal
        )
        
        treeLinesView.depth = depth
        treeLinesView.isLastChild = isLastChild
        treeLinesView.parentLevels = parentLevels
        treeLinesView.drawsChildConnector = hasChildren && isExpanded
        
        let checkboxImageName = isChecked ? "checkmark.square.fill" : "square"
        checkboxButton.setImage(UIImage(systemName: checkboxImageName), for: .normal)
        checkboxButton.tintColor = isChecked ? Colors.rose : .systemGray2
    }
    
    private func setupDotView(depth: Int, hasChildren: Bool) {
        let size = CGFloat(hasChildren == true
                           ? TopicConstants.TopicCell.bigDotSize : TopicConstants.TopicCell.litelDotSize)
        let indent = CGFloat(depth * TopicConstants.TopicCell.factorForIndent)
        
        treeDotView.alpha = depth > 2 ? 0.7 : 1
        treeDotLeadingConstraint?.constant = indent + 18
        treeDotWidthConstraint?.constant = size
        treeDotHeightConstraint?.constant = size
        treeDotView.layer.cornerRadius = size / 2
        treeDotView.layer.borderWidth = size / 4
    }
    
    private func setupLayout() {
        selectionStyle = .none
        backgroundColor = .clear
        contentView.backgroundColor = .white
        
        contentView.insertSubview(treeLinesView, at: 0)
        contentView.addSubview(treeDotView)
        contentView.addSubview(titleLabel)
        contentView.addSubview(chevronButton)
        contentView.addSubview(checkboxButton)
        
        titleLeadingConstraint = titleLabel.leadingAnchor.constraint(
            equalTo: contentView.leadingAnchor,
            constant: 56
        )
        treeDotLeadingConstraint = treeDotView.leadingAnchor.constraint(
            equalTo: contentView.leadingAnchor,
            constant: 18
        )
        treeDotWidthConstraint = treeDotView.widthAnchor.constraint(
            equalToConstant: TopicConstants.TopicCell.litelDotSize
        )
        treeDotHeightConstraint = treeDotView.heightAnchor.constraint(
            equalToConstant: TopicConstants.TopicCell.litelDotSize
        )
        
        NSLayoutConstraint.activate([
            treeLinesView.topAnchor.constraint(
                equalTo: contentView.topAnchor),
            treeLinesView.leadingAnchor.constraint(
                equalTo: contentView.leadingAnchor),
            treeLinesView.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor),
            treeLinesView.widthAnchor.constraint(
                equalToConstant: 100),
            
            treeDotLeadingConstraint!,
            treeDotWidthConstraint!,
            treeDotHeightConstraint!,
            treeDotView.centerYAnchor.constraint(
                equalTo: contentView.centerYAnchor),
            
            titleLeadingConstraint!,

            titleLabel.topAnchor.constraint(
                equalTo: contentView.topAnchor, constant: 10),
            titleLabel.bottomAnchor.constraint(
                equalTo: contentView.bottomAnchor, constant: -10),
            titleLabel.trailingAnchor.constraint(
                lessThanOrEqualTo: chevronButton.leadingAnchor,
                constant: -8),
            
            chevronButton.centerYAnchor.constraint(
                equalTo: contentView.centerYAnchor),
            chevronButton.trailingAnchor.constraint(
                equalTo: checkboxButton.leadingAnchor,
                constant: -16),
            chevronButton.widthAnchor.constraint(
                equalToConstant: 30),
            chevronButton.heightAnchor.constraint(
                equalToConstant: 20),
            
            checkboxButton.centerYAnchor.constraint(
                equalTo: contentView.centerYAnchor),
            checkboxButton.trailingAnchor.constraint(
                equalTo: contentView.trailingAnchor,
                constant: -20),
            checkboxButton.widthAnchor.constraint(
                equalToConstant: 30),
            checkboxButton.heightAnchor.constraint(
                equalToConstant: 30)
        ])
    }
    
    @objc
    private func checkboxTapped() {
        onCheckboxTap?()
    }
    
    @objc
    private func chevronTapped() {
        onChevronTap?()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
