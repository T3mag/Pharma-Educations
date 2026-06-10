import UIKit

final class AccountTableHandler: NSObject, UITableViewDelegate, UITableViewDataSource {
    
    private var items: [AccountStatistics]
    
    init(items: [AccountStatistics]) {
        self.items = items
    }
    
    func updateItems(items: [AccountStatistics]) {
        self.items = items
    }
    
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        items.count
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        guard let cell = tableView.dequeueReusableCell(
            withIdentifier: AccountTableViewCell.reuseIdentifier,
            for: indexPath) as? AccountTableViewCell else {
            return UITableViewCell()
        }
        
        cell.configure(with: items[indexPath.row])
        return cell
    }
}
