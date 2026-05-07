
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
        let chatWithAiVC = ChatViewController()
        let accountVC = UIViewController()
        accountVC.view.backgroundColor = .systemBackground
        
        let simultatorNav = UINavigationController(rootViewController: simulatorsVC)
        let gamesAndTestsNav = UINavigationController(rootViewController: gamesAndTestsVC)
        let chatWithAiNav = UINavigationController(rootViewController: chatWithAiVC)
        let accountNav = UINavigationController(rootViewController: accountVC)
        
        simultatorNav.tabBarItem = UITabBarItem(
            title: Texts.TabBar.simulatorTitle,
            image: UIImage(systemName: Texts.TabBar.simulatorIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedeSimulatorIcon)
        )
        gamesAndTestsNav.tabBarItem = UITabBarItem (
            title: Texts.TabBar.gamesAndTestsTitle,
            image: UIImage(systemName: Texts.TabBar.gamesAndTestsIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedGamesAndTestsIcon)
        )
        chatWithAiNav.tabBarItem = UITabBarItem (
            title: Texts.TabBar.chatWithAiTitile,
            image: UIImage(systemName: Texts.TabBar.chatWithAIIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedChatWithAiIcon)
        )
        accountNav.tabBarItem = UITabBarItem (
            title: Texts.TabBar.accountTitle,
            image: UIImage(systemName: Texts.TabBar.accountIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedAccountIcon)
        )
        
        viewControllers = [simultatorNav, gamesAndTestsNav, chatWithAiNav, accountNav]
    }
}
