import { sqliteTable, text, integer, index, uniqueIndex, primaryKey, real } from "drizzle-orm/sqlite-core";
import { relations } from "drizzle-orm";

// ============================================================================
// SCHEMA VERSION: 12
// This schema must stay in sync with .claude/skills/bazinga-db/scripts/init_db.py
// See: research/dashboard-schema-update-ultrathink.md for schema gap analysis
// ============================================================================

// Sessions table - v9 extended with metadata column
export const sessions = sqliteTable("sessions", {
  sessionId: text("session_id").primaryKey(),
  startTime: text("start_time"),
  endTime: text("end_time"),
  mode: text("mode"), // 'simple' | 'parallel'
  originalRequirements: text("original_requirements"),
  status: text("status").default("active"), // 'active' | 'completed' | 'failed'
  initialBranch: text("initial_branch").default("main"), // v5+
  metadata: text("metadata"), // v9: JSON for original_scope tracking
  createdAt: text("created_at"),
});

// Orchestration Logs table - v8-v9 extended with reasoning and event columns
export const orchestrationLogs = sqliteTable("orchestration_logs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  iteration: integer("iteration"),
  agentType: text("agent_type").notNull(),
  agentId: text("agent_id"),
  content: text("content").notNull(),
  // v8: Reasoning capture columns
  logType: text("log_type").default("interaction"), // 'interaction' | 'reasoning' | 'event'
  reasoningPhase: text("reasoning_phase"), // understanding/approach/decisions/risks/blockers/pivot/completion
  confidenceLevel: text("confidence_level"), // 'high' | 'medium' | 'low'
  referencesJson: text("references_json"), // JSON array of files consulted
  redacted: integer("redacted").default(0), // 1 if secrets were redacted
  groupId: text("group_id"), // Task group context
  // v9: Event logging columns
  eventSubtype: text("event_subtype"), // pm_bazinga/scope_change/validator_verdict
  eventPayload: text("event_payload"), // JSON event data
}, (table) => ({
  sessionIdIdx: index("idx_logs_session_id").on(table.sessionId),
  timestampIdx: index("idx_logs_timestamp").on(table.timestamp),
  reasoningIdx: index("idx_logs_reasoning").on(table.sessionId, table.logType, table.reasoningPhase),
  eventsIdx: index("idx_logs_events").on(table.sessionId, table.logType, table.eventSubtype),
}));

// Task Groups table - CRITICAL: Uses composite primary key (id, session_id)
// v9 extended with item_count, branch/merge tracking, specializations
export const taskGroups = sqliteTable("task_groups", {
  id: text("id").notNull(),
  sessionId: text("session_id").notNull(),
  name: text("name").notNull(),
  status: text("status").default("pending"),
  assignedTo: text("assigned_to"),
  revisionCount: integer("revision_count").default(0),
  lastReviewStatus: text("last_review_status"),
  complexity: integer("complexity"),
  initialTier: text("initial_tier"),
  // v5+ columns
  featureBranch: text("feature_branch"),
  mergeStatus: text("merge_status"), // pending/in_progress/merged/conflict/test_failure
  contextReferences: text("context_references"), // JSON array of context package IDs
  specializations: text("specializations"), // JSON array of specialization paths
  // v9 columns
  itemCount: integer("item_count").default(1),
  createdAt: text("created_at"),
  updatedAt: text("updated_at"),
}, (table) => ({
  // CRITICAL: Composite primary key prevents cross-session collisions
  pk: primaryKey({ columns: [table.id, table.sessionId] }),
  sessionIdIdx: index("idx_groups_session_id").on(table.sessionId),
}));

// Token Usage table
export const tokenUsage = sqliteTable("token_usage", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  agentType: text("agent_type").notNull(),
  agentId: text("agent_id"),
  tokensEstimated: integer("tokens_estimated").notNull(),
}, (table) => ({
  sessionIdIdx: index("idx_tokens_session_id").on(table.sessionId),
}));

// State Snapshots table
export const stateSnapshots = sqliteTable("state_snapshots", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  stateType: text("state_type").notNull(),
  stateData: text("state_data").notNull(), // JSON string
});

