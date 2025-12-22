---
name: graphql
type: api
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# GraphQL Engineering Expertise

## Specialist Profile
GraphQL specialist building flexible APIs. Expert in schema design, federation, and performance optimization.

---

## Patterns to Follow

### Schema Design
- **Relay connection spec**: Cursor pagination with edges/nodes
- **Nullable by default**: Embrace GraphQL's error model
- **Input types for mutations**: Separate from output types
- **Payload pattern**: `{ user, errors }` for mutations
- **Versionless API**: Add fields, deprecate, never remove

### Federation (2025)
<!-- version: apollo-federation >= 2.0 -->
- **Subgraphs per domain**: Users, products, orders
- **Gateway composes schema**: Single entry point
- **@key for entity resolution**: Cross-service references
- **Authenticate at gateway**: Forward identity to subgraphs
- **Authorize in subgraphs**: Each service enforces its rules
- **@shareable directive**: Cross-subgraph field sharing
- **@requires for computed**: Fetch fields from other subgraphs
<!-- version: apollo-federation >= 1.0, apollo-federation < 2.0 -->
- **Federation 1.x**: @extends instead of @shareable pattern

### Performance Patterns
- **DataLoader for N+1**: Batch and cache per request
- **Persisted queries**: Client sends hash, not query
- **Query complexity limits**: Cost per field/type
- **Depth limits**: Prevent deep nesting attacks
- **APQ (Automatic Persisted Queries)**: Reduce bandwidth

### Security
- **Trusted documents**: Allowlist of operations (first-party clients)
- **Query complexity analysis**: Reject expensive queries
- **Depth limiting**: Max nesting depth
- **Introspection control**: Disable in production for private APIs
- **Rate limiting**: Per-query cost-based

### Best Practices
- **Codegen for types**: Generate from schema
- **Resolvers return promises**: Async by default
- **Context for request scope**: User, dataloaders
- **Field-level resolvers**: Lazy loading

---

## Patterns to Avoid

### Schema Anti-Patterns
- ❌ **Verbs in field names**: `getUser` vs `user`
- ❌ **Breaking changes**: Deprecate, don't remove
- ❌ **Giant input types**: Split by concern
- ❌ **Missing pagination**: Unbounded lists

### Performance Anti-Patterns
- ❌ **N+1 queries**: Use DataLoader
- ❌ **Over-fetching in resolvers**: Select only needed fields
- ❌ **No query complexity limits**: DoS vulnerability
- ❌ **Missing caching**: Use persisted queries, response cache

### Federation Anti-Patterns
- ❌ **Overly complex @key fields**: Performance overhead
- ❌ **Ignoring resolver variability**: Different subgraph speeds
- ❌ **Missing gateway metrics**: Chokepoint visibility
- ❌ **No trace propagation**: Disconnected traces

### Security Anti-Patterns
- ❌ **Introspection always on**: Schema exposure
- ❌ **No depth limits**: Nested query attacks
- ❌ **Trusting client-sent queries**: Use persisted queries
- ❌ **Missing rate limits**: Resource exhaustion

---

## Verification Checklist

### Schema
- [ ] Relay-style pagination
- [ ] Input types for mutations
- [ ] Payload pattern for errors
- [ ] Deprecation before removal

### Performance
- [ ] DataLoader for batching
- [ ] Query complexity limits
- [ ] Depth limits configured
- [ ] Caching strategy defined

### Federation
- [ ] Subgraphs per domain
- [ ] Gateway authentication
- [ ] Subgraph authorization
- [ ] Trace context propagation

### Security
- [ ] Introspection disabled in prod
- [ ] Rate limiting configured
- [ ] Persisted queries (if applicable)
- [ ] Input validation

---

## Code Patterns (Reference)

### Schema
- **Connection**: `type UserConnection { edges: [UserEdge!]!; pageInfo: PageInfo!; totalCount: Int! }`
- **Edge**: `type UserEdge { node: User!; cursor: String! }`
- **Payload**: `type CreateUserPayload { user: User; errors: [Error!] }`
- **Input**: `input CreateUserInput { email: String!; displayName: String! }`

### DataLoader
- **Create**: `new DataLoader(async (ids) => { const users = await db.users.findMany({ where: { id: { in: ids } } }); return ids.map(id => users.find(u => u.id === id)); })`
- **Use**: `User: { organization: (parent, _, { orgLoader }) => orgLoader.load(parent.orgId) }`

### Federation
- **Entity**: `type User @key(fields: "id") { id: ID!; email: String! }`
- **Reference resolver**: `User: { __resolveReference: (ref) => users.findById(ref.id) }`

### Security
- **Complexity**: `createComplexityLimitRule(1000)` directive
- **Depth**: `depthLimit(10)` validation rule

