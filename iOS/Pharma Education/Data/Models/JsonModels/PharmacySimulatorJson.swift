
struct PharmacySimulatorRequest: Encodable {
    let customersCount: Int
    
    enum CodingKeys: String, CodingKey {
        case customersCount = "customer_count"
    }
}

struct PharmacySimulatorResponse: Decodable {
    let customers: [Customer]
}

struct Customer: Decodable {
    let scenarioId: String
    let bio: CustomerBio
    let request: String
    let facts: [String]
    let task: String
    
    enum CodingKeys: String, CodingKey {
        case scenarioId = "scenario_id"
        case bio = "customer_profile"
        case request = "customer_request"
        case facts = "visible_facts"
        case task
    }
}

struct CustomerBio: Decodable {
    let age: String
    let gender: String
    let context: String
}

struct UserAnswerRequest: Encodable {
    let scenarioId: String
    let answer: String
    
    enum CodingKeys: String, CodingKey {
        case scenarioId = "scenario_id"
        case answer = "student_answer"
    }
}

struct UserAnswerResponse: Decodable {
    let scenarioId: String
    let score: Int
    let verdict: String
    let feedback: String
    let strengths: [String]
    let mistakes: [String]
    let safetyWarnings: [String]
    let recommendedAnswer: String
    let referencedDrugs: [String]
    
    enum CodingKeys: String, CodingKey {
        case scenarioId = "scenario_id"
        case score
        case verdict
        case feedback
        case strengths
        case mistakes
        case safetyWarnings = "safety_warnings"
        case recommendedAnswer = "recommended_answer"
        case referencedDrugs = "referenced_drugs"
    }
}
