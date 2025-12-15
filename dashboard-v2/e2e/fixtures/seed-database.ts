/**
 * Database Seeder for E2E Tests
 *
 * Creates realistic orchestration data for testing all dashboard features.
 * This seeder creates multiple sessions with varying states to test:
 * - Active, completed, and failed sessions
 * - Multiple task groups with different statuses
 * - Orchestration logs with reasoning entries
 * - Success criteria with various states
 * - Token usage data
 * - Skill outputs
 */

import Database from "better-sqlite3";
import path from "path";

// Test data constants
export const SESSION_IDS = {
  COMPLETED: "bazinga_test_completed_001",
  ACTIVE: "bazinga_test_active_002",
  FAILED: "bazinga_test_failed_003",
  MULTI_GROUP: "bazinga_test_multigroup_004",
};

const AGENT_TYPES = ["project_manager", "developer", "qa_expert", "tech_lead", "orchestrator"];

function getTimestamp(offsetMinutes: number = 0): string {
  const date = new Date();
  date.setMinutes(date.getMinutes() - offsetMinutes);
  return date.toISOString();
}

export function seedTestDatabase(dbPath: string): void {
  const db = new Database(dbPath);

  // Enable foreign keys
  db.pragma("foreign_keys = ON");

  // Create tables if they don't exist
  createTables(db);

  // Clean existing test data
  cleanTestData(db);

  // Seed fresh test data
  seedSessions(db);
  seedTaskGroups(db);
  seedOrchestrationLogs(db);
  seedTokenUsage(db);
  seedSuccessCriteria(db);
  seedSkillOutputs(db);
  seedContextPackages(db);

  db.close();
  console.log("✓ Test database seeded successfully");
}

/**
 * Create all necessary tables for the dashboard
 * Uses IF NOT EXISTS to be idempotent
 */
