import { sqliteTable, text, integer, index, primaryKey, real } from "drizzle-orm/sqlite-core";
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
  // v12: UNIQUE constraint for race condition prevention
  uniqueIdx: index("idx_skill_unique").on(
    table.sessionId, table.skillName, table.agentType, table.groupId, table.iteration
  ),
}));

// Configuration table
export const configuration = sqliteTable("configuration", {
  key: text("key").primaryKey(),
  value: text("value").notNull(), // JSON string
  updatedAt: text("updated_at"),
});

// Decisions table
export const decisions = sqliteTable("decisions", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  iteration: integer("iteration"),
  decisionType: text("decision_type").notNull(),
  decisionData: text("decision_data").notNull(), // JSON string
});

// Model Config table
export const modelConfig = sqliteTable("model_config", {
  agentRole: text("agent_role").primaryKey(),
  model: text("model").notNull(),
  rationale: text("rationale"),
  updatedAt: text("updated_at"),
});

// ============================================================================
// NEW TABLES (v4+)
// ============================================================================

// Success Criteria table - v4: BAZINGA validation tracking
export const successCriteria = sqliteTable("success_criteria", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  criterion: text("criterion").notNull(),
  category: text("category"),
  status: text("status").default("pending"), // pending/met/failed
  verifiedAt: text("verified_at"),
  verifiedBy: text("verified_by"),
  evidence: text("evidence"),
  createdAt: text("created_at"),
}, (table) => ({
  sessionCriterionIdx: index("idx_criteria_session").on(table.sessionId, table.criterion),
  sessionStatusIdx: index("idx_criteria_status").on(table.sessionId, table.status),
}));

// Context Packages table - v4/v10: Inter-agent context sharing
export const contextPackages = sqliteTable("context_packages", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  groupId: text("group_id"),
  packageType: text("package_type").notNull(), // research/failures/decisions/handoff/investigation
  filePath: text("file_path").notNull(),
  producerAgent: text("producer_agent").notNull(),
  // v10 columns
  priority: text("priority").default("medium"), // low/medium/high/critical
  summary: text("summary"),
  sizeBytes: integer("size_bytes"),
  version: integer("version").default(1),
  supersedesId: integer("supersedes_id"),
  scope: text("scope").default("group"), // group/session
  createdAt: text("created_at"),
}, (table) => ({
  sessionIdx: index("idx_packages_session").on(table.sessionId),
  priorityIdx: index("idx_packages_priority").on(table.sessionId, table.priority, table.createdAt),
}));

// Context Package Consumers table - v4: Who consumed what context
export const contextPackageConsumers = sqliteTable("context_package_consumers", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  packageId: integer("package_id").notNull(),
  agentType: text("agent_type").notNull(),
  consumedAt: text("consumed_at"),
  iteration: integer("iteration").default(1),
});

// Development Plans table - v4
export const developmentPlans = sqliteTable("development_plans", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  planType: text("plan_type").notNull(),
  planData: text("plan_data").notNull(), // JSON string
  createdAt: text("created_at"),
  updatedAt: text("updated_at"),
});

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
  decisions: many(decisions),
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

export const decisionsRelations = relations(decisions, ({ one }) => ({
  session: one(sessions, {
    fields: [decisions.sessionId],
    references: [sessions.sessionId],
  }),
}));

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
