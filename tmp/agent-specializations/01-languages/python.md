---
name: python
type: language
priority: 1
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Python Engineering Expertise

## Specialist Profile
Python specialist building clean, maintainable code. Expert in type hints, async patterns, and Pythonic idioms.

## Implementation Guidelines

### Type Hints

<!-- version: python >= 3.10 -->
```python
def get_user(user_id: str) -> User | None:
    return db.users.get(user_id)

def process_users(users: list[User]) -> dict[str, User]:
    return {u.id: u for u in users}
```

<!-- version: python < 3.10 -->
```python
from typing import Optional, Dict, List

def get_user(user_id: str) -> Optional[User]:
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

<!-- version: python < 3.10 -->
```python
@dataclass(frozen=True)
class User:
    id: str
    email: str
    display_name: str
```

### Pattern Matching

<!-- version: python >= 3.10 -->
```python
def handle_event(event: Event) -> str:
    match event:
        case UserCreated(user_id=uid):
            return f"User {uid} created"
        case UserDeleted(user_id=uid):
            return f"User {uid} deleted"
        case _:
            return "Unknown event"
```

### Async Patterns

```python
import asyncio

async def fetch_users(user_ids: list[str]) -> list[User]:
    tasks = [fetch_user(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, User)]
```

### Context Managers

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def database_transaction():
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
```

## Patterns to Avoid
- ❌ Mutable default arguments (`def foo(items=[])`)
- ❌ Bare `except:` (catch specific exceptions)
- ❌ Using `type()` for type checks (use `isinstance()`)
- ❌ Global mutable state
- ❌ `from module import *`

## Verification Checklist
- [ ] Type hints on all public functions
- [ ] Docstrings on public functions/classes
- [ ] Dataclasses for data containers
- [ ] Context managers for resources
- [ ] Proper async/await (no blocking in async)
