---
name: gin-fiber
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [go]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Gin/Fiber Engineering Expertise

## Specialist Profile
Go web framework specialist building high-performance APIs. Expert in Gin, Fiber, and idiomatic Go patterns.

---

## Patterns to Follow

### Application Structure
- **Handler structs**: Inject dependencies via constructor
- **Service layer**: Business logic separate from handlers
- **Repository pattern**: Data access abstraction
- **Config struct**: Environment-based configuration
- **Wire/manual DI**: Explicit dependency wiring

### Handler Patterns
- **Context propagation**: Pass `ctx context.Context`
- **Structured responses**: Consistent JSON format
- **Proper status codes**: 201, 204, 400, 404, 500
- **Error return convention**: Return error, let middleware handle
- **Binding with validation**: `ShouldBindJSON` + validator tags
<!-- version: gin >= 1.9 -->
- **Engine.ContextWithFallback**: Context pool reuse optimizations
- **Trusted proxies config**: Better proxy detection
<!-- version: fiber >= 2.0 -->
- **Express-compatible API**: Familiar syntax for Node.js devs
- **Zero memory allocation routing**: Fast router implementation
<!-- version: fiber >= 3.0 -->
- **Context API changes**: Breaking changes in context methods

### Middleware
- **Recovery**: Panic recovery for resilience
- **Logging**: Request/response logging
- **Auth middleware**: JWT validation
- **Rate limiting**: Protect endpoints
- **CORS**: Configure for API access

### Error Handling
- **Custom error types**: Domain-specific errors
- **Error middleware**: Central error handler
- **Error wrapping**: Add context with `fmt.Errorf("...: %w", err)`
- **Structured error responses**: Code + message format

### Graceful Shutdown
- **Signal handling**: SIGTERM, SIGINT
- **Timeout for shutdown**: Give requests time to complete
- **Close connections**: Database, cache, etc.
- **Health endpoints**: `/health`, `/ready`

---

## Patterns to Avoid

### Handler Anti-Patterns
- ❌ **Panic in handlers**: Return errors instead
- ❌ **Global state**: Inject dependencies
- ❌ **Ignoring context**: Propagate for cancellation
- ❌ **Business logic in handlers**: Use services

### Error Anti-Patterns
- ❌ **Swallowing errors**: Always handle or return
- ❌ **Generic error messages**: Provide context
- ❌ **Panic for errors**: Reserve for unrecoverable
- ❌ **No error middleware**: Handle consistently

### Concurrency Anti-Patterns
- ❌ **Goroutine leaks**: Always ensure exit path
- ❌ **Missing sync**: Protect shared state
- ❌ **Ignoring context cancellation**: Check in loops
- ❌ **Blocking without timeout**: Use context deadline

### API Anti-Patterns
- ❌ **Missing validation**: Validate all input
- ❌ **Inconsistent response format**: Standardize structure
- ❌ **No graceful shutdown**: Requests get dropped
- ❌ **Missing health checks**: Hard to monitor

---

## Verification Checklist

### Application
- [ ] Dependency injection configured
- [ ] Service layer for logic
- [ ] Configuration from environment
- [ ] Graceful shutdown implemented

### Error Handling
- [ ] Custom error types
- [ ] Error middleware
- [ ] Consistent response format
- [ ] Error logging

### Security
- [ ] Authentication middleware
- [ ] Input validation
- [ ] Rate limiting
- [ ] CORS configured

### Operational
- [ ] Health check endpoints
- [ ] Request logging
- [ ] Panic recovery
- [ ] Metrics endpoint

---

## Code Patterns (Reference)

### Gin Constructs
- **Handler**: `func (h *UserHandler) Create(c *gin.Context) { var req Request; c.ShouldBindJSON(&req); ... }`
- **Router**: `r.Group("/api").Use(AuthMiddleware()).GET("/users", h.GetAll)`
- **Middleware**: `func Auth() gin.HandlerFunc { return func(c *gin.Context) { ... c.Next() } }`
- **Recovery**: `r.Use(gin.Recovery())`

### Fiber Constructs
- **Handler**: `func (h *UserHandler) Create(c *fiber.Ctx) error { var req Request; c.BodyParser(&req); ... }`
- **Router**: `api := app.Group("/api", AuthMiddleware); api.Get("/users", h.GetAll)`
- **Error handler**: `app := fiber.New(fiber.Config{ErrorHandler: customHandler})`

### Shared Patterns
- **Graceful shutdown**: `srv.Shutdown(ctx)` with signal handling
- **Health**: `GET /health -> {"status": "ok"}`

