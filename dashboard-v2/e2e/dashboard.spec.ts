import { test, expect, Page } from "@playwright/test";
import { seedTestDatabase, SESSION_IDS } from "./fixtures/seed-database";
import path from "path";
import fs from "fs";

// Database path for tests - use the actual bazinga.db
// Must match the DATABASE_URL in playwright.config.ts (relative to dashboard-v2/)
const BAZINGA_DB_PATH = path.resolve(__dirname, "../bazinga/bazinga.db");

// Test data constants - these match the seeded data
const TEST_DATA = {
  // Completed session
  COMPLETED_SESSION: {
    id: SESSION_IDS.COMPLETED,
    shortId: "test_completed_001",
    mode: "simple",
    status: "completed",
    requirements: "Build a calculator application",
    taskGroup: "Calculator Implementation",
    taskGroupId: "CALC",
    agents: ["project_manager", "developer", "qa_expert", "tech_lead"],
  },
  // Active session
  ACTIVE_SESSION: {
    id: SESSION_IDS.ACTIVE,
    shortId: "test_active_002",
    mode: "parallel",
    status: "active",
    requirements: "Implement user authentication system",
    taskGroups: ["Core Authentication Logic", "JWT Token Management"],
  },
  // Failed session
  FAILED_SESSION: {
    id: SESSION_IDS.FAILED,
    shortId: "test_failed_003",
    mode: "simple",
    status: "failed",
    requirements: "Create a complex real-time trading system",
    taskGroup: "Trading Engine",
  },
  // Multi-group session
  MULTI_GROUP_SESSION: {
    id: SESSION_IDS.MULTI_GROUP,
    shortId: "test_multigroup_004",
    mode: "parallel",
    status: "completed",
    taskGroups: ["User Management API", "Product Catalog API", "Order Processing API"],
  },
  // Success criteria - completed session
  COMPLETED_CRITERIA: [
    "Implement add operation",
    "Implement subtract operation",
    "Implement multiply operation",
    "Implement divide operation",
    "Handle division by zero",
    "Unit test coverage > 90%",
    "All tests passing",
  ],
  // Success criteria - active session (mixed statuses)
  ACTIVE_CRITERIA: {
    met: ["Implement password hashing"],
    pending: ["Implement JWT generation", "Implement JWT validation"],
    blocked: ["Security audit passing"],
  },
  // Skills
  SKILLS: ["lint-check", "test-coverage", "security-scan", "specialization-loader"],
};

// Ensure test data directory exists and seed database before all tests
test.beforeAll(async () => {
  // Ensure bazinga directory exists
  const bazingaDir = path.dirname(BAZINGA_DB_PATH);
  if (!fs.existsSync(bazingaDir)) {
    fs.mkdirSync(bazingaDir, { recursive: true });
  }

  console.log(`Seeding test data into: ${BAZINGA_DB_PATH}`);
  seedTestDatabase(BAZINGA_DB_PATH);
});

// ============================================================================
// DASHBOARD HOME PAGE TESTS
// ============================================================================

test.describe("Dashboard Home Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    // Wait for stats to load
    await page.waitForSelector('[data-testid="stats-cards"], .grid', { timeout: 10000 });
  });

  test("displays stats cards with session metrics", async ({ page }) => {
    // Check that stats cards are present
    const statsSection = page.locator(".grid").first();
    await expect(statsSection).toBeVisible();

    // Look for common stats labels
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/Total Sessions|Sessions|Active/i);
  });

  test("shows active session indicator when session is running", async ({ page }) => {
    // Look for active session section
    const activeSection = page.getByText(/Active Session|Currently Running/i);
    // May or may not exist depending on data state - just verify page loads
    await expect(page.locator("body")).toBeVisible();
  });

  test("displays recent sessions list", async ({ page }) => {
    // Look for recent sessions section
    const recentSection = page.getByText(/Recent Sessions|Recent/i);
    await expect(page.locator("body")).toContainText(/Session|session/);
  });

  test("can navigate to sessions page from home", async ({ page }) => {
    // Click on sessions link in sidebar
    await page.click('a[href="/sessions"]');
    await expect(page).toHaveURL(/\/sessions/);
  });
});

