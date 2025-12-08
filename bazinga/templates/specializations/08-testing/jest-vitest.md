---
name: jest-vitest
type: testing
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer, qa_expert]
---

> This guidance is supplementary. It helps you write better tests for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Jest/Vitest Testing Expertise

## Specialist Profile
Testing specialist using Jest or Vitest. Expert in unit testing, mocking, and test-driven development for JavaScript/TypeScript applications.

---

## Patterns to Follow

### Test Structure
- **Arrange-Act-Assert**: Clear test phases
- **Descriptive names**: `it('should return null when user not found')`
- **One assertion per test**: When practical, for clear failure messages
- **Test isolation**: Each test independent, no shared state

### Test Organization
- **`describe` blocks**: Group related tests logically
- **Setup/teardown**: Use `beforeEach`/`afterEach` for shared setup
- **Test files**: Co-locate with source (`*.test.ts` or `__tests__/`)
- **Test coverage**: Focus on behavior, not line coverage percentage

### Mocking
- **Mock modules**: `jest.mock('module')` / `vi.mock('module')`
- **Spy on methods**: `jest.spyOn(obj, 'method')` / `vi.spyOn(obj, 'method')`
- **Mock implementations**: `mockFn.mockReturnValue(value)`
- **Clear mocks**: `jest.clearAllMocks()` / `vi.clearAllMocks()` in `beforeEach`

### Async Testing
- **async/await**: `it('loads data', async () => { await ... })`
- **Timers**: `jest.useFakeTimers()` / `vi.useFakeTimers()` for time-dependent code
- **Wait for**: Use `waitFor` or `findBy*` for async DOM updates

### Assertions
- **toBe**: For primitives and same reference
- **toEqual**: For deep object comparison
- **toMatchObject**: For partial object matching
- **toThrow**: For error assertions
- **Snapshot**: For UI components (use sparingly)

---

## Patterns to Avoid

### Test Anti-Patterns
- ❌ **Testing implementation**: Test behavior, not internal details
- ❌ **Flaky tests**: No random data, no timing dependencies
- ❌ **Large test files**: Break into focused test suites
- ❌ **Copy-paste tests**: Extract shared setup to helpers

### Mocking Issues
- ❌ **Over-mocking**: If everything is mocked, what are you testing?
- ❌ **Leaking mocks**: Always restore/clear mocks between tests
- ❌ **Mocking what you don't own**: Mock your adapters, not third-party APIs
- ❌ **Complex mock setups**: Simplify or test at higher level

### Coverage Traps
- ❌ **Coverage as goal**: 100% coverage doesn't mean good tests
- ❌ **Testing getters/setters**: Only test if they have logic
- ❌ **Testing framework code**: Test your code, not the library

### Structural Issues
- ❌ **Shared mutable state**: Tests should not depend on each other
- ❌ **Test order dependency**: Tests must pass in any order
- ❌ **Environment leakage**: Clean up files, databases, etc.

---

## Verification Checklist

### Test Quality
- [ ] Each test has a clear, descriptive name
- [ ] Tests are independent and can run in any order
- [ ] Mocks are cleared/restored between tests
- [ ] No flaky tests (consistent pass/fail)

### Coverage
- [ ] Critical paths have tests
- [ ] Edge cases covered (null, empty, boundary values)
- [ ] Error conditions tested
- [ ] Async behavior tested

### Maintenance
- [ ] Tests co-located with source code
- [ ] Shared setup extracted to helpers
- [ ] No duplicate test logic

---

## Code Patterns (Reference)

### Basic Test Structure
```javascript
describe('UserService', () => {
  beforeEach(() => {
    jest.clearAllMocks(); // or vi.clearAllMocks()
  });

  it('should return user by id', async () => {
    // Arrange
    const mockUser = { id: '1', name: 'Test' };
    userRepo.findById.mockResolvedValue(mockUser);

    // Act
    const result = await userService.getUser('1');

    // Assert
    expect(result).toEqual(mockUser);
    expect(userRepo.findById).toHaveBeenCalledWith('1');
  });
});
```

### Mocking Patterns
- **Module mock**: `jest.mock('./module', () => ({ fn: jest.fn() }))`
- **Spy**: `const spy = jest.spyOn(obj, 'method').mockReturnValue(42)`
- **Timer**: `jest.advanceTimersByTime(1000)` / `vi.advanceTimersByTime(1000)`

### Assertions
- **Equality**: `expect(value).toBe(expected)`
- **Object**: `expect(obj).toEqual({ key: 'value' })`
- **Contains**: `expect(array).toContain(item)`
- **Throws**: `expect(() => fn()).toThrow('error message')`
- **Called**: `expect(mockFn).toHaveBeenCalledWith(arg)`
