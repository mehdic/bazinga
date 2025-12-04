---
name: playwright-cypress
type: testing
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer, qa_expert]
requires: [typescript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Playwright/Cypress E2E Expertise

## Specialist Profile
E2E testing specialist building browser automation. Expert in page objects, visual testing, and test reliability.

## Implementation Guidelines

### Playwright Tests

```typescript
// tests/e2e/users.spec.ts
import { test, expect } from '@playwright/test';
import { UsersPage } from './pages/UsersPage';

test.describe('Users Management', () => {
  let usersPage: UsersPage;

  test.beforeEach(async ({ page }) => {
    usersPage = new UsersPage(page);
    await usersPage.goto();
  });

  test('should display users list', async () => {
    await expect(usersPage.usersList).toBeVisible();
    await expect(usersPage.userCards).toHaveCount(await usersPage.getUserCount());
  });

  test('should create new user', async () => {
    await usersPage.clickCreateUser();
    await usersPage.fillUserForm({
      email: 'new@test.com',
      displayName: 'New User',
    });
    await usersPage.submitForm();

    await expect(usersPage.successToast).toBeVisible();
    await expect(usersPage.userCards.last()).toContainText('New User');
  });

  test('should filter users by status', async () => {
    await usersPage.filterByStatus('active');

    const users = await usersPage.getVisibleUsers();
    for (const user of users) {
      expect(user.status).toBe('active');
    }
  });
});
```

### Page Objects

```typescript
// tests/e2e/pages/UsersPage.ts
import { Page, Locator } from '@playwright/test';

export class UsersPage {
  readonly page: Page;
  readonly usersList: Locator;
  readonly userCards: Locator;
  readonly createButton: Locator;
  readonly successToast: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usersList = page.getByTestId('users-list');
    this.userCards = page.getByTestId('user-card');
    this.createButton = page.getByRole('button', { name: 'Create User' });
    this.successToast = page.getByRole('alert').filter({ hasText: 'Success' });
  }

  async goto() {
    await this.page.goto('/users');
    await this.usersList.waitFor();
  }

  async clickCreateUser() {
    await this.createButton.click();
    await this.page.getByRole('dialog').waitFor();
  }

  async fillUserForm(data: { email: string; displayName: string }) {
    await this.page.getByLabel('Email').fill(data.email);
    await this.page.getByLabel('Display Name').fill(data.displayName);
  }

  async submitForm() {
    await this.page.getByRole('button', { name: 'Submit' }).click();
  }

  async filterByStatus(status: string) {
    await this.page.getByRole('combobox', { name: 'Status' }).selectOption(status);
    await this.page.waitForLoadState('networkidle');
  }

  async getUserCount(): Promise<number> {
    return this.userCards.count();
  }

  async getVisibleUsers() {
    const cards = await this.userCards.all();
    return Promise.all(
      cards.map(async (card) => ({
        name: await card.getByTestId('user-name').textContent(),
        status: await card.getByTestId('user-status').textContent(),
      }))
    );
  }
}
```

### Cypress Tests

```typescript
// cypress/e2e/users.cy.ts
describe('Users Management', () => {
  beforeEach(() => {
    cy.intercept('GET', '/api/users*').as('getUsers');
    cy.visit('/users');
    cy.wait('@getUsers');
  });

  it('should display users list', () => {
    cy.getByTestId('users-list').should('be.visible');
    cy.getByTestId('user-card').should('have.length.greaterThan', 0);
  });

  it('should create new user', () => {
    cy.intercept('POST', '/api/users').as('createUser');

    cy.contains('button', 'Create User').click();
    cy.getByLabel('Email').type('new@test.com');
    cy.getByLabel('Display Name').type('New User');
    cy.contains('button', 'Submit').click();

    cy.wait('@createUser').its('response.statusCode').should('eq', 201);
    cy.contains('[role="alert"]', 'Success').should('be.visible');
  });
});
```

## Patterns to Avoid
- ❌ Hard-coded waits (use proper assertions)
- ❌ Flaky selectors (use data-testid)
- ❌ Testing through UI what can be API tested
- ❌ Coupled tests

## Verification Checklist
- [ ] Page Object Pattern
- [ ] Data-testid selectors
- [ ] Network interception
- [ ] Proper waiting strategies
- [ ] Visual regression tests
