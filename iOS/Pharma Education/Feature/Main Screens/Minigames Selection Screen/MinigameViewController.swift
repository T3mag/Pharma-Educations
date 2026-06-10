
import UIKit

final class MinigameViewController: UIViewController {
    
    private let contentView: MinigameView = .init(frame: .zero)
    private let collectionViewHandler: MinigameCollectionViewHandler
    private let viewModel: MinigameViewModelProtocol

    init(collectionViewHandler: MinigameCollectionViewHandler = MinigameCollectionViewHandler(),
         viewModel: MinigameViewModelProtocol = MinigameViewModel()) {
        self.collectionViewHandler = collectionViewHandler
        self.viewModel = viewModel
        super.init(nibName: nil, bundle: nil)
        collectionViewHandler.updateMinigames(with: self.viewModel.testGames)
        setupBindings()
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()

        contentView.setupCollectionView(
            dataSources: collectionViewHandler,
            delegate: collectionViewHandler)
    }
    
    override func loadView() {
        view = contentView
    }
    
    func setupBindings() {
        collectionViewHandler.onCellTap = {[weak self] type in
            let vc = TopicViewController(minigameType: type)
            self?.navigationController?.pushViewController(vc, animated: true)
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

}
