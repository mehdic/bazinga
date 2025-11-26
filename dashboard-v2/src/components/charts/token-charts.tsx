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
import { formatTokens } from "@/lib/utils";

// Color palette for agents
const AGENT_COLORS: Record<string, string> = {
  pm: "#8b5cf6",           // purple
  developer: "#3b82f6",    // blue
  qa_expert: "#22c55e",    // green
  tech_lead: "#f97316",    // orange
  orchestrator: "#6b7280", // gray
  investigator: "#ec4899", // pink
  senior_engineer: "#14b8a6", // teal
};

const MODEL_COLORS: Record<string, string> = {
  opus: "#f97316",    // orange
  sonnet: "#8b5cf6",  // purple
  haiku: "#22c55e",   // green
};

interface TokenBreakdownItem {
  agentType: string;
  modelTier: string | null;
  total: number | null;
  cost: number | null;
}

interface TokenTimelineItem {
  id: number;
  sessionId: string;
  agentType: string;
  agentId: string | null;
  modelTier: string | null;
  tokensUsed: number;
  estimatedCost: number | null;
  timestamp: string;
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
      model: item.modelTier || "unknown",
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
              fill={AGENT_COLORS[entry.name] || "#6b7280"}
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
    const date = new Date(item.timestamp);
    const bucket = `${date.getHours()}:${String(date.getMinutes()).padStart(2, "0")}`;

    if (!acc[bucket]) {
      acc[bucket] = { time: bucket, tokens: 0, cost: 0 };
    }
    acc[bucket].tokens += item.tokensUsed;
    acc[bucket].cost += item.estimatedCost || 0;
    return acc;
  }, {} as Record<string, { time: string; tokens: number; cost: number }>);

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

export function TokenByModelChart({ breakdown }: { breakdown: TokenBreakdownItem[] }) {
  // Group by model tier
  const modelData = breakdown.reduce((acc, item) => {
    const model = item.modelTier || "unknown";
    if (!acc[model]) {
      acc[model] = { model, tokens: 0, cost: 0 };
    }
    acc[model].tokens += item.total || 0;
    acc[model].cost += item.cost || 0;
    return acc;
  }, {} as Record<string, { model: string; tokens: number; cost: number }>);

  const data = Object.values(modelData).filter((item) => item.tokens > 0);

  if (data.length === 0) {
    return (
      <div className="flex h-[200px] items-center justify-center text-muted-foreground">
        No model data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          type="number"
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickFormatter={(value) => formatTokens(value)}
        />
        <YAxis
          type="category"
          dataKey="model"
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          width={60}
        />
        <Tooltip
          formatter={(value: number) => formatTokens(value)}
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
        />
        <Bar dataKey="tokens" name="Tokens">
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={MODEL_COLORS[entry.model] || "#6b7280"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TokenCostChart({ timeline }: { timeline: TokenTimelineItem[] }) {
  // Aggregate cost by agent type
  const agentCosts = timeline.reduce((acc, item) => {
    if (!acc[item.agentType]) {
      acc[item.agentType] = 0;
    }
    acc[item.agentType] += item.estimatedCost || 0;
    return acc;
  }, {} as Record<string, number>);

  const data = Object.entries(agentCosts)
    .filter(([_, cost]) => cost > 0)
    .map(([agent, cost]) => ({
      agent,
      cost: parseFloat(cost.toFixed(6)),
    }))
    .sort((a, b) => b.cost - a.cost);

  if (data.length === 0) {
    return (
      <div className="flex h-[200px] items-center justify-center text-muted-foreground">
        No cost data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="agent"
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickFormatter={(value) => `$${value.toFixed(4)}`}
        />
        <Tooltip
          formatter={(value: number) => [`$${value.toFixed(6)}`, "Cost"]}
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
        />
        <Bar dataKey="cost" name="Estimated Cost">
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={AGENT_COLORS[entry.agent] || "#6b7280"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
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
