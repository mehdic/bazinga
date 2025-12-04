---
name: backend-api
type: domain
priority: 3
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Backend API Engineering Expertise

## Specialist Profile
Backend API specialist designing RESTful and GraphQL APIs. Expert in HTTP semantics, resource design, pagination, and API versioning.

---

## Patterns to Follow

### Resource Design
- **Nouns, not verbs**: `/users`, `/orders`, not `/getUsers`
- **Plural naming**: `/users/{id}` for consistency
- **Nested resources**: `/users/{id}/orders` for relationships
- **Flat when possible**: Deep nesting > 2 levels is hard to maintain
- **Consistent naming**: snake_case or camelCase, not mixed

### HTTP Methods & Status Codes
- **GET 200**: Success with body
- **POST 201**: Created, include Location header
- **PUT 200/204**: Full replace, idempotent
- **PATCH 200**: Partial update
- **DELETE 204**: No content on success
- **400**: Malformed request, validation failure
- **401**: Missing or invalid authentication
- **403**: Authenticated but not authorized
- **404**: Resource doesn't exist
- **409**: Conflict (duplicate, version mismatch)
- **422**: Valid syntax but semantic errors
- **429**: Rate limit exceeded, include Retry-After

### Pagination (2025)
- **Cursor-based preferred**: More efficient for large datasets
- **Offset/limit for small sets**: Simpler, `?limit=20&offset=40`
- **Include metadata**: `has_more`, `next_cursor`, `total` (if cheap)
- **Consistent structure**: Same pagination object across endpoints
- **Field selection**: Allow `?fields=id,name` to reduce payload
<!-- version: openapi >= 3.1 -->
- **JSON Schema 2020-12**: Full schema compatibility in OpenAPI
- **Webhooks definition**: Callback endpoints in spec

### Versioning
- **URI versioning**: `/api/v1/` (60% developer preference, 2025)
- **Support N+2 versions**: At least two previous versions
- **Deprecation notices**: Sunset header, docs warning
- **Major versions only**: No `/v1.2/`, use response evolution

### Error Responses
- **Structured format**: `error.code`, `error.message`, `error.details`
- **Request ID**: Include for debugging/support
- **Field-level errors**: For validation failures
- **Documentation link**: Reference error code docs
- **No stack traces**: Never expose internals to clients

### Idempotency
- **Idempotency-Key header**: For non-idempotent POST operations
- **Store results**: Return cached response on retry
- **24-hour TTL**: Reasonable key retention
- **Client-generated**: UUIDv4 recommended

### Rate Limiting
- **X-RateLimit-Limit**: Requests allowed per window
- **X-RateLimit-Remaining**: Requests remaining
- **X-RateLimit-Reset**: Unix timestamp for reset
- **Retry-After**: Seconds to wait on 429

---

## Patterns to Avoid

### Resource Anti-Patterns
- ❌ **Verbs in URLs**: `/api/getUsers`, `/api/createOrder`
- ❌ **Mixed naming**: `user_id` in one endpoint, `userId` in another
- ❌ **Deep nesting**: `/users/{id}/orders/{id}/items/{id}/reviews`
- ❌ **CRUD in URL**: `/users/delete/{id}`

### Response Anti-Patterns
- ❌ **200 for errors**: Use proper status codes
- ❌ **Stack traces in errors**: Security risk
- ❌ **Inconsistent error format**: Different structures per endpoint
- ❌ **Missing pagination**: Unbounded list responses

### Versioning Anti-Patterns
- ❌ **No versioning**: Breaking changes without warning
- ❌ **Minor versions in URI**: `/api/v1.2.3/`
- ❌ **Breaking without deprecation**: Instant removal

### Security Anti-Patterns
- ❌ **Secrets in URLs**: Logged everywhere
- ❌ **No rate limiting**: DoS vulnerability
- ❌ **Missing authentication**: Open endpoints
- ❌ **Over-fetching by default**: Return minimal data

---

## Verification Checklist

### Design
- [ ] Resource naming follows nouns/plural convention
- [ ] HTTP methods used correctly (GET idempotent, POST creates)
- [ ] Status codes are accurate (201 for creation, 404 for missing)
- [ ] Nested resources max 2 levels deep

### Pagination & Filtering
- [ ] All list endpoints paginated
- [ ] Cursor or offset pagination implemented
- [ ] Field selection available (`?fields=`)
- [ ] Sorting/filtering parameters documented

### Versioning & Evolution
- [ ] API version in URI
- [ ] Deprecation policy documented
- [ ] Changelog maintained
- [ ] Breaking changes announced

### Error Handling
- [ ] Structured error responses
- [ ] Request ID in all responses
- [ ] No internal details exposed
- [ ] Documentation links provided

### Security & Headers
- [ ] Rate limiting headers present
- [ ] Idempotency-Key for POST mutations
- [ ] CORS configured appropriately
- [ ] Content-Type validation

---

## Code Patterns (Reference)

### Resource Endpoints
- **List**: `GET /api/v1/users?limit=20&cursor=abc`
- **Create**: `POST /api/v1/users` → 201 + Location header
- **Read**: `GET /api/v1/users/{id}` → 200
- **Update**: `PATCH /api/v1/users/{id}` → 200
- **Delete**: `DELETE /api/v1/users/{id}` → 204

### Error Response
- **Format**: `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...], "request_id": "req_abc" } }`

### Pagination Response
- **Cursor**: `{ "data": [...], "pagination": { "next_cursor": "eyJ...", "has_more": true } }`
- **Offset**: `{ "data": [...], "meta": { "page": 2, "per_page": 20, "total": 150 } }`

### Headers
- **Request**: `Authorization: Bearer ...`, `X-Request-ID`, `X-Idempotency-Key`
- **Response**: `X-RateLimit-*`, `ETag`, `Cache-Control`

