---
name: laravel
type: framework
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [php]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Laravel Engineering Expertise

## Specialist Profile
Laravel specialist building PHP web applications. Expert in Eloquent, service container, and Laravel ecosystem.

---

## Patterns to Follow

### Eloquent Models
- **Casts for types**: `protected $casts = ['status' => UserStatus::class]`
- **Scopes for queries**: `scopeActive(Builder $query)`
- **Accessors/Mutators**: `Attribute::make(get: fn() => ...)`
- **Relationships**: Define all associations
- **Fillable/Guarded**: Mass assignment protection

### Request/Response
- **Form Requests**: Validation in dedicated classes
- **API Resources**: Transform models for JSON
- **Resource collections**: Paginated responses
- **Explicit status codes**: 201 for create, 204 for delete

### Service Layer
- **Services for business logic**: Not in controllers
- **Repository pattern optional**: Eloquent is enough for most
- **Constructor injection**: Let container resolve
- **Actions for single operations**: Invokable classes
- **DB::transaction**: Wrap related operations

### Queues & Jobs
- **Background processing**: `dispatch(new ProcessOrder($order))`
- **Job middleware**: Rate limiting, uniqueness
- **Retries and backoff**: Configure per job
- **Horizon for Redis queues**: Monitoring dashboard

### Laravel 11+
<!-- version: laravel >= 11 -->
- **Slimmer skeleton**: Less boilerplate
- **Per-second rate limiting**: More granular
- **Model casts method**: Dynamic casts
- **Health check endpoint**: Built-in

---

## Patterns to Avoid

### Controller Anti-Patterns
- ❌ **Fat controllers**: Use services/actions
- ❌ **Validation in controller**: Use Form Requests
- ❌ **Direct model exposure**: Use API Resources
- ❌ **Raw queries without bindings**: SQL injection

### Eloquent Anti-Patterns
- ❌ **N+1 queries**: Use `with()` eager loading
- ❌ **`.all()` without pagination**: Memory issues
- ❌ **Mass update without care**: Skips events
- ❌ **Guarded empty array**: Security risk

### Architecture Anti-Patterns
- ❌ **Logic in Blade views**: Move to controllers/services
- ❌ **Circular dependencies**: Restructure
- ❌ **Global functions for business logic**: Use classes
- ❌ **Events for critical flows**: Hard to debug

### Testing Anti-Patterns
- ❌ **Testing implementation**: Test behavior
- ❌ **No factory usage**: Use model factories
- ❌ **Shared database state**: RefreshDatabase trait
- ❌ **Mocking too much**: Integration tests valuable

---

## Verification Checklist

### Architecture
- [ ] Form Requests for validation
- [ ] API Resources for responses
- [ ] Services for business logic
- [ ] Jobs for async work

### Eloquent
- [ ] Eager loading configured
- [ ] Scopes for common queries
- [ ] Casts for type safety
- [ ] Indexes on query fields

### Security
- [ ] Mass assignment protected
- [ ] Authorization policies
- [ ] Rate limiting configured
- [ ] CSRF for web routes

### Testing
- [ ] Feature tests for HTTP
- [ ] Unit tests for services
- [ ] Factories for models
- [ ] RefreshDatabase trait

---

## Code Patterns (Reference)

### Recommended Constructs
- **Form Request**: `class StoreUserRequest extends FormRequest { public function rules(): array {...} }`
- **API Resource**: `class UserResource extends JsonResource { public function toArray($request): array {...} }`
- **Service**: `class UserService { public function create(array $data): User { return DB::transaction(fn() => ...); } }`
- **Scope**: `public function scopeActive(Builder $query): Builder { return $query->where('status', 'active'); }`
- **Eager load**: `User::with(['profile', 'orders'])->paginate()`
- **Job**: `class ProcessOrder implements ShouldQueue { public function handle(): void {...} }`

