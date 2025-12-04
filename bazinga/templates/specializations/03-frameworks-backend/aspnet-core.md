---
name: aspnet-core
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [csharp]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# ASP.NET Core Engineering Expertise

## Specialist Profile
ASP.NET Core specialist building enterprise web APIs. Expert in dependency injection, middleware, and .NET ecosystem.

---

## Patterns to Follow

### Dependency Injection
- **Constructor injection**: Default pattern
- **Interface abstractions**: `IUserService` for testability
- **Scoped for request lifetime**: Database contexts
- **Singleton for stateless**: Services without state
- **Options pattern**: `IOptions<TConfig>` for configuration

### Controllers vs Minimal APIs
- **Minimal API for simple**: Less ceremony
- **Controllers for complex**: Filters, model binding features
- **Thin controllers**: Delegate to services
- **ActionResult<T>**: Type-safe responses

### Validation
- **FluentValidation**: Complex validation rules
- **Data annotations**: Simple validation
- **Model binding**: Automatic request deserialization
- **Problem Details**: RFC 7807 error format

### Async Best Practices
- **CancellationToken everywhere**: Pass through call chain
- **`async Task` returns**: Not `async void`
- **ConfigureAwait(false)**: In libraries only
- **No .Result or .Wait()**: Use await

### EF Core
- **AsNoTracking for reads**: Performance optimization
- **Explicit includes**: Eager loading
- **AutoMapper ProjectTo**: Query-time projection
- **Migrations**: Database version control

---

## Patterns to Avoid

### DI Anti-Patterns
- ❌ **Service locator**: Inject dependencies
- ❌ **Static services**: Hard to test
- ❌ **Captive dependencies**: Scoped in singleton
- ❌ **Circular dependencies**: Restructure

### Async Anti-Patterns
- ❌ **`.Result` or `.Wait()`**: Causes deadlocks
- ❌ **`async void`**: Exceptions can't be caught
- ❌ **Missing CancellationToken**: Lost cancellation
- ❌ **Fire-and-forget without care**: Exceptions lost

### Controller Anti-Patterns
- ❌ **Business logic in controllers**: Use services
- ❌ **No validation**: Always validate input
- ❌ **Missing authorization**: `[Authorize]` attribute
- ❌ **Returning entities**: Use DTOs

### EF Core Anti-Patterns
- ❌ **N+1 queries**: Use Include or ProjectTo
- ❌ **Tracking when unnecessary**: Use AsNoTracking
- ❌ **DbContext as singleton**: Use scoped
- ❌ **No pagination**: Use Skip/Take

---

## Verification Checklist

### Architecture
- [ ] Dependency injection throughout
- [ ] Services for business logic
- [ ] DTOs for API boundaries
- [ ] Global exception handling

### Async
- [ ] CancellationToken propagated
- [ ] No blocking async (.Result/.Wait())
- [ ] Proper async Task returns
- [ ] Async throughout stack

### Validation
- [ ] FluentValidation configured
- [ ] Model validation on all endpoints
- [ ] Problem Details for errors
- [ ] Custom validators where needed

### Testing
- [ ] Unit tests with mocked services
- [ ] Integration tests with WebApplicationFactory
- [ ] xUnit or NUnit setup
- [ ] Test database strategy

---

## Code Patterns (Reference)

### Minimal API
<!-- version: dotnet >= 7 -->
- **Route**: `app.MapGet("/users/{id}", async (Guid id, IUserService svc, CancellationToken ct) => ...)`
- **Group**: `var users = app.MapGroup("/api/users").RequireAuthorization()`

### Controllers
- **Controller**: `[ApiController] [Route("api/[controller]")] class UsersController : ControllerBase {}`
- **Action**: `[HttpGet("{id}")] async Task<ActionResult<UserDto>> Get(Guid id, CancellationToken ct)`
- **Injection**: `public UsersController(IUserService userService) { _userService = userService; }`

### Services
- **Interface**: `interface IUserService { Task<UserDto?> GetByIdAsync(Guid id, CancellationToken ct); }`
- **Implementation**: `class UserService : IUserService { private readonly AppDbContext _ctx; ... }`
- **Registration**: `builder.Services.AddScoped<IUserService, UserService>()`

### Validation
- **Validator**: `class CreateUserValidator : AbstractValidator<CreateUserRequest> { ... }`
- **Registration**: `builder.Services.AddValidatorsFromAssemblyContaining<Program>()`

