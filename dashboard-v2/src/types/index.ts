// Session types
export interface Session {
  id: number;
  sessionId: string;
  startTime: string;
  endTime: string | null;
  status: string;
  mode: string | null;
  originalRequirements: string | null;
  developerCount: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface SessionWithRelations extends Session {
  taskGroups: TaskGroup[];
  logs: OrchestrationLog[];
  successCriteria: SuccessCriterion[];
  tokenUsage: TokenUsage[];
}

// Task Group types
export interface TaskGroup {
  id: number;
  sessionId: string;
  groupId: string;
  name: string;
  status: string;
  assignedTo: string | null;
  revisionCount: number | null;
  complexity: number | null;
  initialTier: string | null;
  currentStage: string | null;
  lastReviewStatus: string | null;
  riskScore: number | null;
  createdAt: string;
  updatedAt: string;
}

// Orchestration Log types
export interface OrchestrationLog {
  id: number;
  sessionId: string;
  timestamp: string;
  iteration: number | null;
  agentType: string;
  agentId: string | null;
  content: string;
  statusCode: string | null;
  tokensUsed: number | null;
  modelTier: string | null;
}

// Token Usage types
export interface TokenUsage {
  id: number;
  sessionId: string;
  timestamp: string;
  agentType: string;
  agentId: string | null;
  modelTier: string;
  tokensUsed: number;
  estimatedCost: number | null;
}

// Success Criteria types
export interface SuccessCriterion {
  id: number;
  sessionId: string;
  criterion: string;
  status: string;
  actual: string | null;
  evidence: string | null;
  requiredForCompletion: number | null;
  verifiedAt: string | null;
}

// State Snapshot types
export interface StateSnapshot {
  id: number;
  sessionId: string;
  timestamp: string;
  snapshotType: "pm_state" | "orchestrator_state" | "group_state";
  data: Record<string, unknown>;
}

// Quality Metrics types
export interface QualityMetric {
  id: number;
  sessionId: string;
  timestamp: string;
  metricType: "coverage" | "security" | "lint" | "review";
  value: number;
  details: Record<string, unknown> | null;
}

// Dashboard Stats types
export interface DashboardStats {
  totalSessions: number;
  activeSessions: number;
  completedSessions: number;
  failedSessions: number;
  totalTokens: number;
  totalCost: number;
  avgDuration: number;
  successRate: number;
}

// Agent Activity types
export interface AgentActivity {
  agentType: string;
  agentId: string;
  status: "idle" | "working" | "complete";
  currentTask: string | null;
  startTime: string | null;
  modelTier: string;
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
