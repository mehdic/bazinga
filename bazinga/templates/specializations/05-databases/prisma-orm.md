---
name: prisma-orm
type: database
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Prisma ORM Engineering Expertise

## Specialist Profile
Prisma specialist building type-safe database access. Expert in schema design, query optimization, and Prisma ecosystem.

---

## Patterns to Follow

### Schema Design
- **Explicit @map for naming**: `@map("snake_case")` for DB columns
- **@@map for table names**: Keep Prisma model names PascalCase
- **Compound indexes**: `@@index([field1, field2])` for common queries
- **onDelete/onUpdate**: Explicit referential actions
- **Enums for status fields**: Type-safe, self-documenting

### Query Optimization
- **Select specific fields**: Reduce data transfer
- **Include for related data**: Avoid N+1
- **Batch with createMany/updateMany**: More efficient
- **Cursor pagination**: For large datasets
- **Raw queries for complex**: `$queryRaw` when needed

### Query Compiler (2025)
<!-- version: prisma >= 6 -->
- **Rust-free mode**: TypeScript-only, faster large queries
- **Reduced CPU footprint**: No engine binary
- **Faster complex queries**: Especially joins/aggregations
- **Same API**: No code changes needed

### Prisma Ecosystem
- **Prisma Accelerate**: Connection pooling, caching
- **Prisma Pulse**: Real-time database events
- **Prisma Optimize**: Query analysis and recommendations
- **OpenTelemetry integration**: Tracing and metrics

### Migration Best Practices
- **prisma migrate for production**: Version-controlled migrations
- **prisma db push for prototyping**: Fast iteration
- **Never edit deployed migrations**: Create follow-up migrations
- **Seed scripts**: Consistent test data

---

## Patterns to Avoid

### Query Anti-Patterns
- ❌ **N+1 queries**: Use include/select
- ❌ **Fetching entire relations**: Use take/skip on relations
- ❌ **Raw queries for simple ops**: Use type-safe client
- ❌ **Missing select on large models**: Fetch only needed fields
- ❌ **Not using transactions**: For related operations

### Client Anti-Patterns
- ❌ **Multiple PrismaClient instances**: Connection pool exhaustion
- ❌ **No singleton pattern**: Create once, reuse
- ❌ **Missing error handling**: Catch PrismaClientKnownRequestError
- ❌ **Ignoring connection limits**: Especially in serverless

### Schema Anti-Patterns
- ❌ **Missing indexes on filtered fields**: Slow queries
- ❌ **No referential actions**: Orphaned data
- ❌ **Implicit many-to-many without control**: Use explicit join table
- ❌ **No @map/@@@map**: Inconsistent naming

### Migration Anti-Patterns
- ❌ **db push in production**: Use migrate
- ❌ **Editing deployed migrations**: Schema drift
- ❌ **Missing rollback strategy**: Plan for failures
- ❌ **Large migrations without testing**: Stage first

---

## Verification Checklist

### Schema
- [ ] Indexes on query fields
- [ ] Explicit referential actions
- [ ] @map/@@map for naming
- [ ] Enums for status fields

### Queries
- [ ] include for related data
- [ ] select for partial fields
- [ ] Transactions for multi-ops
- [ ] Cursor pagination for lists

### Client
- [ ] Singleton PrismaClient
- [ ] Error handling for Prisma errors
- [ ] Connection limits appropriate
- [ ] Middleware for logging/metrics

### Migrations
- [ ] prisma migrate in CI/CD
- [ ] Seed scripts maintained
- [ ] Migration history in git
- [ ] Tested in staging first

---

## Code Patterns (Reference)

### Schema
- **Model**: `model User { id String @id @default(uuid()) email String @unique @@map("users") }`
- **Relation**: `posts Post[] // 1:many` or `profile Profile? // 1:1`
- **Index**: `@@index([status, createdAt(sort: Desc)])`
- **Enum**: `enum Status { ACTIVE INACTIVE PENDING }`

### Queries
- **Select fields**: `prisma.user.findMany({ select: { id: true, email: true } })`
- **Include relation**: `prisma.user.findUnique({ where: { id }, include: { posts: { take: 10 } } })`
- **Cursor pagination**: `prisma.user.findMany({ take: 20, skip: 1, cursor: { id: lastId } })`
- **Batch create**: `prisma.user.createMany({ data: users, skipDuplicates: true })`

### Transactions
- **Interactive**: `prisma.$transaction(async (tx) => { await tx.user.create(...); await tx.profile.create(...); })`
- **Batch**: `prisma.$transaction([prisma.user.create(...), prisma.profile.create(...)])`

### Raw Query
- **SQL**: `prisma.$queryRaw<Stats[]>\`SELECT status, COUNT(*)::int FROM users GROUP BY status\``
- **Execute**: `prisma.$executeRaw\`UPDATE users SET status = 'inactive' WHERE ...\``

