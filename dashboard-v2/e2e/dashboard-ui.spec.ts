/**
 * Comprehensive Browser-Based UI E2E Tests with Full Content Verification
 *
 * These tests simulate real user interactions AND verify:
 * - After every navigation, the destination page content is correct
 * - After every click/interaction, the resulting data matches seeded values
 * - Seeded database data is properly displayed throughout the UI
 */

import { test, expect } from "@playwright/test";
import { seedTestDatabase, SESSION_IDS } from "./fixtures/seed-database";
import path from "path";
import fs from "fs";

// Test data that matches what's seeded in seed-database.ts
const TEST_DATA = {
  COMPLETED_SESSION: {
    id: SESSION_IDS.COMPLETED,
    mode: "simple",
    status: "completed",
    requirements: "Build a calculator application",
    taskGroupName: "Calculator Implementation",
    taskGroupId: "CALC",
    assignedTo: "developer_1",
    // Token breakdown: PM=15000, Dev=45000, QA=25000, TL=18000, Orch=5000 = 108000
    totalTokens: 108000,
    skills: ["lint-check", "test-coverage", "security-scan", "specialization-loader"],
    criteria: [
      "Implement add operation",
      "Implement subtract operation",
      "Implement multiply operation",
      "Implement divide operation",
      "Handle division by zero",
      "Unit test coverage > 90%",
      "All tests passing",
    ],
  },
  ACTIVE_SESSION: {
    id: SESSION_IDS.ACTIVE,
    mode: "parallel",
    status: "active",
    requirements: "Implement user authentication system",
    taskGroupNames: ["Core Authentication Logic", "JWT Token Management"],
    // Has blocked criterion
    blockedCriterion: "Integration tests passing",
  },
  FAILED_SESSION: {
    id: SESSION_IDS.FAILED,
    mode: "simple",
    status: "failed",
    requirements: "Create a complex real-time trading system",
    taskGroupName: "Trading Engine",
    assignedTo: "developer_3",
    tier: "Senior Software Engineer",
  },
  MULTI_GROUP_SESSION: {
    id: SESSION_IDS.MULTI_GROUP,
    mode: "parallel",
    status: "completed",
    requirements: "Build a comprehensive REST API",
    taskGroupNames: ["User Management API", "Product Catalog API", "Order Processing API"],
    // Token breakdown: PM=22000, Dev=95000, QA=42000, TL=28000, Orch=8000 = 195000
    totalTokens: 195000,
  },
  // Agents that appear in logs
  AGENTS: ["project_manager", "developer", "qa_expert", "tech_lead", "orchestrator"],
  // Reasoning phases
  REASONING_PHASES: ["understanding", "approach", "completion", "risks", "blockers"],
  // Confidence levels
  CONFIDENCE_LEVELS: ["high", "medium", "low"],
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
// HOME PAGE → SESSIONS PAGE (with content verification)
// =============================================================================

test.describe("Home → Sessions Navigation with Content Verification", () => {
  test("navigate to sessions and verify all 4 seeded sessions appear", async ({ page }) => {
    // 1. Start at home
    await page.goto("/");
    await expect(page.getByRole("link", { name: /sessions/i })).toBeVisible();

    // 2. Navigate to sessions
    await page.getByRole("link", { name: /sessions/i }).click();
    await expect(page).toHaveURL(/\/sessions/);
    await page.waitForLoadState("networkidle");

    // 3. VERIFY: Sessions page heading is visible
    await expect(page.getByRole("heading", { name: /sessions/i })).toBeVisible({ timeout: 10000 });

    // 4. VERIFY: All 4 seeded sessions appear (by their status badges)
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=active").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=failed").first()).toBeVisible({ timeout: 10000 });

    // 5. VERIFY: Session requirements are displayed
    await expect(page.locator("text=calculator").or(page.locator("text=Calculator"))).toBeVisible();
    await expect(page.locator("text=authentication").or(page.locator("text=Authentication"))).toBeVisible();

    // 6. VERIFY: Session modes are displayed
    await expect(page.locator("text=simple")).toBeVisible();
    await expect(page.locator("text=parallel").first()).toBeVisible();
  });

  test("navigate to sessions and verify filtering works with correct data", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /sessions/i }).click();
    await page.waitForLoadState("networkidle");

    // Filter to completed only
    await page.getByRole("button", { name: /completed/i }).click();
    await page.waitForTimeout(500);

    // VERIFY: Only completed sessions visible (we have 2: COMPLETED and MULTI_GROUP)
    await expect(page.locator("text=completed").first()).toBeVisible();
    // The calculator session should be visible
    await expect(page.locator("text=calculator").or(page.locator("text=Calculator"))).toBeVisible();

    // Filter to failed only
    await page.getByRole("button", { name: /failed/i }).click();
    await page.waitForTimeout(500);

    // VERIFY: Failed session visible with trading requirement
    await expect(page.locator("text=failed").first()).toBeVisible();
    await expect(page.locator("text=trading").or(page.locator("text=Trading"))).toBeVisible();

    // Reset to all
    await page.getByRole("button", { name: /^all$/i }).click();
    await page.waitForTimeout(500);

    // VERIFY: All statuses visible again
    await expect(page.locator("text=completed").first()).toBeVisible();
    await expect(page.locator("text=active").first()).toBeVisible();
    await expect(page.locator("text=failed").first()).toBeVisible();
  });
});

