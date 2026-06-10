
import UIKit

final class MinigameView: UIView {
    
    private lazy var backgroundDesignView: UIView = BackgroundDesignView()
    
    private lazy var collectionView: UICollectionView = {
        let layout = UICollectionViewFlowLayout()
        layout.scrollDirection = .vertical
        layout.minimumLineSpacing = MinigameConstants.General.contentViewMinimumSpacing
        layout.minimumInteritemSpacing = MinigameConstants.General.contentViewMinimumSpacing
        
        let collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        collectionView.translatesAutoresizingMaskIntoConstraints = false
        collectionView.backgroundColor = .clear
        collectionView.showsVerticalScrollIndicator = false
        collectionView.register(
            MinigameCollectionViewCell.self,
            forCellWithReuseIdentifier: MinigameCollectionViewCell.reuseIdentifier)
        collectionView.register(
            MinigameTitleCollectionViewCell.self,
            forCellWithReuseIdentifier: MinigameTitleCollectionViewCell.reuseIdentifier)
        return collectionView
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupHierhacy()
        setupLayout()
    }
    
    func setupCollectionView(
        dataSources: UICollectionViewDataSource,
        delegate: UICollectionViewDelegate) {
            collectionView.dataSource = dataSources
            collectionView.delegate = delegate
    }
    
    private func setupHierhacy() {
        addSubview(backgroundDesignView)
        addSubview(collectionView)
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            backgroundDesignView.topAnchor.constraint(
                equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(
                equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(
                equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(
                equalTo: bottomAnchor)
        ])
        
        NSLayoutConstraint.activate([
            collectionView.topAnchor.constraint(
                equalTo: topAnchor),
            collectionView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: MinigameConstants.General.indentsFromSaveArea),
            collectionView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -MinigameConstants.General.indentsFromSaveArea),
            collectionView.bottomAnchor.constraint(
                equalTo: bottomAnchor),
        ])
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
}
