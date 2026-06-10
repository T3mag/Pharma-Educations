import UIKit

final class PharmacyViewController: UIViewController {
    
    private let loadingView: LoadingView = .init(frame: .zero)
    private let contentView = PharmacyView(frame: .zero)
    private let viewModel: PharmacyViewModelProtocol
    private var remainingSeconds: Int
    private var timer: Timer?
    private var isFinishing = false
    
    init(
        timeInMinutes: Int,
        countCustomers: Int,
        viewModel: PharmacyViewModelProtocol = PharmacyViewModel()
    ) {
        self.remainingSeconds = max(0, timeInMinutes) * 60
        self.viewModel = viewModel
        self.viewModel.configureCustomersCount(countCustomers)
        super.init(nibName: nil, bundle: nil)
        setupActions()
    }
    
    override func loadView() {
        setupViews()
    }
    
    private func setupActions() {
        contentView.onConfirmTap = { [weak self] userAnswer in
            self?.proceedQuestion(userAnswer: userAnswer)
        }
    }
    
    private func setupViews() {
        view = loadingView
        
        viewModel.loadCustomers { [weak self] result in
            switch result {
            case .success(_):
                self?.proceedQuestion(userAnswer: nil)
                self?.contentView.configureTimer(time: self?.formattedRemainingTime() ?? "00:00")
                self?.view = self?.contentView
                self?.startTimer()
            case .failure(let error):
                print(error)
                self?.navigationController?.popViewController(animated: true)
            }
        }
        
    }
    
    private func proceedQuestion(userAnswer: String?) {
        guard !isFinishing else { return }
        
        switch viewModel.proceed(userAnswer: userAnswer) {
        case .question(let customer):
            contentView.configure(
                customer: customer,
                currentClient: viewModel.currentClientNumber,
                totalClients: viewModel.totalClientsCount,
                animated: userAnswer != nil
            )
        case .final(_):
            finishGame()
        }
    }
    
    private func finishGame() {
        isFinishing = true
        timer?.invalidate()
        timer = nil
        view = loadingView
        
        Task { [weak self] in
            guard let self else { return }
            let feedbacks = await viewModel.waitForFeedbackResponses()
            
            await MainActor.run {
                let finishViewController = PharmacyFinishViewController(
                    feedbacks: feedbacks,
                    customers: self.viewModel.customers
                )
                self.navigationController?.pushViewController(finishViewController, animated: true)
            }
        }
    }
    
    private func startTimer() {
        timer?.invalidate()
        
        guard remainingSeconds > 0 else {
            finishTimer()
            return
        }
        
        let timer = Timer(timeInterval: 1, repeats: true) { [weak self] _ in
            self?.updateTimer()
        }
        self.timer = timer
        RunLoop.main.add(timer, forMode: .common)
    }
    
    private func updateTimer() {
        remainingSeconds -= 1
        contentView.configureTimer(time: formattedRemainingTime())
        
        if remainingSeconds <= 0 {
            finishTimer()
        }
    }
    
    private func finishTimer() {
        timer?.invalidate()
        timer = nil
        remainingSeconds = 0
        contentView.configureTimer(time: formattedRemainingTime())
        proceedAfterTimeout()
    }

    private func proceedAfterTimeout() {
        guard !isFinishing else { return }

        switch viewModel.proceedAfterTimeout() {
        case .question(let customer):
            contentView.configure(
                customer: customer,
                currentClient: viewModel.currentClientNumber,
                totalClients: viewModel.totalClientsCount,
                animated: true
            )
        case .final:
            finishGame()
        }
    }
    
    private func formattedRemainingTime() -> String {
        let minutes = remainingSeconds / 60
        let seconds = remainingSeconds % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        navigationController?.setNavigationBarHidden(true, animated: animated)
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        navigationController?.setNavigationBarHidden(false, animated: animated)
        timer?.invalidate()
        timer = nil
    }
    
    deinit {
        timer?.invalidate()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