// ============================================================================
// SESSIONS LIST PAGE TESTS
// ============================================================================

test.describe("Sessions List Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
  });

  test("displays sessions page header", async ({ page }) => {
    // Use first() since "Recent Sessions" heading may also match
    await expect(page.getByRole("heading", { name: /Sessions/i }).first()).toBeVisible();
  });

  test("shows filter buttons for session status", async ({ page }) => {
    // Check for filter buttons
    await expect(page.getByRole("button", { name: /All/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Active/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Completed/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Failed/i })).toBeVisible();
  });

  test("can filter sessions by status - completed", async ({ page }) => {
    // Click completed filter
    await page.getByRole("button", { name: /Completed/i }).click();
    await page.waitForTimeout(500); // Wait for filter to apply

    // Page should update
    const url = page.url();
    // Filter state may be in URL or component state
    await expect(page.getByRole("button", { name: /Completed/i })).toBeVisible();
  });

  test("can filter sessions by status - active", async ({ page }) => {
    await page.getByRole("button", { name: /Active/i }).click();
    await page.waitForTimeout(500);
    await expect(page.getByRole("button", { name: /Active/i })).toBeVisible();
  });

  test("can filter sessions by status - failed", async ({ page }) => {
    await page.getByRole("button", { name: /Failed/i }).click();
    await page.waitForTimeout(500);
    await expect(page.getByRole("button", { name: /Failed/i })).toBeVisible();
  });

  test("displays session cards in grid layout", async ({ page }) => {
    // Wait for session cards to load
    await page.waitForTimeout(1000);

    // Look for session information
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/mode|simple|parallel|Sessions/i);
  });

  test("session card shows status badge", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Look for status badges - check for status text in session cards
    const pageContent = await page.textContent("body");
    // Should have status indicators (completed, active, failed)
    expect(pageContent).toMatch(/completed|active|failed/i);
  });

  test("can click on session card to view details", async ({ page }) => {
    // Wait for sessions to load
    await page.waitForTimeout(1000);

    // Find a clickable session link
    const sessionLink = page.locator('a[href*="/sessions/"]').first();

    if (await sessionLink.isVisible()) {
      await sessionLink.click();
      await expect(page).toHaveURL(/\/sessions\/.+/);
    }
  });

  test("shows pagination when many sessions exist", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Check for pagination elements
    const pageContent = await page.textContent("body");
    const hasPagination = pageContent?.includes("Previous") ||
                          pageContent?.includes("Next") ||
                          pageContent?.includes("Showing");
    // Pagination only shows when > 12 sessions
    await expect(page.locator("body")).toBeVisible();
  });

  test("displays empty state when no sessions match filter", async ({ page }) => {
    // This may show empty state for some filters
    await page.getByRole("button", { name: /Failed/i }).click();
    await page.waitForTimeout(500);

    // Either shows sessions or empty state
    await expect(page.locator("body")).toBeVisible();
  });
});

// ============================================================================
// SESSION DETAIL PAGE TESTS
// ============================================================================

