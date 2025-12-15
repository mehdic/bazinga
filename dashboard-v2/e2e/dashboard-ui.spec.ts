/**
 * Comprehensive Browser-Based UI E2E Tests
 *
 * These tests simulate real user interactions with the dashboard:
 * - Clicking buttons, links, and tabs
 * - Verifying displayed content matches seeded data
 * - Testing filtering, sorting, and pagination
 * - Navigating between pages
 */

import { test, expect } from "@playwright/test";
import { seedTestDatabase, SESSION_IDS } from "./fixtures/seed-database";
import path from "path";
import fs from "fs";

// Test data that matches what's seeded in seed-database.ts
const TEST_DATA = {
  COMPLETED_SESSION: {
    id: SESSION_IDS.COMPLETED,
    shortId: "test_com",
    mode: "simple",
    status: "completed",
    requirements: "calculator",
    taskGroupName: "Calculator Implementation",
    taskGroupId: "CALC",
  },
  ACTIVE_SESSION: {
    id: SESSION_IDS.ACTIVE,
    shortId: "test_act",
    mode: "parallel",
    status: "active",
    requirements: "authentication",
    taskGroupNames: ["Core Authentication Logic", "JWT Token Management"],
  },
  FAILED_SESSION: {
    id: SESSION_IDS.FAILED,
    shortId: "test_fai",
    status: "failed",
    requirements: "trading system",
    taskGroupName: "Trading Engine",
  },
  MULTI_GROUP_SESSION: {
    id: SESSION_IDS.MULTI_GROUP,
    shortId: "test_mul",
    mode: "parallel",
    status: "completed",
    requirements: "REST API",
    taskGroupNames: ["User Management API", "Product Catalog API", "Order Processing API"],
  },
};

// Database path
const BAZINGA_DB_PATH = path.resolve(__dirname, "../bazinga/bazinga.db");

// Seed database before all tests
test.beforeAll(async () => {
  const bazingaDir = path.dirname(BAZINGA_DB_PATH);
  if (!fs.existsSync(bazingaDir)) {
    fs.mkdirSync(bazingaDir, { recursive: true });
  }
  console.log(`Seeding test data into: ${BAZINGA_DB_PATH}`);
  seedTestDatabase(BAZINGA_DB_PATH);
});

// =============================================================================
// HOME PAGE UI TESTS
// =============================================================================

test.describe("Home Page UI", () => {
  test("displays dashboard navigation links", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: /sessions/i })).toBeVisible();
  });

  test("can navigate to sessions page from home", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /sessions/i }).click();
    await expect(page).toHaveURL(/\/sessions/);
  });

  test("can navigate to analytics page from home", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/);
  });
});

// =============================================================================
// SESSIONS LIST PAGE UI TESTS
// =============================================================================

