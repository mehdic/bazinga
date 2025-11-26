"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { trpc } from "@/lib/trpc/client";
import { formatTokens } from "@/lib/utils";
import {
  Activity,
  CheckCircle2,
  XCircle,
  Zap,
} from "lucide-react";

export function StatsCards() {
  const { data: stats, isLoading } = trpc.sessions.getStats.useQuery();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 rounded bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const cards = [
    {
      title: "Total Sessions",
      value: stats.totalSessions,
      icon: Activity,
      description: `${stats.activeSessions} active`,
      color: "text-blue-500",
    },
    {
      title: "Completed",
      value: stats.completedSessions,
      icon: CheckCircle2,
      description: `${stats.successRate.toFixed(1)}% success rate`,
      color: "text-green-500",
    },
    {
      title: "Failed",
      value: stats.failedSessions,
      icon: XCircle,
      description: "Sessions with errors",
      color: "text-red-500",
    },
    {
      title: "Total Tokens",
      value: formatTokens(stats.totalTokens),
      icon: Zap,
      description: "Across all sessions",
      color: "text-yellow-500",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
            <p className="text-xs text-muted-foreground">{card.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