function createTables(db: Database.Database): void {
  // Sessions table
  db.exec(`
    CREATE TABLE IF NOT EXISTS sessions (
      session_id TEXT PRIMARY KEY,
      start_time TEXT,
      end_time TEXT,
      mode TEXT,
      original_requirements TEXT,
      status TEXT DEFAULT 'active',
      initial_branch TEXT DEFAULT 'main',
      metadata TEXT,
      created_at TEXT
    )
  `);

  // Orchestration logs table
  db.exec(`
    CREATE TABLE IF NOT EXISTS orchestration_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      timestamp TEXT,
      iteration INTEGER,
      agent_type TEXT NOT NULL,
      agent_id TEXT,
      content TEXT NOT NULL,
      log_type TEXT DEFAULT 'interaction',
      reasoning_phase TEXT,
      confidence_level TEXT,
      references_json TEXT,
      redacted INTEGER DEFAULT 0,
      group_id TEXT,
      event_subtype TEXT,
      event_payload TEXT
    )
  `);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_logs_session_id ON orchestration_logs(session_id)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON orchestration_logs(timestamp)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_logs_reasoning ON orchestration_logs(session_id, log_type, reasoning_phase)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_logs_events ON orchestration_logs(session_id, log_type, event_subtype)`);

  // Task groups table
  db.exec(`
    CREATE TABLE IF NOT EXISTS task_groups (
      id TEXT NOT NULL,
      session_id TEXT NOT NULL,
      name TEXT NOT NULL,
      status TEXT DEFAULT 'pending',
      assigned_to TEXT,
      revision_count INTEGER DEFAULT 0,
      last_review_status TEXT,
      complexity INTEGER,
      initial_tier TEXT CHECK(initial_tier IS NULL OR initial_tier IN ('Developer', 'Senior Software Engineer')),
      feature_branch TEXT,
      merge_status TEXT,
      context_references TEXT,
      specializations TEXT,
      item_count INTEGER DEFAULT 1,
      created_at TEXT,
      updated_at TEXT,
      PRIMARY KEY (id, session_id)
    )
  `);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_groups_session_id ON task_groups(session_id)`);

  // Token usage table
  db.exec(`
    CREATE TABLE IF NOT EXISTS token_usage (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      timestamp TEXT,
      agent_type TEXT NOT NULL,
      agent_id TEXT,
      tokens_estimated INTEGER NOT NULL
    )
  `);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_tokens_session_id ON token_usage(session_id)`);

  // State snapshots table
  db.exec(`
    CREATE TABLE IF NOT EXISTS state_snapshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      timestamp TEXT,
      state_type TEXT NOT NULL,
      state_data TEXT NOT NULL
    )
  `);

  // Skill outputs table
  db.exec(`
    CREATE TABLE IF NOT EXISTS skill_outputs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      timestamp TEXT,
      skill_name TEXT NOT NULL,
      output_data TEXT NOT NULL,
      agent_type TEXT,
      group_id TEXT,
      iteration INTEGER DEFAULT 1
    )
  `);
  db.exec(`CREATE UNIQUE INDEX IF NOT EXISTS idx_skill_unique ON skill_outputs(session_id, skill_name, agent_type, group_id, iteration)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_skill_session ON skill_outputs(session_id)`);

  // Success criteria table
  db.exec(`
    CREATE TABLE IF NOT EXISTS success_criteria (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      criterion TEXT NOT NULL,
      status TEXT DEFAULT 'pending',
      actual TEXT,
      evidence TEXT,
      required_for_completion INTEGER DEFAULT 1,
      created_at TEXT,
      updated_at TEXT
    )
  `);
  db.exec(`CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_criterion ON success_criteria(session_id, criterion)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_criteria_session_status ON success_criteria(session_id, status)`);

  // Context packages table
  db.exec(`
    CREATE TABLE IF NOT EXISTS context_packages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      group_id TEXT,
      package_type TEXT NOT NULL,
      file_path TEXT NOT NULL,
      producer_agent TEXT NOT NULL,
      priority TEXT NOT NULL DEFAULT 'medium',
      summary TEXT NOT NULL,
      size_bytes INTEGER,
      version INTEGER DEFAULT 1,
      supersedes_id INTEGER,
      scope TEXT DEFAULT 'group',
      created_at TEXT
    )
  `);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_cp_session ON context_packages(session_id)`);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_packages_priority_ranking ON context_packages(session_id, priority, created_at)`);

  // Context package consumers table
  db.exec(`
    CREATE TABLE IF NOT EXISTS context_package_consumers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      package_id INTEGER NOT NULL,
      agent_type TEXT NOT NULL,
      consumed_at TEXT,
      iteration INTEGER DEFAULT 1
    )
  `);
  db.exec(`CREATE INDEX IF NOT EXISTS idx_consumers_package ON context_package_consumers(package_id)`);

  // Schema version table (for capability detection)
  db.exec(`
    CREATE TABLE IF NOT EXISTS schema_version (
      version INTEGER PRIMARY KEY
    )
  `);
  // Insert version 12 if not exists
  db.exec(`INSERT OR IGNORE INTO schema_version (version) VALUES (12)`);
}

function cleanTestData(db: Database.Database): void {
  const testSessionIds = Object.values(SESSION_IDS);
  const placeholders = testSessionIds.map(() => "?").join(", ");

  // Helper to safely delete from a table (ignores if table doesn't exist)
  const safeDelete = (sql: string) => {
    try {
      db.prepare(sql).run(...testSessionIds);
    } catch {
      // Table doesn't exist yet, that's OK
    }
  };

  // Delete in order respecting foreign key constraints
  safeDelete(`DELETE FROM context_package_consumers WHERE package_id IN (SELECT id FROM context_packages WHERE session_id IN (${placeholders}))`);
  safeDelete(`DELETE FROM context_packages WHERE session_id IN (${placeholders})`);
  safeDelete(`DELETE FROM skill_outputs WHERE session_id IN (${placeholders})`);
  safeDelete(`DELETE FROM success_criteria WHERE session_id IN (${placeholders})`);
  safeDelete(`DELETE FROM token_usage WHERE session_id IN (${placeholders})`);
  safeDelete(`DELETE FROM orchestration_logs WHERE session_id IN (${placeholders})`);
  safeDelete(`DELETE FROM task_groups WHERE session_id IN (${placeholders})`);
  safeDelete(`DELETE FROM state_snapshots WHERE session_id IN (${placeholders})`);
  safeDelete(`DELETE FROM sessions WHERE session_id IN (${placeholders})`);
}

function seedSessions(db: Database.Database): void {
  const insert = db.prepare(`
    INSERT INTO sessions (session_id, start_time, end_time, mode, original_requirements, status, initial_branch, metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // 1. Completed session
  insert.run(
    SESSION_IDS.COMPLETED,
    getTimestamp(120), // Started 2 hours ago
    getTimestamp(60),  // Ended 1 hour ago
    "simple",
    "Build a calculator application with add, subtract, multiply, divide operations. Include comprehensive unit tests.",
    "completed",
    "main",
    JSON.stringify({ original_scope: "calculator_app", pm_bazinga_sent: true }),
    getTimestamp(120)
  );

  // 2. Active session
  insert.run(
    SESSION_IDS.ACTIVE,
    getTimestamp(30), // Started 30 minutes ago
    null,
    "parallel",
    "Implement user authentication system with JWT tokens, password hashing, and role-based access control.",
    "active",
    "feature/auth",
    JSON.stringify({ original_scope: "auth_system" }),
    getTimestamp(30)
  );

  // 3. Failed session
  insert.run(
    SESSION_IDS.FAILED,
    getTimestamp(180), // Started 3 hours ago
    getTimestamp(150), // Failed 2.5 hours ago
    "simple",
    "Create a complex real-time trading system with websocket support.",
    "failed",
    "main",
    JSON.stringify({ failure_reason: "complexity_exceeded" }),
    getTimestamp(180)
  );

  // 4. Multi-group parallel session
  insert.run(
    SESSION_IDS.MULTI_GROUP,
    getTimestamp(90),
    getTimestamp(15),
    "parallel",
    "Build a REST API with user management, product catalog, and order processing modules.",
    "completed",
    "develop",
    JSON.stringify({ original_scope: "rest_api", parallel_count: 3 }),
    getTimestamp(90)
  );
}

