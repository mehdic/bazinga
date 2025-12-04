---
name: fastapi
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# FastAPI Engineering Expertise

## Specialist Profile
FastAPI specialist building high-performance APIs. Expert in async Python, Pydantic, and OpenAPI.

## Implementation Guidelines

### Route Structure

```python
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr

app = FastAPI(title="User API", version="1.0.0")

class CreateUserRequest(BaseModel):
    email: EmailStr
    display_name: str

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str

    class Config:
        from_attributes = True

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    user = User(email=request.email, display_name=request.display_name)
    db.add(user)
    await db.commit()
    return user
```

### Dependency Injection

```python
from functools import lru_cache
from typing import Annotated

@lru_cache
def get_settings():
    return Settings()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
```

### Exception Handling

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
```

### Background Tasks

```python
from fastapi import BackgroundTasks

async def send_email(email: str, subject: str, body: str):
    await email_service.send(email, subject, body)

@app.post("/users")
async def create_user(
    request: CreateUserRequest,
    background_tasks: BackgroundTasks,
):
    user = await user_service.create(request)
    background_tasks.add_task(send_email, user.email, "Welcome!", "...")
    return user
```

### Router Organization

```python
# routers/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: str): ...

# main.py
from routers import users, orders
app.include_router(users.router)
app.include_router(orders.router)
```

## Patterns to Avoid
- ❌ Sync database calls (use async)
- ❌ Business logic in routes (use services)
- ❌ No response models (always define them)
- ❌ Catching generic Exception

## Verification Checklist
- [ ] Pydantic models for request/response
- [ ] Dependency injection for DB/services
- [ ] Proper HTTP status codes
- [ ] Exception handlers defined
- [ ] OpenAPI docs accurate
