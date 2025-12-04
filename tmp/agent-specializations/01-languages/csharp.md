---
name: csharp
type: language
priority: 1
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# C# Engineering Expertise

## Specialist Profile
.NET specialist building enterprise applications. Expert in modern C# features, async patterns, and LINQ.

## Implementation Guidelines

### Record Types

<!-- version: csharp >= 9 -->
```csharp
public record CreateUserRequest(string Email, string DisplayName);

public record User(Guid Id, string Email, string DisplayName, DateTime CreatedAt);
```

<!-- version: csharp < 9 -->
```csharp
public class CreateUserRequest
{
    public string Email { get; }
    public string DisplayName { get; }

    public CreateUserRequest(string email, string displayName)
    {
        Email = email;
        DisplayName = displayName;
    }
}
```

### Null Safety

<!-- version: csharp >= 8 -->
```csharp
#nullable enable

public class UserService
{
    public User? FindById(Guid id) => _repository.Find(id);

    public string GetDisplayName(User? user)
        => user?.DisplayName ?? "Unknown";
}
```

### LINQ Patterns

```csharp
public IEnumerable<UserDto> GetActiveUsers()
{
    return _context.Users
        .Where(u => u.IsActive)
        .OrderByDescending(u => u.CreatedAt)
        .Select(u => new UserDto(u.Id, u.Email, u.DisplayName))
        .ToList();
}
```

### Async/Await

```csharp
public async Task<Result<User>> CreateUserAsync(
    CreateUserRequest request,
    CancellationToken cancellationToken = default)
{
    var existingUser = await _repository.FindByEmailAsync(
        request.Email, cancellationToken);

    if (existingUser is not null)
        return Result.Failure<User>("Email already exists");

    var user = new User(Guid.NewGuid(), request.Email, request.DisplayName);
    await _repository.AddAsync(user, cancellationToken);

    return Result.Success(user);
}
```

### Dependency Injection

```csharp
public class UserService : IUserService
{
    private readonly IUserRepository _repository;
    private readonly ILogger<UserService> _logger;

    public UserService(IUserRepository repository, ILogger<UserService> logger)
    {
        _repository = repository;
        _logger = logger;
    }
}
```

## Patterns to Avoid
- ❌ Ignoring nullable warnings
- ❌ Blocking on async (`Result`, `.Wait()`)
- ❌ Empty catch blocks
- ❌ Service Locator pattern

## Verification Checklist
- [ ] Nullable reference types enabled
- [ ] Async all the way down
- [ ] CancellationToken passed through
- [ ] Constructor injection for DI
