---
name: csharp
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# C# Engineering Expertise

## Specialist Profile
.NET specialist building enterprise applications. Expert in modern C# features, async patterns, and LINQ.

---

## Patterns to Follow

### Async/Await Best Practices
- **Async all the way**: Once async, propagate through entire call stack
- **Return Task/Task<T>**: Never `async void` except event handlers
- **CancellationToken everywhere**: Pass through all async methods
- **ConfigureAwait(false) in libraries**: Avoid capturing sync context
- **Task.WhenAll for parallel**: Run independent operations concurrently
- **IAsyncEnumerable for streams**: Async iteration over sequences

### Null Safety (C# 8+)
- **Enable nullable**: `#nullable enable` or in project file
- **Explicit nullability**: `string?` vs `string` for intent
- **Null-coalescing**: `??` for defaults, `??=` for assignment
- **Null-conditional**: `?.` to safely navigate
- **Pattern matching**: `is not null` over `!= null`

### Modern C# Features
<!-- version: csharp >= 9 -->
- **Records**: `record User(string Id, string Email)` for immutable data
- **Init-only setters**: `public string Name { get; init; }`
- **Target-typed new**: `User user = new(...)` when type is clear

<!-- version: csharp >= 10 -->
- **File-scoped namespaces**: `namespace MyApp;` (no braces)
- **Global usings**: Common namespaces in one place
- **Record structs**: Value-type records for performance

<!-- version: csharp >= 11 -->
- **Required members**: `required string Name` in records/classes
- **Raw string literals**: `"""multiline"""` for embedded text

### Dependency Injection
- **Constructor injection**: Explicit dependencies, testable
- **Interface segregation**: Small, focused interfaces
- **Scoped services**: Per-request in web applications
- **Options pattern**: `IOptions<T>` for configuration

### LINQ Usage
- **Method syntax**: Prefer over query syntax for consistency
- **Deferred execution**: Understand when queries execute
- **Materialize when needed**: `.ToList()` when re-enumeration is expensive
- **Async LINQ**: `ToListAsync()` with EF Core

---

## Patterns to Avoid

### Async Anti-Patterns
- ❌ **`async void`**: Exceptions can't be caught; use `async Task`
- ❌ **`.Result` and `.Wait()`**: Causes deadlocks; await instead
- ❌ **`Task.Run` for I/O**: Only for CPU-bound work
- ❌ **Fire-and-forget**: Unobserved exceptions crash app
- ❌ **Missing CancellationToken**: Can't cancel long operations
- ❌ **`async` without `await`**: Unnecessary state machine overhead

### Null Handling Issues
- ❌ **Ignoring nullable warnings**: They prevent NullReferenceException
- ❌ **`!` (null-forgiving) abuse**: Hides real nullability issues
- ❌ **Not validating external data**: Trust boundaries need null checks

### Code Quality Issues
- ❌ **God classes**: Split by responsibility
- ❌ **Deep inheritance**: Prefer composition
- ❌ **Service Locator**: Use constructor injection
- ❌ **Static dependencies**: Hard to test; inject instead
- ❌ **Empty catch blocks**: At minimum log the exception

### Performance Anti-Patterns
- ❌ **String concatenation in loops**: Use StringBuilder
- ❌ **LINQ in hot paths without care**: Can allocate unexpectedly
- ❌ **Unnecessary boxing**: Avoid `object` for value types
- ❌ **Large struct copies**: Pass by `in` reference

### Exception Handling
- ❌ **Catching Exception**: Catch specific types
- ❌ **`throw ex`**: Loses stack trace; use `throw`
- ❌ **Exceptions for control flow**: Use return values/patterns

---

## Verification Checklist

### Nullable Reference Types
- [ ] `<Nullable>enable</Nullable>` in project file
- [ ] No nullable warnings (treat as errors)
- [ ] External input validated at boundaries
- [ ] No `!` without documented reason

### Async Code
- [ ] No `async void` (except event handlers)
- [ ] No `.Result` or `.Wait()` calls
- [ ] CancellationToken passed through all async methods
- [ ] `ConfigureAwait(false)` in library code

### Code Quality
- [ ] Constructor injection for dependencies
- [ ] Records used for DTOs and value objects
- [ ] LINQ used appropriately (not over-used)
- [ ] No empty catch blocks

### Testing
- [ ] Dependencies injectable via interfaces
- [ ] No static state that prevents testing
- [ ] Async tests use `async Task`

---

## Code Patterns (Reference)

### Recommended Constructs
- **Record**: `public record UserDto(string Id, string Email);`
- **Async method**: `public async Task<T> GetAsync(CancellationToken ct)`
- **Null handling**: `user?.Name ?? "Unknown"`
- **Pattern matching**: `if (result is { Success: true, Data: var data })`
- **LINQ**: `.Where(x => x.Active).Select(x => x.Name).ToList()`
- **Result pattern**: `Result<T>.Success(value)` / `Result<T>.Failure(error)`
- **Options**: `services.Configure<MyOptions>(config.GetSection("My"))`
