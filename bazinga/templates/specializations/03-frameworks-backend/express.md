---
name: express
type: framework
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Express.js Engineering Expertise

## Specialist Profile
Express specialist building Node.js APIs. Expert in middleware patterns, error handling, and TypeScript integration.

---

## Patterns to Follow

### Application Structure
- **Layered architecture**: Routes → Controllers → Services → Repositories
- **Middleware pipeline**: Ordered execution for cross-cutting concerns
- **Router organization**: Feature-based routing
- **Config management**: Environment-based configuration
- **Dependency injection**: Manual or via container

### Error Handling
- **Central error handler**: Single middleware at end of chain
- **Async wrapper**: Catch promise rejections automatically
- **Custom error classes**: Domain-specific with status codes
- **Error logging**: Log before responding
- **Never expose internals**: Sanitize error messages

### Middleware Patterns
- **Validation middleware**: Zod/Joi schemas
- **Authentication middleware**: JWT/session validation
- **Rate limiting**: Protect against abuse
- **Request logging**: Morgan or custom
- **CORS/Helmet**: Security headers

### TypeScript Best Practices
- **Typed request handlers**: Generic Request types
- **Typed responses**: Response<ResponseBody>
- **Strict mode**: Enable all strict checks
- **DTO interfaces**: For request/response shapes

### Async Patterns
- **async/await over callbacks**: Modern syntax
- **Async wrapper utility**: No try/catch in every route
- **Promise rejection handling**: Global handler
- **Graceful shutdown**: Handle SIGTERM/SIGINT
<!-- version: express >= 5.0 -->
- **Native async support**: Routes can be async without wrapper
- **Promise-based middleware**: Errors automatically caught
- **app.router deprecated**: Use new routing patterns
<!-- version: express < 5.0 -->
- **Async wrapper required**: Wrap async routes manually
- **express-async-errors**: Alternative for global async handling

---

## Patterns to Avoid

### Error Handling Anti-Patterns
- ❌ **Try/catch in every route**: Use async wrapper
- ❌ **Swallowing errors**: Always log and respond
- ❌ **Leaking stack traces**: Hide in production
- ❌ **No global handler**: Unhandled rejections crash

### Architecture Anti-Patterns
- ❌ **Business logic in routes**: Use services
- ❌ **God router**: Split by feature
- ❌ **Callback-based async**: Use async/await
- ❌ **Hardcoded config**: Use environment variables

### Middleware Anti-Patterns
- ❌ **Order-dependent bugs**: Document middleware order
- ❌ **Missing next() calls**: Hang requests
- ❌ **Sync blocking operations**: Use async
- ❌ **No request validation**: Validate all inputs

### Security Anti-Patterns
- ❌ **No Helmet**: Missing security headers
- ❌ **No rate limiting**: DoS vulnerability
- ❌ **SQL/NoSQL injection**: Use parameterized queries
- ❌ **Missing CORS config**: Overly permissive default

---

## Verification Checklist

### Error Handling
- [ ] Central error handler middleware
- [ ] Async wrapper for routes
- [ ] Custom error classes
- [ ] Proper status codes

### Security
- [ ] Helmet middleware
- [ ] CORS configured
- [ ] Rate limiting enabled
- [ ] Input validation

### Architecture
- [ ] Layered structure (controller/service)
- [ ] Router organization by feature
- [ ] TypeScript strict mode
- [ ] Environment configuration

### Testing
- [ ] Supertest for HTTP tests
- [ ] Jest/Vitest setup
- [ ] Mocked services
- [ ] Integration test coverage

---

## Code Patterns (Reference)

### Recommended Constructs
- **Async wrapper**: `const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next)`
- **Error class**: `class AppError extends Error { constructor(statusCode, code, message) {...} }`
- **Error handler**: `app.use((err, req, res, next) => { res.status(err.statusCode || 500).json({error: ...}) })`
- **Validation**: `const validate = (schema) => (req, res, next) => { schema.parse(req.body); next(); }`
- **Router**: `router.post('/', validate(schema), asyncHandler(controller.create))`
- **Graceful shutdown**: `process.on('SIGTERM', () => server.close(() => process.exit(0)))`