function seedTaskGroups(db: Database.Database): void {
  const insert = db.prepare(`
    INSERT INTO task_groups (id, session_id, name, status, assigned_to, revision_count, last_review_status, complexity, initial_tier, feature_branch, merge_status, context_references, specializations, item_count, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // NOTE: initial_tier has CHECK constraint: IN ('Developer', 'Senior Software Engineer')

  // Completed session - single group
  insert.run(
    "CALC",
    SESSION_IDS.COMPLETED,
    "Calculator Implementation",
    "completed",
    "developer_1",
    0,
    "approved",
    5,
    "Developer",  // Must be 'Developer' or 'Senior Software Engineer'
    "feature/calculator",
    "merged",
    JSON.stringify(["ctx_1", "ctx_2"]),
    JSON.stringify(["python", "testing"]),
    4,
    getTimestamp(120),
    getTimestamp(60)
  );

  // Active session - multiple groups in progress
  insert.run(
    "AUTH-CORE",
    SESSION_IDS.ACTIVE,
    "Core Authentication Logic",
    "in_progress",
    "developer_2",
    1,
    "needs_revision",
    7,
    "Developer",
    "feature/auth-core",
    "pending",
    JSON.stringify(["ctx_3"]),
    JSON.stringify(["python", "security"]),
    3,
    getTimestamp(30),
    getTimestamp(5)
  );

  insert.run(
    "AUTH-JWT",
    SESSION_IDS.ACTIVE,
    "JWT Token Management",
    "pending",
    null,
    0,
    null,
    6,
    "Developer",
    null,
    null,
    null,
    JSON.stringify(["python", "jwt"]),
    2,
    getTimestamp(30),
    getTimestamp(30)
  );

  // Failed session - blocked group (escalated to SSE)
  insert.run(
    "TRADING",
    SESSION_IDS.FAILED,
    "Trading Engine",
    "failed",
    "developer_3",
    3,
    "blocked",
    10,
    "Senior Software Engineer",  // Complex task escalated to SSE
    "feature/trading",
    null,
    null,
    JSON.stringify(["python", "websockets"]),
    5,
    getTimestamp(180),
    getTimestamp(150)
  );

  // Multi-group session - completed groups
  insert.run(
    "API-USERS",
    SESSION_IDS.MULTI_GROUP,
    "User Management API",
    "completed",
    "developer_1",
    0,
    "approved",
    4,
    "Developer",
    "feature/api-users",
    "merged",
    JSON.stringify(["ctx_4"]),
    JSON.stringify(["python", "rest"]),
    3,
    getTimestamp(90),
    getTimestamp(45)
  );

  insert.run(
    "API-PRODUCTS",
    SESSION_IDS.MULTI_GROUP,
    "Product Catalog API",
    "completed",
    "developer_2",
    1,
    "approved",
    5,
    "Developer",
    "feature/api-products",
    "merged",
    JSON.stringify(["ctx_5"]),
    JSON.stringify(["python", "rest"]),
    4,
    getTimestamp(90),
    getTimestamp(30)
  );

  insert.run(
    "API-ORDERS",
    SESSION_IDS.MULTI_GROUP,
    "Order Processing API",
    "completed",
    "developer_3",
    2,
    "approved",
    6,
    "Developer",
    "feature/api-orders",
    "merged",
    JSON.stringify(["ctx_6"]),
    JSON.stringify(["python", "rest", "transactions"]),
    5,
    getTimestamp(90),
    getTimestamp(15)
  );
}

function seedOrchestrationLogs(db: Database.Database): void {
  const insert = db.prepare(`
    INSERT INTO orchestration_logs (session_id, timestamp, iteration, agent_type, agent_id, content, log_type, reasoning_phase, confidence_level, references_json, redacted, group_id, event_subtype, event_payload)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // Completed session logs
  const completedLogs = [
    { agent: "orchestrator", content: "Session initialized. Spawning Project Manager for requirements analysis.", logType: "interaction", iteration: 1 },
    { agent: "project_manager", content: "Analyzing requirements for calculator application. Breaking down into task groups.", logType: "interaction", iteration: 1 },
    { agent: "project_manager", content: "Understanding the requirements: User wants a basic calculator with four operations. Need to ensure proper error handling for division by zero.", logType: "reasoning", phase: "understanding", confidence: "high", refs: ["requirements.md"], iteration: 1, groupId: "CALC" },
    { agent: "developer", content: "Implementing Calculator class with add, subtract, multiply, divide methods.", logType: "interaction", iteration: 1, groupId: "CALC" },
    { agent: "developer", content: "Approach: Using Python class-based design with type hints. Each operation as a separate method for clarity.", logType: "reasoning", phase: "approach", confidence: "high", refs: ["calculator.py"], iteration: 1, groupId: "CALC" },
    { agent: "qa_expert", content: "Running comprehensive test suite. All 51 tests passing.", logType: "interaction", iteration: 1, groupId: "CALC" },
    { agent: "qa_expert", content: "Test coverage at 98%. Edge cases covered including division by zero, large numbers, floating point precision.", logType: "reasoning", phase: "completion", confidence: "high", refs: ["test_calculator.py"], iteration: 1, groupId: "CALC" },
    { agent: "tech_lead", content: "Code review complete. Implementation follows best practices. Approved for merge.", logType: "interaction", iteration: 1, groupId: "CALC" },
    { agent: "project_manager", content: "All success criteria met. BAZINGA!", logType: "event", eventSubtype: "pm_bazinga", eventPayload: JSON.stringify({ criteria_met: 7, total: 7 }), iteration: 1 },
  ];

  completedLogs.forEach((log, idx) => {
    insert.run(
      SESSION_IDS.COMPLETED,
      getTimestamp(120 - idx * 5),
      log.iteration,
      log.agent,
      `${log.agent}_1`,
      log.content,
      log.logType,
      log.phase || null,
      log.confidence || null,
      log.refs ? JSON.stringify(log.refs) : null,
      0,
      log.groupId || null,
      log.eventSubtype || null,
      log.eventPayload || null
    );
  });

  // Active session logs
  const activeLogs = [
    { agent: "orchestrator", content: "Session initialized in parallel mode. Spawning Project Manager.", logType: "interaction", iteration: 1 },
    { agent: "project_manager", content: "Analyzing authentication requirements. Identified 3 parallel task groups: Core Auth, JWT, and RBAC.", logType: "interaction", iteration: 1 },
    { agent: "project_manager", content: "Understanding: Complex auth system requires careful security considerations. JWT for stateless auth, bcrypt for password hashing.", logType: "reasoning", phase: "understanding", confidence: "high", refs: ["auth_spec.md"], iteration: 1, groupId: "global" },
    { agent: "developer", content: "Implementing core authentication logic with password hashing.", logType: "interaction", iteration: 1, groupId: "AUTH-CORE" },
    { agent: "developer", content: "Using bcrypt with work factor 12 for password hashing. Implementing timing-safe comparison.", logType: "reasoning", phase: "approach", confidence: "medium", refs: ["auth/core.py"], iteration: 1, groupId: "AUTH-CORE" },
    { agent: "qa_expert", content: "Security tests identified potential timing attack vulnerability. Returning for revision.", logType: "interaction", iteration: 1, groupId: "AUTH-CORE" },
    { agent: "qa_expert", content: "Risk identified: Current implementation may leak timing information during password comparison.", logType: "reasoning", phase: "risks", confidence: "high", refs: ["test_auth.py"], iteration: 1, groupId: "AUTH-CORE" },
  ];

  activeLogs.forEach((log, idx) => {
    insert.run(
      SESSION_IDS.ACTIVE,
      getTimestamp(30 - idx * 3),
      log.iteration,
      log.agent,
      `${log.agent}_1`,
      log.content,
      log.logType,
      log.phase || null,
      log.confidence || null,
      log.refs ? JSON.stringify(log.refs) : null,
      log.agent === "qa_expert" ? 1 : 0, // Mark QA logs as potentially redacted
      log.groupId || null,
      null,
      null
    );
  });

  // Failed session logs
  const failedLogs = [
    { agent: "orchestrator", content: "Session initialized for trading system.", logType: "interaction", iteration: 1 },
    { agent: "project_manager", content: "WARNING: Complexity score 10/10. This may exceed single-session capacity.", logType: "interaction", iteration: 1 },
    { agent: "developer", content: "Attempting to implement websocket trading engine.", logType: "interaction", iteration: 1, groupId: "TRADING" },
    { agent: "developer", content: "Blocker: Real-time requirements exceed current implementation capacity. Need external websocket library integration.", logType: "reasoning", phase: "blockers", confidence: "low", refs: ["trading_engine.py"], iteration: 1, groupId: "TRADING" },
    { agent: "qa_expert", content: "Cannot complete testing. Core functionality not implemented.", logType: "interaction", iteration: 2, groupId: "TRADING" },
    { agent: "tech_lead", content: "Escalation required. Task complexity exceeds current agent capabilities.", logType: "event", eventSubtype: "escalation", eventPayload: JSON.stringify({ reason: "complexity", suggested_action: "break_down_task" }), iteration: 3 },
  ];

  failedLogs.forEach((log, idx) => {
    insert.run(
      SESSION_IDS.FAILED,
      getTimestamp(180 - idx * 5),
      log.iteration,
      log.agent,
      `${log.agent}_1`,
      log.content,
      log.logType,
      log.phase || null,
      log.confidence || null,
      log.refs ? JSON.stringify(log.refs) : null,
      0,
      log.groupId || null,
      log.eventSubtype || null,
      log.eventPayload || null
    );
  });

  // Multi-group session logs (abbreviated)
  const multiGroupLogs = [
    { agent: "orchestrator", content: "Parallel mode activated. 3 developers assigned.", logType: "interaction", iteration: 1 },
    { agent: "project_manager", content: "Task groups created: API-USERS, API-PRODUCTS, API-ORDERS", logType: "interaction", iteration: 1 },
    { agent: "developer", content: "User API implemented with CRUD endpoints.", logType: "interaction", iteration: 1, groupId: "API-USERS" },
    { agent: "developer", content: "Product catalog API complete with search functionality.", logType: "interaction", iteration: 1, groupId: "API-PRODUCTS" },
    { agent: "developer", content: "Order processing with transaction support implemented.", logType: "interaction", iteration: 1, groupId: "API-ORDERS" },
    { agent: "qa_expert", content: "All API endpoints tested. 127 tests passing.", logType: "interaction", iteration: 1 },
    { agent: "tech_lead", content: "All modules approved. Ready for integration.", logType: "interaction", iteration: 1 },
    { agent: "project_manager", content: "BAZINGA! All API modules complete.", logType: "event", eventSubtype: "pm_bazinga", eventPayload: JSON.stringify({ parallel_completion: true }), iteration: 1 },
  ];

  multiGroupLogs.forEach((log, idx) => {
    insert.run(
      SESSION_IDS.MULTI_GROUP,
      getTimestamp(90 - idx * 8),
      log.iteration,
      log.agent,
      `${log.agent}_${(idx % 3) + 1}`,
      log.content,
      log.logType,
      null,
      null,
      null,
      0,
      log.groupId || null,
      log.eventSubtype || null,
      log.eventPayload || null
    );
  });
}

function seedTokenUsage(db: Database.Database): void {
  const insert = db.prepare(`
    INSERT INTO token_usage (session_id, timestamp, agent_type, agent_id, tokens_estimated)
    VALUES (?, ?, ?, ?, ?)
  `);

  // Token usage for completed session
  const completedTokens = [
    { agent: "project_manager", tokens: 15000 },
    { agent: "developer", tokens: 45000 },
    { agent: "qa_expert", tokens: 25000 },
    { agent: "tech_lead", tokens: 18000 },
    { agent: "orchestrator", tokens: 5000 },
  ];

  completedTokens.forEach((t, idx) => {
    insert.run(SESSION_IDS.COMPLETED, getTimestamp(120 - idx * 10), t.agent, `${t.agent}_1`, t.tokens);
  });

  // Token usage for active session
  const activeTokens = [
    { agent: "project_manager", tokens: 12000 },
    { agent: "developer", tokens: 28000 },
    { agent: "qa_expert", tokens: 15000 },
    { agent: "orchestrator", tokens: 3500 },
  ];

  activeTokens.forEach((t, idx) => {
    insert.run(SESSION_IDS.ACTIVE, getTimestamp(30 - idx * 5), t.agent, `${t.agent}_1`, t.tokens);
  });

  // Token usage for failed session
  const failedTokens = [
    { agent: "project_manager", tokens: 8000 },
    { agent: "developer", tokens: 35000 },
    { agent: "qa_expert", tokens: 5000 },
    { agent: "tech_lead", tokens: 12000 },
    { agent: "orchestrator", tokens: 4000 },
  ];

  failedTokens.forEach((t, idx) => {
    insert.run(SESSION_IDS.FAILED, getTimestamp(180 - idx * 8), t.agent, `${t.agent}_1`, t.tokens);
  });

  // Token usage for multi-group session (higher due to parallel work)
  const multiGroupTokens = [
    { agent: "project_manager", tokens: 22000 },
    { agent: "developer", tokens: 95000 }, // 3 parallel developers
    { agent: "qa_expert", tokens: 42000 },
    { agent: "tech_lead", tokens: 28000 },
    { agent: "orchestrator", tokens: 8000 },
  ];

  multiGroupTokens.forEach((t, idx) => {
    insert.run(SESSION_IDS.MULTI_GROUP, getTimestamp(90 - idx * 12), t.agent, `${t.agent}_1`, t.tokens);
  });
}

function seedSuccessCriteria(db: Database.Database): void {
  const insert = db.prepare(`
    INSERT INTO success_criteria (session_id, criterion, status, actual, evidence, required_for_completion, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  // Completed session - all criteria met
  const completedCriteria = [
    { criterion: "Implement add operation", status: "met", actual: "add() method implemented", evidence: "calculator.py:15-20" },
    { criterion: "Implement subtract operation", status: "met", actual: "subtract() method implemented", evidence: "calculator.py:22-27" },
    { criterion: "Implement multiply operation", status: "met", actual: "multiply() method implemented", evidence: "calculator.py:29-34" },
    { criterion: "Implement divide operation", status: "met", actual: "divide() method with zero check", evidence: "calculator.py:36-43" },
    { criterion: "Handle division by zero", status: "met", actual: "Raises ValueError", evidence: "test_calculator.py:45-50" },
    { criterion: "Unit test coverage > 90%", status: "met", actual: "98% coverage", evidence: "coverage.xml" },
    { criterion: "All tests passing", status: "met", actual: "51/51 tests pass", evidence: "pytest output" },
  ];

  completedCriteria.forEach((c) => {
    insert.run(SESSION_IDS.COMPLETED, c.criterion, c.status, c.actual, c.evidence, 1, getTimestamp(120), getTimestamp(60));
  });

  // Active session - mixed criteria
  const activeCriteria = [
    { criterion: "Implement password hashing", status: "met", actual: "bcrypt implementation", evidence: "auth/hash.py", required: 1 },
    { criterion: "Implement JWT generation", status: "pending", actual: null, evidence: null, required: 1 },
    { criterion: "Implement JWT validation", status: "pending", actual: null, evidence: null, required: 1 },
    { criterion: "Role-based access control", status: "pending", actual: null, evidence: null, required: 1 },
    { criterion: "Security audit passing", status: "blocked", actual: "Timing attack vulnerability", evidence: "qa_report.md", required: 1 },
    { criterion: "API documentation", status: "pending", actual: null, evidence: null, required: 0 },
  ];

  activeCriteria.forEach((c) => {
    insert.run(SESSION_IDS.ACTIVE, c.criterion, c.status, c.actual, c.evidence, c.required, getTimestamp(30), getTimestamp(5));
  });

  // Failed session - failed criteria
  const failedCriteria = [
    { criterion: "Implement websocket connection", status: "failed", actual: "Not implemented", evidence: "Complexity exceeded" },
    { criterion: "Real-time price updates", status: "failed", actual: "Blocked by websocket", evidence: null },
    { criterion: "Order execution engine", status: "blocked", actual: "Dependency on websocket", evidence: null },
  ];

  failedCriteria.forEach((c) => {
    insert.run(SESSION_IDS.FAILED, c.criterion, c.status, c.actual, c.evidence, 1, getTimestamp(180), getTimestamp(150));
  });

  // Multi-group session - all met
  const multiGroupCriteria = [
    { criterion: "User CRUD endpoints", status: "met", actual: "GET/POST/PUT/DELETE /users", evidence: "api/users.py" },
    { criterion: "Product catalog endpoints", status: "met", actual: "Full catalog API", evidence: "api/products.py" },
    { criterion: "Order processing endpoints", status: "met", actual: "Order lifecycle API", evidence: "api/orders.py" },
    { criterion: "API authentication", status: "met", actual: "JWT middleware", evidence: "middleware/auth.py" },
    { criterion: "Integration tests passing", status: "met", actual: "127/127 tests pass", evidence: "pytest output" },
  ];

  multiGroupCriteria.forEach((c) => {
    insert.run(SESSION_IDS.MULTI_GROUP, c.criterion, c.status, c.actual, c.evidence, 1, getTimestamp(90), getTimestamp(15));
  });
}

function seedSkillOutputs(db: Database.Database): void {
  const insert = db.prepare(`
    INSERT INTO skill_outputs (session_id, timestamp, skill_name, output_data, agent_type, group_id, iteration)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);

  // Completed session skill outputs
  insert.run(
    SESSION_IDS.COMPLETED,
    getTimestamp(100),
    "lint-check",
    JSON.stringify({ passed: true, errors: 0, warnings: 2, files_checked: 5 }),
    "developer",
    "CALC",
    1
  );

  insert.run(
    SESSION_IDS.COMPLETED,
    getTimestamp(90),
    "test-coverage",
    JSON.stringify({ coverage_percent: 98, lines_covered: 245, lines_total: 250, uncovered_lines: [12, 34, 78, 156, 201] }),
    "qa_expert",
    "CALC",
    1
  );

  insert.run(
    SESSION_IDS.COMPLETED,
    getTimestamp(80),
    "security-scan",
    JSON.stringify({ passed: true, critical: 0, high: 0, medium: 1, low: 3, findings: ["SQL injection: false positive in test file"] }),
    "tech_lead",
    "CALC",
    1
  );

  insert.run(
    SESSION_IDS.COMPLETED,
    getTimestamp(110),
    "specialization-loader",
    JSON.stringify({ templates_used: ["python", "testing"], token_count: 850, composed_identity: "Python Developer with testing focus" }),
    "developer",
    "CALC",
    1
  );

  // Active session skill outputs
  insert.run(
    SESSION_IDS.ACTIVE,
    getTimestamp(20),
    "security-scan",
    JSON.stringify({ passed: false, critical: 1, high: 0, medium: 2, low: 1, findings: ["Timing attack vulnerability in password comparison"] }),
    "qa_expert",
    "AUTH-CORE",
    1
  );

  insert.run(
    SESSION_IDS.ACTIVE,
    getTimestamp(25),
    "codebase-analysis",
    JSON.stringify({ similar_patterns: ["existing auth in legacy module"], reusable_utilities: ["hash_utils.py"], architectural_notes: "Consider middleware pattern" }),
    "project_manager",
    null,
    1
  );

  // Multi-group session skill outputs
  insert.run(
    SESSION_IDS.MULTI_GROUP,
    getTimestamp(50),
    "api-contract-validation",
    JSON.stringify({ valid: true, endpoints: 24, breaking_changes: 0, deprecated: 2 }),
    "tech_lead",
    null,
    1
  );

  insert.run(
    SESSION_IDS.MULTI_GROUP,
    getTimestamp(40),
    "test-coverage",
    JSON.stringify({ coverage_percent: 94, lines_covered: 892, lines_total: 949, uncovered_lines: [45, 67, 89] }),
    "qa_expert",
    null,
    1
  );
}

function seedContextPackages(db: Database.Database): void {
  const insertPackage = db.prepare(`
    INSERT INTO context_packages (session_id, group_id, package_type, file_path, producer_agent, priority, summary, size_bytes, version, supersedes_id, scope, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const insertConsumer = db.prepare(`
    INSERT INTO context_package_consumers (package_id, agent_type, consumed_at, iteration)
    VALUES (?, ?, ?, ?)
  `);

  // Completed session context packages
  const pkg1Id = insertPackage.run(
    SESSION_IDS.COMPLETED,
    "CALC",
    "research",
    "bazinga/context/calc_research.md",
    "project_manager",
    "high",
    "Calculator implementation research and requirements analysis",
    2048,
    1,
    null,
    "group",
    getTimestamp(115)
  ).lastInsertRowid;

  insertConsumer.run(pkg1Id, "developer", getTimestamp(110), 1);
  insertConsumer.run(pkg1Id, "qa_expert", getTimestamp(95), 1);

  const pkg2Id = insertPackage.run(
    SESSION_IDS.COMPLETED,
    "CALC",
    "handoff",
    "bazinga/context/calc_handoff.md",
    "developer",
    "medium",
    "Developer to QA handoff documentation",
    1024,
    1,
    null,
    "group",
    getTimestamp(95)
  ).lastInsertRowid;

  insertConsumer.run(pkg2Id, "qa_expert", getTimestamp(90), 1);
  insertConsumer.run(pkg2Id, "tech_lead", getTimestamp(85), 1);

  // Active session context packages
  const pkg3Id = insertPackage.run(
    SESSION_IDS.ACTIVE,
    null,
    "research",
    "bazinga/context/auth_research.md",
    "project_manager",
    "critical",
    "Security research for authentication implementation",
    4096,
    1,
    null,
    "global",
    getTimestamp(28)
  ).lastInsertRowid;

  insertConsumer.run(pkg3Id, "developer", getTimestamp(25), 1);

  // Multi-group session context packages
  const pkg4Id = insertPackage.run(
    SESSION_IDS.MULTI_GROUP,
    null,
    "decisions",
    "bazinga/context/api_architecture.md",
    "tech_lead",
    "high",
    "API architecture decisions and patterns",
    3072,
    1,
    null,
    "global",
    getTimestamp(85)
  ).lastInsertRowid;

  // Three different developers consumed this (unique constraint on package_id, agent_type, iteration)
  insertConsumer.run(pkg4Id, "developer_1", getTimestamp(80), 1);
  insertConsumer.run(pkg4Id, "developer_2", getTimestamp(78), 1);
  insertConsumer.run(pkg4Id, "developer_3", getTimestamp(76), 1);
}

// CLI execution
if (require.main === module) {
  const dbPath = process.argv[2] || path.resolve(__dirname, "../../test-data/test.db");
  console.log(`Seeding database at: ${dbPath}`);
  seedTestDatabase(dbPath);
}
