
import UIKit

final class MainTabBarController: UITabBarController {
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)

        navigationController?.setNavigationBarHidden(true, animated: animated)
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        navigationController?.setNavigationBarHidden(false, animated: animated)
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupTabs()
    }
    
    private func setupTabs() {
        
        let simulatorsVC = SimulatorsViewController()        
        let minigameVC = MinigameViewController()
        let AIAssistantVC = AIAssistantViewController()
        let accountVC = AccountViewController()
        
        tabBar.tintColor = Colors.rose
        simulatorsVC.tabBarItem = UITabBarItem(
            title: Texts.TabBar.simulatorTitle,
            image: UIImage(systemName: Texts.TabBar.simulatorIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedSimulatorIcon)
        )
        minigameVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.gamesAndTestsTitle,
            image: UIImage(systemName: Texts.TabBar.gamesAndTestsIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedGamesAndTestsIcon)
        )
        AIAssistantVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.chatWithAITitle,
            image: UIImage(systemName: Texts.TabBar.chatWithAIIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedChatWithAiIcon)
        )
        accountVC.tabBarItem = UITabBarItem (
            title: Texts.TabBar.accountTitle,
            image: UIImage(systemName: Texts.TabBar.accountIcon),
            selectedImage: UIImage(systemName: Texts.TabBar.selectedAccountIcon)
        )
        
        viewControllers = [simulatorsVC, minigameVC, AIAssistantVC, accountVC]
    }
}
