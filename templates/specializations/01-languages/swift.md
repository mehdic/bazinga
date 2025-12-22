---
name: swift
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Swift Engineering Expertise

## Specialist Profile
Swift specialist building safe, performant applications. Expert in protocols, value types, and Swift concurrency.

---

## Patterns to Follow

### Value Types & Mutability
- **Structs over classes**: Default to structs; classes only for reference semantics
- **Immutable by default**: `let` over `var`
- **Copy-on-write**: Leverage for efficient value semantics
- **Protocol extensions**: Share behavior without inheritance

### Optional Handling
- **Guard for early exit**: `guard let user = user else { return }`
- **Optional chaining**: `user?.profile?.name`
- **Nil coalescing**: `name ?? "Unknown"`
- **Optional map/flatMap**: Transform without unwrapping
- **if let for conditional binding**: When you need the value in scope

### Swift Concurrency (5.5+)
- **async/await**: Replace completion handlers
- **Actors for isolation**: Protect mutable state from data races
- **@MainActor for UI**: Ensure UI updates on main thread
- **TaskGroup for parallel work**: Structured concurrent operations
- **Sendable for thread safety**: Mark types safe to pass across isolation
- **@concurrent for explicit parallelism** (6.2+): Opt into concurrent execution

### Protocol-Oriented Design
- **Protocol with associated types**: Generic abstractions
- **Protocol extensions**: Default implementations
- **Composition over inheritance**: Combine small protocols
- **Existential types**: `any Protocol` for runtime polymorphism

### Error Handling
- **Typed throws** (Swift 6): `throws(MyError)` for specific error types
- **Result type**: For async operations without throwing
- **Custom error enums**: Domain-specific error cases
- **Error context**: Add context when re-throwing

---

## Patterns to Avoid

### Optional Abuse
- ❌ **Force unwrapping `!`**: Crashes at runtime; use safe alternatives
- ❌ **Implicit unwrapped optionals**: Only for IBOutlets; avoid elsewhere
- ❌ **Nested optional unwrapping**: Flatten with `flatMap`
- ❌ **Force try `try!`**: Handle errors properly

### Concurrency Anti-Patterns
- ❌ **Split isolation types**: Don't mix `@MainActor` and non-isolated in one type
- ❌ **Actor protocol conformance with sync methods**: Actors are async by nature
- ❌ **Async on non-Sendable types**: Data races waiting to happen
- ❌ **Actors as queues**: They're not; use proper queue abstractions
- ❌ **DispatchQueue when async/await available**: Modernize to structured concurrency

### Design Issues
- ❌ **Classes when structs work**: Avoid reference semantics overhead
- ❌ **Deep inheritance hierarchies**: Max 2 levels; prefer protocols
- ❌ **Massive view controllers**: Extract to coordinators, view models
- ❌ **Callbacks when async available**: Convert to async/await

### Swift 6 Migration Pitfalls
- ❌ **Swift 5 mode without warnings**: Builds incorrect mental model
- ❌ **Ignoring concurrency warnings**: They're errors in Swift 6
- ❌ **Overusing @preconcurrency**: Temporary fix only; migrate properly

---

## Verification Checklist

### Type Safety
- [ ] No force unwrapping (`!`) without certainty
- [ ] Optionals handled with `guard`/`if let`
- [ ] Error enums for failure cases
- [ ] Structs preferred over classes

### Swift 6 Concurrency
- [ ] No data race warnings
- [ ] Actors for shared mutable state
- [ ] @MainActor for UI code
- [ ] Sendable types for cross-isolation
- [ ] async/await over completion handlers

### Protocol Design
- [ ] Small, focused protocols
- [ ] Extensions for default implementations
- [ ] Associated types for generic abstractions
- [ ] Composition over inheritance

### Performance
- [ ] Value types for data
- [ ] Lazy properties where appropriate
- [ ] Copy-on-write for large collections
- [ ] Profile with Instruments

---

## Code Patterns (Reference)

### Recommended Constructs
- **Struct**: `struct User: Identifiable, Codable, Sendable { let id: UUID; let email: String }`
- **Actor**: `actor UserService { func findById(_ id: UUID) async throws -> User }`
- **Guard**: `guard let user = user else { throw UserError.notFound }`
- **Result**: `func fetch() -> Result<User, UserError>`
- **TaskGroup**: `try await withThrowingTaskGroup(of: User.self) { group in ... }`
- **Protocol**: `protocol Repository { associatedtype Entity; func find(_ id: UUID) async throws -> Entity? }`
<!-- version: swift >= 6 -->
- **Typed throws**: `func load() throws(LoadError) -> Data`
- **@concurrent**: `@concurrent func process() async -> Result`

