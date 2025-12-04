---
name: scala
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Scala Engineering Expertise

## Specialist Profile
Scala specialist blending functional and object-oriented paradigms. Expert in type safety, immutability, and effect systems (Cats Effect/ZIO).

---

## Patterns to Follow

### Functional Foundations
- **Immutability by default**: Case classes, `val`, immutable collections
- **Pure functions**: No side effects; referential transparency
- **Option over null**: Never use `null`; always `Option[T]`
- **Either for errors**: `Either[Error, Result]` for recoverable failures
- **For comprehensions**: Compose monadic operations cleanly

### Type System Usage
- **Strong types over primitives**: `case class UserId(value: String)` for type safety
- **Sealed traits for ADTs**: Exhaustive pattern matching
- **Type aliases for clarity**: `type Result[A] = Either[AppError, A]`
- **Variance annotations**: `+A` covariant, `-A` contravariant when needed

### Effect Systems
- **ZIO environment pattern**: `ZIO[R, E, A]` for dependencies, errors, results
- **Cats Effect IO**: Lazy, referentially transparent effects
- **Resource management**: `Resource` or `ZIO.acquireRelease` for cleanup
- **Error channels**: Use typed errors (`E`) not `Throwable`

### Scala 3 Features
<!-- version: scala >= 3 -->
- **Given/using over implicit**: Clearer context parameters
- **Extension methods**: `extension (s: String) def toSlug: String`
- **Opaque types**: Zero-cost type wrappers
- **Enums**: Native algebraic data types
- **Union/intersection types**: `String | Int`, `A & B`

### Code Organization
- **Small, focused modules**: Single responsibility
- **Tagless final for abstraction**: `F[_]: Monad` for polymorphic effects
- **Companion objects**: Factory methods, type class instances
- **Package objects sparingly**: Prefer explicit imports

---

## Patterns to Avoid

### Type System Abuse
- ❌ **Weakly-typed values**: `String` for IDs; use newtypes
- ❌ **Omitting return types**: Always annotate public methods
- ❌ **`Any` or `AnyRef`**: Lose type safety; use proper generics
- ❌ **Overusing implicits**: Makes code hard to follow; be explicit

### Effect System Anti-Patterns
- ❌ **`unsafeRunSync` in production**: Only at application edge
- ❌ **Wrapping pure code in IO**: No benefit; adds overhead
- ❌ **Monad transformers in public APIs**: Use ZIO environment or tagless final
- ❌ **Ignoring `traverse`**: Use `traverse` not `map` + `sequence`
- ❌ **Blocking in async context**: Use proper async primitives

### Functional Anti-Patterns
- ❌ **`null` anywhere**: Use `Option` always
- ❌ **Mutable state**: Use `Ref`, `State` monad, or actors
- ❌ **Exceptions for control flow**: Use `Either` or typed errors
- ❌ **Side effects in pure functions**: Wrap in effect type
- ❌ **Passing dependencies as functions**: Use proper DI or Reader

### Code Smells
- ❌ **God objects**: Split by domain
- ❌ **Deep inheritance**: Prefer composition and type classes
- ❌ **Non-exhaustive pattern matching**: Compiler warnings are errors
- ❌ **Ignoring compiler warnings**: Enable `-Xfatal-warnings`

---

## Verification Checklist

### Type Safety
- [ ] No `null` usage
- [ ] All public methods have return types
- [ ] Strong types for domain values (newtypes)
- [ ] Pattern matches exhaustive

### Functional Style
- [ ] Immutable data structures
- [ ] Pure functions (side effects wrapped)
- [ ] `Either`/ZIO error handling (not exceptions)
- [ ] For comprehensions for monadic composition

### Effect System
- [ ] Effects suspended properly (IO, ZIO)
- [ ] Resources cleaned up (`Resource`, `ZIO.acquireRelease`)
- [ ] No `unsafeRunSync` except at edge
- [ ] Typed error channels used

### Tooling
- [ ] Scalafix rules pass
- [ ] Scapegoat/WartRemover checks
- [ ] `-Xlint` warnings addressed
- [ ] Scalafmt formatting applied

---

## Code Patterns (Reference)

### Recommended Constructs
- **Case class**: `case class User(id: UserId, email: Email)`
- **Sealed trait**: `sealed trait UserError; case class NotFound(id: UserId) extends UserError`
- **Option handling**: `user.map(_.name).getOrElse("Unknown")`
- **Either**: `def create(req: Request): Either[ValidationError, User]`
- **For comprehension**: `for { user <- findUser(id); profile <- user.profile } yield profile`
<!-- version: scala >= 3 -->
- **Extension**: `extension (s: String) def toSlug = s.toLowerCase.replaceAll("[^a-z0-9]+", "-")`
- **Given**: `given Ordering[User] = Ordering.by(_.createdAt)`
- **Opaque type**: `opaque type UserId = String`