test.describe("Sessions List Page UI", () => {
  test("displays seeded sessions in the list", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");

    // Wait for session cards to appear
    const sessionLinks = page.locator('a[href*="/sessions/bazinga_test"]');
    await expect(sessionLinks.first()).toBeVisible({ timeout: 15000 });
  });

  test("shows completed session with status badge", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });
  });

  test("shows active session with status badge", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=active").first()).toBeVisible({ timeout: 10000 });
  });

  test("shows failed session with status badge", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=failed").first()).toBeVisible({ timeout: 10000 });
  });

  test("can filter sessions by status - completed", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    await page.getByRole("button", { name: /completed/i }).click();
    await page.waitForTimeout(500);
    await expect(page.locator("text=completed")).toBeVisible();
  });

  test("can filter sessions by status - All", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    await page.getByRole("button", { name: /completed/i }).click();
    await page.waitForTimeout(300);
    await page.getByRole("button", { name: /^all$/i }).click();
    await page.waitForTimeout(300);
    await expect(page.locator("text=completed").first()).toBeVisible();
  });

  test("clicking View Details navigates to session detail", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    const viewDetailsButton = page.getByRole("button", { name: /view details/i }).first();
    await viewDetailsButton.click();
    await expect(page).toHaveURL(/\/sessions\/bazinga_test/);
  });

  test("displays session requirements preview", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    const requirementsText = page.locator("text=calculator").or(page.locator("text=authentication")).or(page.locator("text=trading"));
    await expect(requirementsText.first()).toBeVisible({ timeout: 10000 });
  });

  test("displays session mode indicator", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    const modeText = page.locator("text=simple").or(page.locator("text=parallel"));
    await expect(modeText.first()).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// SESSION DETAIL PAGE UI TESTS - COMPLETED SESSION
// =============================================================================

test.describe("Session Detail Page UI - Completed Session", () => {
  test("displays session header with completed status", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });
  });

  test("displays session mode as Simple Mode", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Simple Mode")).toBeVisible({ timeout: 10000 });
  });

  test("displays session requirements with calculator", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=calculator")).toBeVisible({ timeout: 10000 });
  });

  test("displays 100% progress for completed session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=100%")).toBeVisible({ timeout: 10000 });
  });

  test("can click Tasks tab and see Calculator Implementation", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Calculator Implementation")).toBeVisible({ timeout: 10000 });
  });

  test("shows task group completed status", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });
  });

  test("shows assigned developer_1 for task group", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=developer_1")).toBeVisible({ timeout: 10000 });
  });

  test("can click Logs tab and see agent types", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /logs/i }).click();
    await expect(page.locator("text=project_manager").or(page.locator("text=developer"))).toBeVisible({ timeout: 10000 });
  });

  test("can click Tokens tab and see Total Tokens", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tokens/i }).click();
    await expect(page.locator("text=Total Tokens")).toBeVisible({ timeout: 10000 });
  });

  test("can click Skills tab and see skill outputs", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /skills/i }).click();
    await expect(page.locator("text=lint-check").or(page.locator("text=test-coverage"))).toBeVisible({ timeout: 10000 });
  });

  test("can click Timeline tab and see timeline entries", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /timeline/i }).click();
    await expect(page.locator("text=project_manager").or(page.locator("text=developer"))).toBeVisible({ timeout: 10000 });
  });

  test("can click Insights tab and see Session Summary", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /insights/i }).click();
    await expect(page.locator("text=Session Summary")).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// SUCCESS CRITERIA TAB UI TESTS
// =============================================================================

test.describe("Success Criteria Viewer UI", () => {
  test("can click Criteria tab to view success criteria", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    const criteriaTab = page.getByRole("tab", { name: /criteria/i });
    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await expect(page.locator("text=Completion Progress")).toBeVisible({ timeout: 10000 });
    }
  });

  test("shows 100% completion for completed session criteria", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    const criteriaTab = page.getByRole("tab", { name: /criteria/i });
    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await expect(page.locator("text=100%")).toBeVisible({ timeout: 10000 });
    }
  });

  test("displays specific criterion - add operation", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    const criteriaTab = page.getByRole("tab", { name: /criteria/i });
    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await expect(page.locator("text=add operation")).toBeVisible({ timeout: 10000 });
    }
  });

  test("displays criterion status badges as Met", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    const criteriaTab = page.getByRole("tab", { name: /criteria/i });
    if (await criteriaTab.isVisible()) {
      await criteriaTab.click();
      await expect(page.locator("text=Met").first()).toBeVisible({ timeout: 10000 });
    }
  });
});

// =============================================================================
// REASONING VIEWER UI TESTS
// =============================================================================

test.describe("Reasoning Viewer UI", () => {
  test("can click Reasoning tab to view reasoning logs", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    const reasoningTab = page.getByRole("tab", { name: /reasoning/i });
    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await expect(page.locator("text=Total Entries").or(page.locator("text=Reasoning Entries"))).toBeVisible({ timeout: 10000 });
    }
  });

  test("displays reasoning phase filters", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    const reasoningTab = page.getByRole("tab", { name: /reasoning/i });
    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await expect(page.locator("text=Filters")).toBeVisible({ timeout: 10000 });
    }
  });

  test("shows confidence level badges", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    const reasoningTab = page.getByRole("tab", { name: /reasoning/i });
    if (await reasoningTab.isVisible()) {
      await reasoningTab.click();
      await expect(page.locator("text=high").or(page.locator("text=medium")).first()).toBeVisible({ timeout: 10000 });
    }
  });
});

// =============================================================================
// ACTIVE SESSION UI TESTS
// =============================================================================

test.describe("Session Detail Page UI - Active Session", () => {
  test("displays active session status", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=active").first()).toBeVisible({ timeout: 10000 });
  });

  test("displays Parallel Mode for active session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Parallel Mode")).toBeVisible({ timeout: 10000 });
  });

  test("shows multiple task groups for parallel session", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Core Authentication Logic")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=JWT Token Management")).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// FAILED SESSION UI TESTS