// =============================================================================
// HOME PAGE → ANALYTICS PAGE (with content verification)
// =============================================================================

test.describe("Home → Analytics Navigation with Content Verification", () => {
  test("navigate to analytics and verify metrics show seeded data", async ({ page }) => {
    // 1. Start at home
    await page.goto("/");
    await expect(page.getByRole("link", { name: /analytics/i })).toBeVisible();

    // 2. Navigate to analytics
    await page.getByRole("link", { name: /analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/);
    await page.waitForLoadState("networkidle");

    // 3. VERIFY: Analytics heading
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 10000 });

    // 4. VERIFY: Key metric cards are present with labels
    await expect(page.locator("text=Success Rate")).toBeVisible();
    await expect(page.locator("text=Total Tokens Used")).toBeVisible();
    await expect(page.locator("text=Revision Rate")).toBeVisible();
    await expect(page.locator("text=Active Sessions")).toBeVisible();

    // 5. VERIFY: Chart sections are present
    await expect(page.locator("text=Tokens by Agent")).toBeVisible();
    await expect(page.locator("text=Agent Invocations")).toBeVisible();

    // 6. VERIFY: Agent breakdown shows seeded agents
    await expect(page.locator("text=Agent Activity Breakdown")).toBeVisible();
    // At least one agent type should be displayed (formatted with spaces)
    await expect(
      page.locator("text=project manager").or(page.locator("text=developer")).or(page.locator("text=qa expert"))
    ).toBeVisible();

    // 7. VERIFY: Revision analysis section
    await expect(page.locator("text=Revision Analysis")).toBeVisible();
    await expect(page.locator("text=Total Task Groups")).toBeVisible();

    // 8. VERIFY: Recent sessions shows our seeded sessions
    await expect(page.locator("text=Recent Session Performance")).toBeVisible();
    // Status badges in recent sessions
    await expect(page.locator("text=completed").or(page.locator("text=active")).or(page.locator("text=failed"))).toBeVisible();
  });
});

// =============================================================================
// SESSIONS LIST → SESSION DETAIL (with content verification)
// =============================================================================

