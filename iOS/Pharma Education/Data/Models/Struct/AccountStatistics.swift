
struct AccountStatistics {
    let title: String
    let icon: String
    var accessory: Accessory

    enum Accessory {
        case value(String)
        case chevron
        case `switch`
    }
}
