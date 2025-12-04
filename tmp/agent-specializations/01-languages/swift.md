---
name: swift
type: language
priority: 1
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Swift Engineering Expertise

## Specialist Profile
Swift specialist building safe, performant applications. Expert in protocols, value types, and Swift concurrency.

## Implementation Guidelines

### Structs and Value Types

```swift
struct User: Identifiable, Codable {
    let id: UUID
    let email: String
    let displayName: String
    let createdAt: Date

    init(id: UUID = UUID(), email: String, displayName: String) {
        self.id = id
        self.email = email
        self.displayName = displayName
        self.createdAt = Date()
    }
}
```

### Optionals

```swift
func findUser(id: UUID) -> User? {
    repository.find(id)
}

func getDisplayName(user: User?) -> String {
    user?.displayName ?? "Unknown"
}

// Guard for early exit
func processUser(_ user: User?) throws {
    guard let user = user else {
        throw UserError.notFound
    }
    // user is now non-optional
}
```

### Swift Concurrency

```swift
actor UserService {
    private let repository: UserRepository

    func findById(_ id: UUID) async throws -> User {
        try await repository.find(id)
    }

    func fetchAll(ids: [UUID]) async throws -> [User] {
        try await withThrowingTaskGroup(of: User?.self) { group in
            for id in ids {
                group.addTask { try? await self.findById(id) }
            }
            return try await group.compactMap { $0 }.reduce(into: []) { $0.append($1) }
        }
    }
}
```

### Protocol-Oriented Design

```swift
protocol Repository {
    associatedtype Entity
    func find(_ id: UUID) async throws -> Entity?
    func save(_ entity: Entity) async throws
}

struct UserRepository: Repository {
    typealias Entity = User

    func find(_ id: UUID) async throws -> User? { ... }
    func save(_ entity: User) async throws { ... }
}
```

### Result Type

```swift
enum UserError: Error {
    case notFound
    case invalidEmail
}

func createUser(email: String) -> Result<User, UserError> {
    guard email.contains("@") else {
        return .failure(.invalidEmail)
    }
    let user = User(email: email, displayName: "")
    return .success(user)
}
```

## Patterns to Avoid
- ❌ Force unwrapping `!` without certainty
- ❌ Classes when structs work
- ❌ Inheritance when protocols work
- ❌ Callbacks when async/await available

## Verification Checklist
- [ ] Prefer structs over classes
- [ ] No force unwrapping
- [ ] Protocols for abstraction
- [ ] async/await for concurrency
- [ ] Codable for serialization
