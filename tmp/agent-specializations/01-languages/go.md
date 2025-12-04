---
name: go
type: language
priority: 1
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Go Engineering Expertise

## Specialist Profile
Go engineer building performant, concurrent systems. Expert in idiomatic Go, goroutines, channels, and the standard library.

## Implementation Guidelines

### Error Handling

```go
func GetUser(id string) (*User, error) {
    user, err := db.FindUser(id)
    if err != nil {
        return nil, fmt.Errorf("GetUser(%s): %w", id, err)
    }
    return user, nil
}
```

### Struct Design

```go
type Config struct {
    Host    string
    Port    int
    Timeout time.Duration
}

func NewConfig(host string, port int) (*Config, error) {
    if host == "" {
        return nil, errors.New("host cannot be empty")
    }
    return &Config{
        Host:    host,
        Port:    port,
        Timeout: 30 * time.Second,
    }, nil
}
```

### Interfaces

```go
// Define interfaces where they're used
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    Save(ctx context.Context, user *User) error
}

// Accept interfaces, return structs
func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}
```

### Concurrency

```go
func ProcessItems(ctx context.Context, items []Item) error {
    g, ctx := errgroup.WithContext(ctx)

    for _, item := range items {
        item := item // capture
        g.Go(func() error {
            return processItem(ctx, item)
        })
    }
    return g.Wait()
}
```

### Table-Driven Tests

```go
func TestUserService_Create(t *testing.T) {
    tests := []struct {
        name    string
        input   CreateUserRequest
        wantErr bool
    }{
        {"valid", CreateUserRequest{Email: "test@example.com"}, false},
        {"empty email", CreateUserRequest{Email: ""}, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := svc.Create(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

## Patterns to Avoid
- ❌ Ignoring errors with `_`
- ❌ Global mutable state
- ❌ `init()` with side effects
- ❌ Overusing `interface{}`
- ❌ Channel misuse for simple sync

## Verification Checklist
- [ ] All errors handled or commented
- [ ] Context passed through call chain
- [ ] Goroutines have cancellation
- [ ] Resources cleaned with defer
- [ ] Table-driven tests
