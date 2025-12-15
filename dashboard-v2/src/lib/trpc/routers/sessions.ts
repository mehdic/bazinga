import { z } from "zod";
import { router, publicProcedure } from "../server";
import { db } from "../../db/client";
import {
  sessions,
  orchestrationLogs,
  taskGroups,
  tokenUsage,
  stateSnapshots,
  skillOutputs,
  // NOTE: decisions table removed from init_db.py - do not import
  successCriteria,
  contextPackages,
  contextPackageConsumers,
} from "../../db/schema";
import { desc, eq, and, gte, lte, like, count, sql } from "drizzle-orm";
import { detectCapabilities } from "../../db/capabilities";

export const sessionsRouter = router({
  // ============================================================================
  // CAPABILITY DETECTION
  // ============================================================================

  // Get schema capabilities for graceful degradation
  // NOTE: detectCapabilities() is synchronous (uses better-sqlite3 sync API)
  getCapabilities: publicProcedure.query(() => {
    return detectCapabilities();
  }),

  // ============================================================================
  // SESSION QUERIES
  // ============================================================================

  // List all sessions with pagination and filters
  list: publicProcedure
    .input(
      z.object({
        limit: z.number().min(1).max(100).default(20),
        offset: z.number().default(0),
        status: z.enum(["all", "active", "completed", "failed"]).default("all"),
        dateFrom: z.string().optional(),
        dateTo: z.string().optional(),
        search: z.string().optional(),
      })
    )
    .query(async ({ input }) => {
      const conditions = [];
      if (input.status !== "all") {
        conditions.push(eq(sessions.status, input.status));
      }
      if (input.dateFrom) {
        conditions.push(gte(sessions.startTime, input.dateFrom));
      }
      if (input.dateTo) {
        conditions.push(lte(sessions.startTime, input.dateTo));
      }
      if (input.search) {
        conditions.push(like(sessions.originalRequirements, `%${input.search}%`));
      }

      const results = await db
        .select()
        .from(sessions)
        .where(conditions.length > 0 ? and(...conditions) : undefined)
        .orderBy(desc(sessions.startTime))
        .limit(input.limit)
        .offset(input.offset);

      const totalResult = await db
        .select({ count: count() })
        .from(sessions)
        .where(conditions.length > 0 ? and(...conditions) : undefined);

      return {
        sessions: results,
        total: totalResult[0]?.count || 0,
        hasMore: input.offset + results.length < (totalResult[0]?.count || 0),
      };
    }),

  // Get single session by ID with all relations
  getById: publicProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input }) => {
      const session = await db
        .select()
        .from(sessions)
        .where(eq(sessions.sessionId, input.sessionId))
        .limit(1);

      if (!session[0]) {
        return null;
      }

      // Fetch core related data with try/catch for backward compat
      // Older DBs may lack v8/v9 columns (log_type, event_subtype, etc.)
      let logs: typeof orchestrationLogs.$inferSelect[] = [];
      let groups: typeof taskGroups.$inferSelect[] = [];

      try {
        logs = await db
          .select()
          .from(orchestrationLogs)
          .where(eq(orchestrationLogs.sessionId, input.sessionId))
          .orderBy(orchestrationLogs.timestamp)
          .limit(200);
      } catch {
        // Schema mismatch - older DB lacks v8/v9 columns, return empty
        logs = [];
      }

      try {
        groups = await db
          .select()
          .from(taskGroups)
          .where(eq(taskGroups.sessionId, input.sessionId));
      } catch {
        // Schema mismatch - older DB lacks v5/v9 columns, return empty
        groups = [];
      }

      const [tokens, snapshots] = await Promise.all([
        db
          .select()
          .from(tokenUsage)
          .where(eq(tokenUsage.sessionId, input.sessionId))
          .orderBy(desc(tokenUsage.timestamp)),
        db
          .select()
          .from(stateSnapshots)
          .where(eq(stateSnapshots.sessionId, input.sessionId))
          .orderBy(desc(stateSnapshots.timestamp))
          .limit(20),
      ]);

      // Try to fetch success criteria (may not exist in older DBs)
      let criteria: typeof successCriteria.$inferSelect[] = [];
      try {
        criteria = await db
          .select()
          .from(successCriteria)
          .where(eq(successCriteria.sessionId, input.sessionId))
          .orderBy(successCriteria.id);
      } catch {
        // Table doesn't exist - ignore
      }

      // Try to fetch context packages (may not exist in older DBs)
      let packages: typeof contextPackages.$inferSelect[] = [];
      try {
        packages = await db
          .select()
          .from(contextPackages)
          .where(eq(contextPackages.sessionId, input.sessionId))
          .orderBy(desc(contextPackages.createdAt));
      } catch {
        // Table doesn't exist - ignore
      }

      return {
        ...session[0],
        logs,
        taskGroups: groups,
        tokenUsage: tokens,
        stateSnapshots: snapshots,
        successCriteria: criteria,
        contextPackages: packages,
      };
    }),

  // Get dashboard stats
  getStats: publicProcedure.query(async () => {
    const [totalResult, activeResult, completedResult, failedResult] = await Promise.all([
      db.select({ count: count() }).from(sessions),
      db.select({ count: count() }).from(sessions).where(eq(sessions.status, "active")),
      db.select({ count: count() }).from(sessions).where(eq(sessions.status, "completed")),
      db.select({ count: count() }).from(sessions).where(eq(sessions.status, "failed")),
    ]);

    const tokensResult = await db
      .select({ total: sql<number>`COALESCE(SUM(${tokenUsage.tokensEstimated}), 0)` })
      .from(tokenUsage);

    const total = totalResult[0]?.count || 0;
    const completed = completedResult[0]?.count || 0;

    return {
      totalSessions: total,
      activeSessions: activeResult[0]?.count || 0,
      completedSessions: completed,
      failedSessions: failedResult[0]?.count || 0,
      totalTokens: tokensResult[0]?.total || 0,
      successRate: total > 0 ? (completed / total) * 100 : 0,
    };
  }),

  // Get active session (most recent active)
  getActive: publicProcedure.query(async () => {
    const active = await db
      .select()
      .from(sessions)
      .where(eq(sessions.status, "active"))
      .orderBy(desc(sessions.startTime))
      .limit(1);

    return active[0] || null;
  }),

  // ============================================================================
  // LOGS QUERIES (with v8+ reasoning support)
  // ============================================================================

  // Get logs for a session with pagination and filtering
  // Wrapped in try/catch for backward compat with older DBs lacking v8/v9 columns
  getLogs: publicProcedure
    .input(
      z.object({
        sessionId: z.string(),
        limit: z.number().min(1).max(500).default(50),
        offset: z.number().default(0),
        agentType: z.string().optional(),
        logType: z.enum(["all", "interaction", "reasoning", "event"]).default("all"),
      })
    )
    .query(async ({ input }) => {
      try {
        const conditions = [eq(orchestrationLogs.sessionId, input.sessionId)];
        if (input.agentType) {
          conditions.push(eq(orchestrationLogs.agentType, input.agentType));
        }
        if (input.logType !== "all") {
          conditions.push(eq(orchestrationLogs.logType, input.logType));
        }

        const logs = await db
          .select()
          .from(orchestrationLogs)
          .where(and(...conditions))
          .orderBy(orchestrationLogs.timestamp)
          .limit(input.limit)
          .offset(input.offset);

        const totalResult = await db
          .select({ count: count() })
          .from(orchestrationLogs)
          .where(and(...conditions));

        return {
          logs,
          total: totalResult[0]?.count || 0,
          hasMore: input.offset + logs.length < (totalResult[0]?.count || 0),
        };
      } catch {
        // Older DB lacks v8/v9 columns - return empty result
        return { logs: [], total: 0, hasMore: false };
      }
    }),

  // Get reasoning logs with phase filtering (v8+)
  getReasoning: publicProcedure
    .input(
      z.object({
        sessionId: z.string(),
        limit: z.number().min(1).max(500).default(50),
        offset: z.number().default(0),
        groupId: z.string().optional(),
        phase: z.string().optional(),
        agentType: z.string().optional(),
        confidenceLevel: z.enum(["all", "high", "medium", "low"]).default("all"),
      })
    )
    .query(async ({ input }) => {
      try {
        const conditions = [
          eq(orchestrationLogs.sessionId, input.sessionId),
          eq(orchestrationLogs.logType, "reasoning"),
        ];
        if (input.groupId) {
          conditions.push(eq(orchestrationLogs.groupId, input.groupId));
        }
        if (input.phase) {
          conditions.push(eq(orchestrationLogs.reasoningPhase, input.phase));
        }
        if (input.agentType) {
          conditions.push(eq(orchestrationLogs.agentType, input.agentType));
        }
        if (input.confidenceLevel !== "all") {
          conditions.push(eq(orchestrationLogs.confidenceLevel, input.confidenceLevel));
        }

        const logs = await db
          .select()
          .from(orchestrationLogs)
          .where(and(...conditions))
          .orderBy(orchestrationLogs.timestamp)
          .limit(input.limit)
          .offset(input.offset);

        const totalResult = await db
          .select({ count: count() })
          .from(orchestrationLogs)
          .where(and(...conditions));

        return {
          logs: logs.map((log) => {
            // Parse references per-row to avoid one bad JSON breaking all results
            let references: string[] = [];
            if (log.referencesJson) {
              try {
                references = JSON.parse(log.referencesJson);
              } catch {
                // Malformed JSON - default to empty array
                references = [];
              }
            }
            return {
              ...log,
              redacted: log.redacted === 1,
              references,
            };
          }),
          total: totalResult[0]?.count || 0,
          hasMore: input.offset + logs.length < (totalResult[0]?.count || 0),
        };
      } catch {
        // log_type column doesn't exist in older DBs
        return { logs: [], total: 0, hasMore: false };
      }
    }),

  // Get reasoning summary/stats for a session
  getReasoningSummary: publicProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input }) => {
      try {
        const [total, byPhase, byAgent, byConfidence, redacted] = await Promise.all([
          db
            .select({ count: count() })
            .from(orchestrationLogs)
            .where(
              and(
                eq(orchestrationLogs.sessionId, input.sessionId),
                eq(orchestrationLogs.logType, "reasoning")
              )
            ),
          db
            .select({
              phase: orchestrationLogs.reasoningPhase,
              count: sql<number>`COUNT(*)`,
            })
            .from(orchestrationLogs)
            .where(
              and(
                eq(orchestrationLogs.sessionId, input.sessionId),
                eq(orchestrationLogs.logType, "reasoning")
              )
            )
            .groupBy(orchestrationLogs.reasoningPhase),
          db
            .select({
              agent: orchestrationLogs.agentType,
              count: sql<number>`COUNT(*)`,
            })
            .from(orchestrationLogs)
            .where(
              and(
                eq(orchestrationLogs.sessionId, input.sessionId),
                eq(orchestrationLogs.logType, "reasoning")
              )
            )
            .groupBy(orchestrationLogs.agentType),
          db
            .select({
              level: orchestrationLogs.confidenceLevel,
              count: sql<number>`COUNT(*)`,
            })
            .from(orchestrationLogs)
            .where(
              and(
                eq(orchestrationLogs.sessionId, input.sessionId),
                eq(orchestrationLogs.logType, "reasoning")
              )
            )
            .groupBy(orchestrationLogs.confidenceLevel),
          db
            .select({ count: count() })
            .from(orchestrationLogs)
            .where(
              and(
                eq(orchestrationLogs.sessionId, input.sessionId),
                eq(orchestrationLogs.logType, "reasoning"),
                eq(orchestrationLogs.redacted, 1)
              )
            ),
        ]);

        return {
          totalEntries: total[0]?.count || 0,
          byPhase: Object.fromEntries(byPhase.map((p) => [p.phase || "unknown", p.count])),
          byAgent: Object.fromEntries(byAgent.map((a) => [a.agent, a.count])),
          byConfidence: Object.fromEntries(byConfidence.map((c) => [c.level || "unknown", c.count])),
          redactedCount: redacted[0]?.count || 0,
        };
      } catch {
        return {
          totalEntries: 0,
          byPhase: {},
          byAgent: {},
          byConfidence: {},
          redactedCount: 0,
        };
      }
    }),

  // Get events for a session (v9+)
  getEvents: publicProcedure
    .input(
      z.object({
        sessionId: z.string(),
        limit: z.number().min(1).max(100).default(50),
        offset: z.number().default(0),
        subtype: z.string().optional(),
      })
    )
    .query(async ({ input }) => {
      try {
        const conditions = [
          eq(orchestrationLogs.sessionId, input.sessionId),
          eq(orchestrationLogs.logType, "event"),
        ];
        if (input.subtype) {
          conditions.push(eq(orchestrationLogs.eventSubtype, input.subtype));
        }

        const events = await db
          .select()
          .from(orchestrationLogs)
          .where(and(...conditions))
          .orderBy(orchestrationLogs.timestamp)
          .limit(input.limit)
          .offset(input.offset);

        return events.map((event) => {
          // Parse eventPayload per-row to avoid one bad JSON breaking all results
          let eventPayload = null;
          if (event.eventPayload) {
            try {
              eventPayload = JSON.parse(event.eventPayload);
            } catch {
              // Malformed JSON - keep as null
              eventPayload = null;
            }
          }
          return {
            id: event.id,
            sessionId: event.sessionId,
            timestamp: event.timestamp,
            agentType: event.agentType,
            eventSubtype: event.eventSubtype,
            eventPayload,
          };
        });
      } catch {
        return [];
      }
    }),

  // ============================================================================
  // SUCCESS CRITERIA QUERIES (v4+)
  // ============================================================================

  // Get success criteria for a session
  getSuccessCriteria: publicProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input }) => {
      try {
        const criteria = await db
          .select()
          .from(successCriteria)
          .where(eq(successCriteria.sessionId, input.sessionId))
          .orderBy(successCriteria.id);

        return criteria;
      } catch {
        return [];
      }
    }),

  // Get success criteria summary
  // ACTUAL status values: 'pending' | 'met' | 'blocked' | 'failed'
  getCriteriaSummary: publicProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input }) => {
      try {
        const criteria = await db
          .select()
          .from(successCriteria)
          .where(eq(successCriteria.sessionId, input.sessionId));

        let met = 0,
          pending = 0,
          blocked = 0,
          failed = 0;

        for (const c of criteria) {
          if (c.status === "met") {
            met++;
          } else if (c.status === "blocked") {
            blocked++;
          } else if (c.status === "failed") {
            failed++;
          } else {
            pending++;
          }
        }

        return {
          total: criteria.length,
          met,
          pending,
          blocked,
          failed,
        };
      } catch {
        return { total: 0, met: 0, pending: 0, blocked: 0, failed: 0 };
      }
    }),

  // ============================================================================
  // CONTEXT PACKAGES QUERIES (v4/v10+)
  // ============================================================================

  // Get context packages for a session
  getContextPackages: publicProcedure
    .input(
      z.object({
        sessionId: z.string(),
        groupId: z.string().optional(),
        packageType: z.string().optional(),
        priority: z.enum(["all", "low", "medium", "high", "critical"]).default("all"),
      })
    )
    .query(async ({ input }) => {
      try {
        const conditions = [eq(contextPackages.sessionId, input.sessionId)];
        if (input.groupId) {
          conditions.push(eq(contextPackages.groupId, input.groupId));
        }
        if (input.packageType) {
          conditions.push(eq(contextPackages.packageType, input.packageType));
        }
        if (input.priority !== "all") {
          conditions.push(eq(contextPackages.priority, input.priority));
        }

        const packages = await db
          .select()
          .from(contextPackages)
          .where(and(...conditions))
          .orderBy(desc(contextPackages.createdAt));

        return packages;
      } catch {
        return [];
      }
    }),

  // Get context package consumers
  getContextConsumers: publicProcedure
    .input(z.object({ packageId: z.number() }))
    .query(async ({ input }) => {
      try {
        const consumers = await db
          .select()
          .from(contextPackageConsumers)
          .where(eq(contextPackageConsumers.packageId, input.packageId))
          .orderBy(contextPackageConsumers.consumedAt);

        return consumers;
      } catch {
        return [];
      }
    }),

  // ============================================================================
  // TOKEN & METRICS QUERIES
  // ============================================================================

  // Get token usage breakdown for a session
  getTokenBreakdown: publicProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input }) => {
      const breakdown = await db
        .select({
          agentType: tokenUsage.agentType,
          total: sql<number>`SUM(${tokenUsage.tokensEstimated})`,
        })
        .from(tokenUsage)
        .where(eq(tokenUsage.sessionId, input.sessionId))
        .groupBy(tokenUsage.agentType);

      const timeline = await db
        .select()
        .from(tokenUsage)
        .where(eq(tokenUsage.sessionId, input.sessionId))
        .orderBy(tokenUsage.timestamp);

      return { breakdown, timeline };
    }),

  // Get agent performance metrics across all sessions
  getAgentMetrics: publicProcedure.query(async () => {
    const tokensByAgent = await db
      .select({
        agentType: tokenUsage.agentType,
        totalTokens: sql<number>`SUM(${tokenUsage.tokensEstimated})`,
        invocations: sql<number>`COUNT(*)`,
      })
      .from(tokenUsage)
      .groupBy(tokenUsage.agentType);

    const logsByAgent = await db
      .select({
        agentType: orchestrationLogs.agentType,
        logCount: sql<number>`COUNT(*)`,
      })
      .from(orchestrationLogs)
      .groupBy(orchestrationLogs.agentType);

    const revisionStats = await db
      .select({
        totalGroups: sql<number>`COUNT(*)`,
        revisedGroups: sql<number>`SUM(CASE WHEN ${taskGroups.revisionCount} > 1 THEN 1 ELSE 0 END)`,
        avgRevisions: sql<number>`AVG(${taskGroups.revisionCount})`,
      })
      .from(taskGroups);

    return {
      tokensByAgent,
      logsByAgent,
      revisionStats: revisionStats[0] || { totalGroups: 0, revisedGroups: 0, avgRevisions: 0 },
    };
  }),

  // ============================================================================
  // SKILL OUTPUTS QUERIES (v11-12+)
  // ============================================================================

  // Get skill outputs for a session
  getSkillOutputs: publicProcedure
    .input(
      z.object({
        sessionId: z.string(),
        skillName: z.string().optional(),
        agentType: z.string().optional(),
        groupId: z.string().optional(),
      })
    )
    .query(async ({ input }) => {
      const conditions = [eq(skillOutputs.sessionId, input.sessionId)];
      if (input.skillName) {
        conditions.push(eq(skillOutputs.skillName, input.skillName));
      }
      if (input.agentType) {
        conditions.push(eq(skillOutputs.agentType, input.agentType));
      }
      if (input.groupId) {
        conditions.push(eq(skillOutputs.groupId, input.groupId));
      }

      const outputs = await db
        .select()
        .from(skillOutputs)
        .where(and(...conditions))
        .orderBy(desc(skillOutputs.timestamp));

      return outputs.map((output) => ({
        ...output,
        outputData: (() => {
          try {
            return JSON.parse(output.outputData);
          } catch {
            return output.outputData;
          }
        })(),
      }));
    }),

  // NOTE: getDecisions removed - decisions table does not exist in init_db.py
  // Decision data is now stored in orchestration_logs with log_type='event'
});
