---
name: java
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Java Engineering Expertise

## Specialist Profile
Enterprise Java engineer with deep JVM expertise. Writes idiomatic, performant code leveraging modern Java features appropriate to the project version.

## Implementation Guidelines

### Immutable Data Types

<!-- version: java >= 16 -->
```java
public record CreateUserRequest(
    @NotBlank String email,
    @NotBlank String displayName
) {}
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

    public String email() { return email; }
    public String displayName() { return displayName; }
}
```

### Null-Safe Operations

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

### Service Layer Pattern

<!-- style: uses_lombok -->
```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {
    private final UserRepository userRepository;

    public Optional<UserDto> findById(UUID id) {
        return userRepository.findById(id).map(this::toDto);
    }

    @Transactional
    public UserDto create(CreateUserRequest request) {
        User user = User.builder()
            .email(request.email())
            .build();
        return toDto(userRepository.save(user));
    }
}
```

<!-- style: !uses_lombok -->
```java
@Service
@Transactional(readOnly = true)
public class UserService {
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}
```

### Stream Operations

```java
public List<UserDto> findActiveUsers() {
    return userRepository.findAll().stream()
        .filter(User::isActive)
        .map(this::toDto)
        .sorted(Comparator.comparing(UserDto::createdAt).reversed())
        .collect(Collectors.toList());
}
```

## Patterns to Avoid
- ❌ Returning null (use `Optional<T>`)
- ❌ Field injection with `@Autowired` (use constructor)
- ❌ Raw generic types (`List` instead of `List<User>`)
- ❌ Mutable DTOs in APIs
<!-- version: java < 10 -->
- ❌ `var` keyword (Java 10+ only)
<!-- version: java < 14 -->
- ❌ Records (Java 14+ only)

## Verification Checklist
- [ ] Uses `Optional` for nullable returns
- [ ] Constructor injection for dependencies
- [ ] Immutable DTOs/value objects
- [ ] Proper resource management (try-with-resources)
- [ ] Stream API where appropriate
