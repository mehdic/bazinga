---
name: php
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# PHP Engineering Expertise

## Specialist Profile
Modern PHP specialist. Expert in PHP 8+ features, type safety, PSR standards, and secure coding practices.

---

## Patterns to Follow

### Type Safety (PHP 8+)
- **Strict types declaration**: `declare(strict_types=1);` at top of every file
- **Typed properties**: All class properties explicitly typed
- **Constructor property promotion**: Reduce boilerplate with `public readonly`
- **Union types**: `string|int` for multiple valid types
- **Nullable types**: `?string` for optional values
- **Return type declarations**: All methods return typed values

### Object Design
- **Readonly classes** (8.2+): Immutable DTOs with `readonly class`
- **Enums** (8.1+): Type-safe constants with backed enums
- **Constructor injection**: Dependencies via constructor, not setter injection
- **Final by default**: Mark classes `final` unless designed for inheritance
- **Interface segregation**: Small, focused interfaces

### Modern Syntax
- **Match expression** (8.0+): Replace switch for value assignment
- **Named arguments**: `create(email: $email, name: $name)` for clarity
- **Null safe operator**: `$user?->profile?->name` for safe chaining
- **Arrow functions**: `fn($x) => $x * 2` for simple callbacks
- **Attributes** (8.0+): Replace docblock annotations

### Security Practices
- **Parameterized queries**: Always use PDO prepared statements
- **Password hashing**: `password_hash()` with `PASSWORD_ARGON2ID`
- **Input validation**: Validate all external input at boundaries
- **Output escaping**: `htmlspecialchars()` for HTML context
- **CSRF protection**: Token validation on state-changing requests

### PSR Compliance
- **PSR-4**: Autoloading standard for class files
- **PSR-12**: Extended coding style guide
- **PSR-7/15**: HTTP message interfaces for middleware
- **PSR-11**: Container interface for dependency injection

---

## Patterns to Avoid

### Type System Issues
- ❌ **Untyped parameters/returns**: Always declare types
- ❌ **Mixed type abuse**: Too broad; use unions or generics
- ❌ **Array for structured data**: Use DTOs with typed properties
- ❌ **Stringly-typed code**: Use enums, value objects, constants

### Security Anti-Patterns
- ❌ **SQL string interpolation**: Always use prepared statements
- ❌ **`eval()` and `create_function()`**: Never execute dynamic code
- ❌ **`@` error suppression**: Hides bugs; handle errors explicitly
- ❌ **Client-only validation**: Always validate server-side
- ❌ **Trusting `$_GET/$_POST` directly**: Sanitize and validate first
- ❌ **`include` with user input**: Path traversal vulnerability

### Design Anti-Patterns
- ❌ **God class (Blob)**: Split by responsibility
- ❌ **Service Locator**: Use constructor injection instead
- ❌ **Static methods for services**: Untestable; inject dependencies
- ❌ **Spaghetti code**: Separate concerns (validation, logic, output)
- ❌ **Magic methods overuse**: Explicit is better than implicit

### Code Smells
- ❌ **Long methods**: >20 lines needs decomposition
- ❌ **Deep nesting**: Max 3 levels; use early returns
- ❌ **Global state**: Use dependency injection
- ❌ **Exception for control flow**: Use conditionals

---

## Verification Checklist

### Type Safety
- [ ] `declare(strict_types=1)` in all files
- [ ] All parameters and returns typed
- [ ] PHPStan/Psalm at level 8+ passes
- [ ] No `@var` docblocks (types in code)

### Security
- [ ] All queries use prepared statements
- [ ] Input validated at boundaries
- [ ] Output escaped appropriately
- [ ] `password_hash()` for credentials
- [ ] No `eval()`, `assert()` with strings

### Modern PHP
- [ ] Constructor promotion used
- [ ] Readonly where appropriate
- [ ] Enums for finite sets
- [ ] Match expressions over switch

### Standards
- [ ] PSR-4 autoloading
- [ ] PSR-12 style compliance
- [ ] Composer for dependencies

---

## Code Patterns (Reference)

### Recommended Constructs
<!-- version: php >= 8.2 -->
- **Readonly DTO**: `readonly class CreateUserRequest { public function __construct(public string $email) {} }`
- **Backed enum**: `enum Status: string { case Active = 'active'; case Inactive = 'inactive'; }`
- **Match**: `$message = match($status) { Status::Active => 'Active', default => 'Unknown' };`
- **Null safe**: `$name = $user?->profile?->displayName ?? 'Unknown';`
- **Constructor injection**: `public function __construct(private readonly UserRepository $repo) {}`
- **Named arguments**: `$user = User::create(email: $email, name: $name);`

