---
name: playwright-cypress
type: testing
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer, qa_expert]
requires: [typescript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Playwright/Cypress E2E Expertise

## Specialist Profile
E2E testing specialist building browser automation. Expert in page objects, visual testing, and test reliability.

---

## Patterns to Follow

### Test Structure
- **Page Object Model**: Encapsulate page interactions
- **data-testid selectors**: Stable, decoupled from styling
- **Descriptive test names**: `should create user with valid data`
- **Arrange-Act-Assert**: Clear test phases
- **Single responsibility**: One behavior per test

### Playwright Patterns (2025)
<!-- version: playwright >= 1.20 -->
- **Auto-waiting built-in**: No manual waits needed
- **Parallel execution**: Native, fast
- **Multiple browsers**: Chrome, Firefox, WebKit
- **Trace Viewer**: Deep debugging on failure
- **API mocking**: `page.route()` for isolation
<!-- version: playwright >= 1.35 -->
- **UI mode**: Interactive test runner with watch mode
- **Component testing**: Native React/Vue/Svelte support
<!-- version: playwright >= 1.40 -->
- **Annotations API**: `test.step()`, `test.slow()`, `test.fixme()`
<!-- version: playwright >= 1.44 -->
- **Clock API**: Mock Date, setTimeout, setInterval

### Cypress Patterns
<!-- version: cypress >= 10.0 -->
- **cy.intercept()**: Network stubbing
- **Auto-retry assertions**: Handles async naturally
- **Time-travel debugging**: Inspect each step
- **Component testing**: Native support
- **Real-time reloading**: Fast feedback
<!-- version: cypress >= 12.0 -->
- **Test isolation default**: Each test starts fresh
- **Improved component testing**: Better framework support
<!-- version: cypress >= 13.0 -->
- **Session API improvements**: Persistent auth across tests
<!-- version: cypress < 10.0 -->
- **Legacy cy.route()**: Use cy.intercept() instead (deprecated)

### Reliability Patterns
- **API shortcuts for setup**: Seed data via API, not UI
- **Isolated test data**: Each test creates its own
- **Retry flaky tests**: `retries: 2` in config
- **Visual regression**: Percy, Applitools, or built-in
- **Cross-browser testing**: CI matrix

### CI/CD Integration
- **Headless by default**: Faster in CI
- **Artifacts on failure**: Screenshots, videos, traces
- **Parallel sharding**: Split across workers
- **Flaky test detection**: Track over time

---

## Patterns to Avoid

### Selector Anti-Patterns
- ❌ **CSS classes for selectors**: Fragile, change often
- ❌ **XPath for simple elements**: Use semantic selectors
- ❌ **Auto-generated IDs**: Unstable between builds
- ❌ **Text-based only**: May change with i18n

### Test Anti-Patterns
- ❌ **Hard-coded waits (sleep)**: Flaky, slow
- ❌ **Testing via UI what's faster via API**: Slow, brittle
- ❌ **Shared mutable state**: Tests affect each other
- ❌ **Sequential dependencies**: Tests should be independent
- ❌ **Giant test files**: Hard to maintain

### Maintenance Anti-Patterns
- ❌ **Duplicated selectors**: Use page objects
- ❌ **No retry strategy**: Flaky test fatigue
- ❌ **Missing CI artifacts**: Can't debug failures
- ❌ **Ignoring flaky tests**: Tech debt builds up

---

## Verification Checklist

### Structure
- [ ] Page Object Pattern used
- [ ] data-testid for key elements
- [ ] Tests are independent
- [ ] Single assertion focus

### Reliability
- [ ] No hard-coded waits
- [ ] Network mocking where needed
- [ ] Retry configuration
- [ ] Test isolation (data, state)

### CI/CD
- [ ] Headless mode configured
- [ ] Artifacts on failure
- [ ] Parallel execution
- [ ] Cross-browser matrix

### Reporting
- [ ] HTML report generation
- [ ] Video/screenshot on failure
- [ ] Trace files (Playwright)
- [ ] Coverage integration

---

## Code Patterns (Reference)

### Playwright
- **Page Object**: `class UsersPage { constructor(page: Page) { this.usersList = page.getByTestId('users-list'); } }`
- **Test**: `test('should display users', async ({ page }) => { await expect(page.getByTestId('user-card')).toHaveCount(3); });`
- **API mock**: `await page.route('/api/users', route => route.fulfill({ json: users }));`
- **Wait for network**: `await page.waitForResponse('/api/users');`

### Cypress
- **Intercept**: `cy.intercept('GET', '/api/users').as('getUsers'); cy.wait('@getUsers');`
- **Custom command**: `Cypress.Commands.add('login', (email) => { cy.request('POST', '/api/login', { email }); });`
- **Assertion**: `cy.getByTestId('user-card').should('have.length.greaterThan', 0);`

### Both
- **data-testid**: `<button data-testid="submit-btn">Submit</button>`
- **Page Object method**: `async fillForm(data) { await this.emailInput.fill(data.email); }`

