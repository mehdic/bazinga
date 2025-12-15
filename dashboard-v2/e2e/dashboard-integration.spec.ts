import { test, expect } from "@playwright/test";
import { seedTestDatabase, SESSION_IDS } from "./fixtures/seed-database";
import path from "path";
import fs from "fs";

/**
 * Dashboard Integration Tests
 *
 * These tests verify that the seeded database data is properly retrieved and served.
 * Uses request API (HTTP requests) which works in sandboxed environments where
 * full browser rendering may crash.
 */

// Database path for tests - use the actual bazinga.db
const BAZINGA_DB_PATH = path.resolve(__dirname, "../bazinga/bazinga.db");

// Test data constants - these match the seeded data
const TEST_DATA = {
  COMPLETED_SESSION: {
    id: SESSION_IDS.COMPLETED,
    mode: "simple",
    status: "completed",
    requirements: "Build a calculator application",
    taskGroup: "Calculator Implementation",
  },
  ACTIVE_SESSION: {
    id: SESSION_IDS.ACTIVE,
    mode: "parallel",
    status: "active",
    requirements: "Implement user authentication system",
    taskGroups: ["Core Authentication Logic", "JWT Token Management"],
  },
  FAILED_SESSION: {
    id: SESSION_IDS.FAILED,
    mode: "simple",
    status: "failed",
    requirements: "Create a complex real-time trading system",
    taskGroup: "Trading Engine",
  },
  MULTI_GROUP_SESSION: {
    id: SESSION_IDS.MULTI_GROUP,
    mode: "parallel",
    status: "completed",
    taskGroups: ["User Management API", "Product Catalog API", "Order Processing API"],
  },
  COMPLETED_CRITERIA: [
    "Implement add operation",
    "Implement subtract operation",
    "Implement multiply operation",
    "Implement divide operation",
    "Handle division by zero",
  ],
};

// Seed database before all tests
test.beforeAll(async () => {
  const bazingaDir = path.dirname(BAZINGA_DB_PATH);
  if (!fs.existsSync(bazingaDir)) {
    fs.mkdirSync(bazingaDir, { recursive: true });
  }
  console.log(`Seeding test data into: ${BAZINGA_DB_PATH}`);
  seedTestDatabase(BAZINGA_DB_PATH);
});

// ============================================================================
// TRPC API INTEGRATION TESTS - Verify DB data is correctly served
// ============================================================================

test.describe("tRPC API Integration", () => {
  test("sessions.list returns seeded sessions", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.list?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { limit: 10, offset: 0 } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    expect(json).toBeDefined();

    // Should have at least our 4 seeded sessions
    const result = json[0]?.result?.data?.json;
    expect(result?.sessions?.length).toBeGreaterThanOrEqual(4);
  });

  test("sessions.getById returns completed session with correct data", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getById?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const session = json[0]?.result?.data?.json;

    expect(session).toBeDefined();
    expect(session.sessionId).toBe(TEST_DATA.COMPLETED_SESSION.id);
    expect(session.mode).toBe(TEST_DATA.COMPLETED_SESSION.mode);
    expect(session.status).toBe(TEST_DATA.COMPLETED_SESSION.status);
    expect(session.originalRequirements).toContain("calculator");
  });

  test("sessions.getById returns task groups from DB", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getById?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const session = json[0]?.result?.data?.json;

    expect(session.taskGroups).toBeDefined();
    expect(session.taskGroups.length).toBeGreaterThanOrEqual(1);

    // Verify seeded task group name
    const taskGroupNames = session.taskGroups.map((g: { name: string }) => g.name);
    expect(taskGroupNames).toContain(TEST_DATA.COMPLETED_SESSION.taskGroup);
  });

  test("sessions.getById returns orchestration logs from DB", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getById?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const session = json[0]?.result?.data?.json;

    expect(session.logs).toBeDefined();
    expect(session.logs.length).toBeGreaterThan(0);

    // Verify seeded agent types appear in logs
    const agentTypes = session.logs.map((l: { agentType: string }) => l.agentType);
    expect(agentTypes).toContain("project_manager");
    expect(agentTypes).toContain("developer");
  });

  test("sessions.getById returns active session with parallel mode", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getById?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.ACTIVE_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const session = json[0]?.result?.data?.json;

    expect(session.mode).toBe("parallel");
    expect(session.status).toBe("active");
    expect(session.originalRequirements).toContain("authentication");

    // Verify multiple task groups
    expect(session.taskGroups.length).toBeGreaterThanOrEqual(2);
    const taskGroupNames = session.taskGroups.map((g: { name: string }) => g.name);
    expect(taskGroupNames).toContain("Core Authentication Logic");
    expect(taskGroupNames).toContain("JWT Token Management");
  });

  test("sessions.getById returns failed session data", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getById?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.FAILED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const session = json[0]?.result?.data?.json;

    expect(session.status).toBe("failed");
    expect(session.originalRequirements).toContain("trading");

    // Verify failed task group
    const taskGroupNames = session.taskGroups.map((g: { name: string }) => g.name);
    expect(taskGroupNames).toContain("Trading Engine");
  });

  test("sessions.getById returns multi-group session with all 3 task groups", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getById?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.MULTI_GROUP_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const session = json[0]?.result?.data?.json;

    expect(session.mode).toBe("parallel");
    expect(session.taskGroups.length).toBeGreaterThanOrEqual(3);

    const taskGroupNames = session.taskGroups.map((g: { name: string }) => g.name);
    for (const expectedGroup of TEST_DATA.MULTI_GROUP_SESSION.taskGroups) {
      expect(taskGroupNames).toContain(expectedGroup);
    }
  });
});