// Skill Outputs table - v11-12 extended with agent/group/iteration
export const skillOutputs = sqliteTable("skill_outputs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  skillName: text("skill_name").notNull(),
  outputData: text("output_data").notNull(), // JSON string
  // v11 columns for multi-invocation tracking
  agentType: text("agent_type"),
  groupId: text("group_id"),
  iteration: integer("iteration").default(1),
}, (table) => ({
  // v12: UNIQUE constraint for race condition prevention - MUST be uniqueIndex
  uniqueIdx: uniqueIndex("idx_skill_unique").on(
    table.sessionId, table.skillName, table.agentType, table.groupId, table.iteration
  ),
  // Session lookup index
  sessionIdx: index("idx_skill_session").on(table.sessionId),
}));

// NOTE: configuration, decisions, and model_config tables were REMOVED from init_db.py
// See: research/empty-tables-analysis.md
// DO NOT add them back - they do not exist in the database

// ============================================================================
// NEW TABLES (v4+)
// ============================================================================

// Success Criteria table - v4: BAZINGA validation tracking
// ACTUAL schema from init_db.py - status has different values than originally assumed
export const successCriteria = sqliteTable("success_criteria", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  criterion: text("criterion").notNull(),
  status: text("status").default("pending"), // 'pending' | 'met' | 'blocked' | 'failed'
  actual: text("actual"), // Actual value achieved
  evidence: text("evidence"),
  requiredForCompletion: integer("required_for_completion").default(1), // BOOLEAN as integer
  createdAt: text("created_at"),
  updatedAt: text("updated_at"),
}, (table) => ({
  // UNIQUE index - matches init_db.py CREATE UNIQUE INDEX
  uniqueCriterionIdx: uniqueIndex("idx_unique_criterion").on(table.sessionId, table.criterion),
  sessionStatusIdx: index("idx_criteria_session_status").on(table.sessionId, table.status),
}));

// Context Packages table - v4/v10: Inter-agent context sharing
// ACTUAL schema: priority and summary are NOT NULL, scope is 'group'|'global'
export const contextPackages = sqliteTable("context_packages", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  groupId: text("group_id"),
  packageType: text("package_type").notNull(), // research/failures/decisions/handoff/investigation
  filePath: text("file_path").notNull(),
  producerAgent: text("producer_agent").notNull(),
  // v10 columns
  priority: text("priority").notNull().default("medium"), // low/medium/high/critical
  summary: text("summary").notNull(),
  sizeBytes: integer("size_bytes"),
  version: integer("version").default(1),
  supersedesId: integer("supersedes_id"),
  scope: text("scope").default("group"), // 'group' | 'global' (NOT 'session')
  createdAt: text("created_at"),
}, (table) => ({
  sessionIdx: index("idx_cp_session").on(table.sessionId),
  priorityIdx: index("idx_packages_priority_ranking").on(table.sessionId, table.priority, table.createdAt),
}));

// Context Package Consumers table - v4: Who consumed what context
export const contextPackageConsumers = sqliteTable("context_package_consumers", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  packageId: integer("package_id").notNull(),
  agentType: text("agent_type").notNull(),
  consumedAt: text("consumed_at"),
  iteration: integer("iteration").default(1),
}, (table) => ({
  // Index for getContextConsumers query performance
  packageIdx: index("idx_consumers_package").on(table.packageId),
}));

// Development Plans table - v3
// ACTUAL schema from init_db.py - session_id is UNIQUE
export const developmentPlans = sqliteTable("development_plans", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(), // UNIQUE constraint enforced by index below
  originalPrompt: text("original_prompt").notNull(),
  planText: text("plan_text").notNull(),
  phases: text("phases").notNull(), // JSON string
  currentPhase: integer("current_phase"),
  totalPhases: integer("total_phases").notNull(),
  createdAt: text("created_at"),
  updatedAt: text("updated_at"),
  metadata: text("metadata"), // JSON string
}, (table) => ({
  // UNIQUE constraint on session_id - one plan per session
  sessionIdx: uniqueIndex("idx_devplans_session_unique").on(table.sessionId),
}));

// ============================================================================
// NEW TABLES (v10: Context Engineering System)
// ============================================================================

// Error Patterns table - v10: Learning from failed-then-succeeded agents
export const errorPatterns = sqliteTable("error_patterns", {
  patternHash: text("pattern_hash").notNull(),
  projectId: text("project_id").notNull(),
  signatureJson: text("signature_json").notNull(),
  solution: text("solution").notNull(),
  confidence: real("confidence").default(0.5),
  occurrences: integer("occurrences").default(1),
  lang: text("lang"),
  lastSeen: text("last_seen"),
  createdAt: text("created_at"),
  ttlDays: integer("ttl_days").default(90),
}, (table) => ({
  pk: primaryKey({ columns: [table.patternHash, table.projectId] }),
  projectIdx: index("idx_patterns_project").on(table.projectId, table.lang),
}));

