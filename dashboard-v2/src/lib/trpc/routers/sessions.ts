import { z } from "zod";
import { router, publicProcedure } from "../server";
import { db } from "../../db/client";
import { sessions, orchestrationLogs, taskGroups, successCriteria, tokenUsage, stateSnapshots } from "../../db/schema";
import { desc, eq, and, gte, lte, like, count, sql } from "drizzle-orm";

export const sessionsRouter = router({
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
      let query = db.select().from(sessions);

      // Build where conditions
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

      // Get total count for pagination
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

      // Fetch related data
      const [logs, groups, criteria, tokens, snapshots] = await Promise.all([
        db
          .select()
          .from(orchestrationLogs)
          .where(eq(orchestrationLogs.sessionId, input.sessionId))
          .orderBy(desc(orchestrationLogs.timestamp))
          .limit(200),
        db
          .select()
          .from(taskGroups)
          .where(eq(taskGroups.sessionId, input.sessionId)),
        db
          .select()
          .from(successCriteria)
          .where(eq(successCriteria.sessionId, input.sessionId)),
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

      return {
        ...session[0],
        logs,
        taskGroups: groups,
        successCriteria: criteria,
        tokenUsage: tokens,
        stateSnapshots: snapshots,
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

    // Get total tokens
    const tokensResult = await db
      .select({ total: sql<number>`COALESCE(SUM(${tokenUsage.tokensUsed}), 0)` })
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

  // Get recent logs for a session
  getLogs: publicProcedure
    .input(
      z.object({
        sessionId: z.string(),
        limit: z.number().default(50),
        offset: z.number().default(0),
        agentType: z.string().optional(),
      })
    )
    .query(async ({ input }) => {
      const conditions = [eq(orchestrationLogs.sessionId, input.sessionId)];
      if (input.agentType) {
        conditions.push(eq(orchestrationLogs.agentType, input.agentType));
      }

      const logs = await db
        .select()
        .from(orchestrationLogs)
        .where(and(...conditions))
        .orderBy(desc(orchestrationLogs.timestamp))
        .limit(input.limit)
        .offset(input.offset);

      return logs;
    }),

  // Get token usage breakdown for a session
  getTokenBreakdown: publicProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input }) => {
      const breakdown = await db
        .select({
          agentType: tokenUsage.agentType,
          modelTier: tokenUsage.modelTier,
          total: sql<number>`SUM(${tokenUsage.tokensUsed})`,
          cost: sql<number>`SUM(${tokenUsage.estimatedCost})`,
        })
        .from(tokenUsage)
        .where(eq(tokenUsage.sessionId, input.sessionId))
        .groupBy(tokenUsage.agentType, tokenUsage.modelTier);

      const timeline = await db
        .select()
        .from(tokenUsage)
        .where(eq(tokenUsage.sessionId, input.sessionId))
        .orderBy(tokenUsage.timestamp);

      return { breakdown, timeline };
    }),

  // Get agent performance metrics across all sessions
  getAgentMetrics: publicProcedure.query(async () => {
    // Tokens by agent type
    const tokensByAgent = await db
      .select({
        agentType: tokenUsage.agentType,
        totalTokens: sql<number>`SUM(${tokenUsage.tokensUsed})`,
        totalCost: sql<number>`SUM(${tokenUsage.estimatedCost})`,
        invocations: sql<number>`COUNT(*)`,
      })
      .from(tokenUsage)
      .groupBy(tokenUsage.agentType);

    // Tokens by model tier
    const tokensByModel = await db
      .select({
        modelTier: tokenUsage.modelTier,
        totalTokens: sql<number>`SUM(${tokenUsage.tokensUsed})`,
        totalCost: sql<number>`SUM(${tokenUsage.estimatedCost})`,
        invocations: sql<number>`COUNT(*)`,
      })
      .from(tokenUsage)
      .groupBy(tokenUsage.modelTier);

    // Log counts by agent (activity level)
    const logsByAgent = await db
      .select({
        agentType: orchestrationLogs.agentType,
        logCount: sql<number>`COUNT(*)`,
        blockedCount: sql<number>`SUM(CASE WHEN ${orchestrationLogs.statusCode} = 'BLOCKED' THEN 1 ELSE 0 END)`,
        failedCount: sql<number>`SUM(CASE WHEN ${orchestrationLogs.statusCode} = 'FAILED' THEN 1 ELSE 0 END)`,
      })
      .from(orchestrationLogs)
      .groupBy(orchestrationLogs.agentType);

    // Revision patterns (task groups with multiple revisions)
    const revisionStats = await db
      .select({
        totalGroups: sql<number>`COUNT(*)`,
        revisedGroups: sql<number>`SUM(CASE WHEN ${taskGroups.revisionCount} > 1 THEN 1 ELSE 0 END)`,
        avgRevisions: sql<number>`AVG(${taskGroups.revisionCount})`,
      })
      .from(taskGroups);

    return {
      tokensByAgent,
      tokensByModel,
      logsByAgent,
      revisionStats: revisionStats[0] || { totalGroups: 0, revisedGroups: 0, avgRevisions: 0 },
    };
  }),
});
