---
name: security-auditing
type: security
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer, tech_lead]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Security Auditing Expertise

## Specialist Profile
Security specialist auditing application security. Expert in OWASP vulnerabilities, secure coding, and threat modeling.

---

## Patterns to Follow

### Input Validation
- **Sanitize for context**: HTML, SQL, shell differently
- **Parameterized queries always**: Never concatenate
- **Content-Type validation**: Reject unexpected types
- **Size limits**: Prevent DoS via large inputs
<!-- version: zod >= 3.0 -->
- **Schema validation (Zod)**: Type-safe, inferred TypeScript types
- **Transform and refine**: Data transformation in schema
<!-- version: zod >= 3.22 -->
- **z.pipe()**: Composable validation pipelines
<!-- version: joi >= 17.0 -->
- **Schema validation (Joi)**: Powerful object validation
- **Extended types**: Custom validation extensions

### Password Security
- **Memory-hard hashing**: 64MB+, 3+ iterations
- **Password strength rules**: Min 12 chars, complexity
- **Breach database check**: HaveIBeenPwned API
- **Rate limiting login attempts**: Prevent brute force
<!-- version: argon2 >= 1.3 -->
- **Argon2id**: Current best algorithm (OWASP recommended)
- **Parameters**: m=65536, t=3, p=4 (minimum)
<!-- version: node >= 20 -->
- **Native crypto.scrypt**: Built-in for Node.js apps
<!-- version: bcrypt < argon2 -->
- **bcrypt fallback**: Cost factor 12+ if Argon2 unavailable

### Authorization
- **RBAC or ABAC**: Role or attribute-based
- **Principle of least privilege**: Minimal access
- **Resource-level checks**: Not just role checks
- **Deny by default**: Explicit grants only
- **Audit logging**: Who did what, when

### Security Headers
- **Content-Security-Policy**: Script sources
- **Strict-Transport-Security**: HTTPS only
- **X-Content-Type-Options**: nosniff
- **X-Frame-Options**: Clickjacking prevention
- **Referrer-Policy**: Control leakage

### Secrets Management
- **Environment variables**: Not in code
- **Secret managers**: Vault, AWS Secrets Manager
- **Rotation capability**: Regular key changes
- **Access audit**: Who accessed what
- **No secrets in logs**: Redact sensitive data

---

## Patterns to Avoid

### Injection Anti-Patterns
- ❌ **String concatenation for SQL**: Use params
- ❌ **User input in shell commands**: Command injection
- ❌ **Unsanitized HTML output**: XSS
- ❌ **eval() on user input**: Code injection

### Authentication Anti-Patterns
- ❌ **MD5/SHA1 for passwords**: Use Argon2id
- ❌ **Password in URL params**: Logged everywhere
- ❌ **No rate limiting**: Brute force attacks
- ❌ **Timing attacks**: Non-constant comparison

### Authorization Anti-Patterns
- ❌ **Client-side only checks**: Easily bypassed
- ❌ **Role check without resource check**: IDOR
- ❌ **Trusting client IDs**: Verify ownership
- ❌ **No audit trail**: Can't detect breaches

### Data Anti-Patterns
- ❌ **Secrets in code/logs**: Exposure risk
- ❌ **Sensitive data unencrypted**: At rest or transit
- ❌ **PII in error messages**: Information leakage
- ❌ **No data retention policy**: Excessive storage

---

## Verification Checklist

### Input
- [ ] Schema validation on all endpoints
- [ ] Parameterized queries
- [ ] Output encoding for context
- [ ] Size limits configured

### Authentication
- [ ] Argon2id password hashing
- [ ] Rate limiting on auth
- [ ] Constant-time comparisons
- [ ] Breach password check

### Authorization
- [ ] RBAC/ABAC implemented
- [ ] Resource-level checks
- [ ] Deny by default
- [ ] Audit logging enabled

### Infrastructure
- [ ] Security headers configured
- [ ] Secrets in secret manager
- [ ] TLS 1.3 only
- [ ] Dependency scanning

---

## Code Patterns (Reference)

### Input Validation (Zod)
- **Schema**: `z.object({ email: z.string().email().max(255), name: z.string().min(2).max(100) })`
- **Parse**: `const data = schema.parse(req.body)` (throws on invalid)
- **Sanitize HTML**: `DOMPurify.sanitize(dirty, { ALLOWED_TAGS: ['b', 'i', 'a'] })`

### Password (Argon2)
- **Hash**: `argon2.hash(password, { type: argon2.argon2id, memoryCost: 65536, timeCost: 3 })`
- **Verify**: `argon2.verify(hash, password)`
- **Constant-time**: `crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b))`

### Authorization
- **RBAC**: `const permissions = rolePermissions[user.role]; if (!permissions.includes(required)) throw new ForbiddenError()`
- **Resource check**: `if (order.userId !== user.id && user.role !== 'admin') throw new ForbiddenError()`

### Headers (Helmet)
- **Setup**: `app.use(helmet({ contentSecurityPolicy: { directives: { defaultSrc: ["'self'"] } }, hsts: { maxAge: 31536000 } }))`

### SQL (Parameterized)
- **Query**: `db.query('SELECT * FROM users WHERE email = $1', [email])`

