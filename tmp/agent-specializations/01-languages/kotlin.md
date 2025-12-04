---
name: kotlin
type: language
priority: 1
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Kotlin Engineering Expertise

## Specialist Profile
Kotlin specialist building concise, safe applications. Expert in null safety, coroutines, and functional patterns.

## Implementation Guidelines

### Data Classes

```kotlin
data class User(
    val id: String,
    val email: String,
    val displayName: String,
    val createdAt: Instant = Instant.now()
)

data class CreateUserRequest(
    val email: String,
    val displayName: String
)
```

### Null Safety

```kotlin
fun findUser(id: String): User? = repository.findById(id)

fun getDisplayName(user: User?): String =
    user?.displayName ?: "Unknown"

// Safe call chain
val city = user?.address?.city ?: "Unknown"

// Let for null checks
user?.let { processUser(it) }
```

### Coroutines

```kotlin
suspend fun fetchUsers(ids: List<String>): List<User> = coroutineScope {
    ids.map { id ->
        async { userService.findById(id) }
    }.awaitAll().filterNotNull()
}

fun CoroutineScope.processUsersConcurrently(users: List<User>) {
    users.forEach { user ->
        launch {
            processUser(user)
        }
    }
}
```

### Extension Functions

```kotlin
fun String.toSlug(): String =
    lowercase()
        .replace(Regex("[^a-z0-9]+"), "-")
        .trim('-')

fun <T> List<T>.secondOrNull(): T? = getOrNull(1)
```

### Sealed Classes

```kotlin
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String) : Result<Nothing>()
}

fun processResult(result: Result<User>) = when (result) {
    is Result.Success -> println(result.data)
    is Result.Error -> println(result.message)
}
```

## Patterns to Avoid
- ❌ `!!` operator (find a safer way)
- ❌ Platform types from Java
- ❌ Mutable collections when immutable works
- ❌ Callbacks when coroutines available

## Verification Checklist
- [ ] No `!!` in production code
- [ ] Data classes for DTOs
- [ ] Coroutines for async
- [ ] Sealed classes for state
- [ ] Extension functions where appropriate