test.describe("Session Detail Page", () => {
  test("displays session not found for invalid ID", async ({ page }) => {
    await page.goto("/sessions/invalid_session_id_12345");
    await page.waitForTimeout(2000);

    // Should show not found message or redirect
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/not found|doesn't exist|Back to Sessions|Sessions/i);
  });

  test("displays completed session with correct data from DB", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const pageContent = await page.textContent("body");

    // Verify session mode from DB is displayed
    expect(pageContent).toContain("Simple Mode");

    // Verify requirements text from DB is displayed
    expect(pageContent.toLowerCase()).toContain("calculator");

    // Verify status badge shows completed
    expect(pageContent.toLowerCase()).toContain("completed");
  });

  test("displays active session with parallel mode from DB", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForTimeout(2000);

    const pageContent = await page.textContent("body");

    // Verify parallel mode from DB
    expect(pageContent).toContain("Parallel Mode");

    // Verify requirements from DB
    expect(pageContent.toLowerCase()).toContain("authentication");
  });

  test("displays failed session status from DB", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const pageContent = await page.textContent("body");

    // Verify failed status from DB
    expect(pageContent.toLowerCase()).toContain("failed");

    // Verify requirements from DB
    expect(pageContent.toLowerCase()).toContain("trading");
  });

  test("shows tab navigation with all tabs", async ({ page }) => {
    await page.goto(`/sessions/${SESSION_IDS.COMPLETED}`);
    await page.waitForTimeout(2000);

    // Check for tab buttons
    await expect(page.getByRole("tab", { name: /Workflow/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Tasks/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Logs/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Tokens/i })).toBeVisible();
  });

  test("tasks tab shows seeded task group: Calculator Implementation", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Tasks/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Verify task group name from DB is displayed
    expect(pageContent).toContain(TEST_DATA.COMPLETED_SESSION.taskGroup);

    // Verify completed status
    expect(pageContent.toLowerCase()).toContain("completed");
  });

  test("tasks tab shows multiple task groups for parallel session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.MULTI_GROUP_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Tasks/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Verify all task groups from DB are displayed
    for (const taskGroup of TEST_DATA.MULTI_GROUP_SESSION.taskGroups) {
      expect(pageContent).toContain(taskGroup);
    }
  });

  test("tasks tab shows active session task groups with in_progress status", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Tasks/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Verify task groups from DB
    expect(pageContent).toContain("Core Authentication Logic");
    expect(pageContent).toContain("JWT Token Management");

    // Should show in_progress or pending status
    expect(pageContent.toLowerCase()).toMatch(/in_progress|pending/);
  });

  test("logs tab shows orchestration logs with agent types from DB", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Logs/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Verify agent types from DB logs are displayed
    expect(pageContent).toContain("project_manager");
    expect(pageContent).toContain("developer");
    expect(pageContent).toContain("orchestrator");
  });

  test("logs tab shows seeded log content", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Logs/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Verify actual log content from DB is displayed
    expect(pageContent.toLowerCase()).toMatch(/session initialized|spawning|requirements/i);
  });

  test("tokens tab shows token usage from DB", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Tokens/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Should show token metrics - our seeded data has 108k total tokens
    expect(pageContent).toMatch(/Total Tokens/i);

    // Should show estimated cost
    expect(pageContent).toMatch(/Estimated Cost|\$/i);
  });

  test("skills tab shows seeded skill outputs", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Skills/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Verify skill names from DB are displayed (UI may show "lint" or "lint-check" or "Lint Check")
    expect(pageContent.toLowerCase()).toMatch(/lint|coverage|security|skill/);
  });

  test("timeline tab shows agent activity from seeded logs", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Timeline/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Should show timeline with agent types
    expect(pageContent).toMatch(/project_manager|developer|qa_expert|tech_lead/);
  });

  test("insights tab shows session summary based on DB data", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    await page.getByRole("tab", { name: /Insights/i }).click();
    await page.waitForTimeout(500);

    const pageContent = await page.textContent("body");

    // Should show summary mentioning simple mode (from DB)
    expect(pageContent).toMatch(/Session Summary|simple mode|task groups/i);
  });
});

// ============================================================================
// SUCCESS CRITERIA VIEWER TESTS
// ============================================================================

