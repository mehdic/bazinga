---
name: security-auditing
type: security
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer, tech_lead]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Security Auditing Expertise

## Specialist Profile
Security specialist auditing application security. Expert in OWASP vulnerabilities, secure coding, and threat modeling.

## Implementation Guidelines

### Input Validation

```typescript
// middleware/validation.ts
import { z } from 'zod';
import DOMPurify from 'isomorphic-dompurify';

// Schema with strict validation
const createUserSchema = z.object({
  email: z.string().email().max(255),
  displayName: z.string().min(2).max(100).regex(/^[\w\s-]+$/),
  password: z.string()
    .min(12)
    .regex(/[A-Z]/, 'Must contain uppercase')
    .regex(/[a-z]/, 'Must contain lowercase')
    .regex(/[0-9]/, 'Must contain number')
    .regex(/[^A-Za-z0-9]/, 'Must contain special character'),
});

// Sanitization for user content
export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p'],
    ALLOWED_ATTR: ['href'],
  });
}

// SQL parameterization (never concatenate)
const user = await db.query(
  'SELECT * FROM users WHERE email = $1 AND status = $2',
  [email, status]
);
```

### Authentication

```typescript
// auth/password.ts
import argon2 from 'argon2';

export async function hashPassword(password: string): Promise<string> {
  return argon2.hash(password, {
    type: argon2.argon2id,
    memoryCost: 65536,
    timeCost: 3,
    parallelism: 4,
  });
}

export async function verifyPassword(hash: string, password: string): Promise<boolean> {
  return argon2.verify(hash, password);
}

// Rate limiting
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: 'Too many login attempts',
  keyGenerator: (req) => req.ip + req.body.email,
});

// Constant-time comparison
import { timingSafeEqual } from 'crypto';
function safeCompare(a: string, b: string): boolean {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  return bufA.length === bufB.length && timingSafeEqual(bufA, bufB);
}
```

### Authorization

```typescript
// auth/rbac.ts
type Permission = 'users:read' | 'users:write' | 'orders:read' | 'admin:*';

const rolePermissions: Record<string, Permission[]> = {
  user: ['users:read'],
  admin: ['users:read', 'users:write', 'orders:read'],
  superadmin: ['admin:*'],
};

export function hasPermission(user: User, permission: Permission): boolean {
  const permissions = rolePermissions[user.role] ?? [];
  return permissions.includes(permission) ||
         permissions.includes('admin:*');
}

// Middleware
export function requirePermission(permission: Permission) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!hasPermission(req.user, permission)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}

// Resource-level authorization
export async function canAccessOrder(user: User, orderId: string): Promise<boolean> {
  const order = await db.orders.findById(orderId);
  return order?.userId === user.id || user.role === 'admin';
}
```

### Security Headers

```typescript
// middleware/security.ts
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'", process.env.API_URL],
      frameSrc: ["'none'"],
      objectSrc: ["'none'"],
    },
  },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
}));

// CORS
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
}));
```

## Patterns to Avoid
- ❌ String concatenation in SQL
- ❌ MD5/SHA1 for passwords
- ❌ Storing secrets in code
- ❌ Missing rate limiting

## Verification Checklist
- [ ] Input validation (Zod/Joi)
- [ ] Parameterized queries
- [ ] Argon2id for passwords
- [ ] RBAC with least privilege
- [ ] Security headers (Helmet)
