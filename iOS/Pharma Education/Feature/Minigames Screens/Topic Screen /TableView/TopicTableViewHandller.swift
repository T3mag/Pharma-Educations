import UIKit

final class TopicTableViewHandler: NSObject, UITableViewDataSource, UITableViewDelegate {
    private enum Section: Int, CaseIterable {
        case search
        case selectAll
    }
    
    var onSetTopics: ((Int) -> Void)?
    private(set) var questionsCount: Int = 1
    private var topics: [TopicNode] = []
    private var expandedIds: Set<String> = []
    private var selectedIds: Set<String> = [] {
        didSet {
            onSetTopics?(selectedIds.count)
        }
    }
    
    private var specialSectionsCount: Int {
        Section.allCases.count
    }
    
    var selectedTopicIds: Set<String> {
        selectedIds.filter { isRequestableTopicId($0) }
    }
    
    func updateTopics(_ topics: [TopicNode]) {
        self.topics = topics
        selectedIds = selectedIds.intersection(allTopicIds())
    }
    
    func numberOfSections(in tableView: UITableView) -> Int {
        specialSectionsCount + topics.count
    }
    
    func tableView(_ tableView: UITableView, heightForHeaderInSection section: Int) -> CGFloat {
        3
    }
    
    func tableView(_ tableView: UITableView, viewForHeaderInSection section: Int) -> UIView? {
        let view = UIView()
        view.backgroundColor = .clear
        return view
    }
    
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        if Section(rawValue: section) != nil {
            return 1
        }
        
        guard let root = topic(for: section) else {
            return 0
        }
        
