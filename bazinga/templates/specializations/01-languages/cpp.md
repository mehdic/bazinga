---
name: cpp
type: language
priority: 1
token_estimate: 650
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# C++ Engineering Expertise

## Specialist Profile
C++ specialist building performant systems. Expert in modern C++, RAII, memory safety, and the C++ Core Guidelines.

---

## Patterns to Follow

### Resource Management (RAII)
- **Acquire in constructor, release in destructor**: Automatic cleanup
- **Smart pointers for ownership**: `unique_ptr`, `shared_ptr`, `weak_ptr`
- **Rule of Zero**: Prefer to not write special member functions
- **Rule of Five**: If you write one, write all (destructor, copy/move ctor/assign)
- **`std::exchange` for move**: Clean move semantics

### Modern C++ Types
<!-- version: cpp >= 17 -->
- **`std::optional`**: Nullable values without pointers
- **`std::variant`**: Type-safe union
- **`std::string_view`**: Non-owning string reference
- **Structured bindings**: `auto [key, value] = pair;`
- **`if` with initializer**: `if (auto it = map.find(k); it != map.end())`

<!-- version: cpp >= 20 -->
- **Concepts**: Constrain templates with readable requirements
- **Ranges**: Composable, lazy sequence operations
- **`std::span`**: Non-owning view over contiguous sequences
- **Modules**: Replace header includes for faster compilation
- **Coroutines**: Async/generators with `co_await`, `co_yield`

<!-- version: cpp >= 23 -->
- **`std::expected`**: Error handling without exceptions
- **`std::flat_map`**: Cache-friendly associative container
- **`std::print`/`std::println`**: Modern formatted output
- **Deducing `this`**: Simplifies CRTP and recursive lambdas

### Memory Safety
- **Const correctness**: `const` everywhere applicable
- **References over pointers**: When null isn't valid
- **`constexpr` for compile-time**: Move computation to compile time
- **Bounds checking**: Use `.at()` or sanitizers in debug

### API Design
- **Pass by const ref**: Large objects as `const T&`
- **Return by value**: RVO/NRVO optimizes copies away
- **`[[nodiscard]]`**: Force callers to use return values
- **Strong types**: Wrap primitives for type safety

### Concurrency
- **`std::jthread`** (C++20): Auto-joining thread with stop token
- **`std::atomic`**: Lock-free primitives
- **`std::mutex` with `std::lock_guard`**: RAII locking
- **`std::shared_mutex`**: Reader-writer locks

---

## Patterns to Avoid

### Memory Errors
- ❌ **Raw `new`/`delete`**: Use smart pointers or containers
- ❌ **C-style arrays**: Use `std::array` or `std::vector`
- ❌ **Manual memory management**: RAII handles it
- ❌ **Dangling references**: Lifetime issues; use ownership semantics
- ❌ **Uninitialized variables**: Always initialize

### Unsafe Practices
- ❌ **C-style casts**: Use `static_cast`, `dynamic_cast`, `reinterpret_cast`
- ❌ **`NULL`**: Use `nullptr`
- ❌ **`using namespace std`** globally: Pollutes namespace
- ❌ **Macro abuse**: Use `constexpr`, `inline`, templates instead
- ❌ **`void*` for polymorphism**: Use templates or type erasure

### Design Anti-Patterns
- ❌ **Copy-paste programming (Lava Flow)**: Factor into abstractions
- ❌ **God classes**: Split responsibilities
- ❌ **Deep inheritance**: Prefer composition
- ❌ **Premature optimization**: Profile first
- ❌ **Ignoring compiler warnings**: Treat as errors (`-Werror`)

### Exception Safety Issues
- ❌ **Throwing from destructors**: Terminates; use `noexcept`
- ❌ **Catching by value**: Catch by const reference
- ❌ **Empty catch blocks**: At least log the exception
- ❌ **`throw;` in catch without exception**: Undefined behavior

---

## Verification Checklist

### Memory Safety
- [ ] No raw `new`/`delete`
- [ ] Smart pointers for ownership
- [ ] RAII for all resources
- [ ] AddressSanitizer clean in tests
- [ ] Valgrind shows no leaks

### Modern C++
- [ ] `nullptr` over `NULL`
- [ ] `auto` with clear types
- [ ] Range-based for loops
- [ ] Structured bindings where appropriate
- [ ] `std::optional`/`std::variant` for sum types

### Const Correctness
- [ ] Member functions `const` where possible
- [ ] Parameters `const&` for read-only
- [ ] `constexpr` for compile-time evaluation
- [ ] `[[nodiscard]]` on pure functions

### Build Quality
- [ ] Compiles with `-Wall -Wextra -Werror`
- [ ] No warnings from static analyzers
- [ ] clang-tidy checks pass
- [ ] Move semantics implemented correctly

---

## Code Patterns (Reference)

### Recommended Constructs
- **Smart pointer**: `auto user = std::make_unique<User>("id", "email");`
- **Optional**: `std::optional<User> findById(std::string_view id);`
- **RAII**: `std::lock_guard<std::mutex> lock(mutex_);`
- **Structured binding**: `for (const auto& [key, value] : map) { ... }`
<!-- version: cpp >= 20 -->
- **Concept**: `template<typename T> concept Printable = requires(T t) { std::cout << t; };`
- **Span**: `void process(std::span<const int> data);`
<!-- version: cpp >= 23 -->
- **Expected**: `std::expected<User, Error> createUser(const Request& req);`
- **Print**: `std::println("User: {} ({})", user.name, user.id);`