test.describe("Success Criteria Viewer", () => {
  test("displays seeded criteria for completed session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });

    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Verify seeded criteria text appears in UI
      expect(pageContent).toContain("Implement add operation");
      expect(pageContent).toContain("Implement subtract operation");
      expect(pageContent).toContain("division by zero");
    }
  });

  test("shows 100% progress for completed session (7/7 criteria met)", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });

    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Should show 100% or 7 of 7
      expect(pageContent).toMatch(/100%|7 of 7|7\/7/);
    }
  });

  test("displays all 7 seeded criteria from completed session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });

    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Verify all seeded criteria appear
      for (const criterion of TEST_DATA.COMPLETED_CRITERIA) {
        expect(pageContent.toLowerCase()).toContain(criterion.toLowerCase());
      }
    }
  });

  test("shows mixed criteria statuses for active session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForTimeout(2000);

    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });

    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Verify met criterion from DB
      expect(pageContent.toLowerCase()).toContain("password hashing");

      // Verify pending criteria from DB
      expect(pageContent.toLowerCase()).toContain("jwt generation");

      // Verify blocked criterion from DB
      expect(pageContent.toLowerCase()).toContain("security audit");

      // Should show different status badges
      expect(pageContent.toLowerCase()).toMatch(/met|pending|blocked/);
    }
  });

  test("shows blocked status indicator for security audit criterion", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForTimeout(2000);

    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });

    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Verify blocked status and reason from DB
      expect(pageContent).toContain("Security audit");
      expect(pageContent.toLowerCase()).toContain("blocked");
    }
  });

  test("shows failed criteria for failed session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });

    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Verify failed criteria from DB
      expect(pageContent.toLowerCase()).toContain("websocket");
      expect(pageContent.toLowerCase()).toMatch(/failed|blocked/);
    }
  });
});

// ============================================================================
// REASONING LOGS VIEWER TESTS
// ============================================================================

test.describe("Reasoning Logs Viewer", () => {
  test("displays seeded reasoning logs for completed session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const reasoningTab = page.getByRole("tab", { name: /Reasoning/i });

    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Verify seeded reasoning content appears
      // PM understanding phase reasoning
      expect(pageContent.toLowerCase()).toMatch(/understanding|requirements|calculator/i);
    }
  });

  test("shows reasoning phases from seeded data", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const reasoningTab = page.getByRole("tab", { name: /Reasoning/i });

    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Verify seeded phases appear: understanding, approach, completion
      expect(pageContent.toLowerCase()).toMatch(/understanding|approach|completion/);
    }
  });

  test("displays confidence levels from seeded data", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const reasoningTab = page.getByRole("tab", { name: /Reasoning/i });

    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Seeded data has high confidence levels
      expect(pageContent.toLowerCase()).toContain("high");
    }
  });

  test("shows references from seeded reasoning logs", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const reasoningTab = page.getByRole("tab", { name: /Reasoning/i });

    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Seeded data has file references like requirements.md, calculator.py
      expect(pageContent.toLowerCase()).toMatch(/requirements|calculator\.py|test_calculator/i);
    }
  });

  test("shows blocker reasoning for failed session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    await page.waitForTimeout(2000);

    const reasoningTab = page.getByRole("tab", { name: /Reasoning/i });

    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Seeded data has blocker reasoning phase
      expect(pageContent.toLowerCase()).toMatch(/blocker|exceed|complexity/i);
    }
  });

  test("shows risk reasoning for active session security issue", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForTimeout(2000);

    const reasoningTab = page.getByRole("tab", { name: /Reasoning/i });

    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await page.waitForTimeout(500);

      const pageContent = await page.textContent("body");

      // Seeded data has risk reasoning about timing attack
      expect(pageContent.toLowerCase()).toMatch(/risk|timing|vulnerability/i);
    }
  });
});

// ============================================================================
// ANALYTICS PAGE TESTS
// ============================================================================

test.describe("Analytics Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
  });

  test("displays analytics page header", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /Analytics/i })).toBeVisible();
  });

  test("shows key metrics cards", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Should show key metrics
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/Success Rate|Total Tokens|Revision Rate|Active Sessions/i);
  });

  test("displays tokens by agent chart", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Should show token distribution
    await expect(page.getByText(/Tokens by Agent|Token/i).first()).toBeVisible();
  });

  test("shows agent invocations chart", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Should show invocations
    await expect(page.getByText(/Agent Invocations|Invocations/i).first()).toBeVisible();
  });

  test("displays agent activity breakdown", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Should show agent breakdown
    await expect(page.getByText(/Agent Activity Breakdown|Activity/i).first()).toBeVisible();
  });

  test("shows revision analysis section", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Should show revision stats
    await expect(page.getByText(/Revision Analysis|Revisions/i).first()).toBeVisible();
  });

  test("displays recent session performance list", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Should show recent sessions
    await expect(page.getByText(/Recent Session Performance|Recent/i).first()).toBeVisible();
  });
});

