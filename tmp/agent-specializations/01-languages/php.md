---
name: php
type: language
priority: 1
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# PHP Engineering Expertise

## Specialist Profile
Modern PHP specialist. Expert in PHP 8+ features, type safety, and PSR standards.

## Implementation Guidelines

### Type Declarations

<!-- version: php >= 8.0 -->
```php
class UserService
{
    public function __construct(
        private readonly UserRepository $repository,
        private readonly LoggerInterface $logger,
    ) {}

    public function findById(string $id): ?User
    {
        return $this->repository->find($id);
    }

    public function create(CreateUserRequest $request): User
    {
        $user = new User(
            id: Uuid::uuid4()->toString(),
            email: $request->email,
            displayName: $request->displayName,
        );

        $this->repository->save($user);
        return $user;
    }
}
```

### DTOs with Readonly

<!-- version: php >= 8.2 -->
```php
readonly class CreateUserRequest
{
    public function __construct(
        public string $email,
        public string $displayName,
    ) {}
}
```

### Enums

<!-- version: php >= 8.1 -->
```php
enum UserStatus: string
{
    case Active = 'active';
    case Inactive = 'inactive';
    case Pending = 'pending';

    public function isAccessible(): bool
    {
        return $this === self::Active;
    }
}
```

### Match Expression

<!-- version: php >= 8.0 -->
```php
public function getStatusMessage(UserStatus $status): string
{
    return match ($status) {
        UserStatus::Active => 'User is active',
        UserStatus::Inactive => 'User is inactive',
        UserStatus::Pending => 'User is pending approval',
    };
}
```

### Null Safe Operator

<!-- version: php >= 8.0 -->
```php
$displayName = $user?->profile?->displayName ?? 'Unknown';
```

## Patterns to Avoid
- ❌ Untyped parameters/returns
- ❌ Array for structured data (use DTOs)
- ❌ Static methods for services
- ❌ `@` error suppression

## Verification Checklist
- [ ] Strict types declared
- [ ] All parameters/returns typed
- [ ] Constructor promotion used
- [ ] Readonly where appropriate
- [ ] PSR-4 autoloading
