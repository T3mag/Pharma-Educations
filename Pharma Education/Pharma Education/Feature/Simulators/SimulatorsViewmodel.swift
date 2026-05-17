
protocol SimulatorsViewmodelProtocol {
    var testGames: [SimulatorItem] { get }
}

final class SimulatorsViewmodel: SimulatorsViewmodelProtocol {
    var testGames: [SimulatorItem] = [
        SimulatorItem(imageName: "Pharmacist", title: "Фармацефт", subtitle: "Помогайте клиентам, проверяйте взаимодействие с ними и рекомендуйте подходящие лекарства."),
        SimulatorItem(imageName: "Emergency Room", title: "Приемное отделение", subtitle: "Принимайте быстрые решения в критических ситуациях и спасайте жизни."),
        SimulatorItem(imageName: "Toxicology", title: "Токсикология", subtitle: "Определите ядовитые вещества и выберите правильное противоядие.")
    ]
}

