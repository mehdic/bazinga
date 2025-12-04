---
name: cpp
type: language
priority: 1
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# C++ Engineering Expertise

## Specialist Profile
C++ specialist building performant systems. Expert in modern C++, RAII, and memory safety.

## Implementation Guidelines

### Modern C++ Types

<!-- version: cpp >= 17 -->
```cpp
#include <optional>
#include <string_view>
#include <variant>

class UserService {
public:
    std::optional<User> findById(std::string_view id) const {
        if (auto it = users_.find(std::string{id}); it != users_.end()) {
            return it->second;
        }
        return std::nullopt;
    }
};
```

### Smart Pointers

```cpp
// Unique ownership
auto user = std::make_unique<User>("id", "email@example.com");

// Shared ownership (when needed)
auto sharedUser = std::make_shared<User>("id", "email@example.com");

// Weak reference
std::weak_ptr<User> weakRef = sharedUser;

// Never use raw new/delete for ownership
```

### RAII Pattern

```cpp
class DatabaseConnection {
public:
    DatabaseConnection(std::string_view connStr)
        : conn_(db_connect(connStr.data())) {}

    ~DatabaseConnection() {
        if (conn_) db_close(conn_);
    }

    // Non-copyable
    DatabaseConnection(const DatabaseConnection&) = delete;
    DatabaseConnection& operator=(const DatabaseConnection&) = delete;

    // Movable
    DatabaseConnection(DatabaseConnection&& other) noexcept
        : conn_(std::exchange(other.conn_, nullptr)) {}

private:
    db_handle* conn_;
};
```

### Structured Bindings

<!-- version: cpp >= 17 -->
```cpp
std::map<std::string, User> users;

for (const auto& [id, user] : users) {
    std::cout << id << ": " << user.name << '\n';
}

auto [iter, inserted] = users.try_emplace("id", User{});
```

### Concepts

<!-- version: cpp >= 20 -->
```cpp
template<typename T>
concept Printable = requires(T t) {
    { std::cout << t } -> std::same_as<std::ostream&>;
};

template<Printable T>
void print(const T& value) {
    std::cout << value << '\n';
}
```

## Patterns to Avoid
- ❌ Raw new/delete
- ❌ C-style casts (use static_cast, etc.)
- ❌ NULL (use nullptr)
- ❌ Manual memory management
- ❌ Using namespace std globally

## Verification Checklist
- [ ] RAII for resources
- [ ] Smart pointers for ownership
- [ ] const correctness
- [ ] No memory leaks (use sanitizers)
- [ ] Move semantics where appropriate
