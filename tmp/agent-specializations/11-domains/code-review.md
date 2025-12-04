---
name: code-review
type: domain
priority: 3
token_estimate: 350
compatible_with: [tech_lead, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Code Review Expertise

## Specialist Profile
Code review specialist ensuring quality and maintainability. Expert in identifying issues, suggesting improvements, and maintaining standards.

## Review Guidelines

### Security Review Checklist

```markdown
## Security Review Points

### Input Handling
- [ ] All user input validated and sanitized
- [ ] SQL queries use parameterized statements
- [ ] No string concatenation for queries
- [ ] HTML output properly escaped (XSS prevention)

### Authentication & Authorization
- [ ] Passwords hashed with modern algorithm (Argon2, bcrypt)
- [ ] Session tokens are cryptographically random
- [ ] Authorization checks at every endpoint
- [ ] Sensitive actions require re-authentication

### Data Protection
- [ ] No secrets in code or logs
- [ ] PII encrypted at rest
- [ ] Audit logging for sensitive operations
- [ ] Proper error messages (no stack traces to users)

### Dependencies
- [ ] No known vulnerabilities in dependencies
- [ ] Dependencies pinned to specific versions
- [ ] Minimal dependency surface
```

### Performance Review

```markdown
## Performance Review Points

### Database
- [ ] N+1 queries eliminated
- [ ] Proper indexes for query patterns
- [ ] Pagination for list endpoints
- [ ] Connection pooling configured

### Caching
- [ ] Cache invalidation strategy defined
- [ ] TTLs appropriate for data freshness
- [ ] Cache keys are consistent and namespaced

### API Design
- [ ] Response payloads minimal (no over-fetching)
- [ ] Async operations for long-running tasks
- [ ] Rate limiting configured
- [ ] Compression enabled
```

### Code Quality Feedback

```typescript
// Example: Constructive feedback patterns

// ❌ Vague feedback
// "This code is bad"

// ✅ Specific, actionable feedback
// "Consider extracting this into a separate function for better testability.
//  The current implementation mixes validation and business logic, making
//  it harder to unit test. Something like:
//
//  function validateOrder(order: Order): ValidationResult { ... }
//  function processValidOrder(order: Order): ProcessResult { ... }"

// ❌ Demanding
// "Change this to use reduce"

// ✅ Suggestive with reasoning
// "This could be simplified using reduce(), which would also make the
//  intent clearer. However, if the team prefers the explicit loop for
//  readability, that's also fine. WDYT?"

// ❌ Blocking on style
// "BLOCKER: Use single quotes instead of double quotes"

// ✅ Non-blocking style suggestions
// "nit: We typically use single quotes in this codebase, but not blocking."
```

### Review Response Templates

```markdown
## Approval Template
✅ **LGTM**

Nice work on this feature! A few observations:
- Great test coverage, especially edge cases
- Clean separation of concerns
- Consider adding a comment explaining [X] for future readers

## Changes Requested Template
🔄 **Changes Requested**

Good progress! A few items to address before merging:

**Must fix:**
1. [Security] Input validation missing on line X
2. [Bug] Race condition in concurrent access

**Suggestions (non-blocking):**
- Consider extracting helper function for readability
- Minor: typo in comment on line Y

Let me know if you have questions!
```

## Patterns to Avoid
- ❌ Nitpicking style over substance
- ❌ Blocking without explanation
- ❌ Rewriting author's code
- ❌ Delayed reviews (>24h)

## Verification Checklist
- [ ] Security issues identified
- [ ] Performance implications considered
- [ ] Tests adequate for changes
- [ ] Documentation updated
- [ ] Constructive tone maintained
