---
name: go
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Go Engineering Expertise

## Specialist Profile
Go specialist building efficient, concurrent systems. Expert in idiomatic Go, error handling, and concurrency patterns.

---

## Patterns to Follow

### Core Philosophy
- **Composition over inheritance**: Embed types, don't create hierarchies
- **Accept interfaces, return structs**: Flexible inputs, concrete outputs
- **Small interfaces**: 1-2 methods; io.Reader/Writer are ideals
- **Make the zero value useful**: Design types so default value is valid
- **Clear is better than clever**: Explicit, readable code over tricks

### Generics
<!-- version: go >= 1.18 -->
- **Type parameters**: `func Map[T, U any](items []T, f func(T) U) []U`
- **Constraints**: Use `comparable`, `any`, or custom interfaces
- **Type inference**: Let compiler infer types when obvious
<!-- version: go < 1.18 -->
- **No generics**: Use `interface{}` with type assertions, or code generation

### Error Handling
- **Return errors**: Don't panic for expected failures
- **Wrap errors**: `fmt.Errorf("operation failed: %w", err)` for context
- **Check errors immediately**: Handle after every call that returns error
- **Errors are values**: Can be inspected, compared, contain state
- **Sentinel errors**: `var ErrNotFound = errors.New("not found")` for known conditions
- **errors.Is/As**: For error inspection, not type assertions

### Context Usage
- **First parameter**: `func DoThing(ctx context.Context, ...)` convention
- **Propagate context**: Pass through all function calls
- **Timeout/cancellation**: Use for request-scoped operations
- **Never store in struct**: Pass explicitly in method calls
- **Background for startup**: `context.Background()` only at top-level

### Concurrency
- **Goroutines are cheap**: Use liberally for concurrent I/O
- **Channels for communication**: Share memory by communicating
- **sync.WaitGroup**: For waiting on goroutine completion
- **errgroup**: For concurrent tasks with error propagation
- **Mutex for state**: When shared state is simpler than channels
- **Close channels from sender**: Receiver should not close
<!-- version: go >= 1.21 -->
- **Structured logging**: Use `log/slog` for structured, leveled logs
- **Slices package**: Use `slices.Sort()`, `slices.Contains()` instead of sort.Slice
- **Maps package**: Use `maps.Clone()`, `maps.Keys()` for map operations
<!-- version: go >= 1.22 -->
- **Range over integers**: `for i := range 10 { }` instead of `for i := 0; i < 10; i++`
- **Enhanced ServeMux**: Pattern matching with `{param}` and methods in patterns

### Package Design
- **Internal packages**: For private implementation details
- **One package, one purpose**: High cohesion, low coupling
- **Avoid init()**: Prefer explicit initialization
- **Document exported symbols**: Every public name needs a comment

### Testing
- **Table-driven tests**: `[]struct{ name, input, expected }` pattern
- **t.Parallel()**: For independent tests
- **testdata/ directory**: For test fixtures
- **Example functions**: `func ExampleFoo()` for documentation

---

## Patterns to Avoid

### Error Handling Anti-Patterns
- ❌ **Ignoring errors**: `result, _ := DoThing()` - always handle
- ❌ **Panic for expected errors**: Use error returns; panic is for bugs
- ❌ **Error strings capital/punctuation**: Errors are composed; keep lowercase
- ❌ **Wrapping without context**: Just `return err` loses information

### Concurrency Anti-Patterns
- ❌ **Goroutine leaks**: Always ensure goroutines can exit
- ❌ **Closing channel from receiver**: Sender closes; receiver ranges
- ❌ **Shared state without sync**: Race conditions
- ❌ **Unbuffered channel as queue**: Use buffered or proper queue

### Design Anti-Patterns
- ❌ **Interface pollution**: Don't define interfaces before you have 2+ implementations
- ❌ **Return interfaces**: Return concrete types; accept interfaces
- ❌ **Large interfaces**: Prefer many small interfaces
- ❌ **Getter/setter methods**: Access fields directly if appropriate

### Code Style Issues
- ❌ **Stutter in names**: `user.UserName` → `user.Name`
- ❌ **Unnecessary else**: Use early return instead
- ❌ **Package-level state**: Makes testing hard; use dependency injection
- ❌ **init() for complex setup**: Prefer explicit initialization

### Slice/Map Issues
- ❌ **Nil slice check before len**: `len(nil) == 0`, check is redundant
- ❌ **Range copy for large items**: Use index or pointer: `for i := range items`
- ❌ **Append to slice parameter**: Can modify caller's backing array

### Performance Traps
- ❌ **String concatenation in loops**: Use strings.Builder
- ❌ **Growing slice without capacity**: Preallocate with `make([]T, 0, cap)`
- ❌ **defer in hot loop**: Has overhead; extract to function if needed
- ❌ **Unnecessary allocations**: Reuse buffers, use sync.Pool

---

## Verification Checklist

### Error Handling
- [ ] All errors checked immediately after call
- [ ] Errors wrapped with context: `fmt.Errorf("doing X: %w", err)`
- [ ] Sentinel errors exported and documented
- [ ] No panic except for programmer errors

### Concurrency
- [ ] All goroutines can exit (context cancellation, channel close)
- [ ] Shared state protected by mutex or channel
- [ ] Context propagated through function calls
- [ ] errgroup for concurrent operations with errors

### Code Quality
- [ ] `go vet` passes
- [ ] `golangci-lint` passes (staticcheck, ineffassign, etc.)
- [ ] No exported names without documentation
- [ ] Consistent naming (MixedCaps, not underscores)

### Testing
- [ ] Table-driven tests for multiple cases
- [ ] Race detector passes: `go test -race`
- [ ] Coverage adequate for critical paths

---

## Code Patterns (Reference)

### Recommended Idioms
- **Error wrap**: `return fmt.Errorf("fetching user %s: %w", id, err)`
- **Functional options**: `NewServer(WithPort(8080), WithTimeout(30*time.Second))`
- **Table tests**: `tests := []struct{ name, input, want string }{...}`
- **Context first**: `func (s *Service) GetUser(ctx context.Context, id string) (*User, error)`
- **Interface declaration**: `type Reader interface { Read(p []byte) (n int, err error) }`
- **Constructor**: `func NewService(repo Repository) *Service { return &Service{repo: repo} }`
- **Zero value**: Design so `var s MyStruct` is usable without explicit init
<!-- version: go >= 1.18 -->
- **Generic function**: `func Map[T, U any](s []T, f func(T) U) []U { ... }`
- **Generic constraint**: `type Ordered interface { ~int | ~float64 | ~string }`
<!-- version: go >= 1.21 -->
- **Structured log**: `slog.Info("user created", "id", user.ID, "email", user.Email)`
- **Slices helper**: `slices.Sort(items)` instead of `sort.Slice(items, func(i, j int) bool { ... })`
<!-- version: go >= 1.22 -->
- **Range integer**: `for i := range n { use(i) }` for counting loops
- **HTTP routing**: `mux.HandleFunc("GET /users/{id}", handler)` with method and path params
