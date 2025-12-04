---
name: python
type: language
priority: 1
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow, routing, and reporting rules take precedence over this guidance.

# Python Engineering Expertise

## Specialist Profile

Python specialist building clean, maintainable code. Expert in type hints, async patterns, and Pythonic idioms.

## Implementation Guidelines

### Type Hints

<!-- version: python >= 3.10 -->
```python
from typing import TypeAlias

UserId: TypeAlias = str
UserDict: TypeAlias = dict[str, str | int | None]

def get_user(user_id: UserId) -> User | None:
    """Fetch user by ID."""
    return db.users.get(user_id)

def process_users(users: list[User]) -> dict[str, User]:
    return {u.id: u for u in users}
```

<!-- version: python >= 3.9, python < 3.10 -->
```python
from typing import Optional, Dict, List

def get_user(user_id: str) -> Optional[User]:
    """Fetch user by ID."""
    return db.users.get(user_id)

def process_users(users: List[User]) -> Dict[str, User]:
    return {u.id: u for u in users}
```

<!-- version: python < 3.9 -->
```python
from typing import Optional, Dict, List

def get_user(user_id: str) -> Optional[User]:
    """Fetch user by ID."""
    return db.users.get(user_id)

def process_users(users: List[User]) -> Dict[str, User]:
    return {u.id: u for u in users}
```

### Dataclasses

<!-- version: python >= 3.10 -->
```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True, slots=True)
class User:
    id: str
    email: str
    display_name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
```

<!-- version: python >= 3.7, python < 3.10 -->
```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class User:
    id: str
    email: str
    display_name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### Pattern Matching

<!-- version: python >= 3.10 -->
```python
def handle_event(event: Event) -> str:
    match event:
        case UserCreated(user_id=uid):
            return f"User {uid} created"
        case UserDeleted(user_id=uid, reason=r):
            return f"User {uid} deleted: {r}"
        case _:
            return "Unknown event"
```

<!-- version: python < 3.10 -->
```python
def handle_event(event: Event) -> str:
    if isinstance(event, UserCreated):
        return f"User {event.user_id} created"
    elif isinstance(event, UserDeleted):
        return f"User {event.user_id} deleted: {event.reason}"
    else:
        return "Unknown event"
```

### Async Patterns

```python
import asyncio
from typing import AsyncIterator

async def fetch_users(user_ids: list[str]) -> list[User]:
    """Fetch multiple users concurrently."""
    tasks = [fetch_user(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, User)]

async def stream_events() -> AsyncIterator[Event]:
    """Stream events from queue."""
    async with event_queue.subscribe() as subscription:
        async for event in subscription:
            yield event
```

### Context Managers

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator

@asynccontextmanager
async def database_transaction() -> AsyncIterator[Connection]:
    conn = await pool.acquire()
    try:
        await conn.execute("BEGIN")
        yield conn
        await conn.execute("COMMIT")
    except Exception:
        await conn.execute("ROLLBACK")
        raise
    finally:
        await pool.release(conn)

# Usage
async with database_transaction() as conn:
    await conn.execute("INSERT INTO users ...")
```

### Error Handling

```python
from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

@dataclass
class Result(Generic[T, E]):
    value: T | None = None
    error: E | None = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @classmethod
    def ok(cls, value: T) -> 'Result[T, E]':
        return cls(value=value)

    @classmethod
    def err(cls, error: E) -> 'Result[T, E]':
        return cls(error=error)
```

## Patterns to Avoid

- Mutable default arguments (use `None` and set in body)
- Bare `except:` (catch specific exceptions)
- Using `type()` for type checking (use `isinstance()`)
- Global mutable state
- Overly broad imports (`from module import *`)
- Ignoring type hints

## Verification Checklist

- [ ] Type hints on all public functions
- [ ] Docstrings on public functions and classes
- [ ] Dataclasses for data containers
- [ ] Context managers for resource management
- [ ] Proper async/await usage (no blocking in async)
- [ ] Exception handling with specific types
