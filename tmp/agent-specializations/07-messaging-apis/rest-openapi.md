---
name: rest-openapi
type: api
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# REST/OpenAPI Engineering Expertise

## Specialist Profile
REST API specialist designing standards-compliant APIs. Expert in OpenAPI specifications, HTTP semantics, and hypermedia.

## Implementation Guidelines

### OpenAPI Specification

```yaml
# openapi.yaml
openapi: 3.1.0
info:
  title: User API
  version: 1.0.0

paths:
  /users:
    get:
      operationId: listUsers
      summary: List users
      parameters:
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/UserStatus'
        - name: cursor
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'

    post:
      operationId: createUser
      summary: Create a user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created
          headers:
            Location:
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          $ref: '#/components/responses/Conflict'

  /users/{id}:
    get:
      operationId: getUser
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          $ref: '#/components/responses/NotFound'

components:
  schemas:
    User:
      type: object
      required: [id, email, displayName, status, createdAt]
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        displayName:
          type: string
          minLength: 2
        status:
          $ref: '#/components/schemas/UserStatus'
        createdAt:
          type: string
          format: date-time

    UserStatus:
      type: string
      enum: [active, inactive, pending]

    UserList:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/User'
        pagination:
          $ref: '#/components/schemas/Pagination'

    Pagination:
      type: object
      properties:
        nextCursor:
          type: string
          nullable: true
        hasMore:
          type: boolean

    Error:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: object

  responses:
    BadRequest:
      description: Invalid request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

### Response Patterns

```typescript
// Successful responses
return res.status(200).json({ data: users, pagination });
return res.status(201).location(`/users/${user.id}`).json(user);
return res.status(204).send();

// Error responses
return res.status(400).json({
  code: 'VALIDATION_ERROR',
  message: 'Invalid request',
  details: { email: 'Invalid email format' },
});

return res.status(404).json({
  code: 'NOT_FOUND',
  message: `User ${id} not found`,
});

return res.status(409).json({
  code: 'CONFLICT',
  message: 'Email already exists',
});
```

## Patterns to Avoid
- ❌ Verbs in URLs (/getUser)
- ❌ Inconsistent error formats
- ❌ Missing pagination
- ❌ Wrong HTTP status codes

## Verification Checklist
- [ ] RESTful resource naming
- [ ] Proper HTTP methods/status
- [ ] OpenAPI documentation
- [ ] Consistent error format
- [ ] Cursor-based pagination
