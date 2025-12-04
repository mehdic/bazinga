---
name: typescript
type: language
priority: 1
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow, routing, and reporting rules take precedence over this guidance.

# TypeScript Engineering Expertise

## Specialist Profile

TypeScript specialist building type-safe applications. Expert in advanced type system features, generics, and compile-time guarantees.

## Implementation Guidelines

### Type Definitions

```typescript
// Prefer interfaces for object shapes
interface User {
  id: string;
  email: string;
  displayName: string;
  createdAt: Date;
}

// Use type aliases for unions, intersections, and utilities
type UserRole = 'admin' | 'user' | 'guest';
type PartialUser = Partial<User>;
type UserWithRole = User & { role: UserRole };
```

### Discriminated Unions

```typescript
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

function processResult<T>(result: Result<T>): T | null {
  if (result.success) {
    return result.data;
  }
  console.error(result.error);
  return null;
}
```

### Generic Functions

```typescript
async function fetchData<T>(url: string): Promise<Result<T>> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return { success: false, error: new Error(`HTTP ${response.status}`) };
    }
    const data: T = await response.json();
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error as Error };
  }
}

// Usage with type inference
const result = await fetchData<User[]>('/api/users');
```

### Utility Types

```typescript
// Pick specific fields
type UserPreview = Pick<User, 'id' | 'displayName'>;

// Omit fields
type CreateUserDto = Omit<User, 'id' | 'createdAt'>;

// Make fields required
type RequiredUser = Required<User>;

// Readonly
type ImmutableUser = Readonly<User>;

// Record for maps
type UserCache = Record<string, User>;
```

### Type Guards

```typescript
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value
  );
}

function processValue(value: unknown) {
  if (isUser(value)) {
    // TypeScript knows value is User here
    console.log(value.email);
  }
}
```

### Branded Types

```typescript
type UserId = string & { readonly __brand: 'UserId' };
type OrderId = string & { readonly __brand: 'OrderId' };

function createUserId(id: string): UserId {
  return id as UserId;
}

function getUser(id: UserId): User {
  // Can't accidentally pass OrderId
}
```

### Null Safety

```typescript
// Use optional chaining
const userName = user?.profile?.displayName ?? 'Unknown';

// Nullish coalescing
const port = config.port ?? 3000;

// Assert non-null only when certain
function processUser(user: User | null) {
  if (!user) {
    throw new Error('User required');
  }
  // user is narrowed to User
  return user.email;
}
```

### Async Patterns

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      await new Promise(r => setTimeout(r, 2 ** attempt * 100));
    }
  }

  throw lastError!;
}
```

## Patterns to Avoid

- Using `any` (use `unknown` and type guards instead)
- Non-null assertion `!` without certainty
- Type assertions `as` without validation
- Implicit any in function parameters
- `Object` or `{}` as types (use `Record` or specific interfaces)
- Enums for simple constants (use string literal unions)

## Verification Checklist

- [ ] Strict mode enabled in tsconfig.json
- [ ] No `any` types (or explicit comments if necessary)
- [ ] Proper null/undefined handling
- [ ] Generic functions where reuse is needed
- [ ] Type guards for runtime validation
- [ ] Discriminated unions for complex states
