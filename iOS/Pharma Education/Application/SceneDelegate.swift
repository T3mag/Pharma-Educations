
import UIKit
internal import Combine

class SceneDelegate: UIResponder, UIWindowSceneDelegate {

    var window: UIWindow?
    private let sessionManager: SessionManagerProtocol = SessionManager.shared
    private let userService: UserServiceProtocol = UserService.shared
    private var cancellables = Set<AnyCancellable>()


    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
        guard let windowScene = (scene as? UIWindowScene) else { return }
        
        let window = UIWindow(windowScene: windowScene)
        self.window = window
        window.rootViewController = LaunchViewController()
        window.makeKeyAndVisible()
        
        sessionManager.start()
        _ = UserService.shared
        
        Publishers.CombineLatest(
            sessionManager.userPublisher,
            userService.userInfoPublisher
        )
        .dropFirst()
        .receive(on: DispatchQueue.main)
        .sink { [weak self] user, userInfo in
            guard user != nil else {
                self?.setRootViewController(
                    UINavigationController(rootViewController: LoginViewController())
                )
                return
            }
            
            guard userInfo != nil else {
                return
            }
            
            self?.setRootViewController(UINavigationController(rootViewController:MainTabBarController()))
        }
        .store(in: &cancellables)
        
    }

    func sceneDidDisconnect(_ scene: UIScene) {
    }

    func sceneDidBecomeActive(_ scene: UIScene) {
    }

    func sceneWillResignActive(_ scene: UIScene) {
    }

    func sceneWillEnterForeground(_ scene: UIScene) {
    }

    func sceneDidEnterBackground(_ scene: UIScene) {
        (UIApplication.shared.delegate as? AppDelegate)?.saveContext()
    }
    
    private func setRootViewController(_ viewController: UIViewController, animated: Bool = true) {
        guard let window else { return }
        
        if isSameRootViewController(viewController) {
            return
        }
        
        guard animated else {
            window.rootViewController = viewController
            return
        }

        UIView.transition(
            with: window,
            duration: 0.35,
            options: [.transitionCrossDissolve, .curveEaseInOut],
            animations: {
                window.rootViewController = viewController
            }
        )
    }
    
    private func isSameRootViewController(_ viewController: UIViewController) -> Bool {
        let currentRootViewController = (window?.rootViewController as? UINavigationController)?.viewControllers.first
            ?? window?.rootViewController
        let newRootViewController = (viewController as? UINavigationController)?.viewControllers.first
            ?? viewController

        switch (currentRootViewController, newRootViewController) {
        case (is MainTabBarController, is MainTabBarController):
            return true
        case (is LoginViewController, is LoginViewController):
            return true
        default:
            return false
        }
    }
}
