import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";
import { relations } from "drizzle-orm";

// Sessions table
export const sessions = sqliteTable("sessions", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull().unique(),
  startTime: text("start_time").notNull(),
  endTime: text("end_time"),
  status: text("status").notNull().default("active"),
  mode: text("mode").default("simple"),
  originalRequirements: text("original_requirements"),
  developerCount: integer("developer_count").default(1),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

// Orchestration Logs table
export const orchestrationLogs = sqliteTable("orchestration_logs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp").notNull(),
  iteration: integer("iteration").default(0),
  agentType: text("agent_type").notNull(),
  agentId: text("agent_id"),
  content: text("content").notNull(),
  statusCode: text("status_code"),
  tokensUsed: integer("tokens_used"),
  modelTier: text("model_tier"),
});

// Task Groups table
export const taskGroups = sqliteTable("task_groups", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  groupId: text("group_id").notNull(),
  name: text("name").notNull(),
  status: text("status").notNull().default("pending"),
  assignedTo: text("assigned_to"),
  revisionCount: integer("revision_count").default(0),
  complexity: integer("complexity"),
  initialTier: text("initial_tier"),
  currentStage: text("current_stage").default("pending"),
  lastReviewStatus: text("last_review_status"),
  riskScore: real("risk_score"),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

// Token Usage table
export const tokenUsage = sqliteTable("token_usage", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp").notNull(),
  agentType: text("agent_type").notNull(),
  agentId: text("agent_id"),
  modelTier: text("model_tier").notNull(),
  tokensUsed: integer("tokens_used").notNull(),
  estimatedCost: real("estimated_cost"),
});

// Success Criteria table
export const successCriteria = sqliteTable("success_criteria", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  criterion: text("criterion").notNull(),
  status: text("status").notNull().default("pending"),
  actual: text("actual"),
  evidence: text("evidence"),
  requiredForCompletion: integer("required_for_completion").default(1),
  verifiedAt: text("verified_at"),
});

// State Snapshots table
export const stateSnapshots = sqliteTable("state_snapshots", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp").notNull(),
  snapshotType: text("snapshot_type").notNull(),
  data: text("data").notNull(), // JSON string
});

// Development Plans table
export const developmentPlans = sqliteTable("development_plans", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  originalPrompt: text("original_prompt"),
  planText: text("plan_text"),
  phases: text("phases"), // JSON string
  currentPhase: integer("current_phase").default(0),
  totalPhases: integer("total_phases").default(1),
  metadata: text("metadata"), // JSON string
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

// Quality Metrics table
export const qualityMetrics = sqliteTable("quality_metrics", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp").notNull(),
  metricType: text("metric_type").notNull(),
  value: real("value").notNull(),
  details: text("details"), // JSON string
});

// Skill Outputs table
export const skillOutputs = sqliteTable("skill_outputs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp").notNull(),
  skillName: text("skill_name").notNull(),
  outputData: text("output_data").notNull(), // JSON string
});

// Decisions table
export const decisions = sqliteTable("decisions", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sessionId: text("session_id").notNull(),
  timestamp: text("timestamp").notNull(),
  iteration: integer("iteration"),
  decisionType: text("decision_type").notNull(),
  decisionData: text("decision_data").notNull(), // JSON string
});

// Relations
export const sessionsRelations = relations(sessions, ({ many }) => ({
  logs: many(orchestrationLogs),
  taskGroups: many(taskGroups),
  tokenUsage: many(tokenUsage),
  successCriteria: many(successCriteria),
  stateSnapshots: many(stateSnapshots),
  qualityMetrics: many(qualityMetrics),
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

export const successCriteriaRelations = relations(successCriteria, ({ one }) => ({
  session: one(sessions, {
    fields: [successCriteria.sessionId],
    references: [sessions.sessionId],
  }),
}));
