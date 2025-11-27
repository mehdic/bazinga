"use client";

import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatTokens, AGENT_COLORS_HEX } from "@/lib/utils";

// Matches actual database schema - no modelTier, cost, or estimatedCost columns
interface TokenBreakdownItem {
  agentType: string;
  total: number | null;
}

interface TokenTimelineItem {
  id: number;
  sessionId: string;
  agentType: string;
  agentId: string | null;
  tokensEstimated: number;
  timestamp: string | null;
}

interface TokenChartsProps {
  breakdown: TokenBreakdownItem[];
  timeline: TokenTimelineItem[];
}

export function TokenPieChart({ breakdown }: { breakdown: TokenBreakdownItem[] }) {
  const data = breakdown
    .filter((item) => item.total && item.total > 0)
    .map((item) => ({
      name: item.agentType,
      value: item.total || 0,
    }));

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
        No token data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          label={({ name, percent }) =>
            `${name} (${(percent * 100).toFixed(0)}%)`
          }
          labelLine={false}
        >
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
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
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function TokenTimelineChart({ timeline }: { timeline: TokenTimelineItem[] }) {
  // Group tokens by timestamp (bucketed by minute)
  const bucketedData = timeline.reduce((acc, item) => {
    if (!item.timestamp) return acc;
    const date = new Date(item.timestamp);
    const bucket = `${date.getHours()}:${String(date.getMinutes()).padStart(2, "0")}`;

    if (!acc[bucket]) {
      acc[bucket] = { time: bucket, tokens: 0 };
    }
    acc[bucket].tokens += item.tokensEstimated;
    return acc;
  }, {} as Record<string, { time: string; tokens: number }>);

  const data = Object.values(bucketedData);

  // Calculate cumulative tokens
  let cumulative = 0;
  const cumulativeData = data.map((item) => {
    cumulative += item.tokens;
    return { ...item, cumulative };
  });

  if (cumulativeData.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
        No timeline data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={cumulativeData}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="time"
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickFormatter={(value) => formatTokens(value)}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            formatTokens(value),
            name === "cumulative" ? "Total Tokens" : "Tokens",
          ]}
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="cumulative"
          name="Cumulative Tokens"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="tokens"
          name="Per Minute"
          stroke="#22c55e"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// TokenByModelChart removed - modelTier column not in actual database schema
// Keeping function signature for backwards compatibility
export function TokenByModelChart({ breakdown: _breakdown }: { breakdown: TokenBreakdownItem[] }) {
  return (
    <div className="flex h-[200px] items-center justify-center text-muted-foreground">
      Model tier data not available
    </div>
  );
}

// TokenCostChart removed - estimatedCost column not in actual database schema
// Keeping function signature for backwards compatibility
export function TokenCostChart({ timeline: _timeline }: { timeline: TokenTimelineItem[] }) {
  return (
    <div className="flex h-[200px] items-center justify-center text-muted-foreground">
      Cost data not available
    </div>
  );
}

export function TokenCharts({ breakdown, timeline }: TokenChartsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Token Distribution by Agent</CardTitle>
        </CardHeader>
        <CardContent>
          <TokenPieChart breakdown={breakdown} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Token Consumption Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <TokenTimelineChart timeline={timeline} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Tokens by Model Tier</CardTitle>
        </CardHeader>
        <CardContent>
          <TokenByModelChart breakdown={breakdown} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Estimated Cost by Agent</CardTitle>
        </CardHeader>
        <CardContent>
          <TokenCostChart timeline={timeline} />
        </CardContent>
      </Card>
    </div>
  );
}
