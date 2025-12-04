---
name: fastapi
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# FastAPI Engineering Expertise

## Specialist Profile
FastAPI specialist building high-performance APIs. Expert in async Python, Pydantic, and dependency injection.

---

## Patterns to Follow

### Dependency Injection
- **Use Annotated**: `Annotated[Service, Depends(get_service)]`
- **Caching**: Dependencies cached within request by default
- **Nested dependencies**: Compose for complex requirements
- **Override for testing**: `app.dependency_overrides[dep] = mock`
- **DB sessions as dependencies**: Proper lifecycle management

### Pydantic Models
- **Request/Response separation**: Different models for input/output
<!-- version: pydantic >= 2 -->
- **`model_config = {'from_attributes': True}`**: For ORM model conversion
- **`@field_validator`**: For field-level validation
- **`model_validator(mode='after')`**: For cross-field validation
<!-- version: pydantic < 2 -->
- **`class Config: orm_mode = True`**: For ORM model conversion
- **`@validator`**: For field-level validation
- **`@root_validator`**: For cross-field validation
<!-- version: pydantic >= 1.8 -->
- **Field validation**: Use `Field()` with constraints

### Async Best Practices
- **Async all the way**: Don't mix sync I/O in async routes
- **Proper DB drivers**: Use async drivers (asyncpg, aiomysql)
- **Background tasks**: For fire-and-forget operations
- **Streaming responses**: For large data transfers
- **Lifespan context**: For startup/shutdown logic

### Project Structure
- **Router organization**: `/routers/{domain}.py`
- **Service layer**: Business logic separate from routes
- **Repository pattern**: Data access abstraction
- **Schema module**: Pydantic models organized
- **Thin routes**: Orchestration only, not business logic

### Error Handling
- **Custom exception classes**: Domain-specific errors
- **Exception handlers**: Consistent error responses
- **HTTPException for HTTP errors**: Standard HTTP semantics
- **Validation error formatting**: User-friendly messages

---

## Patterns to Avoid

### Async Anti-Patterns
- ❌ **Sync I/O in async routes**: Blocks event loop
- ❌ **Sync DB drivers**: Use async (asyncpg, not psycopg2)
- ❌ **Sync dependencies in async routes**: Makes them sync
- ❌ **CPU-bound in event loop**: Offload to thread pool

### DI Anti-Patterns
- ❌ **Global state**: Use dependencies instead
- ❌ **Hardcoded dependencies**: Inject for testability
- ❌ **Creating sessions in routes**: Use dependency injection
- ❌ **Missing cleanup**: Ensure resources are released

### Route Anti-Patterns
- ❌ **Business logic in routes**: Use services
- ❌ **No response model**: Always define return types
- ❌ **Catching generic Exception**: Catch specific exceptions
- ❌ **No request validation**: Pydantic handles it; use it

### Performance Anti-Patterns
- ❌ **Unbounded queries**: Always paginate
- ❌ **N+1 in async loops**: Use batch fetching
- ❌ **No connection pooling**: Configure pool size
- ❌ **Sync file I/O**: Use aiofiles

---

## Verification Checklist

### Type Safety
- [ ] Pydantic models for all request/response
- [ ] `Annotated` for dependencies
- [ ] Return types on all endpoints
- [ ] Strict mode in Pydantic

### Async
- [ ] Async DB driver used
- [ ] No sync I/O in async routes
- [ ] Background tasks for slow ops
- [ ] Proper lifespan handling

### Architecture
- [ ] Router organization by domain
- [ ] Service layer for logic
- [ ] Dependency injection throughout
- [ ] Custom exception handlers

### Testing
- [ ] AsyncClient for async tests
- [ ] dependency_overrides for mocking
- [ ] TestClient for sync tests
- [ ] pytest-asyncio configured

---

## Code Patterns (Reference)

### Recommended Constructs
- **Route**: `@router.post("/users", response_model=UserResponse, status_code=201)`
- **Dependency**: `async def get_db(): async with session() as s: yield s`
- **Annotated DI**: `db: Annotated[AsyncSession, Depends(get_db)]`
- **Pydantic**: `class UserCreate(BaseModel): email: EmailStr; name: str = Field(min_length=2)`
- **Exception handler**: `@app.exception_handler(AppError) async def handle(req, exc): ...`
- **Background task**: `background_tasks.add_task(send_email, user.email)`
- **Lifespan**: `@asynccontextmanager async def lifespan(app): yield`

