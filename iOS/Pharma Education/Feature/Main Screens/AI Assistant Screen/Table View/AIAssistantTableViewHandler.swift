
import UIKit

final class AIAssistantTableViewHandler: NSObject, UITableViewDataSource, UITableViewDelegate {
    
    private var items: [ListItem<ChatMessage>] = [.title]
    
    init(with messages: [ChatMessage] = []) {
        self.items = [.title] + messages.map{ ListItem.item($0) }
    }
    
    func updateMessages(messages: [ChatMessage]) {
        self.items = [.title] + messages.map{ ListItem.item($0) }
    }
    
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        items.count
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        
        switch items[indexPath.row] {
        case .title:
            guard let titleCell = tableView.dequeueReusableCell(
                withIdentifier: AIAssistantTitleTableViewCell.reuseIdentifier,
                for: indexPath) as? AIAssistantTitleTableViewCell else {
                return UITableViewCell()
            }
            return titleCell
        case .item(let message):
            guard let messageCell = tableView.dequeueReusableCell(
                withIdentifier: AIAssistantMessageTableViewCell.reuseIdentifier,
                for: indexPath) as? AIAssistantMessageTableViewCell else {
                return UITableViewCell()
            }
            messageCell.configure(with: message)
            return messageCell
        }
    }
}
