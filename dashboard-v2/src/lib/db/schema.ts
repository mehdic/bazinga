import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";
import { relations } from "drizzle-orm";

// Sessions table - matches actual database schema
// Primary key is session_id (TEXT), not autoincrement id
export const sessions = sqliteTable("sessions", {
  sessionId: text("session_id").primaryKey(),
  startTime: text("start_time"),
  endTime: text("end_time"),
  mode: text("mode"),
  originalRequirements: text("original_requirements"),
  status: text("status").default("active"),
  createdAt: text("created_at"),
});

// Orchestration Logs table - matches actual database schema
// Note: No status_code, tokens_used, or model_tier columns in actual DB
export const orchestrationLogs = sqliteTable("orchestration_logs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  iteration: integer("iteration"),
  agentType: text("agent_type").notNull(),
  agentId: text("agent_id"),
  content: text("content").notNull(),
});

// Task Groups table - matches actual database schema
// Primary key is id (TEXT), not autoincrement integer
export const taskGroups = sqliteTable("task_groups", {
  id: text("id").primaryKey(),
  sessionId: text("session_id").notNull(),
  name: text("name").notNull(),
  status: text("status").default("pending"),
  assignedTo: text("assigned_to"),
  revisionCount: integer("revision_count").default(0),
  lastReviewStatus: text("last_review_status"),
  complexity: integer("complexity"),
  initialTier: text("initial_tier"),
  createdAt: text("created_at"),
  updatedAt: text("updated_at"),
});

// Token Usage table - matches actual database schema
// Note: Uses tokens_estimated, no model_tier or estimated_cost
export const tokenUsage = sqliteTable("token_usage", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  agentType: text("agent_type").notNull(),
  agentId: text("agent_id"),
  tokensEstimated: integer("tokens_estimated").notNull(),
});

// State Snapshots table - matches actual database schema
// Note: Uses state_type and state_data column names
export const stateSnapshots = sqliteTable("state_snapshots", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  stateType: text("state_type").notNull(),
  stateData: text("state_data").notNull(), // JSON string
});

// Skill Outputs table - matches actual database schema
export const skillOutputs = sqliteTable("skill_outputs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  skillName: text("skill_name").notNull(),
  outputData: text("output_data").notNull(), // JSON string
});

// Configuration table - matches actual database schema
export const configuration = sqliteTable("configuration", {
  key: text("key").primaryKey(),
  value: text("value").notNull(), // JSON string
  updatedAt: text("updated_at"),
});

// Decisions table - matches actual database schema
export const decisions = sqliteTable("decisions", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp"),
  iteration: integer("iteration"),
  decisionType: text("decision_type").notNull(),
  decisionData: text("decision_data").notNull(), // JSON string
});

// Model Config table - matches actual database schema
export const modelConfig = sqliteTable("model_config", {
  agentRole: text("agent_role").primaryKey(),
  model: text("model").notNull(),
  rationale: text("rationale"),
  updatedAt: text("updated_at"),
});

// Relations
export const sessionsRelations = relations(sessions, ({ many }) => ({
  logs: many(orchestrationLogs),
  taskGroups: many(taskGroups),
  tokenUsage: many(tokenUsage),
  stateSnapshots: many(stateSnapshots),
  skillOutputs: many(skillOutputs),
  decisions: many(decisions),
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
