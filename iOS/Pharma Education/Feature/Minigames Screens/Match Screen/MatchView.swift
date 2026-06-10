
import UIKit

final class MatchView: UIView {
    
    var onNextTap: ((_ answer: [String: String]) -> Void)?
    private var leftItems: [MatchItem] = []
    private var rightItems: [MatchItem] = []
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 30
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var titleStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = 10
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var progressStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 10
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var matchBoardView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .clear
        view.clipsToBounds = false
        return view
    }()
    
    private lazy var cardColumnsStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .horizontal
        stackView.alignment = .fill
        stackView.distribution = .fillEqually
        stackView.spacing = 44
        stackView.translatesAutoresizingMaskIntoConstraints = false
        return stackView
    }()
    
    private lazy var leftCardsStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fillEqually
        stackView.spacing = 18
        return stackView
    }()
    
    private lazy var rightCardsStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fillEqually
        stackView.spacing = 18
        return stackView
    }()
    
    private let connectionCanvasView = MatchConnectionCanvasView()
    private let backgroundDesignView = BackgroundDesignView()
    
    private var leftCards: [MatchCardView] = []
    private var rightCards: [MatchCardView] = []
    private var connections: [Int: Int] = [:]
    private var selectedLeftIndex: Int?
    private var draggingLeftIndex: Int?
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Сопоставление"
        label.textColor = .black
        label.font = UIFont.systemFont(ofSize: 30, weight: .bold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var subTitleLabel: UILabel = {
        let label = UILabel()
        label.text = "Соедините препарат с группой"
        label.textColor = .gray
        label.font = UIFont.systemFont(ofSize: 15, weight: .semibold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var countQuestionsLabel: UILabel = {
        let label = UILabel()
        label.textColor = Colors.rose
        label.font = UIFont.systemFont(ofSize: 13, weight: .semibold)
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private lazy var progressBarView: UIProgressView = {
        let progressView = UIProgressView(progressViewStyle: .default)
        progressView.translatesAutoresizingMaskIntoConstraints = false
        progressView.progressTintColor = Colors.rose
        progressView.trackTintColor = Colors.softPink
        progressView.transform = CGAffineTransform(scaleX: 1, y: 3)
        return progressView
    }()
    
    private lazy var nextButton: UIButton = {
        let button = UIButton()
        button.setTitle("Проверить", for: .normal)
        button.titleLabel?.font = UIFont.systemFont(ofSize: 22, weight: .bold)
        button.backgroundColor = Colors.blackRose
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(nextButtonTap), for: .touchUpInside)
        return button
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierarchy()
        setupLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        
        nextButton.layer.cornerRadius = nextButton.frame.height * 0.2
        nextButton.clipsToBounds = true
        redrawConnections()
    }
    
    func configure(currentQuestion: Int, totalQuestions: Int, cards: (left: [MatchItem], right: [MatchItem])) {
        countQuestionsLabel.text = "Задание \(currentQuestion + 1) из \(totalQuestions)"
        progressBarView.progress = Float(currentQuestion + 1) / Float(totalQuestions)
        
        
        configureCards(terms: cards.left, answers: cards.right)
    }
    
    private func setupHierarchy() {
        addSubview(backgroundDesignView)
        addSubview(rootStackView)
        addSubview(nextButton)
        
        rootStackView.addArrangedSubview(titleStackView)
        rootStackView.addArrangedSubview(progressStackView)
        rootStackView.addArrangedSubview(matchBoardView)
        
        titleStackView.addArrangedSubview(titleLabel)
        titleStackView.addArrangedSubview(subTitleLabel)
        progressStackView.addArrangedSubview(countQuestionsLabel)
        progressStackView.addArrangedSubview(progressBarView)
        
        matchBoardView.addSubview(connectionCanvasView)
        matchBoardView.addSubview(cardColumnsStackView)
        cardColumnsStackView.addArrangedSubview(leftCardsStackView)
        cardColumnsStackView.addArrangedSubview(rightCardsStackView)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        connectionCanvasView.translatesAutoresizingMaskIntoConstraints = false
        
        NSLayoutConstraint.activate([
            backgroundDesignView.topAnchor.constraint(equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            rootStackView.topAnchor.constraint(
                equalTo: safeAreaLayoutGuide.topAnchor,
                constant: 20),
            rootStackView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: 20),
            rootStackView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -20),
            rootStackView.bottomAnchor.constraint(
                lessThanOrEqualTo: nextButton.topAnchor,
                constant: -20),
            
            matchBoardView.heightAnchor.constraint(
                equalToConstant: 520),
            
            connectionCanvasView.topAnchor.constraint(
                equalTo: matchBoardView.topAnchor),
            connectionCanvasView.leadingAnchor.constraint(
                equalTo: matchBoardView.leadingAnchor),
            connectionCanvasView.trailingAnchor.constraint(
                equalTo: matchBoardView.trailingAnchor),
            connectionCanvasView.bottomAnchor.constraint(
                equalTo: matchBoardView.bottomAnchor),
            
            cardColumnsStackView.topAnchor.constraint(
                equalTo: matchBoardView.topAnchor),
            cardColumnsStackView.leadingAnchor.constraint(
                equalTo: matchBoardView.leadingAnchor),
            cardColumnsStackView.trailingAnchor.constraint(
                equalTo: matchBoardView.trailingAnchor),
            cardColumnsStackView.bottomAnchor.constraint(
                equalTo: matchBoardView.bottomAnchor),
            
            nextButton.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: 20),
            nextButton.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -20),
            nextButton.bottomAnchor.constraint(
                equalTo: safeAreaLayoutGuide.bottomAnchor,
                constant: -20),
            nextButton.heightAnchor.constraint(
                equalToConstant: 70)
        ])
    }
    
    private func configureCards(terms: [MatchItem], answers: [MatchItem]) {
        leftItems = terms
        rightItems = answers
        
        leftCards.forEach {
            $0.removeFromSuperview()
        }
        rightCards.forEach {
            $0.removeFromSuperview()
        }
        leftCards.removeAll()
        rightCards.removeAll()
        connections.removeAll()
        selectedLeftIndex = nil
        
        for (index, item) in terms.enumerated() {
            let cardView = MatchCardView(side: .left)
            cardView.configure(title: item.title)
            cardView.onTap = { [weak self] in
                self?.selectLeftCard(at: index)
            }
            cardView.onEndpointPan = { [weak self] gesture in
                self?.handleConnectionPan(gesture, fromLeftIndex: index)
            }
            leftCards.append(cardView)
            leftCardsStackView.addArrangedSubview(cardView)
        }
        
        for (index, item) in answers.enumerated() {
            let cardView = MatchCardView(side: .right)
            cardView.configure(title: item.title)
            cardView.onTap = { [weak self] in
                self?.selectRightCard(at: index)
            }
            rightCards.append(cardView)
            rightCardsStackView.addArrangedSubview(cardView)
        }
        
        redrawConnections()
    }
    
    private func selectLeftCard(at index: Int) {
        selectedLeftIndex = index
        updateCardStates()
    }
    
    private func selectRightCard(at index: Int) {
        guard let selectedLeftIndex else { return }
        connect(leftIndex: selectedLeftIndex, toRightIndex: index)
    }
    
    private func connect(leftIndex: Int, toRightIndex rightIndex: Int) {
        connections[leftIndex] = rightIndex
        for (otherLeftIndex, connectedRightIndex) in connections where otherLeftIndex != leftIndex && connectedRightIndex == rightIndex {
            connections[otherLeftIndex] = nil
        }
        
        selectedLeftIndex = nil
        updateCardStates()
        redrawConnections()
    }
    
    private func updateCardStates() {
        for (index, card) in leftCards.enumerated() {
            card.setSelected(index == selectedLeftIndex || index == draggingLeftIndex)
            card.setConnected(connections[index] != nil)
        }
        
        for (index, card) in rightCards.enumerated() {
            card.setSelected(false)
            card.setConnected(connections.values.contains(index))
        }
    }
    
    private func redrawConnections() {
        let lines = connections.compactMap { leftIndex, rightIndex -> MatchConnectionCanvasView.Line? in
            guard leftCards.indices.contains(leftIndex), rightCards.indices.contains(rightIndex) else {
                return nil
            }
            
            let startPoint = leftCards[leftIndex].endpointCenter(in: connectionCanvasView)
            let endPoint = rightCards[rightIndex].endpointCenter(in: connectionCanvasView)
            return MatchConnectionCanvasView.Line(start: startPoint, end: endPoint)
        }
        
        connectionCanvasView.setLines(lines)
    }
    
    private func handleConnectionPan(_ gesture: UIPanGestureRecognizer, fromLeftIndex leftIndex: Int) {
        guard leftCards.indices.contains(leftIndex) else { return }
        
        let fingerPoint = gesture.location(in: connectionCanvasView)
        let startPoint = leftCards[leftIndex].endpointCenter(in: connectionCanvasView)
        
        switch gesture.state {
        case .began:
            draggingLeftIndex = leftIndex
            selectedLeftIndex = nil
            updateCardStates()
            connectionCanvasView.setTemporaryLine(MatchConnectionCanvasView.Line(start: startPoint, end: fingerPoint))
        case .changed:
            connectionCanvasView.setTemporaryLine(MatchConnectionCanvasView.Line(start: startPoint, end: fingerPoint))
        case .ended:
            if let rightIndex = rightCardIndex(at: fingerPoint) {
                connect(leftIndex: leftIndex, toRightIndex: rightIndex)
            }
            finishDragging()
        case .cancelled, .failed:
            finishDragging()
        default:
            break
        }
    }
    
    private func rightCardIndex(at point: CGPoint) -> Int? {
        rightCards.firstIndex { card in
            let pointInCard = connectionCanvasView.convert(point, to: card)
            return card.bounds.insetBy(dx: -24, dy: -24).contains(pointInCard)
        }
    }
    
    private func finishDragging() {
        draggingLeftIndex = nil
        connectionCanvasView.setTemporaryLine(nil)
        updateCardStates()
        redrawConnections()
    }
    
    @objc
    private func nextButtonTap() {
        var answers: [String: String] = [:]

        for (leftIndex, rightIndex) in connections {
            guard leftItems.indices.contains(leftIndex),
                  rightItems.indices.contains(rightIndex) else {
                continue
            }

            let leftID = leftItems[leftIndex].id
            let rightID = rightItems[rightIndex].id

            answers[leftID] = rightID
        }
        
        onNextTap?(answers)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