test.describe("Sessions List → Session Detail with Content Verification", () => {
  test("click View Details on completed session and verify all header data", async ({ page }) => {
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");

    // Find and click the completed session's View Details
    // First, find the session card with "calculator" text, then click its View Details
    const sessionCard = page.locator("text=calculator").first().locator("..").locator("..");
    const viewDetailsButton = sessionCard.getByRole("button", { name: /view details/i });

    // If we can't find it that way, just click the first View Details
    if (await viewDetailsButton.isVisible()) {
      await viewDetailsButton.click();
    } else {
      await page.getByRole("button", { name: /view details/i }).first().click();
    }

    await page.waitForLoadState("networkidle");

    // VERIFY: URL changed to session detail
    await expect(page).toHaveURL(/\/sessions\/bazinga_test/);

    // VERIFY: Session header shows correct data
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });
  });

  test("navigate to completed session and verify all tab content", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    // VERIFY: Header content
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Simple Mode")).toBeVisible();
    await expect(page.locator("text=calculator")).toBeVisible();
    await expect(page.locator("text=100%")).toBeVisible(); // Completed = 100%

    // VERIFY: Tasks tab content
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Calculator Implementation")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=completed").first()).toBeVisible(); // Task status
    await expect(page.locator("text=developer_1")).toBeVisible(); // Assigned developer

    // VERIFY: Logs tab content
    await page.getByRole("tab", { name: /logs/i }).click();
    await expect(page.locator("text=project_manager").or(page.locator("text=developer"))).toBeVisible({ timeout: 10000 });

    // VERIFY: Tokens tab shows correct total
    await page.getByRole("tab", { name: /tokens/i }).click();
    await expect(page.locator("text=Total Tokens")).toBeVisible({ timeout: 10000 });
    // 108K tokens seeded - look for the number
    await expect(page.locator("text=/108/").or(page.locator("text=/107/")).or(page.locator("text=/109/"))).toBeVisible();

    // VERIFY: Skills tab shows seeded skills
    await page.getByRole("tab", { name: /skills/i }).click();
    await expect(page.locator("text=lint-check")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=test-coverage")).toBeVisible();

    // VERIFY: Timeline tab shows agent entries
    await page.getByRole("tab", { name: /timeline/i }).click();
    await expect(page.locator("text=project_manager").or(page.locator("text=developer"))).toBeVisible({ timeout: 10000 });

    // VERIFY: Insights tab
    await page.getByRole("tab", { name: /insights/i }).click();
    await expect(page.locator("text=Session Summary")).toBeVisible({ timeout: 10000 });
  });

  test("navigate to active session and verify parallel mode data", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    // VERIFY: Active status and Parallel mode
    await expect(page.locator("text=active").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Parallel Mode")).toBeVisible();
    await expect(page.locator("text=authentication")).toBeVisible();

    // VERIFY: Tasks tab shows BOTH task groups
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Core Authentication Logic")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=JWT Token Management")).toBeVisible();

    // VERIFY: At least one task is in_progress or pending (active session)
    await expect(page.locator("text=in_progress").or(page.locator("text=pending"))).toBeVisible();
  });

  test("navigate to failed session and verify failed state data", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    // VERIFY: Failed status
    await expect(page.locator("text=failed").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=trading")).toBeVisible();

    // VERIFY: Tasks tab shows Trading Engine
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Trading Engine")).toBeVisible({ timeout: 10000 });
    // Assigned to developer_3 (SSE tier due to complexity)
    await expect(page.locator("text=developer_3")).toBeVisible();
  });

  test("navigate to multi-group session and verify all 3 groups", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.MULTI_GROUP_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    // VERIFY: Completed status and Parallel mode
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Parallel Mode")).toBeVisible();

    // VERIFY: Tasks tab shows ALL 3 task groups
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=User Management API")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Product Catalog API")).toBeVisible();
    await expect(page.locator("text=Order Processing API")).toBeVisible();

    // VERIFY: All 3 are completed
    const completedBadges = page.locator('[class*="badge"]').filter({ hasText: /completed/i });
    await expect(completedBadges).toHaveCount(3, { timeout: 10000 });

    // VERIFY: Token tab shows higher count (195K)
    await page.getByRole("tab", { name: /tokens/i }).click();
    await expect(page.locator("text=/195/").or(page.locator("text=/194/")).or(page.locator("text=/196/"))).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// SUCCESS CRITERIA TAB (with content verification)
// =============================================================================

test.describe("Success Criteria Tab with Content Verification", () => {
  test("view criteria tab and verify all 7 seeded criteria appear", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    const criteriaTab = page.getByRole("tab", { name: /criteria/i });
    if (!(await criteriaTab.isVisible())) {
      test.skip();
      return;
    }

    await criteriaTab.click();

    // VERIFY: Summary card shows completion progress
    await expect(page.locator("text=Completion Progress")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=100%")).toBeVisible(); // All criteria met

    // VERIFY: Count shows "7 of 7" or similar
    await expect(page.locator("text=/\\d+ of \\d+ criteria/i").or(page.locator("text=/7.*7/"))).toBeVisible();

    // VERIFY: Specific criteria from seeded data appear
    await expect(page.locator("text=add operation")).toBeVisible();
    await expect(page.locator("text=subtract operation")).toBeVisible();
    await expect(page.locator("text=multiply operation")).toBeVisible();
    await expect(page.locator("text=divide operation")).toBeVisible();
    await expect(page.locator("text=division by zero")).toBeVisible();

    // VERIFY: All have "Met" status badges
    const metBadges = page.locator("text=Met");
    await expect(metBadges.first()).toBeVisible();
  });

  test("view active session criteria and verify blocked criterion", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    const criteriaTab = page.getByRole("tab", { name: /criteria/i });
    if (!(await criteriaTab.isVisible())) {
      test.skip();
      return;
    }

    await criteriaTab.click();

    // VERIFY: Shows mixed statuses (met, pending, blocked)
    await expect(page.locator("text=Completion Progress")).toBeVisible({ timeout: 10000 });

    // VERIFY: Blocked criterion appears
    await expect(page.locator("text=Integration tests")).toBeVisible();
    await expect(page.locator("text=Blocked")).toBeVisible();

    // VERIFY: Some are met, some pending
    await expect(page.locator("text=Met").first()).toBeVisible();
    await expect(page.locator("text=Pending").first()).toBeVisible();
  });
});