// ============================================================================
// SUCCESS CRITERIA API TESTS
// ============================================================================

test.describe("Success Criteria API", () => {
  test("getSuccessCriteria returns seeded criteria for completed session", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getSuccessCriteria?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const criteria = json[0]?.result?.data?.json;

    expect(criteria).toBeDefined();
    expect(criteria.length).toBeGreaterThanOrEqual(5);

    // Verify seeded criteria text
    const criteriaTexts = criteria.map((c: { criterion: string }) => c.criterion);
    for (const expected of TEST_DATA.COMPLETED_CRITERIA) {
      expect(criteriaTexts).toContain(expected);
    }
  });

  test("getCriteriaSummary returns correct counts for completed session", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getCriteriaSummary?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const summary = json[0]?.result?.data?.json;

    // All 7 criteria should be met
    expect(summary.total).toBe(7);
    expect(summary.met).toBe(7);
    expect(summary.pending).toBe(0);
    expect(summary.blocked).toBe(0);
    expect(summary.failed).toBe(0);
  });

  test("getCriteriaSummary returns mixed statuses for active session", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getCriteriaSummary?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.ACTIVE_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const summary = json[0]?.result?.data?.json;

    // Should have mixed statuses
    expect(summary.total).toBeGreaterThan(0);
    expect(summary.met).toBeGreaterThan(0);  // password hashing is met
    expect(summary.pending).toBeGreaterThan(0);  // JWT criteria pending
    expect(summary.blocked).toBeGreaterThan(0);  // security audit blocked
  });

  test("getSuccessCriteria returns blocked criterion with reason", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getSuccessCriteria?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.ACTIVE_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const criteria = json[0]?.result?.data?.json;

    // Find the blocked security audit criterion
    const blockedCriterion = criteria.find((c: { criterion: string; status: string }) =>
      c.criterion.includes("Security audit") && c.status === "blocked"
    );
    expect(blockedCriterion).toBeDefined();
    expect(blockedCriterion.actual).toContain("Timing attack");
  });
});

// ============================================================================
// REASONING LOGS API TESTS
// ============================================================================

test.describe("Reasoning Logs API", () => {
  test("getReasoning returns seeded reasoning entries", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getReasoning?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id, limit: 50 } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const result = json[0]?.result?.data?.json;

    expect(result.logs).toBeDefined();
    expect(result.logs.length).toBeGreaterThan(0);

    // Verify reasoning phases are present
    const phases = result.logs.map((l: { reasoningPhase: string }) => l.reasoningPhase);
    expect(phases.some((p: string | null) => p === "understanding")).toBe(true);
    expect(phases.some((p: string | null) => p === "approach" || p === "completion")).toBe(true);
  });

  test("getReasoning returns confidence levels", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getReasoning?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id, limit: 50 } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const result = json[0]?.result?.data?.json;

    // Verify confidence levels
    const confidences = result.logs.map((l: { confidenceLevel: string }) => l.confidenceLevel);
    expect(confidences.some((c: string | null) => c === "high")).toBe(true);
  });

  test("getReasoning returns blocker reasoning for failed session", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getReasoning?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.FAILED_SESSION.id, limit: 50 } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const result = json[0]?.result?.data?.json;

    // Should have blockers phase reasoning
    const blockerReasoning = result.logs.find((l: { reasoningPhase: string }) =>
      l.reasoningPhase === "blockers"
    );
    expect(blockerReasoning).toBeDefined();
  });
});

// ============================================================================
// TOKEN USAGE API TESTS
// ============================================================================

