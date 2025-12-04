---
name: ruby
type: language
priority: 1
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Ruby Engineering Expertise

## Specialist Profile
Ruby specialist writing elegant, expressive code. Expert in Ruby idioms, OOP design, and the Ruby ecosystem.

---

## Patterns to Follow

### Object Design
- **Immutable by default**: `freeze` objects after initialization
- **Keyword arguments**: `def create(email:, name:)` for clarity
- **attr_reader over attr_accessor**: Minimize mutation surface
- **Small classes**: Single responsibility, <100 lines ideal
- **Composition over inheritance**: Inject collaborators

### Service Objects
- **Single public method**: `call` or descriptive verb
- **Dependency injection**: Pass collaborators via constructor
- **Return value objects**: `Success(data)` / `Failure(error)`
- **Explicit dependencies**: No reliance on global state

### Enumerable Patterns
- **Chain methods**: `select`, `map`, `reduce` for transformations
- **Lazy enumerables**: `.lazy` for large/infinite sequences
- **Symbol-to-proc**: `&:method_name` for simple transformations
- **`each_with_object`**: When building up a result

### Error Handling
- **Custom exception hierarchy**: Domain-specific errors
- **Specific rescue**: `rescue SpecificError` not `rescue Exception`
- **Bang methods for danger**: `save!` raises, `save` returns boolean
- **Guard clauses**: Early return for invalid cases

### Ruby Idioms
- **Duck typing**: Respond to messages, don't check types
- **Blocks for callbacks**: Yield for customization points
- **Double splat for options**: `**options` for hash arguments
- **`||=` for memoization**: Cache expensive computations
- **Ternary for simple conditions**: `x ? y : z` not if/else

### Modern Ruby Features
<!-- version: ruby >= 2.7 -->
- **Pattern matching**: `case obj in { name:, age: } then ...`
- **Numbered block params**: `arr.map { _1 * 2 }`
- **Argument forwarding**: `def foo(...); bar(...); end`
<!-- version: ruby >= 3.0 -->
- **Endless methods**: `def double(x) = x * 2`
- **Ractor for parallelism**: True parallel execution (experimental)
- **RBS type signatures**: Separate type definition files
<!-- version: ruby >= 3.1 -->
- **Hash shorthand**: `{ x:, y: }` when var names match keys
- **Anonymous block**: `def foo(&); bar(&); end`
<!-- version: ruby >= 3.2 -->
- **Data class**: `Data.define(:name, :email)` for immutable structs

### Code Organization
- **Module for namespacing**: Group related classes
- **Concerns for shared behavior**: `include`/`extend` carefully
- **Private for implementation**: Default to private methods
- **Semantic versioning**: Follow SemVer for libraries

---

## Patterns to Avoid

### Exception Handling
- ❌ **`rescue Exception`**: Catches system signals; use `StandardError`
- ❌ **Empty rescue blocks**: At minimum log the error
- ❌ **`rescue => e; raise e`**: Just let it propagate
- ❌ **Exceptions for control flow**: Use conditionals instead

### Object-Oriented Issues
- ❌ **God objects**: Classes doing too much; split by responsibility
- ❌ **Deep inheritance**: Max 2-3 levels; prefer composition
- ❌ **Excessive metaprogramming**: Makes code hard to understand
- ❌ **`method_missing` abuse**: Only when truly dynamic

### Code Smells
- ❌ **Long methods**: >10 lines usually needs splitting
- ❌ **Deep nesting**: >2 levels; use early returns
- ❌ **Global variables**: Use dependency injection
- ❌ **`unless` with `else`**: Confusing; use `if` instead
- ❌ **Double negatives**: `!user.inactive?` → `user.active?`

### Performance Issues
- ❌ **N+1 queries**: Use `includes` or `preload` in ActiveRecord
- ❌ **String `+` in loops**: Use `<<` or `join`
- ❌ **Creating objects in loops**: Cache or preallocate
- ❌ **`each` when `map` fits**: Choose the right iterator

### Rails-Specific (if applicable)
- ❌ **Callbacks for business logic**: Use service objects
- ❌ **Fat models**: Extract to services, form objects, query objects
- ❌ **Fat controllers**: Keep thin; delegate to services
- ❌ **Skipping validations**: `save(validate: false)` is dangerous

---

## Verification Checklist

### Code Quality
- [ ] `rubocop` passes with no violations
- [ ] No `rescue Exception` (use `StandardError`)
- [ ] Methods under 10 lines
- [ ] Classes under 100 lines

### Design
- [ ] Objects frozen when immutable
- [ ] Dependency injection used (no global state)
- [ ] Service objects for business logic
- [ ] Single responsibility per class

### Testing (RSpec)
- [ ] Descriptive context blocks
- [ ] One expectation per example (generally)
- [ ] Factories over fixtures (FactoryBot)
- [ ] No database access in unit tests

### Style
- [ ] Keyword arguments for clarity
- [ ] `attr_reader` preferred over `attr_accessor`
- [ ] Early returns (guard clauses)
- [ ] Consistent naming conventions

---

## Code Patterns (Reference)

### Recommended Constructs
- **Service object**: `class CreateUser; def call(email:) ... end; end`
- **Value object**: `User = Struct.new(:id, :email, keyword_init: true)`
- **Result pattern**: `Success(user)` / `Failure(errors)`
- **Memoization**: `@users ||= repository.all`
- **Guard clause**: `return if params.blank?`
- **Enumerable chain**: `users.select(&:active?).map(&:email)`
- **Frozen object**: `def initialize(...); ...; freeze; end`
- **Keyword args**: `def create(email:, name:, role: :user)`
<!-- version: ruby >= 2.7 -->
- **Pattern match**: `case user in { name:, role: :admin } then grant_access`
- **Numbered param**: `items.map { _1.name }`
<!-- version: ruby >= 3.0 -->
- **Endless method**: `def square(x) = x * x`
<!-- version: ruby >= 3.1 -->
- **Hash shorthand**: `{ user:, timestamp: }` (same as `{ user: user, timestamp: timestamp }`)
<!-- version: ruby >= 3.2 -->
- **Data class**: `Person = Data.define(:name, :age)`
