---
name: typescript
type: language
priority: 1
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

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

// Type aliases for unions and utilities
type UserRole = 'admin' | 'user' | 'guest';
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
```

### Utility Types

```typescript
type UserPreview = Pick<User, 'id' | 'displayName'>;
type CreateUserDto = Omit<User, 'id' | 'createdAt'>;
type PartialUser = Partial<User>;
type ReadonlyUser = Readonly<User>;
```

### Null Safety

```typescript
const userName = user?.profile?.displayName ?? 'Unknown';
const port = config.port ?? 3000;
```

## Patterns to Avoid
- ❌ Using `any` (use `unknown` + type guards)
- ❌ Non-null assertion `!` without certainty
- ❌ Type assertions `as` without validation
- ❌ Implicit any in parameters
- ❌ Enums for constants (use string literal unions)

## Verification Checklist
- [ ] Strict mode enabled in tsconfig.json
- [ ] No `any` types
- [ ] Proper null/undefined handling
- [ ] Generic functions where reuse needed
- [ ] Type guards for runtime validation
