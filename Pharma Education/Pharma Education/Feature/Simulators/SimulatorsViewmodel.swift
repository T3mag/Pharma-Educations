
protocol SimulatorsViewmodelProtocol {
    var testGames: [SimulatorItem] { get }
}

final class SimulatorsViewmodel: SimulatorsViewmodelProtocol {
    var testGames: [SimulatorItem] = [
        SimulatorItem(imageName: "Pharmacist", title: "Quizzes", subtitle: "Test your knowledge" + "\n" + "with quick quizzes"),
        SimulatorItem(imageName: "Toxicology", title: "Quizzes", subtitle: "Test your knowledge with quick quizzes")
    ]
}