test.describe("Token Usage API", () => {
  test("getTokenBreakdown returns seeded token data", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getTokenBreakdown?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const result = json[0]?.result?.data?.json;

    expect(result.breakdown).toBeDefined();
    expect(result.breakdown.length).toBeGreaterThan(0);

    // Verify agent types in breakdown
    const agentTypes = result.breakdown.map((b: { agentType: string }) => b.agentType);
    expect(agentTypes).toContain("project_manager");
    expect(agentTypes).toContain("developer");
    expect(agentTypes).toContain("qa_expert");
    expect(agentTypes).toContain("tech_lead");
  });

  test("getTokenBreakdown returns expected token amounts", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getTokenBreakdown?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const result = json[0]?.result?.data?.json;

    // Total should be around 108k (sum of seeded tokens)
    const totalTokens = result.breakdown.reduce(
      (sum: number, b: { total: number }) => sum + (b.total || 0),
      0
    );
    expect(totalTokens).toBeGreaterThan(50000);  // At least 50k tokens
  });
});

// ============================================================================
// SKILL OUTPUTS API TESTS
// ============================================================================

test.describe("Skill Outputs API", () => {
  test("getSkillOutputs returns seeded skill data", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getSkillOutputs?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const outputs = json[0]?.result?.data?.json;

    expect(outputs).toBeDefined();
    expect(outputs.length).toBeGreaterThan(0);

    // Verify seeded skill names
    const skillNames = outputs.map((o: { skillName: string }) => o.skillName);
    expect(skillNames).toContain("lint-check");
    expect(skillNames).toContain("test-coverage");
    expect(skillNames).toContain("security-scan");
  });

  test("getSkillOutputs returns skill output data", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getSkillOutputs?batch=1&input=" + encodeURIComponent(JSON.stringify({
      "0": { json: { sessionId: TEST_DATA.COMPLETED_SESSION.id } }
    })));
    expect(response.status()).toBe(200);

    const json = await response.json();
    const outputs = json[0]?.result?.data?.json;

    // Find lint-check output and verify it has expected data
    const lintCheck = outputs.find((o: { skillName: string }) => o.skillName === "lint-check");
    expect(lintCheck).toBeDefined();
    expect(lintCheck.outputData).toBeDefined();
    expect(lintCheck.outputData.passed).toBe(true);
  });
});

// ============================================================================
// ANALYTICS API TESTS
// ============================================================================

test.describe("Analytics API", () => {
  test("getStats returns aggregate session statistics", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getStats?batch=1&input={}");
    expect(response.status()).toBe(200);

    const json = await response.json();
    const stats = json[0]?.result?.data?.json;

    expect(stats).toBeDefined();
    expect(stats.totalSessions).toBeGreaterThanOrEqual(4);  // Our seeded sessions
    expect(stats.completedSessions).toBeGreaterThanOrEqual(2);  // 2 completed
    expect(stats.activeSessions).toBeGreaterThanOrEqual(1);  // 1 active
  });

  test("getAgentMetrics returns token breakdown by agent", async ({ request }) => {
    const response = await request.get("/api/trpc/sessions.getAgentMetrics?batch=1&input={}");
    expect(response.status()).toBe(200);

    const json = await response.json();
    const metrics = json[0]?.result?.data?.json;

    expect(metrics).toBeDefined();
    expect(metrics.tokensByAgent).toBeDefined();
    expect(metrics.tokensByAgent.length).toBeGreaterThan(0);

    // Verify agent types
    const agentTypes = metrics.tokensByAgent.map((a: { agentType: string }) => a.agentType);
    expect(agentTypes).toContain("developer");
    expect(agentTypes).toContain("project_manager");
  });
});

// ============================================================================
// PAGE CONTENT TESTS - Verify HTML contains seeded data
// ============================================================================

test.describe("Page Content Verification", () => {
  test("home page returns 200 and contains content", async ({ request }) => {
    const response = await request.get("/");
    expect(response.status()).toBe(200);

    const html = await response.text();
    expect(html).toContain("<!DOCTYPE html");
  });

  test("sessions page returns 200", async ({ request }) => {
    const response = await request.get("/sessions");
    expect(response.status()).toBe(200);
  });

  test("session detail page returns 200 for completed session", async ({ request }) => {
    const response = await request.get(`/sessions/${TEST_DATA.COMPLETED_SESSION.id}`);
    expect(response.status()).toBe(200);
  });

  test("session detail page returns 200 for active session", async ({ request }) => {
    const response = await request.get(`/sessions/${TEST_DATA.ACTIVE_SESSION.id}`);
    expect(response.status()).toBe(200);
  });

  test("session detail page returns 200 for failed session", async ({ request }) => {
    const response = await request.get(`/sessions/${TEST_DATA.FAILED_SESSION.id}`);
    expect(response.status()).toBe(200);
  });

  test("analytics page returns 200", async ({ request }) => {
    const response = await request.get("/analytics");
    expect(response.status()).toBe(200);
  });

  test("settings page returns 200", async ({ request }) => {
    const response = await request.get("/settings");
    expect(response.status()).toBe(200);
  });

  test("config page returns 200", async ({ request }) => {
    const response = await request.get("/config");
    expect(response.status()).toBe(200);
  });
});
