"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { trpc } from "@/lib/trpc/client";
import { formatTokens, AGENT_COLORS_HEX } from "@/lib/utils";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Activity,
  TrendingUp,
  Zap,
  Bot,
  AlertTriangle,
  RefreshCw,
  User,
  Code,
  TestTube,
  GitPullRequest,
} from "lucide-react";

const AGENT_ICONS: Record<string, React.ElementType> = {
  pm: User,
  developer: Code,
  qa_expert: TestTube,
  tech_lead: GitPullRequest,
  orchestrator: Bot,
};

export default function AnalyticsPage() {
  const { data: stats } = trpc.sessions.getStats.useQuery();
  const { data: agentMetrics } = trpc.sessions.getAgentMetrics.useQuery();
  const { data: recentSessions } = trpc.sessions.list.useQuery({ limit: 10 });

  // Memoize chart data transformations to avoid recalculating on every render
  const tokensByAgentData = useMemo(
    () =>
      agentMetrics?.tokensByAgent.map((item) => ({
        name: item.agentType,
        tokens: item.totalTokens || 0,
        invocations: item.invocations || 0,
      })) || [],
    [agentMetrics?.tokensByAgent]
  );

  const logsByAgentData = useMemo(
    () =>
      agentMetrics?.logsByAgent.map((item) => ({
        name: item.agentType,
        total: item.logCount || 0,
      })) || [],
    [agentMetrics?.logsByAgent]
  );

  const revisionRate = useMemo(
    () =>
      agentMetrics?.revisionStats.totalGroups
        ? ((agentMetrics.revisionStats.revisedGroups || 0) /
            agentMetrics.revisionStats.totalGroups) *
          100
        : 0,
    [agentMetrics?.revisionStats]
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Activity className="h-6 w-6" />
          Analytics
        </h1>
        <p className="text-muted-foreground">
          Agent performance metrics and insights across all sessions
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-500">
              {(stats?.successRate ?? 0).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.completedSessions || 0} of {stats?.totalSessions || 0} sessions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens Used</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatTokens(stats?.totalTokens || 0)}
            </div>
            <p className="text-xs text-muted-foreground">Across all sessions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Revision Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-500">
              {revisionRate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {agentMetrics?.revisionStats.revisedGroups || 0} of{" "}
              {agentMetrics?.revisionStats.totalGroups || 0} groups
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-500">
              {stats?.activeSessions || 0}
            </div>
            <p className="text-xs text-muted-foreground">Currently running</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Token Distribution by Agent */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Tokens by Agent
            </CardTitle>
          </CardHeader>
          <CardContent>
            {tokensByAgentData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={tokensByAgentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="tokens"
                    label={({ name, percent }) =>
                      `${name} (${(percent * 100).toFixed(0)}%)`
                    }
                    labelLine={false}
                  >
                    {tokensByAgentData.map((entry) => (
                      <Cell
                        key={`token-${entry.name}`}
                        fill={AGENT_COLORS_HEX[entry.name] || "#6b7280"}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => formatTokens(value)}
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                No data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Invocations by Agent */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              Agent Invocations
            </CardTitle>
          </CardHeader>
          <CardContent>
            {logsByAgentData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={logsByAgentData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    type="number"
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                    width={80}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="total" name="Log Count">
                    {logsByAgentData.map((entry) => (
                      <Cell
                        key={`log-${entry.name}`}
                        fill={AGENT_COLORS_HEX[entry.name] || "#6b7280"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                No data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Agent Activity Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Agent Activity Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {logsByAgentData.map((agent) => {
              const Icon = AGENT_ICONS[agent.name] || Bot;
              const tokenData = tokensByAgentData.find((t) => t.name === agent.name);
              // Calculate relative share for progress bar
              const maxLogs = Math.max(...logsByAgentData.map(a => a.total), 1);
              const progressValue = (agent.total / maxLogs) * 100;
              return (
                <div
                  key={agent.name}
                  className="flex items-center gap-4 rounded-lg border p-4"
                >
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-full"
                    style={{ backgroundColor: `${AGENT_COLORS_HEX[agent.name]}20` }}
                  >
                    <Icon
                      className="h-5 w-5"
                      style={{ color: AGENT_COLORS_HEX[agent.name] }}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium capitalize">{agent.name.replaceAll("_", " ")}</span>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{agent.total} logs</Badge>
                        <Badge variant="secondary">
                          {formatTokens(tokenData?.tokens || 0)} tokens
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={progressValue} className="h-2 flex-1" />
                      <span className="text-sm text-muted-foreground w-20 text-right">
                        {tokenData?.invocations || 0} calls
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
            {logsByAgentData.length === 0 && (
              <div className="py-8 text-center text-muted-foreground">
                No agent data available yet
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Revision Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Revision Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold">
                {agentMetrics?.revisionStats.totalGroups || 0}
              </div>
              <p className="text-sm text-muted-foreground">Total Task Groups</p>
            </div>
            <div className="rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold text-yellow-500">
                {agentMetrics?.revisionStats.revisedGroups || 0}
              </div>
              <p className="text-sm text-muted-foreground">Required Revisions</p>
            </div>
            <div className="rounded-lg border p-4 text-center">
              <div className="text-3xl font-bold">
                {(agentMetrics?.revisionStats.avgRevisions || 0).toFixed(1)}
              </div>
              <p className="text-sm text-muted-foreground">Avg Revisions/Group</p>
            </div>
          </div>
          {revisionRate > 30 && (
            <div className="mt-4 rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4">
              <div className="flex items-center gap-2 text-yellow-500">
                <AlertTriangle className="h-5 w-5" />
                <span className="font-medium">High Revision Rate Detected</span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                Consider reviewing requirement clarity or adding validation checkpoints
                to reduce the need for revisions.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Recent Session Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentSessions?.sessions.map((session) => (
              <div
                key={session.sessionId}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div>
                  <p className="font-medium">
                    #{session.sessionId.split("_").pop()?.slice(0, 8)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {session.mode} mode • {session.startTime ? new Date(session.startTime).toLocaleDateString() : "Unknown"}
                  </p>
                </div>
                <div className="text-right">
                  <Badge
                    variant={
                      session.status === "completed"
                        ? "secondary"
                        : session.status === "failed"
                        ? "destructive"
                        : "default"
                    }
                  >
                    {session.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
