
import UIKit

final class MinigameViewController: UIViewController {
    
    private let contentView: MinigameView = .init(frame: .zero)
    private let collectonViewHandler: MinigameCollectionViewHandller
    private let viewModel: MinigameViewModelProtocol

    init(collectonViewHandler: MinigameCollectionViewHandller = MinigameCollectionViewHandller(),
         viewModel: MinigameViewModelProtocol = MinigameViewModel()) {
        self.collectonViewHandler = collectonViewHandler
        self.viewModel = viewModel
        collectonViewHandler.updateMinigames(with: self.viewModel.testGames)
        super.init(nibName: nil, bundle: nil)
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()

        contentView.setupCollectionView(
            dataSources: collectonViewHandler,
            delegate: collectonViewHandler)
    }
    
    override func loadView() {
        view = contentView
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

}