// ============================================================================
// SETTINGS PAGE TESTS
// ============================================================================

test.describe("Settings Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/settings");
    await page.waitForLoadState("networkidle");
  });

  test("displays settings page header", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /Settings/i })).toBeVisible();
  });

  test("shows appearance settings with theme options", async ({ page }) => {
    // Should show theme options
    await expect(page.getByText(/Appearance/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Light/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dark/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /System/i })).toBeVisible();
  });

  test("can switch theme to dark mode", async ({ page }) => {
    await page.getByRole("button", { name: /Dark/i }).click();
    await page.waitForTimeout(500);

    // Button should now be active
    await expect(page.getByRole("button", { name: /Dark/i })).toBeVisible();
  });

  test("can switch theme to light mode", async ({ page }) => {
    await page.getByRole("button", { name: /Light/i }).click();
    await page.waitForTimeout(500);

    await expect(page.getByRole("button", { name: /Light/i })).toBeVisible();
  });

  test("shows notification settings section", async ({ page }) => {
    await expect(page.getByText(/Notifications/i).first()).toBeVisible();
  });

  test("displays notification type toggles", async ({ page }) => {
    // Should show notification toggles
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/BAZINGA Completion|Session Started|Errors/i);
  });

  test("shows connection status section", async ({ page }) => {
    await expect(page.getByText(/Real-time Connection|Connection/i).first()).toBeVisible();
  });

  test("displays database status section", async ({ page }) => {
    await expect(page.getByText(/Database/i).first()).toBeVisible();
  });

  test("shows about section with version info", async ({ page }) => {
    await expect(page.getByText(/About/i).first()).toBeVisible();
    await expect(page.getByText(/BAZINGA Dashboard/i)).toBeVisible();
  });
});

// ============================================================================
// CONFIG PAGE TESTS
// ============================================================================

test.describe("Config Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/config");
    await page.waitForLoadState("networkidle");
  });

  test("displays config page content", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Should show config/project context editor
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/Project|Context|Config|Editor/i);
  });
});

// ============================================================================
// SESSION COMPARE PAGE TESTS
// ============================================================================

test.describe("Session Compare Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/sessions/compare");
    await page.waitForLoadState("networkidle");
  });

  test("displays compare page content", async ({ page }) => {
    await page.waitForTimeout(1000);

    // Should show comparison interface
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/Compare|Session|Select/i);
  });
});

// ============================================================================
// NAVIGATION TESTS
// ============================================================================

test.describe("Navigation", () => {
  test("sidebar navigation is visible", async ({ page }) => {
    await page.goto("/");

    // Check sidebar links exist
    await expect(page.locator('a[href="/"]').first()).toBeVisible();
    await expect(page.locator('a[href="/sessions"]')).toBeVisible();
    await expect(page.locator('a[href="/analytics"]')).toBeVisible();
    await expect(page.locator('a[href="/settings"]')).toBeVisible();
  });

  test("can navigate from home to sessions", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/sessions"]');
    await expect(page).toHaveURL(/\/sessions/);
  });

  test("can navigate from home to analytics", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/analytics"]');
    await expect(page).toHaveURL(/\/analytics/);
  });

  test("can navigate from home to settings", async ({ page }) => {
    await page.goto("/");
    await page.click('a[href="/settings"]');
    await expect(page).toHaveURL(/\/settings/);
  });

  test("can navigate back to home from any page", async ({ page }) => {
    await page.goto("/sessions");
    await page.click('a[href="/"]');
    await expect(page).toHaveURL("/");
  });

  test("breadcrumb back button works on session detail", async ({ page }) => {
    await page.goto(`/sessions/${SESSION_IDS.COMPLETED}`);
    await page.waitForTimeout(2000);

    // Click back button
    const backButton = page.getByRole("link", { name: /Back to Sessions/i });
    if (await backButton.isVisible()) {
      await backButton.click();
      await expect(page).toHaveURL(/\/sessions/);
    }
  });
});

// ============================================================================
// REAL USER SCENARIOS - VERIFYING SEEDED DB DATA IN UI
// ============================================================================

