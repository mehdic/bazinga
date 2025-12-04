---
name: testing-patterns
type: testing
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer, qa_expert]
requires: []
---

> **MANDATORY**: Apply these patterns to ALL code you write. This is NOT optional guidance—these are required practices. Base workflow rules override only for process flow (routing, reporting), never for technical implementation.

# Testing Patterns Engineering Expertise

## Specialist Profile
Testing specialist implementing comprehensive test strategies. Expert in unit, integration, and E2E testing patterns.

---

## Patterns to Follow

### Unit Testing
- **Arrange-Act-Assert (AAA)**: Clear test structure
- **Test behavior, not implementation**: Public API focus
- **One assertion per test (ideally)**: Clear failure reason
- **Fast execution**: Mock external dependencies
- **Descriptive names**: `should_return_error_when_email_invalid`

### Integration Testing
- **Real database (containerized)**: Docker, Testcontainers
- **API contract testing**: HTTP layer
- **Transaction rollback**: Clean state per test
- **Minimal mocking**: Only external services
- **Realistic scenarios**: Happy path + error paths

### Test-Driven Development (TDD)
- **Red-Green-Refactor**: Write failing test first
- **Outer/Inner loop**: Acceptance test → unit tests
- **Small increments**: One test at a time
- **Refactor with confidence**: Tests are safety net

### Test Data
- **Factory pattern**: `buildUser({ email: 'test@example.com' })`
- **Faker for realistic data**: Random but valid
- **Fixtures for complex scenarios**: Reusable setups
- **Database seeding**: Consistent baseline

### Mocking Strategy
- **Mock at boundaries**: External services, time, randomness
- **Don't mock what you own**: Test real interactions
- **Verify mock calls**: Ensure correct usage
- **Reset between tests**: Clean state

---

## Patterns to Avoid

### Unit Test Anti-Patterns
- ❌ **Testing private methods**: Test public behavior
- ❌ **Shared mutable state**: Isolation required
- ❌ **Over-mocking**: Loses confidence
- ❌ **Brittle assertions**: Test essence, not details
- ❌ **Slow tests**: Should run in milliseconds

### Integration Anti-Patterns
- ❌ **Mocking everything**: Defeats purpose
- ❌ **Shared database state**: Tests affect each other
- ❌ **No cleanup**: Data accumulates
- ❌ **Flaky async handling**: Use proper waiting

### General Anti-Patterns
- ❌ **Chasing 100% coverage**: Coverage ≠ quality
- ❌ **No mutation testing**: Tests may be weak
- ❌ **Ignoring flaky tests**: Technical debt
- ❌ **Comments in tests**: Test names should be clear

### Structure Anti-Patterns
- ❌ **Logic in tests**: Keep tests simple
- ❌ **Multiple assertions (unrelated)**: Split tests
- ❌ **Copy-paste test code**: Use factories/helpers
- ❌ **Tests without assertions**: False confidence

---

## Verification Checklist

### Unit Tests
- [ ] AAA pattern followed
- [ ] Tests are isolated
- [ ] Fast execution (<100ms each)
- [ ] Meaningful names

### Integration Tests
- [ ] Real database used
- [ ] Proper cleanup/rollback
- [ ] Contract verification
- [ ] Timeout handling

### Coverage
- [ ] Critical paths covered
- [ ] Edge cases included
- [ ] Error handling tested
- [ ] Mutation testing considered

### Maintenance
- [ ] Factory patterns for data
- [ ] Helper functions for common assertions
- [ ] Clear folder structure
- [ ] CI integration

---

## Code Patterns (Reference)

### Unit Test (Jest)
- **Structure**: `describe('UserService', () => { describe('create', () => { it('should...', () => {}); }); });`
- **Mock**: `const mockRepo = { create: jest.fn().mockResolvedValue(user) };`
- **Assert**: `expect(result).toMatchObject({ email: 'test@example.com' });`

### Integration Test
- **Setup**: `beforeAll(async () => { db = await createTestDatabase(); });`
- **Request**: `const response = await request(app).post('/users').send(userData).expect(201);`
- **Cleanup**: `afterEach(async () => { await db.truncate(['users']); });`

### Factory Pattern
- **Builder**: `function buildUser(overrides = {}) { return { id: faker.string.uuid(), email: faker.internet.email(), ...overrides }; }`

### Helper
- **Custom assertion**: `function expectValidationError(response, field) { expect(response.status).toBe(400); expect(response.body.details).toHaveProperty(field); }`

