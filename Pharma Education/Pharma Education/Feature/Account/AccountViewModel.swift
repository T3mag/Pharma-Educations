
import Foundation

final class AccountViewModel {
    let stats: [AccountStatItem] = [
        AccountStatItem(title: "Дней без пропусков", icon: "flame.fill", accessory: .value("15 дней")),
        AccountStatItem(title: "Кол-во игр", icon: "gamecontroller.fill", accessory: .value("0")),
        AccountStatItem(title: "Кол-во симуляторов", icon: "cross.case.fill", accessory: .value("0")),
        AccountStatItem(title: "Кол-во запросов", icon: "bubble.left.and.bubble.right.fill", accessory: .value("0")),
        AccountStatItem(title: "Достижения", icon: "rosette", accessory: .chevron)
    ]
    
    let settings: [AccountStatItem] = [
        AccountStatItem(title: "Светлая/тёмная тема", icon: "circle.lefthalf.filled", accessory: .switch),
        AccountStatItem(title: "Включить уведомления", icon: "bell.fill", accessory: .switch),
        AccountStatItem(title: "Настроить язык", icon: "globe", accessory: .chevron)
    ]
}

