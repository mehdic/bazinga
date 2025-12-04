---
name: rust
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Rust Engineering Expertise

## Specialist Profile
Rust engineer building safe, performant systems. Expert in ownership, lifetimes, and zero-cost abstractions.

---

## Patterns to Follow

### Ownership & Borrowing
- **Borrow when possible**: `&T` for read, `&mut T` for write - avoid unnecessary clones
- **Take ownership when needed**: When the function must store or transform the value
- **Cow for flexibility**: `Cow<'_, str>` when you might or might not need to allocate
- **Clone explicitly**: Never clone implicitly; make the cost visible

### Error Handling
- **Result for recoverable errors**: Use `Result<T, E>` for operations that can fail
- **`?` operator**: Propagate errors cleanly up the call stack
- **thiserror for library errors**: Derive `Error` trait with meaningful messages
- **anyhow for applications**: When error details matter less than propagation
- **Custom error types**: Group related errors in domain-specific enums
- **Error context**: Add context with `.context()` or `map_err()`

### Type System
- **Newtype pattern**: Wrap primitives for type safety (`struct UserId(String)`)
- **Enums over booleans**: Express state machines with enums
- **Traits for abstraction**: Define behavior contracts, not inheritance
- **Generics with bounds**: `<T: Trait>` for compile-time polymorphism
- **Associated types**: When there's one natural type per implementation
<!-- version: rust >= 1.51 -->
- **Const generics**: `struct Array<T, const N: usize>([T; N])` for compile-time sizes
<!-- version: rust >= 1.75 -->
- **Async traits**: `async fn` in traits with `#[trait_variant::make(Send)]` or RPITIT
<!-- version: rust >= 1.65 -->
- **GATs (Generic Associated Types)**: `type Item<'a>` in trait definitions

### Memory Management
- **Stack by default**: Use stack allocation when size is known
- **Box for heap**: When you need heap allocation or trait objects
- **Arc for shared ownership**: Thread-safe reference counting
- **Rc for single-thread sharing**: When Arc's overhead isn't needed

### Concurrency
- **Send + Sync**: Understand what makes types thread-safe
- **Channels for communication**: `mpsc`, `crossbeam` for message passing
- **RwLock over Mutex**: When reads are more common than writes
- **Tokio for async**: Standard async runtime for I/O-bound work
<!-- version: rust >= 1.63 -->
- **Scoped threads**: `std::thread::scope` for borrowing data in spawned threads
<!-- version: rust >= 1.70 -->
- **OnceCell/OnceLock**: `std::sync::OnceLock` for lazy static initialization

### API Design
- **Accept generic iterators**: `impl IntoIterator<Item = T>`
- **Return concrete types**: Don't return `impl Trait` in public APIs without reason
- **Builder pattern**: For complex construction with many optional fields
- **`impl Into<T>`**: Accept flexible input types

---

## Patterns to Avoid

### Memory & Safety
- ❌ **`unwrap()` in production**: Use `?`, `expect()`, or handle explicitly
- ❌ **`unsafe` without comment**: Every unsafe block needs justification
- ❌ **Global mutable state**: Use dependency injection instead
- ❌ **Excessive `clone()`**: Usually indicates ownership design issue
- ❌ **`Box<dyn Error>`**: Use concrete error types for better handling

### Ownership Issues
- ❌ **Fighting the borrow checker**: Restructure code, don't work around
- ❌ **Unnecessary `'static`**: Use proper lifetime annotations
- ❌ **`Rc<RefCell<T>>` everywhere**: Often indicates design problem
- ❌ **Ignoring lifetimes**: Explicit when needed for clarity

### Error Handling
- ❌ **Panicking for recoverable errors**: Use Result instead
- ❌ **`unwrap_or_default()` hiding errors**: Handle errors explicitly
- ❌ **Stringly-typed errors**: Use typed error enums
- ❌ **Ignoring `#[must_use]`**: Handle or explicitly ignore Results

### Async Issues
- ❌ **`block_on` in async code**: Propagate async instead
- ❌ **Spawning without handle**: Track spawned tasks
- ❌ **`tokio::spawn` without error handling**: Errors are silently dropped
- ❌ **Holding locks across `.await`**: Causes deadlocks

### Clippy Warnings
- ❌ **Ignoring clippy**: It catches real bugs; fix warnings
- ❌ **`#[allow(clippy::*)]` without reason**: Document why lint is wrong
- ❌ **`clippy::pedantic` violations**: Address for production code

---

## Verification Checklist

### Safety
- [ ] No `unwrap()` outside tests
- [ ] All `unsafe` blocks have safety comments
- [ ] `clippy` passes with no warnings
- [ ] `cargo fmt` applied

### Error Handling
- [ ] Error types defined with `thiserror` or `anyhow`
- [ ] Errors have context for debugging
- [ ] `?` used for propagation (not manual matching)
- [ ] `#[must_use]` Results handled

### Memory
- [ ] Ownership clear (owned vs borrowed)
- [ ] No unnecessary clones
- [ ] Lifetimes explicit where helpful
- [ ] Smart pointers used appropriately

### Concurrency
- [ ] Thread safety proven (Send + Sync)
- [ ] No locks held across await points
- [ ] Spawned tasks tracked and joined
- [ ] Channels/mutexes prefer over shared mutable state

---

## Code Patterns (Reference)

### Recommended Constructs
- **Error enum**: `#[derive(thiserror::Error)] pub enum MyError { ... }`
- **Newtype**: `pub struct UserId(pub String);`
- **Builder**: `ConfigBuilder::default().port(8080).build()`
- **Result alias**: `pub type Result<T> = std::result::Result<T, MyError>;`
- **Option combinators**: `opt.map(f).unwrap_or_default()`
- **Iterator chains**: `items.iter().filter(p).map(f).collect()`
- **Error context**: `operation().context("failed to do X")?`
<!-- version: rust >= 1.51 -->
- **Const generic**: `fn zeros<const N: usize>() -> [i32; N] { [0; N] }`
<!-- version: rust >= 1.63 -->
- **Scoped thread**: `thread::scope(|s| { s.spawn(|| use_borrowed_data(&data)); })`
<!-- version: rust >= 1.65 -->
- **Let-else**: `let Some(x) = opt else { return None; };`
<!-- version: rust >= 1.70 -->
- **OnceLock**: `static CONFIG: OnceLock<Config> = OnceLock::new();`