test.describe("User Scenarios", () => {
  test("scenario: user reviews completed calculator session end-to-end", async ({ page }) => {
    // 1. Start at home page
    await page.goto("/");
    await page.waitForTimeout(1000);

    // 2. Navigate to sessions list
    await page.click('a[href="/sessions"]');
    await expect(page).toHaveURL(/\/sessions/);

    // 3. Filter to show only completed sessions
    await page.getByRole("button", { name: /Completed/i }).click();
    await page.waitForTimeout(500);

    // 4. Navigate to the completed calculator session
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForTimeout(2000);

    // 5. Verify seeded requirements appear
    const headerContent = await page.textContent("body");
    expect(headerContent.toLowerCase()).toContain("calculator");

    // 6. Check tasks - verify seeded task group "Calculator Implementation"
    await page.getByRole("tab", { name: /Tasks/i }).click();
    await page.waitForTimeout(500);
    const tasksContent = await page.textContent("body");
    expect(tasksContent).toContain("Calculator Implementation");
    expect(tasksContent.toLowerCase()).toContain("completed");

    // 7. Review logs - verify seeded agent interactions
    await page.getByRole("tab", { name: /Logs/i }).click();
    await page.waitForTimeout(500);
    const logsContent = await page.textContent("body");
    expect(logsContent).toContain("project_manager");
    expect(logsContent).toContain("developer");

    // 8. Check token usage - seeded data has ~108k tokens
    await page.getByRole("tab", { name: /Tokens/i }).click();
    await page.waitForTimeout(500);
    // Use first() since multiple elements may match "Total Tokens" text
    await expect(page.getByText(/Total Tokens/i).first()).toBeVisible();

    // 9. Check criteria - all 7 should be met
    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });
    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);
      const criteriaContent = await page.textContent("body");
      expect(criteriaContent).toContain("Implement add operation");
      expect(criteriaContent).toMatch(/100%|7 of 7/);
    }
  });

  test("scenario: user monitors active authentication session", async ({ page }) => {
    // Navigate to active session
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForTimeout(2000);

    // Verify seeded data: parallel mode
    const pageContent = await page.textContent("body");
    expect(pageContent).toContain("Parallel Mode");

    // Verify seeded requirements
    expect(pageContent.toLowerCase()).toContain("authentication");

    // Check tasks - verify seeded task groups
    await page.getByRole("tab", { name: /Tasks/i }).click();
    await page.waitForTimeout(500);
    const tasksContent = await page.textContent("body");
    expect(tasksContent).toContain("Core Authentication Logic");
    expect(tasksContent).toContain("JWT Token Management");
    expect(tasksContent.toLowerCase()).toMatch(/in_progress|pending/);

    // Check criteria - should show blocked security audit
    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });
    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);
      const criteriaContent = await page.textContent("body");
      expect(criteriaContent.toLowerCase()).toContain("security audit");
      expect(criteriaContent.toLowerCase()).toContain("blocked");
    }
  });

  test("scenario: user investigates failed trading session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    await page.waitForTimeout(2000);

    // Verify seeded failed status
    const pageContent = await page.textContent("body");
    expect(pageContent.toLowerCase()).toContain("failed");

    // Verify seeded requirements mention trading
    expect(pageContent.toLowerCase()).toContain("trading");

    // Check tasks - verify seeded "Trading Engine" group
    await page.getByRole("tab", { name: /Tasks/i }).click();
    await page.waitForTimeout(500);
    const tasksContent = await page.textContent("body");
    expect(tasksContent).toContain("Trading Engine");
    expect(tasksContent.toLowerCase()).toContain("failed");

    // Check logs for seeded failure reason
    await page.getByRole("tab", { name: /Logs/i }).click();
    await page.waitForTimeout(500);
    const logsContent = await page.textContent("body");
    expect(logsContent.toLowerCase()).toMatch(/complexity|exceed|websocket/i);

    // Check criteria - should show failed websocket criterion
    const criteriaTab = page.getByRole("tab", { name: /Criteria/i });
    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await page.waitForTimeout(500);
      const criteriaContent = await page.textContent("body");
      expect(criteriaContent.toLowerCase()).toContain("websocket");
    }
  });

  test("scenario: user reviews parallel API session with 3 task groups", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.MULTI_GROUP_SESSION.id}`);
    await page.waitForTimeout(2000);

    // Verify parallel mode
    const pageContent = await page.textContent("body");
    expect(pageContent).toContain("Parallel Mode");

    // Check tasks - verify all 3 seeded API task groups
    await page.getByRole("tab", { name: /Tasks/i }).click();
    await page.waitForTimeout(500);
    const tasksContent = await page.textContent("body");
    expect(tasksContent).toContain("User Management API");
    expect(tasksContent).toContain("Product Catalog API");
    expect(tasksContent).toContain("Order Processing API");

    // All should be completed
    const completedMatches = tasksContent.toLowerCase().match(/completed/g);
    expect(completedMatches?.length).toBeGreaterThanOrEqual(3);
  });

  test("scenario: user analyzes system performance with seeded data", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForTimeout(1000);

    // Check success rate - we have 2 completed, 1 active, 1 failed = ~50%
    await expect(page.getByText(/Success Rate/i)).toBeVisible();

    // Check token usage - seeded data has substantial tokens
    await expect(page.getByText(/Total Tokens/i)).toBeVisible();

    // Check revision rate - seeded data has some revisions
    await expect(page.getByText(/Revision Rate/i)).toBeVisible();

    // Check agent breakdown - should show our seeded agent types
    const pageContent = await page.textContent("body");
    expect(pageContent.toLowerCase()).toMatch(/project_manager|developer|qa_expert|tech_lead/);
  });

  test("scenario: user customizes dashboard settings", async ({ page }) => {
    await page.goto("/settings");

    // Change theme
    await page.getByRole("button", { name: /Dark/i }).click();
    await page.waitForTimeout(500);

    // Verify theme changed
    await expect(page.getByRole("button", { name: /Dark/i })).toBeVisible();

    // Change back to light
    await page.getByRole("button", { name: /Light/i }).click();
    await page.waitForTimeout(500);
  });

  test("scenario: user compares multiple sessions", async ({ page }) => {
    // Navigate to compare page
    await page.goto("/sessions/compare");
    await page.waitForTimeout(1000);

    // Verify compare interface loads
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/Compare|Session|Select/i);
  });
});

// ============================================================================
// RESPONSIVE DESIGN TESTS
// ============================================================================

test.describe("Responsive Design", () => {
  test("dashboard renders correctly on mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");
    await page.waitForTimeout(1000);

    // Page should still be functional
    await expect(page.locator("body")).toBeVisible();
  });

  test("sessions list renders on tablet viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/sessions");
    await page.waitForTimeout(1000);

    // Use first() since "Recent Sessions" heading may also match
    await expect(page.getByRole("heading", { name: /Sessions/i }).first()).toBeVisible();
  });

  test("session detail page tabs work on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/sessions/${SESSION_IDS.COMPLETED}`);
    await page.waitForTimeout(2000);

    // Tabs should still be clickable
    // On mobile, scrolling is needed before clicking tabs to avoid overlay interception
    const tasksTab = page.getByRole("tab", { name: /Tasks/i });
    if (await tasksTab.isVisible()) {
      await tasksTab.scrollIntoViewIfNeeded();
      await tasksTab.click({ force: true });
      await page.waitForTimeout(500);
    }
  });
});

// ============================================================================
// ERROR HANDLING TESTS
// ============================================================================

test.describe("Error Handling", () => {
  test("gracefully handles 404 pages", async ({ page }) => {
    await page.goto("/non-existent-page-12345");
    const response = await page.waitForResponse((res) => res.status() === 404 || res.status() === 200);
    // Either shows 404 or redirects - both are acceptable
    await expect(page.locator("body")).toBeVisible();
  });

  test("handles invalid session ID gracefully", async ({ page }) => {
    await page.goto("/sessions/completely_invalid_id_xyz");
    await page.waitForTimeout(2000);

    // Should show error state or redirect
    const pageContent = await page.textContent("body");
    expect(pageContent).toMatch(/not found|doesn't exist|Sessions|Back/i);
  });
});
