// ============================================================================
// TYPES VERSION: 12
// These types must stay in sync with src/lib/db/schema.ts
// See: research/dashboard-schema-update-ultrathink.md for schema gap analysis
// ============================================================================

// Session types - v9 extended with metadata
export interface Session {
  sessionId: string;
  startTime: string | null;
  endTime: string | null;
  status: string | null; // 'active' | 'completed' | 'failed'
  mode: string | null; // 'simple' | 'parallel'
  originalRequirements: string | null;
  initialBranch: string | null; // v5+
  metadata: string | null; // v9: JSON for original_scope
  createdAt: string | null;
}

export interface SessionWithRelations extends Session {
  taskGroups: TaskGroup[];
  logs: OrchestrationLog[];
  tokenUsage: TokenUsage[];
  stateSnapshots: StateSnapshot[];
  successCriteria: SuccessCriterion[];
  contextPackages: ContextPackage[];
}

// Task Group types - CRITICAL: Composite PK (id, session_id)
// v9 extended with item_count, branch/merge tracking, specializations
export interface TaskGroup {
  id: string;
  sessionId: string;
  name: string;
  status: string | null;
  assignedTo: string | null;
  revisionCount: number | null;
  complexity: number | null;
  initialTier: string | null;
  lastReviewStatus: string | null;
  // v5+ columns
  featureBranch: string | null;
  mergeStatus: string | null; // pending/in_progress/merged/conflict/test_failure
  contextReferences: string | null; // JSON array of context package IDs
  specializations: string | null; // JSON array of specialization paths
  // v9 columns
  itemCount: number | null;
  createdAt: string | null;
  updatedAt: string | null;
}

// Orchestration Log types - v8-v9 extended with reasoning and event columns
export interface OrchestrationLog {
  id: number;
  sessionId: string;
  timestamp: string | null;
  iteration: number | null;
  agentType: string;
  agentId: string | null;
  content: string;
  // v8: Reasoning capture columns
  logType: string | null; // 'interaction' | 'reasoning' | 'event'
  reasoningPhase: string | null; // understanding/approach/decisions/risks/blockers/pivot/completion
  confidenceLevel: string | null; // 'high' | 'medium' | 'low'
  referencesJson: string | null; // JSON array of files consulted
  redacted: number | null; // 1 if secrets were redacted
  groupId: string | null; // Task group context
  // v9: Event logging columns
  eventSubtype: string | null; // pm_bazinga/scope_change/validator_verdict
  eventPayload: string | null; // JSON event data
}

// Reasoning log (filtered view of OrchestrationLog where logType='reasoning')
export interface ReasoningLog {
  id: number;
  sessionId: string;
  timestamp: string | null;
  agentType: string;
  agentId: string | null;
  content: string;
  reasoningPhase: string;
  confidenceLevel: string | null;
  referencesJson: string | null;
  redacted: boolean;
  groupId: string | null;
}

// Event log (filtered view of OrchestrationLog where logType='event')
export interface EventLog {
  id: number;
  sessionId: string;
  timestamp: string | null;
  agentType: string;
  eventSubtype: string;
  eventPayload: string | null;
}

// Token Usage types
export interface TokenUsage {
  id: number;
  sessionId: string;
  timestamp: string | null;
  agentType: string;
  agentId: string | null;
  tokensEstimated: number;
}

// State Snapshot types
export interface StateSnapshot {
  id: number;
  sessionId: string;
  timestamp: string | null;
  stateType: string;
  stateData: string; // JSON string
}

// Skill Output types - v11-12 extended with agent/group/iteration
export interface SkillOutput {
  id: number;
  sessionId: string;
  timestamp: string | null;
  skillName: string;
  outputData: string | Record<string, unknown>;
  // v11 columns
  agentType: string | null;
  groupId: string | null;
  iteration: number | null;
}

// Decision types
export interface Decision {
  id: number;
  sessionId: string;
  timestamp: string | null;
  iteration: number | null;
  decisionType: string;
  decisionData: string | Record<string, unknown>;
}

// Model Config types
export interface ModelConfig {
  agentRole: string;
  model: string;
  rationale: string | null;
  updatedAt: string | null;
}

// ============================================================================
// NEW TYPES (v4+)
// ============================================================================

