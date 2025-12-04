---
name: elixir
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Elixir Engineering Expertise

## Specialist Profile
Elixir specialist building fault-tolerant systems. Expert in OTP, pattern matching, and the BEAM ecosystem.

---

## Patterns to Follow

### Pattern Matching
- **Function clauses over conditionals**: Multiple function heads for dispatch
- **Destructuring in parameters**: `def process(%User{email: email})`
- **Guard clauses**: `when is_binary(name)` for type constraints
- **Pin operator**: `^expected` to match against existing value
- **Tagged tuples**: `{:ok, result}` / `{:error, reason}` convention

### Data Modeling
- **Structs with `@enforce_keys`**: Required fields validated at compile time
- **Typespecs for all public functions**: `@spec create(map()) :: {:ok, User.t()} | {:error, term()}`
- **Behaviours for contracts**: Define callback interfaces
- **Protocols for polymorphism**: Extend types without modifying them

### OTP Patterns
- **GenServer for state**: Wrap mutable state properly
- **Supervision trees**: "Let it crash" with proper recovery
- **Named processes with Registry**: Dynamic process lookup
- **Task for async work**: `Task.async/await` for concurrent operations
- **Agent for simple state**: When full GenServer isn't needed

### Control Flow
- **`with` for happy path**: Chain operations, handle errors in `else`
- **Pipe operator**: Transform data through function chain
- **`Enum` over recursion**: Built-in functions are optimized
- **Stream for lazy evaluation**: Large/infinite sequences
<!-- version: elixir >= 1.12 -->
- **`then/2` for inline**: `value |> then(fn x -> process(x, extra) end)`
<!-- version: elixir >= 1.14 -->
- **`dbg/1` for debugging**: Drop-in debug macro with location info
<!-- version: elixir >= 1.15 -->
- **Improved exceptions**: Better stacktraces and error formatting

### Phoenix (if applicable)
- **Contexts for business logic**: Bounded contexts, not fat models
- **Changesets for validation**: Single source of validation truth
<!-- version: phoenix >= 1.6 -->
- **HEEx templates**: HTML-aware template syntax
<!-- version: phoenix >= 1.7 -->
- **Verified routes**: `~p"/users/#{user.id}"` for type-safe routes
- **Core components**: Function components over view helpers
<!-- version: elixir >= 1.5 -->
- **Live View for real-time**: Server-rendered reactive UIs
- **PubSub for events**: Decouple components

---

## Patterns to Avoid

### GenServer Anti-Patterns
- ❌ **GenServer for pure computation**: Just use functions; no state needed
- ❌ **Named GenServer with `__MODULE__`**: Blocks scaling; use Registry
- ❌ **Blocking in GenServer**: Timeouts cascade; use async patterns
- ❌ **State for code organization**: Processes are for runtime properties only
- ❌ **Missing supervision**: Always supervise GenServers

### Control Flow Issues
- ❌ **Nested case statements**: Use `with` or pattern matching
- ❌ **Deep nesting**: Extract to helper functions
- ❌ **Ignoring error tuples**: Always handle `{:error, _}`
- ❌ **Catching all exceptions**: Catch specific; let others crash

### Data Anti-Patterns
- ❌ **Primitive obsession**: Use structs for domain entities
- ❌ **Missing typespecs**: Document all public APIs
- ❌ **Mutable-style thinking**: Elixir data is immutable
- ❌ **String keys in maps**: Prefer atoms for internal data

### Phoenix Anti-Patterns
- ❌ **Fat controllers**: Move logic to contexts
- ❌ **Fat schemas**: Extract to embedded schemas, services
- ❌ **Callbacks for business logic**: Explicit function calls
- ❌ **N+1 queries**: Use `Repo.preload` or joins

---

## Verification Checklist

### Code Quality
- [ ] Pattern matching for dispatch
- [ ] `with` for multi-step operations
- [ ] Typespecs on public functions
- [ ] `@moduledoc` and `@doc` present

### OTP
- [ ] GenServers supervised
- [ ] Processes only for state/concurrency
- [ ] Registry for dynamic processes
- [ ] Proper `handle_info` for messages

### Error Handling
- [ ] Tagged tuples consistently used
- [ ] `{:error, _}` cases handled
- [ ] Supervision strategy appropriate
- [ ] `with` else clause covers failures

### Testing
- [ ] Dialyzer passes (typespecs verified)
- [ ] Credo checks pass
- [ ] ExUnit tests cover edge cases
- [ ] Property-based tests for core logic

---

## Code Patterns (Reference)

### Recommended Constructs
- **Struct**: `defstruct [:id, :email]; @type t :: %__MODULE__{id: String.t(), email: String.t()}`
- **Pattern match**: `def handle({:ok, user}), do: ...; def handle({:error, reason}), do: ...`
- **With**: `with {:ok, a} <- step1(), {:ok, b} <- step2(a), do: {:ok, result}`
- **Pipe**: `data |> transform() |> filter() |> format()`
- **GenServer**: `use GenServer; def init(state), do: {:ok, state}`
- **Supervisor**: `children = [{Worker, arg}]; Supervisor.start_link(children, strategy: :one_for_one)`
- **Typespec**: `@spec find(id :: String.t()) :: {:ok, User.t()} | {:error, :not_found}`
<!-- version: elixir >= 1.12 -->
- **then/2**: `user_id |> then(fn id -> get_user(id, opts) end)`
<!-- version: elixir >= 1.14 -->
- **dbg**: `value |> transform() |> dbg() |> store()`
<!-- version: phoenix >= 1.7 -->
- **Verified route**: `~p"/users/#{@user.id}/edit"`