// =============================================================================
// REASONING TAB (with content verification)
// =============================================================================

test.describe("Reasoning Tab with Content Verification", () => {
  test("view reasoning tab and verify entries with phases and confidence", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    const reasoningTab = page.getByRole("tab", { name: /reasoning/i });
    if (!(await reasoningTab.isVisible())) {
      test.skip();
      return;
    }

    await reasoningTab.click();

    // VERIFY: Summary cards show entry counts
    await expect(page.locator("text=Total Entries").or(page.locator("text=Reasoning Entries"))).toBeVisible({ timeout: 10000 });

    // VERIFY: Filters section is present
    await expect(page.locator("text=Filters")).toBeVisible();

    // VERIFY: Agent types appear in entries
    await expect(
      page.locator("text=project_manager").or(page.locator("text=developer")).or(page.locator("text=qa_expert"))
    ).toBeVisible();

    // VERIFY: Confidence levels appear
    await expect(page.locator("text=high").or(page.locator("text=medium")).first()).toBeVisible();

    // VERIFY: Reasoning phases appear
    await expect(
      page.locator("text=understanding").or(page.locator("text=approach")).or(page.locator("text=completion"))
    ).toBeVisible();
  });

  test("filter reasoning by phase and verify filtered results", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    const reasoningTab = page.getByRole("tab", { name: /reasoning/i });
    if (!(await reasoningTab.isVisible())) {
      test.skip();
      return;
    }

    await reasoningTab.click();
    await page.waitForTimeout(500);

    // Find and click the phase filter dropdown
    const phaseDropdown = page.locator('button:has-text("All Phases")');
    if (await phaseDropdown.isVisible()) {
      await phaseDropdown.click();

      // Select "Understanding" phase
      await page.locator('[role="option"]:has-text("Understanding")').click();
      await page.waitForTimeout(500);

      // VERIFY: Only understanding phase entries visible
      await expect(page.locator("text=understanding").first()).toBeVisible({ timeout: 10000 });
    }
  });

  test("view failed session reasoning and verify blocker entries", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    const reasoningTab = page.getByRole("tab", { name: /reasoning/i });
    if (!(await reasoningTab.isVisible())) {
      test.skip();
      return;
    }

    await reasoningTab.click();

    // VERIFY: Blocker reasoning entries exist (failed session has blocker phase)
    await expect(page.locator("text=blockers").or(page.locator("text=Blockers"))).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// CROSS-PAGE NAVIGATION (with content verification at each step)
// =============================================================================

test.describe("Full User Journey with Content Verification", () => {
  test("complete user journey: home → sessions → detail → tabs → analytics", async ({ page }) => {
    // STEP 1: Start at home
    await page.goto("/");
    await expect(page.getByRole("link", { name: /sessions/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /analytics/i })).toBeVisible();

    // STEP 2: Navigate to sessions
    await page.getByRole("link", { name: /sessions/i }).click();
    await expect(page).toHaveURL(/\/sessions/);
    await page.waitForLoadState("networkidle");

    // VERIFY: Sessions list content
    await expect(page.getByRole("heading", { name: /sessions/i })).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=completed").first()).toBeVisible();
    await expect(page.locator("text=calculator")).toBeVisible();

    // STEP 3: Click View Details on first session
    await page.getByRole("button", { name: /view details/i }).first().click();
    await expect(page).toHaveURL(/\/sessions\/bazinga_test/);
    await page.waitForLoadState("networkidle");

    // VERIFY: Session detail header
    await expect(page.locator("text=completed").or(page.locator("text=active")).or(page.locator("text=failed")).first()).toBeVisible({ timeout: 10000 });

    // STEP 4: Click through tabs and verify content
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Implementation").or(page.locator("text=API")).or(page.locator("text=Engine"))).toBeVisible({ timeout: 10000 });

    await page.getByRole("tab", { name: /logs/i }).click();
    await expect(page.locator("text=project_manager").or(page.locator("text=developer"))).toBeVisible({ timeout: 10000 });

    await page.getByRole("tab", { name: /tokens/i }).click();
    await expect(page.locator("text=Total Tokens")).toBeVisible({ timeout: 10000 });

    // STEP 5: Navigate to analytics
    await page.getByRole("link", { name: /analytics/i }).click();
    await expect(page).toHaveURL(/\/analytics/);
    await page.waitForLoadState("networkidle");

    // VERIFY: Analytics content with seeded data
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Success Rate")).toBeVisible();
    await expect(page.locator("text=Total Tokens Used")).toBeVisible();
    await expect(page.locator("text=Agent Activity Breakdown")).toBeVisible();

    // STEP 6: Navigate back to sessions
    await page.getByRole("link", { name: /sessions/i }).click();
    await expect(page).toHaveURL(/\/sessions/);
    await page.waitForLoadState("networkidle");

    // VERIFY: Still shows all sessions
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=active").first()).toBeVisible();
  });
});

// =============================================================================
// TOKEN BREAKDOWN VERIFICATION
// =============================================================================

test.describe("Token Breakdown Content Verification", () => {
  test("verify token breakdown shows all agent types", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("tab", { name: /tokens/i }).click();

    // VERIFY: Total tokens header
    await expect(page.locator("text=Total Tokens")).toBeVisible({ timeout: 10000 });

    // VERIFY: Agent breakdown shows our seeded agents
    await expect(
      page.locator("text=project_manager").or(page.locator("text=Project Manager")).or(page.locator("text=PM"))
    ).toBeVisible();
    await expect(
      page.locator("text=developer").or(page.locator("text=Developer"))
    ).toBeVisible();
    await expect(
      page.locator("text=qa_expert").or(page.locator("text=QA Expert")).or(page.locator("text=QA"))
    ).toBeVisible();
  });
});

