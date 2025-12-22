---
name: python
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Python Engineering Expertise

## Specialist Profile
Python specialist building clean, maintainable code. Expert in type hints, async patterns, and Pythonic idioms.

---

## Patterns to Follow

### Code Structure
- **EAFP over LBYL**: "Easier to Ask Forgiveness than Permission" - use try/except rather than excessive if-checks
- **Context managers**: Always use `with` for resource management (files, connections, locks)
- **Comprehensions**: Prefer list/dict/set comprehensions over manual loops for transformations
- **Generator expressions**: Use for large datasets to avoid memory overhead (`(x for x in items)`)
- **Explicit is better than implicit**: Clear variable names, explicit returns, no magic

### Type System
- **Type hints on all public APIs**: Functions, methods, class attributes
<!-- version: python >= 3.10 -->
- **Use `|` union syntax**: `def foo(x: str | None) -> int | str`
<!-- version: python < 3.10 -->
- **Use `Optional`/`Union`**: `def foo(x: Optional[str]) -> Union[int, str]`
<!-- version: python >= 3.8 -->
- **Protocols over ABCs**: For structural subtyping (duck typing with type safety)
- **TypedDict**: For dictionary schemas, especially API responses
<!-- version: python >= 3.10 -->
- **Frozen dataclasses**: `@dataclass(frozen=True, slots=True)` for immutable data
<!-- version: python >= 3.7, python < 3.10 -->
- **Frozen dataclasses**: `@dataclass(frozen=True)` for immutable data (no slots)

### Error Handling
- **Specific exceptions**: Catch the most specific exception possible
- **Custom exception hierarchy**: Create domain-specific exceptions inheriting from base
- **Exception chaining**: Use `raise NewException from original` to preserve context
- **Result pattern**: Consider `Result[T, E]` types for expected failures (e.g., `returns` library)

### Async Programming
- **Async all the way**: Don't mix sync/async - propagate async up the call stack
- **`asyncio.gather`**: For concurrent I/O operations
<!-- version: python >= 3.11 -->
- **`asyncio.TaskGroup`**: For structured concurrency with proper cancellation
<!-- version: python < 3.11 -->
- **`asyncio.gather` with cancellation**: Manual task management for concurrent operations
<!-- version: python >= 3.8 -->
- **Async context managers**: `@asynccontextmanager` for async resource management

### Dependencies & Structure
- **Dependency injection**: Pass dependencies explicitly, avoid global state
- **Single responsibility**: One purpose per module/class
- **Layered architecture**: Separate business logic from I/O (repositories, services, handlers)

---

## Patterns to Avoid

### Critical Anti-Patterns
- ❌ **Mutable default arguments**: `def foo(items=[])` - use `None` and assign inside
- ❌ **Bare `except:`**: Always catch specific exceptions or at minimum `except Exception:`
- ❌ **`except: pass`**: Silent exception swallowing hides bugs
- ❌ **`from module import *`**: Pollutes namespace, makes dependencies unclear
- ❌ **Global mutable state**: Makes code untestable and unpredictable

### Type & Data Issues
- ❌ **Inconsistent return types**: Function should return one type (or raise exception)
- ❌ **`type()` for type checks**: Use `isinstance()` which handles inheritance
- ❌ **Dict for structured data**: Use dataclasses, NamedTuple, or Pydantic models
- ❌ **String-based type checks**: `if type(x).__name__ == "Foo"` - fragile

### Performance Anti-Patterns
- ❌ **`dict()` over `{}`**: Literal is faster (no name lookup)
- ❌ **`+ ` for string concatenation in loops**: Use `"".join()` or f-strings
- ❌ **List comprehension passed to `all()`/`any()`**: Use generator (short-circuits)
- ❌ **Repeated attribute access**: Cache `self.foo.bar.baz` in local variable

### Async Anti-Patterns
- ❌ **Blocking calls in async**: `time.sleep()`, sync I/O - use async equivalents
- ❌ **`asyncio.run()` in async context**: Already in event loop
- ❌ **Fire-and-forget tasks**: Use `asyncio.create_task()` and store reference

### Code Smells
- ❌ **Overly nested code**: Max 3 levels - extract functions
- ❌ **Long functions**: >20 lines usually needs decomposition
- ❌ **Magic numbers/strings**: Use constants or enums
- ❌ **Print statements for debugging**: Use `logging` module

---

## Verification Checklist

### Type Safety
- [ ] Type hints on all public functions and methods
- [ ] Return types explicitly annotated
- [ ] `mypy --strict` passes (or configured equivalent)
- [ ] No `Any` types without explicit justification

### Code Quality
- [ ] Docstrings on public functions/classes (Google or NumPy style)
- [ ] No unused imports or variables
- [ ] Consistent naming (snake_case functions, PascalCase classes)
- [ ] `ruff` or `flake8` passes with no warnings

### Resource Management
- [ ] All file operations use `with` statement
- [ ] Database connections properly released
- [ ] Async resources use `async with`

### Testing
- [ ] Functions are pure where possible (deterministic, no side effects)
- [ ] Dependencies injectable for testing
- [ ] Edge cases covered (None, empty, boundary values)

---

## Code Patterns (Reference)

### Recommended Constructs
<!-- version: python >= 3.10 -->
- **Union types**: `def foo(x: str | None) -> User | None`
- **Pattern matching**: `match event: case UserCreated(id=uid): ...`
- **Dataclasses**: `@dataclass(frozen=True, slots=True)`
- **Structural pattern matching**: For complex dispatch logic

<!-- version: python >= 3.11 -->
- **TaskGroup**: `async with asyncio.TaskGroup() as tg: tg.create_task(...)`
- **ExceptionGroup**: For handling multiple concurrent exceptions

### Common Idioms
- **Dictionary access**: `d.get(key, default)` not `d[key] if key in d else default`
- **Default mutable fix**: `def foo(items=None): items = items or []`
- **Context manager protocol**: Implement `__enter__`/`__exit__` or use `contextlib`
- **Async iteration**: `async for item in async_generator()`
