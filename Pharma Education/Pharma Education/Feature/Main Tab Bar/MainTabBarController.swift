
import UIKit

final class MainTabBarController: UITabBarController {
    
    override func viewWillAppear(_ animated: Bool) {
        navigationController?.isNavigationBarHidden = true
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupTubs()
    }
    
    private func setupTubs() {
        
        let simulatorsVC = SimulatorsViewController()
        let minagameVC = MinigameViewController()
        let AiAssistentVC = AiAssistentViewController()
        let accountVC = AccountViewController()
        
        tabBar.tintColor = Colors.rose
        simulatorsVC.tabBarItem = UITabBarItem(
            title: Texts.TabBar.simulatorTitle,
            image: UIImage(systemName: Texts.TabBar.simulatorIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedeSimulatorIcon)
        )
        minagameVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.gamesAndTestsTitle,
            image: UIImage(systemName: Texts.TabBar.gamesAndTestsIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedGamesAndTestsIcon)
        )
        AiAssistentVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.chatWithAiTitile,
            image: UIImage(systemName: Texts.TabBar.chatWithAIIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedChatWithAiIcon)
        )
        accountVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.accountTitle,
            image: UIImage(systemName: Texts.TabBar.accountIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedAccountIcon)
        )
        
        viewControllers = [simulatorsVC, minagameVC, AiAssistentVC, accountVC]
    }
}
