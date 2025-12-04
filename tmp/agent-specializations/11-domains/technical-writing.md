---
name: technical-writing
type: domain
priority: 3
token_estimate: 350
compatible_with: [developer, senior_software_engineer, tech_lead]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Technical Writing Expertise

## Specialist Profile
Technical writing specialist creating clear documentation. Expert in API docs, architecture decisions, and user guides.

## Documentation Guidelines

### API Documentation

```yaml
# OpenAPI example with good descriptions
paths:
  /users:
    post:
      summary: Create a new user
      description: |
        Creates a new user account. The email must be unique across the system.
        A welcome email will be sent to the provided address.

        **Rate limit:** 10 requests per minute per IP.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
            examples:
              basic:
                summary: Basic user creation
                value:
                  email: "user@example.com"
                  displayName: "John Doe"
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          description: |
            Invalid request. Common causes:
            - Missing required fields
            - Invalid email format
            - Display name too short
        '409':
          description: Email already exists
```

### Architecture Decision Record

```markdown
# ADR-001: Use PostgreSQL for Primary Database

## Status
Accepted

## Context
We need to choose a primary database for our user management service.
The system will handle ~10K concurrent users with complex querying needs.

Requirements:
- ACID transactions for financial data
- Full-text search for user directory
- JSON storage for flexible user preferences
- Strong ecosystem and tooling

## Decision
We will use PostgreSQL 16 as our primary database.

## Consequences

### Positive
- Mature, battle-tested technology
- Excellent JSON support (JSONB)
- Built-in full-text search
- Strong TypeScript/Node.js ecosystem (Prisma, TypeORM)

### Negative
- Vertical scaling limitations (can be mitigated with read replicas)
- Self-managed requires DBA expertise (can use managed service)

### Risks
- Lock-in to relational model for core entities
- Migration complexity if we need to shard

## Alternatives Considered

### MongoDB
- Rejected: Weaker transaction guarantees, overkill flexibility

### MySQL
- Rejected: Inferior JSON support, less rich feature set
```

### README Structure

```markdown
# Project Name

Brief description of what this project does and why it exists.

## Quick Start

\`\`\`bash
# Clone and install
git clone https://github.com/org/project.git
cd project
npm install

# Configure
cp .env.example .env
# Edit .env with your values

# Run
npm run dev
\`\`\`

## Features

- ✅ Feature one with brief explanation
- ✅ Feature two with brief explanation
- 🚧 Upcoming feature (in progress)

## Architecture

\`\`\`
src/
├── api/          # HTTP handlers
├── services/     # Business logic
├── repositories/ # Data access
└── types/        # TypeScript types
\`\`\`

## API Reference

See [API Documentation](./docs/api.md) for detailed endpoint reference.

## Development

### Prerequisites
- Node.js 20+
- PostgreSQL 16+
- Redis 7+

### Running Tests
\`\`\`bash
npm test           # Unit tests
npm run test:e2e   # End-to-end tests
\`\`\`

### Code Style
This project uses ESLint and Prettier. Run `npm run lint` before committing.

## Deployment

See [Deployment Guide](./docs/deployment.md).

## Contributing

See [Contributing Guidelines](./CONTRIBUTING.md).

## License

MIT - see [LICENSE](./LICENSE)
```

## Patterns to Avoid
- ❌ Outdated documentation
- ❌ Missing examples
- ❌ Jargon without explanation
- ❌ Assuming reader context

## Verification Checklist
- [ ] Examples for all endpoints
- [ ] Error scenarios documented
- [ ] Prerequisites listed
- [ ] Quick start works
- [ ] ADRs for major decisions
