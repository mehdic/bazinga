"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { trpc } from "@/lib/trpc/client";
import { formatTokens } from "@/lib/utils";
import {
  Activity,
  TrendingUp,
  Clock,
  Zap,
  BarChart3,
  PieChart,
} from "lucide-react";

export default function AnalyticsPage() {
  const { data: stats } = trpc.sessions.getStats.useQuery();
  const { data: recentSessions } = trpc.sessions.list.useQuery({ limit: 10 });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Activity className="h-6 w-6" />
          Analytics
        </h1>
        <p className="text-muted-foreground">
          Insights and trends across all orchestration sessions
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
              {stats?.successRate.toFixed(1) || 0}%
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
            <CardTitle className="text-sm font-medium">Avg. Tokens/Session</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {stats?.totalSessions
                ? formatTokens(Math.round((stats.totalTokens || 0) / stats.totalSessions))
                : "0"}
            </div>
            <p className="text-xs text-muted-foreground">Per session average</p>
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

      {/* Charts Placeholder */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Sessions Over Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center rounded-lg border border-dashed">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  Chart visualization coming soon
                </p>
                <p className="text-xs text-muted-foreground">
                  Using Recharts for interactive charts
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Token Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center rounded-lg border border-dashed">
              <div className="text-center">
                <PieChart className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  Pie chart coming soon
                </p>
                <p className="text-xs text-muted-foreground">
                  Token breakdown by agent type
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
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
                    {session.mode} mode • {new Date(session.startTime).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <span
                    className={
                      session.status === "completed"
                        ? "text-green-500"
                        : session.status === "failed"
                        ? "text-red-500"
                        : "text-blue-500"
                    }
                  >
                    {session.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
