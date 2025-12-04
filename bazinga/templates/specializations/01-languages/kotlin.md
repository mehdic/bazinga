---
name: kotlin
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Kotlin Engineering Expertise

## Specialist Profile
Kotlin specialist building concise, safe applications. Expert in null safety, coroutines, and functional patterns.

---

## Patterns to Follow

### Null Safety
- **Leverage the type system**: `String` vs `String?` enforces null handling
- **Elvis operator**: `user?.name ?: "Unknown"` for defaults
- **Safe calls**: `user?.profile?.address` for chaining
- **let for null checks**: `user?.let { processUser(it) }`
- **Require/check**: `requireNotNull(value)` for preconditions

### Coroutines Best Practices
<!-- version: kotlin >= 1.3 -->
- **Structured concurrency**: Always use scoped coroutines
- **Inject dispatchers**: Don't hardcode `Dispatchers.IO`
- **SupervisorJob for isolation**: Child failures don't cancel siblings
- **CancellationException handling**: Use `ensureActive()` in long operations
- **External scope for outliving work**: Inject scope for work that must complete
- **Flow for streams**: Cold streams with backpressure support
<!-- version: kotlin >= 1.6 -->
- **SharedFlow/StateFlow**: Preferred over channels for state management
<!-- version: kotlin >= 1.7 -->
- **Context receivers**: `context(Logger)` for implicit dependencies (experimental)

### Data Modeling
- **Data classes for DTOs**: Automatic `equals`, `hashCode`, `copy`
<!-- version: kotlin >= 1.5 -->
- **Sealed interfaces**: More flexible than sealed classes for hierarchies
- **Value classes**: Zero-cost type safety (`@JvmInline value class UserId(val value: String)`)
<!-- version: kotlin >= 1.1, kotlin < 1.5 -->
- **Inline classes**: Use `inline class` (deprecated in 1.5+, use value class)
<!-- version: kotlin >= 1.0 -->
- **Sealed classes for state**: Exhaustive when expressions
- **Default parameters**: `fun create(name: String, role: Role = Role.User)`
- **Immutable by default**: `val` over `var`, immutable collections
<!-- version: kotlin >= 1.9 -->
- **Data objects**: `data object Singleton` for singletons with toString
- **Enum entries**: `entries` property instead of `values()`

### Functional Patterns
- **Extension functions**: Add behavior without inheritance
- **Higher-order functions**: Pass functions as parameters
- **Scope functions**: `let`, `run`, `with`, `apply`, `also` appropriately
- **Sequence for large collections**: Lazy evaluation

### Idiomatic Kotlin
- **Single-expression functions**: `fun double(x: Int) = x * 2`
- **Named arguments**: `createUser(email = email, name = name)`
- **Destructuring**: `val (id, name) = user`
- **when expression**: Replace switch with exhaustive matching

---

## Patterns to Avoid

### Null Safety Violations
- ❌ **`!!` operator**: Find safer alternative; crashes on null
- ❌ **Platform types from Java**: Add explicit nullability annotations
- ❌ **Ignoring nullable returns**: Handle with `?.` or `?:`
- ❌ **lateinit abuse**: Only for framework injection; prefer constructor init

### Coroutine Anti-Patterns
- ❌ **GlobalScope.launch**: Creates untracked coroutines; memory leaks
- ❌ **Hardcoded Dispatchers**: Inject for testability
- ❌ **Catching Exception broadly**: Swallows CancellationException; use specific types
- ❌ **runBlocking in production**: Blocks thread; defeats async purpose
- ❌ **Fire-and-forget launch**: Always track or supervise spawned work
- ❌ **Ignoring cancellation**: Check `isActive` in CPU-bound loops

### Code Smells
- ❌ **Mutable collections in APIs**: Return immutable; mutate internally only
- ❌ **Callbacks when coroutines available**: Modernize to suspending functions
- ❌ **Java-style getters/setters**: Use properties
- ❌ **`it` in nested lambdas**: Name parameters explicitly
- ❌ **Excessive scope functions**: Makes code hard to follow

### Design Issues
- ❌ **God classes**: Split by responsibility
- ❌ **Inheritance over composition**: Prefer delegation
- ❌ **Companion object abuse**: Not for utility functions; use top-level

---

## Verification Checklist

### Null Safety
- [ ] No `!!` in production code
- [ ] Platform types annotated with `@Nullable`/`@NotNull`
- [ ] Nullable handling at boundaries (APIs, DB)
- [ ] `lateinit` used only when necessary

### Coroutines
- [ ] No GlobalScope usage
- [ ] Dispatchers injected (testable)
- [ ] CancellationException not swallowed
- [ ] Long operations check `isActive`
- [ ] Resources cleaned up with `finally` or `use`

### Idiomatic Code
- [ ] Data classes for DTOs
- [ ] Sealed classes for ADTs
- [ ] Immutable collections exposed
- [ ] Extension functions for utilities

### Testing
- [ ] Dispatchers injectable via DI
- [ ] Coroutine tests use `runTest`
- [ ] TestDispatcher for time control

---

## Code Patterns (Reference)

### Recommended Constructs
- **Data class**: `data class User(val id: String, val email: String)`
- **Sealed class**: `sealed class Result<out T> { data class Success<T>(val data: T) : Result<T>() }`
<!-- version: kotlin >= 1.5 -->
- **Value class**: `@JvmInline value class UserId(val value: String)`
- **Sealed interface**: `sealed interface State { data object Loading : State }`
<!-- version: kotlin >= 1.3 -->
- **Coroutine scope**: `coroutineScope { async { ... } }`
- **Flow**: `flow { emit(value) }.flowOn(Dispatchers.IO)`
<!-- version: kotlin >= 1.0 -->
- **Null handling**: `user?.profile?.name ?: "Unknown"`
- **Extension**: `fun String.toSlug() = lowercase().replace(Regex("[^a-z0-9]+"), "-")`
<!-- version: kotlin >= 1.9 -->
- **Data object**: `data object Disconnected : ConnectionState`
- **Enum entries**: `MyEnum.entries.forEach { ... }` (replaces `values()`)

