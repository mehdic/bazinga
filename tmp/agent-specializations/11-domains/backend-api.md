---
name: backend-api
type: domain
priority: 3
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow, routing, and reporting rules take precedence over this guidance.

# Backend API Engineering Expertise

## Specialist Profile

Backend API specialist designing RESTful and GraphQL APIs. Expert in HTTP semantics, authentication patterns, and API versioning.

## Implementation Guidelines

### RESTful Resource Design

```
# Resource naming (nouns, not verbs)
GET    /api/v1/users           # List users
POST   /api/v1/users           # Create user
GET    /api/v1/users/{id}      # Get user
PUT    /api/v1/users/{id}      # Replace user
PATCH  /api/v1/users/{id}      # Update user
DELETE /api/v1/users/{id}      # Delete user

# Nested resources
GET    /api/v1/users/{id}/orders    # User's orders
POST   /api/v1/users/{id}/orders    # Create order for user

# Filtering, sorting, pagination
GET /api/v1/users?status=active&sort=-created_at&page=2&limit=20
```

### HTTP Status Codes

```
# Success
200 OK           - GET, PUT, PATCH success with body
201 Created      - POST success, include Location header
204 No Content   - DELETE success, PUT/PATCH without body

# Client Errors
400 Bad Request  - Malformed request, validation failure
401 Unauthorized - Missing or invalid authentication
403 Forbidden    - Authenticated but not authorized
404 Not Found    - Resource doesn't exist
409 Conflict     - State conflict (duplicate, version mismatch)
422 Unprocessable - Valid syntax but semantic errors

# Server Errors
500 Internal     - Unexpected server error
503 Unavailable  - Temporary overload or maintenance
```

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Must be a valid email address"
      }
    ],
    "request_id": "req_abc123",
    "documentation_url": "https://api.example.com/docs/errors#VALIDATION_ERROR"
  }
}
```

### Pagination

```json
// Cursor-based (preferred for large datasets)
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIzfQ==",
    "has_more": true
  }
}

// Offset-based (simpler but less efficient)
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### Authentication Patterns

```
# Bearer token (JWT)
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# API key (for service-to-service)
X-API-Key: sk_live_abc123

# Token response
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "dGhpcyBpcyBh..."
}
```

### Rate Limiting Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

### API Versioning

```
# URL path versioning (most common)
GET /api/v1/users
GET /api/v2/users

# Header versioning
Accept: application/vnd.example.v2+json

# Query parameter (least preferred)
GET /api/users?version=2
```

### Request/Response Headers

```
# Request
Content-Type: application/json
Accept: application/json
Authorization: Bearer ...
X-Request-ID: req_abc123
X-Idempotency-Key: idem_xyz789

# Response
Content-Type: application/json; charset=utf-8
X-Request-ID: req_abc123
Cache-Control: private, max-age=0
ETag: "abc123"
```

### Idempotency

```
# Client sends idempotency key
POST /api/v1/payments
X-Idempotency-Key: payment_attempt_12345

# Server stores result, returns cached response on retry
# Safe methods (GET, HEAD, OPTIONS) are inherently idempotent
# PUT, DELETE should be idempotent by design
# POST needs explicit idempotency key for safety
```

## Patterns to Avoid

- Verbs in URLs (`/api/getUsers`)
- Inconsistent naming (mixing snake_case and camelCase)
- Missing pagination on list endpoints
- Exposing internal IDs or stack traces
- 200 OK for errors (use proper status codes)
- Missing Content-Type headers
- Breaking changes without versioning

## Verification Checklist

- [ ] Consistent resource naming (nouns, plural)
- [ ] Proper HTTP methods and status codes
- [ ] Structured error responses with codes
- [ ] Pagination on all list endpoints
- [ ] Rate limiting headers
- [ ] Request/response validation
- [ ] API versioning strategy documented
