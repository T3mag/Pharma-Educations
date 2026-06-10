
import UIKit

final class SimulatorTableViewHandler: NSObject, UITableViewDelegate, UITableViewDataSource {
    
    var onCellTap: ((SimulatorItem) -> Void)?
    
    private var items: [ListItem<SimulatorItem>] = [.title]
    
    init(items: [SimulatorItem] = []) {
        self.items = [.title] + items.map { ListItem.item($0) }
    }
    
    func updateSimulators(items: [SimulatorItem]) {
        self.items = [.title] + items.map { ListItem.item($0) }
    }
    
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        items.count
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        switch items[indexPath.row] {
        case .title:
            guard let titleCell = tableView.dequeueReusableCell(withIdentifier: SimulatorsTableViewTitleCell.reuseIdentifier, for: indexPath) as? SimulatorsTableViewTitleCell else {
                return UITableViewCell()
            }
            return titleCell
        case.item(let item):
            guard let simulatorCell = tableView.dequeueReusableCell(
                withIdentifier: SimulatorsTableViewGameCell.reuseIdentifier,
                for: indexPath) as? SimulatorsTableViewGameCell else {
                return UITableViewCell()
            }
            simulatorCell.configure(item: item)
            return simulatorCell
        }
    }
    
    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        
        guard indexPath.row < items.count else { return }
        
        switch items[indexPath.row] {
        case .title:
            return
        case .item(let item):
            onCellTap?(item)
        }
    }
}
