
struct AccountStatItem {
    let title: String
    let icon: String
    let accessory: Accessory

    enum Accessory {
        case value(String)
        case chevron
        case `switch`
    }
}
