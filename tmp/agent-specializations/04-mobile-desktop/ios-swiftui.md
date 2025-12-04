---
name: ios-swiftui
type: framework
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
requires: [swift]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# iOS/SwiftUI Engineering Expertise

## Specialist Profile
iOS specialist building native apps with SwiftUI. Expert in Combine, async/await, and Apple platform patterns.

## Implementation Guidelines

### Views

```swift
// Views/UserListView.swift
struct UserListView: View {
    @StateObject private var viewModel = UserListViewModel()

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.state {
                case .idle, .loading:
                    ProgressView()
                case .loaded(let users):
                    userList(users)
                case .error(let message):
                    ContentUnavailableView(message, systemImage: "exclamationmark.triangle")
                }
            }
            .navigationTitle("Users")
            .task { await viewModel.loadUsers() }
            .refreshable { await viewModel.loadUsers() }
        }
    }

    @ViewBuilder
    private func userList(_ users: [User]) -> some View {
        List(users) { user in
            NavigationLink(value: user) {
                UserRow(user: user)
            }
        }
        .navigationDestination(for: User.self) { user in
            UserDetailView(user: user)
        }
    }
}
```

### View Models

```swift
// ViewModels/UserListViewModel.swift
@MainActor
final class UserListViewModel: ObservableObject {
    enum State {
        case idle, loading, loaded([User]), error(String)
    }

    @Published private(set) var state: State = .idle

    private let repository: UserRepository

    init(repository: UserRepository = .shared) {
        self.repository = repository
    }

    func loadUsers() async {
        state = .loading
        do {
            let users = try await repository.fetchAll()
            state = .loaded(users)
        } catch {
            state = .error(error.localizedDescription)
        }
    }

    func createUser(_ request: CreateUserRequest) async throws -> User {
        try await repository.create(request)
    }
}
```

### Repository

```swift
// Repositories/UserRepository.swift
actor UserRepository {
    static let shared = UserRepository()

    private let client: APIClient

    init(client: APIClient = .shared) {
        self.client = client
    }

    func fetchAll() async throws -> [User] {
        try await client.request(.get("/users"))
    }

    func create(_ request: CreateUserRequest) async throws -> User {
        try await client.request(.post("/users", body: request))
    }
}
```

### Models

```swift
// Models/User.swift
struct User: Identifiable, Codable, Hashable {
    let id: UUID
    let email: String
    let displayName: String
    let status: Status

    enum Status: String, Codable {
        case active, inactive, pending
    }
}

struct CreateUserRequest: Encodable {
    let email: String
    let displayName: String
}
```

## Patterns to Avoid
- ❌ Force unwrapping optionals
- ❌ Business logic in views
- ❌ Blocking main thread
- ❌ Missing @MainActor for UI updates

## Verification Checklist
- [ ] MVVM architecture
- [ ] Async/await for concurrency
- [ ] Proper state management
- [ ] Navigation using NavigationStack
- [ ] Preview providers for views
