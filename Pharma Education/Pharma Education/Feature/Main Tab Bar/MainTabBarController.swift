
import UIKit

final class MainTabBarController: UITabBarController {
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupTubs()
    }
    
    private func setupTubs() {
        let simulatorsVC = UIViewController()
        simulatorsVC.view.backgroundColor = .systemBackground
        let gamesAndTestsVC = UIViewController()
        gamesAndTestsVC.view.backgroundColor = .systemBackground
        let chatWithAiVC = AiAssistentViewController()
        
        let accountVM = AccountViewModel()
        let accountVC = AccountViewController(viewModel: accountVM)
        
        tabBar.tintColor = Colors.rose
        simulatorsVC.tabBarItem = UITabBarItem(
            title: Texts.TabBar.simulatorTitle,
            image: UIImage(systemName: Texts.TabBar.simulatorIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedeSimulatorIcon)
        )
        gamesAndTestsVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.gamesAndTestsTitle,
            image: UIImage(systemName: Texts.TabBar.gamesAndTestsIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedGamesAndTestsIcon)
        )
        chatWithAiVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.chatWithAiTitile,
            image: UIImage(systemName: Texts.TabBar.chatWithAIIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedChatWithAiIcon)
        )
        accountVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.accountTitle,
            image: UIImage(systemName: Texts.TabBar.accountIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedAccountIcon)
        )
        
        viewControllers = [simulatorsVC, gamesAndTestsVC, chatWithAiVC, accountVC]
    }
}