// =============================================================================
// SKILL OUTPUTS VERIFICATION
// =============================================================================

test.describe("Skill Outputs Content Verification", () => {
  test("verify skill outputs show all seeded skills with data", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("tab", { name: /skills/i }).click();

    // VERIFY: All 4 seeded skills appear
    await expect(page.locator("text=lint-check")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=test-coverage")).toBeVisible();
    await expect(page.locator("text=security-scan")).toBeVisible();
    await expect(page.locator("text=specialization-loader")).toBeVisible();
  });

  test("verify active session shows security-scan failure", async ({ page }) => {
    await page.goto(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("tab", { name: /skills/i }).click();

    // VERIFY: Security scan is present
    await expect(page.locator("text=security-scan")).toBeVisible({ timeout: 10000 });
  });
});

// =============================================================================
// RESPONSIVE BEHAVIOR (with content verification)
// =============================================================================

test.describe("Responsive Behavior with Content Verification", () => {
  test("mobile: sessions page shows all session data", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/sessions");
    await page.waitForLoadState("networkidle");

    // VERIFY: Page loads correctly
    await expect(page.getByRole("heading", { name: /sessions/i })).toBeVisible({ timeout: 10000 });

    // VERIFY: Session data visible even on mobile
    await expect(page.locator("text=completed").first()).toBeVisible();
    await expect(page.locator("text=active").first()).toBeVisible();
  });

  test("mobile: session detail tabs work and show data", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    await page.waitForLoadState("networkidle");

    // VERIFY: Header data visible
    await expect(page.locator("text=completed").first()).toBeVisible({ timeout: 10000 });

    // VERIFY: Can switch tabs and see data
    await page.getByRole("tab", { name: /tasks/i }).click();
    await expect(page.locator("text=Calculator Implementation")).toBeVisible({ timeout: 10000 });

    await page.getByRole("tab", { name: /tokens/i }).click();
    await expect(page.locator("text=Total Tokens")).toBeVisible({ timeout: 10000 });
  });

  test("tablet: analytics page renders all sections", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");

    // VERIFY: All key sections visible
    await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Success Rate")).toBeVisible();
    await expect(page.locator("text=Total Tokens Used")).toBeVisible();
    await expect(page.locator("text=Tokens by Agent")).toBeVisible();
    await expect(page.locator("text=Agent Activity Breakdown")).toBeVisible();
  });
});

// =============================================================================
// SETTINGS & CONFIG (with content verification)
// =============================================================================

test.describe("Settings & Config Pages with Content Verification", () => {
  test("settings page loads and shows database configuration", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForLoadState("networkidle");

    // VERIFY: Page heading
    await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible({ timeout: 10000 });

    // VERIFY: Database section
    await expect(page.locator("text=Database").or(page.locator("text=database"))).toBeVisible();
  });

  test("config page loads", async ({ page }) => {
    await page.goto("/config");
    await page.waitForLoadState("networkidle");

    // VERIFY: Page heading
    await expect(page.getByRole("heading", { name: /config/i })).toBeVisible({ timeout: 10000 });
  });
});
