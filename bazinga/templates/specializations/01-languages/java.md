---
name: java
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Java Engineering Expertise

## Specialist Profile
Java specialist building enterprise applications. Expert in modern Java features, design patterns, and JVM performance.

---

## Patterns to Follow

### Core Principles
- **SOLID principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY (Don't Repeat Yourself)**: Extract common code into reusable methods/classes
- **KISS (Keep It Simple)**: Simplest solution that works; avoid over-engineering
- **YAGNI**: Don't add functionality until needed

### Immutability
<!-- version: java >= 16 -->
- **Records**: `record User(String id, String email) {}` for immutable data
<!-- version: java < 16 -->
- **Final classes**: Use Lombok `@Value` or write immutable classes with final fields
<!-- version: java >= 9 -->
- **Immutable collections**: `List.of()`, `Set.of()`, `Map.of()` for unmodifiable collections
<!-- version: java < 9 -->
- **Immutable collections**: `Collections.unmodifiableList()` or Guava `ImmutableList`
<!-- version: java >= 8 -->
- **Final fields**: Mark fields `final` when they shouldn't change
- **Defensive copying**: Copy mutable parameters/returns to preserve immutability

### Modern Java Features
<!-- version: java >= 14 -->
- **Pattern matching**: `if (obj instanceof String s)` - no explicit cast needed
- **Switch expressions**: `var result = switch(x) { case A -> 1; default -> 0; };`
- **Text blocks**: `"""multiline string"""` for SQL, JSON, etc.

<!-- version: java >= 17 -->
- **Sealed classes**: `sealed class Shape permits Circle, Square` for closed hierarchies

<!-- version: java >= 21 -->
- **Virtual threads**: `Thread.startVirtualThread()` for high-concurrency I/O
- **Record patterns**: Destructuring in pattern matching
- **Sequenced collections**: `getFirst()`, `getLast()`, `reversed()`

### Error Handling
- **Specific exceptions**: Catch the most specific exception type
- **Custom exceptions**: Create domain-specific exception hierarchy
- **Try-with-resources**: For all `AutoCloseable` resources
- **No swallowing**: Never `catch (Exception e) {}` - at minimum log

### Dependency Management
- **Constructor injection**: Prefer over field injection (testable, explicit dependencies)
- **Program to interfaces**: Depend on abstractions, not implementations
- **Composition over inheritance**: Use delegation, not deep hierarchies

### Null Safety
- **Optional for return types**: `Optional<User>` instead of nullable User
- **Never Optional parameters**: Use overloading instead
- **@Nullable/@NonNull annotations**: Document nullability explicitly
- **Objects.requireNonNull()**: Fail fast on null parameters

---

## Patterns to Avoid

### Design Anti-Patterns
- ❌ **God Object**: Class with too many responsibilities; split by domain
- ❌ **Spaghetti Code**: Tangled logic; extract methods, use patterns
- ❌ **Magic Numbers/Strings**: Hardcoded values; use constants or enums
- ❌ **Copy-Paste Programming**: Duplicated code; extract common logic

### Code Smells
- ❌ **Long methods**: >20 lines usually means split needed
- ❌ **Deep nesting**: >3 levels; use early returns, extract methods
- ❌ **Feature envy**: Method uses another class's data more than its own
- ❌ **Primitive obsession**: Use domain types instead of raw primitives

### Null Handling Issues
- ❌ **Returning null from collections**: Return empty collection instead
- ❌ **Optional.get() without check**: Use `orElse()`, `orElseThrow()`, `ifPresent()`
- ❌ **Optional for fields**: Optional is for return types only
- ❌ **Null checks everywhere**: Fix the root cause, use @NonNull

### Resource Management
- ❌ **Manual resource closing**: Use try-with-resources
- ❌ **Catching and ignoring exceptions**: At minimum log the error
- ❌ **`catch (Exception e)`**: Catch specific exceptions

### Performance Anti-Patterns
- ❌ **String concatenation in loops**: Use StringBuilder
- ❌ **Creating objects in loops**: Pool or create outside
- ❌ **Unnecessary boxing**: Use primitives when possible
- ❌ **N+1 queries**: Batch database calls

### Concurrency Issues
- ❌ **Synchronized on mutable field**: Lock on final object
- ❌ **Double-checked locking (incorrect)**: Use volatile or initialization-on-demand
- ❌ **Thread.stop()**: Use interruption instead

---

## Verification Checklist

### Code Quality
- [ ] No `@SuppressWarnings` without justification comment
- [ ] All public APIs have Javadoc
- [ ] No raw types (use generics)
- [ ] No empty catch blocks

### Modern Practices
- [ ] Records used for DTOs and value objects
- [ ] var used for local variables where type is obvious
- [ ] Stream API for collection transformations
- [ ] Optional for nullable returns

### Resource Safety
- [ ] Try-with-resources for all AutoCloseable
- [ ] No resource leaks (connections, streams, etc.)
- [ ] Proper thread pool shutdown

### Testing
- [ ] Constructor injection enables unit testing
- [ ] No static dependencies that prevent mocking
- [ ] Business logic separate from I/O

---

## Code Patterns (Reference)

### Recommended Constructs
<!-- version: java >= 16 -->
- **Record**: `record UserDto(String id, String email) {}`
<!-- version: java >= 17 -->
- **Sealed class**: `sealed interface Shape permits Circle, Square {}`
<!-- version: java >= 14 -->
- **Pattern matching**: `if (shape instanceof Circle c) { use(c.radius()); }`
- **Switch expression**: `var x = switch(status) { case A -> 1; default -> 0; };`
<!-- version: java >= 10 -->
- **var keyword**: `var conn = getConnection()` for obvious types
<!-- version: java >= 8 -->
- **Try-with-resources**: `try (Connection conn = getConnection()) { ... }`
- **Optional**: `findUser(id).map(User::email).orElse("unknown")`
- **Stream**: `users.stream().filter(User::isActive).map(User::getId).collect(Collectors.toList())`
<!-- version: java >= 16 -->
- **Stream toList()**: `users.stream().filter(User::isActive).toList()` (Java 16+)
