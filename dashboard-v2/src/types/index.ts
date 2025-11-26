// Session types - matches actual database schema
// Primary key is session_id (TEXT), not autoincrement id
export interface Session {
  sessionId: string;
  startTime: string | null;
  endTime: string | null;
  status: string | null;
  mode: string | null;
  originalRequirements: string | null;
  createdAt: string | null;
}

export interface SessionWithRelations extends Session {
  taskGroups: TaskGroup[];
  logs: OrchestrationLog[];
  tokenUsage: TokenUsage[];
  stateSnapshots: StateSnapshot[];
}

// Task Group types - matches actual database schema
// Primary key is id (TEXT), not autoincrement integer
export interface TaskGroup {
  id: string;  // TEXT primary key in actual DB
  sessionId: string;
  name: string;
  status: string | null;
  assignedTo: string | null;
  revisionCount: number | null;
  complexity: number | null;
  initialTier: string | null;
  lastReviewStatus: string | null;
  createdAt: string | null;
  updatedAt: string | null;
}

// Orchestration Log types - matches actual database schema
// Note: No statusCode, tokensUsed, or modelTier columns
export interface OrchestrationLog {
  id: number;
  sessionId: string;
  timestamp: string | null;
  iteration: number | null;
  agentType: string;
  agentId: string | null;
  content: string;
}

// Token Usage types - matches actual database schema
// Note: Uses tokensEstimated, no modelTier or estimatedCost
export interface TokenUsage {
  id: number;
  sessionId: string;
  timestamp: string | null;
  agentType: string;
  agentId: string | null;
  tokensEstimated: number;
}

// State Snapshot types - matches actual database schema
// Note: Uses stateType and stateData column names
export interface StateSnapshot {
  id: number;
  sessionId: string;
  timestamp: string | null;
  stateType: string;
  stateData: string; // JSON string
}

// Skill Output types
export interface SkillOutput {
  id: number;
  sessionId: string;
  timestamp: string | null;
  skillName: string;
  outputData: string | Record<string, unknown>;
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
  type: "log" | "state" | "task" | "token";
  data: unknown;
  timestamp: string;
}

// Token breakdown for charts (simplified)
export interface TokenBreakdown {
  agentType: string;
  total: number;
}