// Success Criteria types - v4: BAZINGA validation tracking
// ACTUAL schema from init_db.py - status includes 'blocked'
export interface SuccessCriterion {
  id: number;
  sessionId: string;
  criterion: string;
  status: string | null; // 'pending' | 'met' | 'blocked' | 'failed'
  actual: string | null; // Actual value achieved
  evidence: string | null;
  requiredForCompletion: number | null; // BOOLEAN stored as 0/1
  createdAt: string | null;
  updatedAt: string | null;
}

// Context Package types - v4/v10: Inter-agent context sharing
// ACTUAL schema: priority and summary are NOT NULL, scope is 'group'|'global'
export interface ContextPackage {
  id: number;
  sessionId: string;
  groupId: string | null;
  packageType: string; // research/failures/decisions/handoff/investigation
  filePath: string;
  producerAgent: string;
  // v10 columns
  priority: string; // NOT NULL with default 'medium': low/medium/high/critical
  summary: string; // NOT NULL
  sizeBytes: number | null;
  version: number | null;
  supersedesId: number | null;
  scope: string | null; // 'group' | 'global' (NOT 'session')
  createdAt: string | null;
}

// Context Package Consumer types - v4
export interface ContextPackageConsumer {
  id: number;
  packageId: number;
  agentType: string;
  consumedAt: string | null;
  iteration: number | null;
}

// Development Plan types - v3
// ACTUAL schema from init_db.py - one plan per session (UNIQUE session_id)
export interface DevelopmentPlan {
  id: number;
  sessionId: string; // UNIQUE constraint
  originalPrompt: string;
  planText: string;
  phases: string; // JSON string array
  currentPhase: number | null;
  totalPhases: number;
  createdAt: string | null;
  updatedAt: string | null;
  metadata: string | null; // JSON string
}

// ============================================================================
// NEW TYPES (v10: Context Engineering System)
// ============================================================================

// Error Pattern types - v10
export interface ErrorPattern {
  patternHash: string;
  projectId: string;
  signatureJson: string;
  solution: string;
  confidence: number | null;
  occurrences: number | null;
  lang: string | null;
  lastSeen: string | null;
  createdAt: string | null;
  ttlDays: number | null;
}

// Strategy types - v10
export interface Strategy {
  strategyId: string;
  projectId: string;
  topic: string;
  insight: string;
  helpfulness: number | null;
  lang: string | null;
  framework: string | null;
  lastSeen: string | null;
  createdAt: string | null;
}

// Consumption Scope types - v10
export interface ConsumptionScope {
  scopeId: string;
  sessionId: string;
  groupId: string;
  agentType: string;
  iteration: number;
  packageId: number;
  consumedAt: string | null;
}

// ============================================================================
// SCHEMA CAPABILITY DETECTION
// ============================================================================

// Schema capabilities for graceful degradation with older databases
export interface SchemaCapabilities {
  schemaVersion: number;
  hasReasoningColumns: boolean;
  hasEventColumns: boolean;
  hasSuccessCriteria: boolean;
  hasContextPackages: boolean;
  hasTaskGroupExtensions: boolean;
  hasSkillOutputExtensions: boolean;
  hasContextEngineering: boolean; // error_patterns, strategies, consumption_scope
  hasDevelopmentPlans: boolean; // development_plans table
}

// ============================================================================
// DASHBOARD & ANALYTICS TYPES
// ============================================================================

// Dashboard Stats types
export interface DashboardStats {
  totalSessions: number;
  activeSessions: number;
  completedSessions: number;
  failedSessions: number;
  totalTokens: number;
  successRate: number;
}

// Agent Activity types
export interface AgentActivity {
  agentType: string;
  agentId: string | null;
  status: "idle" | "working" | "complete";
  currentTask: string | null;
  startTime: string | null;
}

// Pattern types (for AI insights)
export interface Pattern {
  type: string;
  severity: "info" | "low" | "medium" | "high";
  message: string;
  recommendation: string;
}

// Real-time update types
export interface SessionUpdate {
  sessionId: string;
  type: "log" | "state" | "task" | "token" | "reasoning" | "event" | "criteria";
  data: unknown;
  timestamp: string;
}

// Token breakdown for charts
export interface TokenBreakdown {
  agentType: string;
  total: number;
}

// Reasoning summary for analytics
export interface ReasoningSummary {
  totalEntries: number;
  byPhase: Record<string, number>;
  byAgent: Record<string, number>;
  byConfidence: Record<string, number>;
  redactedCount: number;
}

// Success criteria summary
// ACTUAL status values: 'pending' | 'met' | 'blocked' | 'failed'
export interface CriteriaSummary {
  total: number;
  met: number;
  pending: number;
  blocked: number;
  failed: number;
}
