# Todo List REST API

A simple Flask-based REST API for managing todo items with in-memory storage.

## Features

- Create, read, update, and delete todo items
- Mark todos as completed
- Filter todos by status
- Input validation
- Comprehensive error handling

## Installation

```bash
pip install -r requirements.txt
```

## Running the API

```bash
python app.py
```

The API will start on `http://localhost:5000`

## Running Tests

```bash
pytest test_api.py -v
```

With coverage:
```bash
pytest test_api.py --cov=. --cov-report=term-missing
```

## API Endpoints

### 1. Create Todo

**POST** `/todos`

Create a new todo item.

**Request Body:**
```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "pending"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### 2. List Todos

**GET** `/todos`

Get all todo items. Optionally filter by status.

**Query Parameters:**
- `status` (optional): Filter by status (pending, in_progress, completed)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "status": "pending",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
]
```

### 3. Get Todo

**GET** `/todos/{id}`

Get a specific todo by ID.

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

**Error:** `404 Not Found`
```json
{
  "error": "Todo with ID 999 not found"
}
```

### 4. Update Todo

**PUT** `/todos/{id}`

Update a todo item. All fields are optional.

**Request Body:**
```json
{
  "title": "Buy groceries and cook",
  "description": "Updated description",
  "status": "in_progress"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Buy groceries and cook",
  "description": "Updated description",
  "status": "in_progress",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:30:00"
}
```

### 5. Delete Todo

**DELETE** `/todos/{id}`

Delete a todo item.

**Response:** `204 No Content`

**Error:** `404 Not Found`

### 6. Mark Complete

**PATCH** `/todos/{id}/complete`

Mark a todo as completed.

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T13:00:00"
}
```

## Data Model

### Todo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | auto | Unique identifier |
| title | string | yes | Todo title (max 200 chars) |
| description | string | no | Todo description (max 1000 chars) |
| status | string | no | Status: pending, in_progress, completed (default: pending) |
| created_at | datetime | auto | Creation timestamp |
| updated_at | datetime | auto | Last update timestamp |

## Validation Rules

- **Title**: Required, max 200 characters
- **Description**: Optional, max 1000 characters
- **Status**: Must be one of: pending, in_progress, completed

## Error Responses

All errors return a JSON response with an error field:

```json
{
  "error": "Error message",
  "details": ["Detailed error 1", "Detailed error 2"]
}
```

### HTTP Status Codes

- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Validation error or invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Architecture

```
tmp/todo-list-api/
├── app.py           # Flask application with routes
├── models.py        # Todo data model and storage
├── validators.py    # Input validation functions
├── test_api.py      # Pytest unit tests
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Technical Details

- **Framework**: Flask 2.0+
- **Storage**: In-memory (dict-based)
- **Testing**: pytest 7.0+
- **Python**: 3.10+

## Limitations

- In-memory storage means data is lost on restart
- No authentication or authorization
- No pagination for large datasets
- Single-threaded (Flask development server)

## Future Enhancements

- Persistent database storage (SQLite, PostgreSQL)
- User authentication and authorization
- Pagination and sorting
- Due dates and priorities
- Tags and categories
- Search functionality
