---
name: aspnet-core
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [csharp]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# ASP.NET Core Engineering Expertise

## Specialist Profile
ASP.NET Core specialist building enterprise web APIs. Expert in dependency injection, middleware, and .NET ecosystem.

## Implementation Guidelines

### Minimal API

<!-- version: dotnet >= 7 -->
```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddDbContext<AppDbContext>();

var app = builder.Build();

var users = app.MapGroup("/api/users");

users.MapGet("/", async (IUserService service) =>
    Results.Ok(await service.GetAllAsync()));

users.MapGet("/{id:guid}", async (Guid id, IUserService service) =>
    await service.GetByIdAsync(id) is User user
        ? Results.Ok(user)
        : Results.NotFound());

users.MapPost("/", async (CreateUserRequest request, IUserService service) =>
{
    var user = await service.CreateAsync(request);
    return Results.Created($"/api/users/{user.Id}", user);
});

app.Run();
```

### Controllers

```csharp
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;

    public UsersController(IUserService userService)
    {
        _userService = userService;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<UserDto>>> GetAll(
        CancellationToken cancellationToken)
    {
        var users = await _userService.GetAllAsync(cancellationToken);
        return Ok(users);
    }

    [HttpGet("{id:guid}")]
    public async Task<ActionResult<UserDto>> GetById(
        Guid id,
        CancellationToken cancellationToken)
    {
        var user = await _userService.GetByIdAsync(id, cancellationToken);
        return user is null ? NotFound() : Ok(user);
    }

    [HttpPost]
    public async Task<ActionResult<UserDto>> Create(
        [FromBody] CreateUserRequest request,
        CancellationToken cancellationToken)
    {
        var user = await _userService.CreateAsync(request, cancellationToken);
        return CreatedAtAction(nameof(GetById), new { id = user.Id }, user);
    }
}
```

### Services

```csharp
public interface IUserService
{
    Task<IEnumerable<UserDto>> GetAllAsync(CancellationToken ct = default);
    Task<UserDto?> GetByIdAsync(Guid id, CancellationToken ct = default);
    Task<UserDto> CreateAsync(CreateUserRequest request, CancellationToken ct = default);
}

public class UserService : IUserService
{
    private readonly AppDbContext _context;
    private readonly IMapper _mapper;

    public UserService(AppDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<IEnumerable<UserDto>> GetAllAsync(CancellationToken ct = default)
    {
        return await _context.Users
            .AsNoTracking()
            .OrderByDescending(u => u.CreatedAt)
            .ProjectTo<UserDto>(_mapper.ConfigurationProvider)
            .ToListAsync(ct);
    }

    public async Task<UserDto> CreateAsync(CreateUserRequest request, CancellationToken ct = default)
    {
        var user = _mapper.Map<User>(request);
        _context.Users.Add(user);
        await _context.SaveChangesAsync(ct);
        return _mapper.Map<UserDto>(user);
    }
}
```

### Validation

```csharp
public class CreateUserRequestValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserRequestValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty()
            .EmailAddress();

        RuleFor(x => x.DisplayName)
            .NotEmpty()
            .MinimumLength(2)
            .MaximumLength(100);
    }
}

// Registration
builder.Services.AddValidatorsFromAssemblyContaining<Program>();
```

### Exception Handling

```csharp
public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (NotFoundException ex)
        {
            context.Response.StatusCode = 404;
            await context.Response.WriteAsJsonAsync(new { error = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unhandled exception");
            context.Response.StatusCode = 500;
            await context.Response.WriteAsJsonAsync(new { error = "Internal error" });
        }
    }
}
```

## Patterns to Avoid
- ❌ Service locator pattern
- ❌ Blocking async (.Result, .Wait())
- ❌ Missing CancellationToken
- ❌ Logic in controllers

## Verification Checklist
- [ ] Dependency injection
- [ ] FluentValidation
- [ ] CancellationToken propagated
- [ ] AutoMapper for DTOs
- [ ] Global exception handling
