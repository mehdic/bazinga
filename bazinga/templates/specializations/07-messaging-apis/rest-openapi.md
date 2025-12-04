---
name: rest-openapi
type: api
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# REST/OpenAPI Engineering Expertise

## Specialist Profile
REST API specialist designing standards-compliant APIs. Expert in OpenAPI, HTTP semantics, and API-first development.

---

## Patterns to Follow

### Resource Design
- **Nouns for resources**: `/users`, `/orders`, not `/getUsers`
- **Hierarchical paths**: `/users/{id}/orders`
- **Plural resource names**: Consistency
- **Kebab-case for multi-word**: `/order-items`
- **Version in path or header**: `/v1/users` or `Accept-Version: v1`

### HTTP Methods & Status
- **GET**: Read (200, 404)
- **POST**: Create (201 with Location header)
- **PUT**: Replace (200, 201)
- **PATCH**: Partial update (200, 204)
- **DELETE**: Remove (204, 404)
- **Proper status codes**: 400 for client error, 500 for server

### Pagination
- **Cursor-based preferred**: Scalable, consistent
- **Link headers or body**: `nextCursor`, `hasMore`
- **Limit with max**: `limit=20`, max 100
- **Total count optional**: Can be expensive

### Error Response Format
- **Consistent structure**: `{ code, message, details }`
- **Machine-readable code**: `VALIDATION_ERROR`
- **Human-readable message**: For debugging
- **Field-level details**: Validation errors per field

### OpenAPI Best Practices
- **Design-first**: Schema before implementation
- **Reusable components**: $ref for schemas, responses
- **Examples for all**: Request/response examples
- **operationId for codegen**: Unique, descriptive
<!-- version: openapi >= 3.1 -->
- **JSON Schema 2020-12**: Full JSON Schema compatibility
- **Webhooks support**: Define callback endpoints
- **pathItems in components**: Reusable path definitions
<!-- version: openapi >= 3.0, openapi < 3.1 -->
- **OpenAPI 3.0**: Use subset of JSON Schema
- **Callbacks**: For async/webhook patterns

### Security
- **HTTPS always**: No exceptions
- **Auth via Authorization header**: Bearer, API key
- **Rate limiting headers**: `X-RateLimit-*`
- **CORS properly configured**: Explicit origins

---

## Patterns to Avoid

### URL Anti-Patterns
- ❌ **Verbs in URLs**: `/getUser`, `/deleteOrder`
- ❌ **Query params for resources**: `?action=delete`
- ❌ **Inconsistent naming**: `/users` and `/order`
- ❌ **Deep nesting**: `/a/{id}/b/{id}/c/{id}/d`

### HTTP Anti-Patterns
- ❌ **GET with body**: Not guaranteed to work
- ❌ **POST for everything**: Use appropriate methods
- ❌ **200 for errors**: Use proper status codes
- ❌ **DELETE with body**: Not standard

### Response Anti-Patterns
- ❌ **Inconsistent error format**: Different shapes
- ❌ **Leaking stack traces**: Security risk
- ❌ **Missing pagination**: Unbounded lists
- ❌ **Wrong Content-Type**: application/json

### Design Anti-Patterns
- ❌ **Breaking changes without versioning**: Break clients
- ❌ **No documentation**: OpenAPI required
- ❌ **Ignoring HTTP caching**: ETag, Cache-Control
- ❌ **Not using HATEOAS when beneficial**: Missing discoverability

---

## Verification Checklist

### Design
- [ ] RESTful resource naming
- [ ] Proper HTTP methods
- [ ] Consistent status codes
- [ ] API versioning strategy

### Documentation
- [ ] OpenAPI 3.1 spec
- [ ] Request/response examples
- [ ] Error responses documented
- [ ] Authentication documented

### Pagination
- [ ] Cursor-based for large sets
- [ ] Limit with maximum
- [ ] Next page indicator
- [ ] Consistent structure

### Security
- [ ] HTTPS only
- [ ] Auth header pattern
- [ ] Rate limiting
- [ ] CORS configured

---

## Code Patterns (Reference)

### OpenAPI Paths
- **List**: `GET /users → 200: UserList`
- **Create**: `POST /users → 201: User (Location header)`
- **Get**: `GET /users/{id} → 200: User, 404: Error`
- **Update**: `PATCH /users/{id} → 200: User`
- **Delete**: `DELETE /users/{id} → 204`

### OpenAPI Schema
- **Object**: `type: object; required: [id, email]; properties: { id: { type: string, format: uuid } }`
- **Enum**: `type: string; enum: [active, inactive, pending]`
- **Ref**: `$ref: '#/components/schemas/User'`

### Response Patterns
- **Success list**: `{ data: [...], pagination: { nextCursor, hasMore } }`
- **Success create**: `res.status(201).location(\`/users/\${user.id}\`).json(user)`
- **Error**: `{ code: 'VALIDATION_ERROR', message: 'Invalid input', details: { email: 'Invalid format' } }`

### Headers
- **Pagination**: `Link: <...?cursor=abc>; rel="next"`
- **Rate limit**: `X-RateLimit-Limit: 100; X-RateLimit-Remaining: 95`
- **Cache**: `Cache-Control: private, max-age=3600; ETag: "abc123"`