        return visibleTopics(for: root).count
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        
        switch indexPath.section {
        case Section.search.rawValue:
            guard let cell = tableView.dequeueReusableCell(
                withIdentifier: QuestionsCountCell.reuseIdentifier,
                for: indexPath
            ) as? QuestionsCountCell else {
                return UITableViewCell()
            }
            
            cell.configure(value: questionsCount)

            cell.onValueChanged = { [weak self] count in
                self?.questionsCount = count
            }
            
            return cell
        case Section.selectAll.rawValue:
            guard let cell = tableView.dequeueReusableCell(
                withIdentifier: SelectedAllCell.reuseIdentifier,
                for: indexPath
            ) as? SelectedAllCell else {
                return UITableViewCell()
            }
            
            cell.configure(isChecked: isAllSelected())
            cell.onCheckboxTap = { [weak self, weak tableView] in
                guard let self else { return }
                self.toggleSelectAll()
                tableView?.reloadData()
            }
            
            return cell
        default:
            guard let cell = tableView.dequeueReusableCell(
                withIdentifier: TopicCell.reuseIdentifier,
                for: indexPath
            ) as? TopicCell,
                  let root = topic(for: indexPath.section) else {
                return UITableViewCell()
            }
            
            let visibleTopics = visibleTopics(for: root)
            guard indexPath.row < visibleTopics.count else {
                return UITableViewCell()
            }
            
            let visibleTopic = visibleTopics[indexPath.row]
            let topic = visibleTopic.topic
            
            cell.configure(
                title: topic.title,
                depth: visibleTopic.depth,
                hasChildren: topic.hasChildren,
                isExpanded: expandedIds.contains(topic.id),
                isChecked: isSelected(topic),
                isLastChild: visibleTopic.isLastChild,
                parentLevels: visibleTopic.parentLevels
            )
            
            cell.onChevronTap = { [weak self, weak tableView] in
                guard let self else { return }
                
                if self.expandedIds.contains(topic.id) {
                    self.expandedIds.remove(topic.id)
                } else {
                    self.expandedIds.insert(topic.id)
                }
                
                tableView?.reloadSections(IndexSet(integer: indexPath.section), with: .automatic)
            }
            
            cell.onCheckboxTap = { [weak self, weak tableView] in
                guard let self else { return }
                self.toggleSelection(for: topic)
                tableView?.reloadData()
            }
            
            return cell
        }
    }
    
    private func topic(for section: Int) -> TopicNode? {
        guard let index = topicIndex(for: section) else {
            return nil
        }
        return topics[index]
    }
    
    private func topicIndex(for section: Int) -> Int? {
        let index = section - specialSectionsCount
        guard index >= 0, index < topics.count else {
            return nil
        }
        return index
    }
    
    private func toggleSelectAll() {
        let ids = allTopicIds()
        if isAllSelected() {
            selectedIds.subtract(ids)
        } else {
            selectedIds.formUnion(compactTopicIds(in: topics))
        }
    }
    
    private func toggleSelection(for topic: TopicNode) {
        if selectedIds.contains(topic.id) {
            selectedIds.subtract(topicIds(in: topic))
        } else if let ancestor = selectedAncestor(of: topic.id) {
            selectedIds.remove(ancestor.id)
            selectedIds.formUnion(compactTopicIds(in: ancestor, excluding: topic.id))
        } else if isRequestableTopicId(topic.id) {
            selectedIds.insert(topic.id)
            selectedIds.subtract(childTopicIds(in: topic))
        } else {
            selectedIds.formUnion(compactTopicIds(in: topic.children))
        }
    }
    
    private func isAllSelected() -> Bool {
        !topics.isEmpty && topics.allSatisfy { isSelected($0) }
    }
    
    private func isSelected(_ topic: TopicNode) -> Bool {
        selectedIds.contains(topic.id) || hasSelectedAncestor(of: topic.id)
    }
    
    private func allTopicIds() -> Set<String> {
        topics.reduce(into: Set<String>()) { result, topic in
            result.formUnion(topicIds(in: topic))
        }
    }
    
    private func topicIds(in topic: TopicNode) -> Set<String> {
        var ids: Set<String> = [topic.id]
        topic.children.forEach { child in
            ids.formUnion(topicIds(in: child))
        }
        return ids
    }
    
    private func childTopicIds(in topic: TopicNode) -> Set<String> {
        topic.children.reduce(into: Set<String>()) { result, child in
            result.formUnion(topicIds(in: child))
        }
    }
    
    private func compactTopicIds(in topics: [TopicNode]) -> Set<String> {
        topics.reduce(into: Set<String>()) { result, topic in
            if isRequestableTopicId(topic.id) {
                result.insert(topic.id)
            } else {
                result.formUnion(compactTopicIds(in: topic.children))
            }
        }
    }
    
    private func compactTopicIds(in topic: TopicNode, excluding excludedTopicId: String) -> Set<String> {
        guard topic.id != excludedTopicId else {
            return []
        }
        
        guard containsTopic(excludedTopicId, in: topic) else {
            return compactTopicIds(in: [topic])
        }
        
        return topic.children.reduce(into: Set<String>()) { result, child in
            result.formUnion(compactTopicIds(in: child, excluding: excludedTopicId))
        }
    }
    
    private func isRequestableTopicId(_ id: String) -> Bool {
        !id.contains(":synthetic:")
    }
    
    private func hasSelectedAncestor(of topicId: String) -> Bool {
        selectedAncestor(of: topicId) != nil
    }
    
    private func selectedAncestor(of topicId: String) -> TopicNode? {
        for topic in topics {
            if let ancestor = selectedAncestor(of: topicId, in: topic, currentSelectedAncestor: nil) {
                return ancestor
            }
        }
        
        return nil
    }
    
    private func selectedAncestor(
        of topicId: String,
        in topic: TopicNode,
        currentSelectedAncestor: TopicNode?
    ) -> TopicNode? {
        if topic.id == topicId {
            return currentSelectedAncestor
        }
        
        let nextSelectedAncestor = selectedIds.contains(topic.id) ? topic : currentSelectedAncestor
        for child in topic.children {
            if let ancestor = selectedAncestor(
                of: topicId,
                in: child,
                currentSelectedAncestor: nextSelectedAncestor
            ) {
                return ancestor
            }
        }
        
        return nil
    }
    
    private func containsTopic(_ topicId: String, in topic: TopicNode) -> Bool {
        topic.id == topicId || topic.children.contains { containsTopic(topicId, in: $0) }
    }
    
    private func visibleTopics(for root: TopicNode) -> [VisibleTopic] {
        var result = [
            VisibleTopic(
                topic: root,
                depth: 0,
                isLastChild: true,
                parentLevels: []
            )
        ]
        
        if expandedIds.contains(root.id) {
            appendVisibleChildren(
                root.children,
                depth: 1,
                parentLevels: [],
                to: &result
            )
        }
        
        return result
    }
    
    private func appendVisibleChildren(
        _ children: [TopicNode],
        depth: Int,
        parentLevels: [Int],
        to result: inout [VisibleTopic]
    ) {
        for (index, child) in children.enumerated() {
            let isLastChild = index == children.count - 1
            
            result.append(
                VisibleTopic(
                    topic: child,
                    depth: depth,
                    isLastChild: isLastChild,
                    parentLevels: parentLevels
                )
            )
            
            guard expandedIds.contains(child.id) else {
                continue
            }
            
            var nextParentLevels = parentLevels
            if !isLastChild {
                nextParentLevels.append(depth)
            }
            
            appendVisibleChildren(
                child.children,
                depth: depth + 1,
                parentLevels: nextParentLevels,
                to: &result
            )
        }
    }
}
