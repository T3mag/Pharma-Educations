struct TopicsTreeResponse: Decodable {
    let topics: [TopicNode]
}

struct TopicNode: Decodable {
    let id: String
    let catalog: String
    let type: String
    let title: String
    let parentId: String?
    let level: Int
    let path: [String]
    let sourcePagePath: String
    let code: String
    let docCount: Int
    let hasChildren: Bool
    let children: [TopicNode]

    enum CodingKeys: String, CodingKey {
        case id
        case catalog
        case type
        case title
        case parentId = "parent_id"
        case level
        case path
        case sourcePagePath = "source_page_path"
        case code
        case docCount = "doc_count"
        case hasChildren = "has_children"
        case children
    }
}
