---
name: ios-swiftui
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [swift]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# iOS/SwiftUI Engineering Expertise

## Specialist Profile
iOS specialist building native apps with SwiftUI. Expert in @Observable, async/await, and modern Apple platform patterns.

---

## Patterns to Follow

### @Observable Macro (iOS 17+)
<!-- version: ios >= 17 -->
- **@Observable class**: Replaces ObservableObject, no @Published needed
- **@State for view model**: `@State private var viewModel = ViewModel()`
- **@Bindable for bindings**: Create bindings from @Observable
- **Automatic observation**: Properties observed without wrappers
- **Migration from ObservableObject**: Cleaner, less boilerplate

### MVVM Architecture
- **View owns ViewModel**: ViewModel as @State or @Observable
- **ViewModel in extension**: `extension UserListView { @Observable class ViewModel { } }`
- **Services injected**: Repository, networking via constructor
- **Actor for thread safety**: `actor UserRepository { }`
- **MainActor for UI**: `@MainActor final class ViewModel`

### Async/Await Patterns
- **Task in .task modifier**: `View.task { await viewModel.load() }`
- **Task cancellation**: Automatic on view disappear
- **AsyncSequence for streams**: Async iteration
- **Structured concurrency**: TaskGroup for parallel work
- **Actor isolation**: Protect mutable state

### SwiftUI View Patterns
- **NavigationStack**: Modern navigation (iOS 16+)
- **navigationDestination**: Type-safe destinations
- **@ViewBuilder for composition**: Reusable view factories
- **View preferences**: Communicate up the hierarchy
- **Environment for DI**: Inject dependencies

### SwiftData (iOS 17+)
<!-- version: ios >= 17 -->
- **@Model macro**: Automatic persistence
- **@Query for fetching**: Reactive queries in views
- **ModelContext for writes**: Insert, update, delete
- **Replaces Core Data**: Simpler, Swift-native

---

## Patterns to Avoid

### Architecture Anti-Patterns
- ❌ **Business logic in views**: Move to ViewModel
- ❌ **Force unwrapping optionals**: Use optional binding
- ❌ **Massive ViewModels**: Split by responsibility
- ❌ **Singletons everywhere**: Use dependency injection
- ❌ **Missing @MainActor**: UI updates on wrong thread

### Async Anti-Patterns
- ❌ **Blocking main thread**: Use async/await
- ❌ **Task.detached without care**: Loses structured concurrency
- ❌ **Ignoring cancellation**: Check Task.isCancelled
- ❌ **Data races in actors**: Proper isolation

### SwiftUI Anti-Patterns
- ❌ **Using @StateObject with @Observable**: Use @State instead
- ❌ **Overusing @EnvironmentObject**: Prefer explicit injection
- ❌ **Missing Identifiable conformance**: List/ForEach issues
- ❌ **Computed properties for heavy work**: Cache results
- ❌ **Nested NavigationStack**: Navigation confusion

### State Anti-Patterns
- ❌ **@ObservedObject for owned state**: Use @StateObject (pre-iOS 17)
- ❌ **Storing derived state**: Compute from source
- ❌ **Passing state deeply**: Use environment or coordinator
- ❌ **Mutable state without isolation**: Use actors

---

## Verification Checklist

### Architecture
- [ ] MVVM with @Observable (iOS 17+)
- [ ] Proper actor isolation
- [ ] @MainActor for ViewModels
- [ ] Dependency injection via init

### Views
- [ ] NavigationStack for navigation
- [ ] Type-safe navigation destinations
- [ ] Proper loading/error states
- [ ] Accessibility modifiers

### Async
- [ ] .task for async work
- [ ] Cancellation handled
- [ ] Error states displayed
- [ ] Loading indicators

### Testing
- [ ] ViewInspector for views
- [ ] XCTest for unit tests
- [ ] @MainActor test isolation
- [ ] Previews as living docs

---

## Code Patterns (Reference)

### @Observable ViewModel
<!-- version: ios >= 17 -->
- **Class**: `@Observable @MainActor final class UserListViewModel { var state: State = .idle; ... }`
- **State enum**: `enum State { case idle, loading, loaded([User]), error(String) }`
- **Load method**: `func load() async { state = .loading; state = try await .loaded(repository.fetchAll()) }`

### Views
- **List view**: `NavigationStack { List(users) { user in NavigationLink(value: user) { UserRow(user: user) } } }`
- **Destination**: `.navigationDestination(for: User.self) { user in UserDetailView(user: user) }`
- **Task**: `.task { await viewModel.load() }`

### Pre-iOS 17
- **ObservableObject**: `final class ViewModel: ObservableObject { @Published var state: State = .idle }`
- **StateObject**: `@StateObject private var viewModel = ViewModel()`

### Actor
- **Repository**: `actor UserRepository { func fetchAll() async throws -> [User] { ... } }`
- **Static shared**: `static let shared = UserRepository()`

