import UIKit

final class LaunchViewController: UIViewController {

    private let contentView: LoadingView = .init(frame: .zero)
    
    override func loadView() {
        view = contentView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
    }
}
