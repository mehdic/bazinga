# Todo List API Feature Specification

## Overview

Create a simple Python REST API for managing todo items using Flask.

## Requirements

### Functional Requirements

1. **Create Todo** - POST /todos - Create a new todo item with title and optional description
2. **List Todos** - GET /todos - List all todo items with optional filtering by status
3. **Get Todo** - GET /todos/{id} - Get a specific todo item by ID
4. **Update Todo** - PUT /todos/{id} - Update title, description, or status
5. **Delete Todo** - DELETE /todos/{id} - Delete a todo item
6. **Mark Complete** - PATCH /todos/{id}/complete - Mark a todo as completed

### Data Model

```python
Todo:
  id: int (auto-generated)
  title: str (required, max 200 chars)
  description: str (optional, max 1000 chars)
  status: str (pending, in_progress, completed)
  created_at: datetime
  updated_at: datetime
```

### Non-Functional Requirements

- Use in-memory storage (dict) for simplicity
- Return proper HTTP status codes (200, 201, 400, 404)
- JSON request/response format
- Input validation with clear error messages

## Acceptance Criteria

- [ ] All 6 endpoints work correctly
- [ ] Proper error handling for invalid IDs
- [ ] Input validation prevents invalid data
- [ ] All unit tests pass
- [ ] Code follows Python best practices

## Target Directory

`tmp/todo-list-api/`