// Strategies table - v10: Successful approaches by topic
export const strategies = sqliteTable("strategies", {
  strategyId: text("strategy_id").primaryKey(),
  projectId: text("project_id").notNull(),
  topic: text("topic").notNull(),
  insight: text("insight").notNull(),
  helpfulness: integer("helpfulness").default(0),
  lang: text("lang"),
  framework: text("framework"),
  lastSeen: text("last_seen"),
  createdAt: text("created_at"),
}, (table) => ({
  projectIdx: index("idx_strategies_project").on(table.projectId, table.framework),
  topicIdx: index("idx_strategies_topic").on(table.topic),
}));

// Consumption Scope table - v10: Iteration-aware context tracking
export const consumptionScope = sqliteTable("consumption_scope", {
  scopeId: text("scope_id").primaryKey(),
  sessionId: text("session_id").notNull(),
  groupId: text("group_id").notNull(),
  agentType: text("agent_type").notNull(),
  iteration: integer("iteration").notNull(),
  packageId: integer("package_id").notNull(),
  consumedAt: text("consumed_at"),
}, (table) => ({
  sessionIdx: index("idx_consumption_session").on(table.sessionId, table.groupId, table.agentType),
}));

// ============================================================================
// RELATIONS
// ============================================================================

export const sessionsRelations = relations(sessions, ({ many }) => ({
  logs: many(orchestrationLogs),
  taskGroups: many(taskGroups),
  tokenUsage: many(tokenUsage),
  stateSnapshots: many(stateSnapshots),
  skillOutputs: many(skillOutputs),
  // NOTE: decisions table removed from init_db.py - no relation
  successCriteria: many(successCriteria),
  contextPackages: many(contextPackages),
  developmentPlans: many(developmentPlans),
  consumptionScope: many(consumptionScope),
}));

export const orchestrationLogsRelations = relations(orchestrationLogs, ({ one }) => ({
  session: one(sessions, {
    fields: [orchestrationLogs.sessionId],
    references: [sessions.sessionId],
  }),
}));

export const taskGroupsRelations = relations(taskGroups, ({ one }) => ({
  session: one(sessions, {
    fields: [taskGroups.sessionId],
    references: [sessions.sessionId],
  }),
}));

export const tokenUsageRelations = relations(tokenUsage, ({ one }) => ({
  session: one(sessions, {
    fields: [tokenUsage.sessionId],
    references: [sessions.sessionId],
  }),
}));

export const stateSnapshotsRelations = relations(stateSnapshots, ({ one }) => ({
  session: one(sessions, {
    fields: [stateSnapshots.sessionId],
    references: [sessions.sessionId],
  }),
}));

export const skillOutputsRelations = relations(skillOutputs, ({ one }) => ({
  session: one(sessions, {
    fields: [skillOutputs.sessionId],
    references: [sessions.sessionId],
  }),
}));

// NOTE: decisionsRelations removed - decisions table does not exist in init_db.py

export const successCriteriaRelations = relations(successCriteria, ({ one }) => ({
  session: one(sessions, {
    fields: [successCriteria.sessionId],
    references: [sessions.sessionId],
  }),
}));

export const contextPackagesRelations = relations(contextPackages, ({ one, many }) => ({
  session: one(sessions, {
    fields: [contextPackages.sessionId],
    references: [sessions.sessionId],
  }),
  consumers: many(contextPackageConsumers),
}));

export const contextPackageConsumersRelations = relations(contextPackageConsumers, ({ one }) => ({
  package: one(contextPackages, {
    fields: [contextPackageConsumers.packageId],
    references: [contextPackages.id],
  }),
}));

export const developmentPlansRelations = relations(developmentPlans, ({ one }) => ({
  session: one(sessions, {
    fields: [developmentPlans.sessionId],
    references: [sessions.sessionId],
  }),
}));

export const consumptionScopeRelations = relations(consumptionScope, ({ one }) => ({
  session: one(sessions, {
    fields: [consumptionScope.sessionId],
    references: [sessions.sessionId],
  }),
  package: one(contextPackages, {
    fields: [consumptionScope.packageId],
    references: [contextPackages.id],
  }),
}));
