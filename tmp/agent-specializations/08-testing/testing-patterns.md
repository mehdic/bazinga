---
name: testing-patterns
type: testing
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer, qa_expert]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Testing Patterns Engineering Expertise

## Specialist Profile
Testing specialist implementing comprehensive test strategies. Expert in unit, integration, and E2E testing patterns.

## Implementation Guidelines

### Unit Tests

```typescript
// services/__tests__/userService.test.ts
import { UserService } from '../userService';
import { createMockRepository, createMockNotifier } from '../../test/mocks';

describe('UserService', () => {
  let service: UserService;
  let mockRepo: ReturnType<typeof createMockRepository>;
  let mockNotifier: ReturnType<typeof createMockNotifier>;

  beforeEach(() => {
    mockRepo = createMockRepository();
    mockNotifier = createMockNotifier();
    service = new UserService(mockRepo, mockNotifier);
  });

  describe('create', () => {
    it('should create user and send welcome notification', async () => {
      const input = { email: 'test@example.com', displayName: 'Test' };
      mockRepo.create.mockResolvedValue({ id: '1', ...input, status: 'pending' });

      const result = await service.create(input);

      expect(result).toMatchObject({ id: '1', email: input.email });
      expect(mockRepo.create).toHaveBeenCalledWith(input);
      expect(mockNotifier.sendWelcome).toHaveBeenCalledWith(
        expect.objectContaining({ email: input.email })
      );
    });

    it('should throw on duplicate email', async () => {
      mockRepo.create.mockRejectedValue(new DuplicateError('email'));

      await expect(service.create({ email: 'exists@test.com', displayName: 'Test' }))
        .rejects.toThrow(DuplicateError);
    });
  });
});
```

### Integration Tests

```typescript
// __tests__/integration/users.test.ts
import { createTestApp, createTestDatabase } from '../setup';
import request from 'supertest';

describe('Users API', () => {
  let app: Express;
  let db: TestDatabase;

  beforeAll(async () => {
    db = await createTestDatabase();
    app = createTestApp(db);
  });

  afterAll(async () => {
    await db.cleanup();
  });

  beforeEach(async () => {
    await db.truncate(['users']);
  });

  describe('POST /users', () => {
    it('should create user and return 201', async () => {
      const response = await request(app)
        .post('/users')
        .send({ email: 'new@test.com', displayName: 'New User' })
        .expect(201);

      expect(response.body).toMatchObject({
        email: 'new@test.com',
        displayName: 'New User',
        status: 'pending',
      });
      expect(response.headers.location).toMatch(/\/users\/[\w-]+/);

      // Verify in database
      const dbUser = await db.users.findByEmail('new@test.com');
      expect(dbUser).toBeTruthy();
    });

    it('should return 409 on duplicate email', async () => {
      await db.users.create({ email: 'exists@test.com', displayName: 'Existing' });

      await request(app)
        .post('/users')
        .send({ email: 'exists@test.com', displayName: 'Duplicate' })
        .expect(409);
    });
  });
});
```

### Test Factories

```typescript
// test/factories/userFactory.ts
import { faker } from '@faker-js/faker';
import { User, CreateUserInput } from '../../types';

export function buildUser(overrides: Partial<User> = {}): User {
  return {
    id: faker.string.uuid(),
    email: faker.internet.email(),
    displayName: faker.person.fullName(),
    status: 'active',
    createdAt: new Date(),
    updatedAt: new Date(),
    ...overrides,
  };
}

export function buildCreateUserInput(overrides: Partial<CreateUserInput> = {}): CreateUserInput {
  return {
    email: faker.internet.email(),
    displayName: faker.person.fullName(),
    ...overrides,
  };
}
```

### Test Helpers

```typescript
// test/helpers/database.ts
export async function withTransaction<T>(
  db: Database,
  fn: (tx: Transaction) => Promise<T>
): Promise<T> {
  const tx = await db.beginTransaction();
  try {
    const result = await fn(tx);
    await tx.rollback(); // Always rollback in tests
    return result;
  } catch (error) {
    await tx.rollback();
    throw error;
  }
}

// test/helpers/assertions.ts
export function expectValidationError(response: Response, field: string) {
  expect(response.status).toBe(400);
  expect(response.body.code).toBe('VALIDATION_ERROR');
  expect(response.body.details).toHaveProperty(field);
}
```

## Patterns to Avoid
- ❌ Testing implementation details
- ❌ Shared mutable state between tests
- ❌ Flaky async tests
- ❌ Over-mocking

## Verification Checklist
- [ ] Isolated test cases
- [ ] Descriptive test names
- [ ] Factory patterns for test data
- [ ] Database cleanup between tests
- [ ] Meaningful assertions
