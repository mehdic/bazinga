---
name: java
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow, routing, and reporting rules take precedence over this guidance.

# Java Engineering Expertise

## Specialist Profile

Enterprise Java engineer with deep JVM expertise. Writes idiomatic, performant code leveraging modern Java features appropriate to the project's version.

## Implementation Guidelines

### Immutable Data Types

<!-- version: java >= 16 -->
```java
public record CreateUserRequest(
    @NotBlank String email,
    @NotBlank String displayName
) {}
```

<!-- version: java >= 14, java < 16 -->
```java
// Records available as preview in Java 14-15
public record CreateUserRequest(String email, String displayName) {}
```

<!-- version: java < 14 -->
```java
public final class CreateUserRequest {
    private final String email;
    private final String displayName;

    public CreateUserRequest(String email, String displayName) {
        this.email = Objects.requireNonNull(email);
        this.displayName = Objects.requireNonNull(displayName);
    }

    public String getEmail() { return email; }
    public String getDisplayName() { return displayName; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof CreateUserRequest)) return false;
        CreateUserRequest that = (CreateUserRequest) o;
        return email.equals(that.email) && displayName.equals(that.displayName);
    }

    @Override
    public int hashCode() {
        return Objects.hash(email, displayName);
    }
}
```

### Local Variable Type Inference

<!-- version: java >= 10 -->
```java
var users = userRepository.findAll();
var config = new HashMap<String, Object>();
```

<!-- version: java < 10 -->
```java
List<User> users = userRepository.findAll();
Map<String, Object> config = new HashMap<>();
```

### Null-Safe Operations (Java 8+)

```java
public Optional<User> findById(Long id) {
    return repository.findById(id);
}

public String getDisplayName(User user) {
    return Optional.ofNullable(user)
        .map(User::getDisplayName)
        .orElse("Unknown");
}
```

### Pattern Matching

<!-- version: java >= 16 -->
```java
if (obj instanceof String s) {
    return s.toLowerCase();
}
```

<!-- version: java < 16 -->
```java
if (obj instanceof String) {
    String s = (String) obj;
    return s.toLowerCase();
}
```

### Text Blocks

<!-- version: java >= 15 -->
```java
String json = """
    {
        "name": "%s",
        "email": "%s"
    }
    """.formatted(name, email);
```

<!-- version: java < 15 -->
```java
String json = String.format(
    "{\n    \"name\": \"%s\",\n    \"email\": \"%s\"\n}",
    name, email
);
```

### Concurrency

<!-- version: java >= 21 -->
```java
// Virtual threads for blocking I/O
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    var futures = tasks.stream()
        .map(task -> executor.submit(() -> processTask(task)))
        .toList();
}
```

<!-- version: java >= 8, java < 21 -->
```java
// Thread pool for concurrent operations
ExecutorService executor = Executors.newFixedThreadPool(
    Runtime.getRuntime().availableProcessors()
);
try {
    List<Future<Result>> futures = tasks.stream()
        .map(task -> executor.submit(() -> processTask(task)))
        .collect(Collectors.toList());
} finally {
    executor.shutdown();
}
```

## Patterns to Avoid

- Returning null from methods (use `Optional<T>`)
- Field injection with `@Autowired` (use constructor injection)
- Raw generic types (always parameterize: `List<User>` not `List`)
- Checked exceptions for control flow
- Mutable DTOs in APIs
<!-- version: java < 10 -->
- N/A: `var` keyword (Java 10+ only)
<!-- version: java < 14 -->
- N/A: Records (Java 14+ only)
<!-- version: java < 15 -->
- N/A: Text blocks (Java 15+ only)
<!-- version: java < 16 -->
- N/A: Pattern matching in instanceof (Java 16+ only)

## Verification Checklist

- [ ] Uses `Optional` for nullable returns
- [ ] Constructor injection for dependencies
- [ ] Immutable DTOs/value objects
- [ ] Proper resource management (try-with-resources)
- [ ] Stream API for collections where appropriate
- [ ] No raw generic types