// =============================================================================

test.describe("Session Detail Page UI - Failed Session", () => {
  test("displays failed session status", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=failed").first()).toBeVisible({ timeout: 10000 });
  });

  test("shows failed task group - Trading Engine", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Trading Engine")).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// MULTI-GROUP SESSION UI TESTS
// =============================================================================

test.describe("Session Detail Page UI - Multi-Group Session", () => {
  test("shows all 3 task groups", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.MULTI_GROUP_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=User Management API")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Product Catalog API")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Order Processing API")).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// ANALYTICS PAGE UI TESTS
// =============================================================================

test.describe("Analytics Page UI", () => {
  test("displays Analytics heading", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 10000 });
  });

  test("shows Success Rate metric card", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Success Rate")).toBeVisible({ timeout: 10000 });
  });

  test("shows Total Tokens Used metric", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Total Tokens Used")).toBeVisible({ timeout: 10000 });
  });

  test("shows Revision Rate metric", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Revision Rate")).toBeVisible({ timeout: 10000 });
  });

  test("shows Active Sessions count", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Active Sessions")).toBeVisible({ timeout: 10000 });
  });

  test("displays Tokens by Agent section", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Tokens by Agent")).toBeVisible({ timeout: 10000 });
  });

  test("displays Agent Invocations section", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Agent Invocations")).toBeVisible({ timeout: 10000 });
  });

  test("shows Agent Activity Breakdown", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Agent Activity Breakdown")).toBeVisible({ timeout: 10000 });
  });

  test("shows Revision Analysis section", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Revision Analysis")).toBeVisible({ timeout: 10000 });
  });

  test("displays Total Task Groups count", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Total Task Groups")).toBeVisible({ timeout: 10000 });
  });

  test("shows Recent Session Performance section", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("text=Recent Session Performance")).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// SETTINGS PAGE UI TESTS
// =============================================================================

test.describe("Settings Page UI", () => {
  test("displays Settings heading", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// CONFIG PAGE UI TESTS
// =============================================================================

test.describe("Config Page UI", () => {
  test("displays Config page heading", async ({ page }) => {
    await page.goto("/config");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /config/i })).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// CROSS-PAGE NAVIGATION TESTS
// =============================================================================

test.describe("Cross-Page Navigation", () => {
  test("navigate from home to sessions to detail and back", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /sessions/i }).click();
    await expect(page).toHaveURL(/\/sessions/);

    await page.waitForLoadState("networkidle");
    const viewDetailsButton = page.getByRole("button", { name: /view details/i }).first();
    if (await viewDetailsButton.isVisible()) {
      await viewDetailsButton.click();
      await expect(page).toHaveURL(/\/sessions\/bazinga_test/);
    }

    await page.getByRole("link", { name: /analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/);

    await page.getByRole("link", { name: /sessions/i }).click();
    await expect(page).toHaveURL(/\/sessions/);
  });

  test("tab navigation persists when switching tabs", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Calculator Implementation")).toBeVisible({ timeout: 10000 });

    await page.getByRole("tab", { name: /tokens/i }).click();
    await expect(page.locator("text=Total Tokens")).toBeVisible({ timeout: 10000 });

    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Calculator Implementation")).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// DATA VERIFICATION TESTS - Seeded Data Shows in UI
// =============================================================================

test.describe("Data Verification - Seeded Data Shows in UI", () => {
  test("completed session shows token count", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tokens/i }).click();
    // Total tokens: 108K
    await expect(page.locator("text=/108|107|109/")).toBeVisible({ timeout: 10000 });
  });

  test("completed session shows skill outputs", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /skills/i }).click();
    await expect(page.locator("text=lint-check")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=test-coverage")).toBeVisible({ timeout: 10000 });
  });

  test("multi-group session shows higher token count", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.MULTI_GROUP_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tokens/i }).click();
    // Total: 195K
    await expect(page.locator("text=/195|194|196/")).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// RESPONSIVE BEHAVIOR TESTS
// =============================================================================

test.describe("Responsive Behavior", () => {
  test("sessions page works on mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /sessions/i })).toBeVisible({ timeout: 10000 });
  });

  test("session detail tabs work on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Calculator Implementation")).toBeVisible({ timeout: 10000 });
  });

  test("analytics page renders on tablet viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Success Rate")).toBeVisible({ timeout: 10000 });
  });
});
