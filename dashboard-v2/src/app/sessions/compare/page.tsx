"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { trpc } from "@/lib/trpc/client";
import { formatDuration, formatTokens, timeAgo } from "@/lib/utils";
import {
  ArrowLeft,
  ArrowLeftRight,
  Clock,
  Users,
  Zap,
  CheckCircle2,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

export default function CompareSessionsPage() {
  const [sessionA, setSessionA] = useState<string>("");
  const [sessionB, setSessionB] = useState<string>("");

  const { data: sessions } = trpc.sessions.list.useQuery({
    limit: 50,
    offset: 0,
    status: "all",
  });

  const { data: dataA } = trpc.sessions.getById.useQuery(
    { sessionId: sessionA },
    { enabled: !!sessionA }
  );

  const { data: dataB } = trpc.sessions.getById.useQuery(
    { sessionId: sessionB },
    { enabled: !!sessionB }
  );

  const { data: tokensA } = trpc.sessions.getTokenBreakdown.useQuery(
    { sessionId: sessionA },
    { enabled: !!sessionA }
  );

  const { data: tokensB } = trpc.sessions.getTokenBreakdown.useQuery(
    { sessionId: sessionB },
    { enabled: !!sessionB }
  );

  const totalTokensA = tokensA?.breakdown.reduce((sum, b) => sum + (b.total || 0), 0) || 0;
  const totalTokensB = tokensB?.breakdown.reduce((sum, b) => sum + (b.total || 0), 0) || 0;

  const getDurationMs = (session: typeof dataA) => {
    if (!session || !session.startTime) return 0;
    const start = new Date(session.startTime).getTime();
    const end = session.endTime ? new Date(session.endTime).getTime() : Date.now();
    return end - start;
  };

  const durationA = getDurationMs(dataA);
  const durationB = getDurationMs(dataB);

  // Revision-based metrics (actual DB has revisionCount, not successCriteria)
  const totalRevisionsA = dataA?.taskGroups?.reduce((sum, g) => sum + (g.revisionCount || 0), 0) || 0;
  const totalRevisionsB = dataB?.taskGroups?.reduce((sum, g) => sum + (g.revisionCount || 0), 0) || 0;

  const getTrend = (a: number, b: number, lowerIsBetter = false) => {
    if (a === b) return <Minus className="h-4 w-4 text-muted-foreground" />;
    const aIsBetter = lowerIsBetter ? a < b : a > b;
    return aIsBetter ? (
      <TrendingUp className="h-4 w-4 text-green-500" />
    ) : (
      <TrendingDown className="h-4 w-4 text-red-500" />
    );
  };

  const getPercentDiff = (a: number, b: number) => {
    if (b === 0) return a > 0 ? "+100%" : "0%";
    const diff = ((a - b) / b) * 100;
    return diff > 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/sessions">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ArrowLeftRight className="h-6 w-6" />
            Compare Sessions
          </h1>
          <p className="text-sm text-muted-foreground">
            Side-by-side comparison of orchestration sessions
          </p>
        </div>
      </div>

      {/* Session Selectors */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Session A</CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={sessionA} onValueChange={setSessionA}>
              <SelectTrigger>
                <SelectValue placeholder="Select a session" />
              </SelectTrigger>
              <SelectContent>
                {sessions?.sessions.map((s) => (
                  <SelectItem
                    key={s.sessionId}
                    value={s.sessionId}
                    disabled={s.sessionId === sessionB}
                  >
                    {s.sessionId.split("_").pop()?.slice(0, 8)} - {s.status} (
                    {timeAgo(s.startTime)})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Session B</CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={sessionB} onValueChange={setSessionB}>
              <SelectTrigger>
                <SelectValue placeholder="Select a session" />
              </SelectTrigger>
              <SelectContent>
                {sessions?.sessions.map((s) => (
                  <SelectItem
                    key={s.sessionId}
                    value={s.sessionId}
                    disabled={s.sessionId === sessionA}
                  >
                    {s.sessionId.split("_").pop()?.slice(0, 8)} - {s.status} (
                    {timeAgo(s.startTime)})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      </div>

      {/* Comparison Results */}
      {dataA && dataB && (
        <>
          {/* Overview Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Overview Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {/* Status */}
                <div className="grid grid-cols-3 gap-4 items-center">
                  <div className="text-right">
                    <Badge
                      variant={
                        dataA.status === "completed" ? "secondary" : "destructive"
                      }
                    >
                      {dataA.status}
                    </Badge>
                  </div>
                  <div className="text-center text-sm text-muted-foreground">
                    Status
                  </div>
                  <div className="text-left">
                    <Badge
                      variant={
                        dataB.status === "completed" ? "secondary" : "destructive"
                      }
                    >
                      {dataB.status}
                    </Badge>
                  </div>
                </div>

                <Separator />

                {/* Mode */}
                <div className="grid grid-cols-3 gap-4 items-center">
                  <div className="text-right flex items-center justify-end gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="capitalize">{dataA.mode || "unknown"}</span>
                  </div>
                  <div className="text-center text-sm text-muted-foreground">
                    Mode
                  </div>
                  <div className="text-left flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="capitalize">{dataB.mode || "unknown"}</span>
                  </div>
                </div>

                <Separator />

                {/* Duration */}
                <div className="grid grid-cols-3 gap-4 items-center">
                  <div className="text-right flex items-center justify-end gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{formatDuration(durationA)}</span>
                    {getTrend(durationB, durationA, true)}
                  </div>
                  <div className="text-center text-sm text-muted-foreground">
                    Duration
                  </div>
                  <div className="text-left flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{formatDuration(durationB)}</span>
                    <span className="text-xs text-muted-foreground">
                      ({getPercentDiff(durationB, durationA)})
                    </span>
                  </div>
                </div>

                <Separator />

                {/* Tokens */}
                <div className="grid grid-cols-3 gap-4 items-center">
                  <div className="text-right flex items-center justify-end gap-2">
                    <Zap className="h-4 w-4 text-muted-foreground" />
                    <span>{formatTokens(totalTokensA)}</span>
                    {getTrend(totalTokensB, totalTokensA, true)}
                  </div>
                  <div className="text-center text-sm text-muted-foreground">
                    Total Tokens
                  </div>
                  <div className="text-left flex items-center gap-2">
                    <Zap className="h-4 w-4 text-muted-foreground" />
                    <span>{formatTokens(totalTokensB)}</span>
                    <span className="text-xs text-muted-foreground">
                      ({getPercentDiff(totalTokensB, totalTokensA)})
                    </span>
                  </div>
                </div>

                <Separator />

                {/* Task Groups */}
                <div className="grid grid-cols-3 gap-4 items-center">
                  <div className="text-right">
                    <span>{dataA.taskGroups?.length || 0} groups</span>
                  </div>
                  <div className="text-center text-sm text-muted-foreground">
                    Task Groups
                  </div>
                  <div className="text-left">
                    <span>{dataB.taskGroups?.length || 0} groups</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Revisions Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Task Groups & Revisions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {/* Session A Task Groups */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Session A</span>
                    <Badge variant="outline">
                      {totalRevisionsA} total revisions
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    {dataA.taskGroups?.map((g) => (
                      <div
                        key={g.id}
                        className="flex items-center gap-2 text-sm"
                      >
                        {g.status === "completed" ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="truncate flex-1">{g.name}</span>
                        <Badge variant="secondary" className="text-xs">
                          {g.revisionCount || 0} rev
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Session B Task Groups */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Session B</span>
                    <Badge variant="outline">
                      {totalRevisionsB} total revisions
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    {dataB.taskGroups?.map((g) => (
                      <div
                        key={g.id}
                        className="flex items-center gap-2 text-sm"
                      >
                        {g.status === "completed" ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="truncate flex-1">{g.name}</span>
                        <Badge variant="secondary" className="text-xs">
                          {g.revisionCount || 0} rev
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Token Breakdown Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Token Usage by Agent</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {/* Session A Tokens */}
                <div className="space-y-3">
                  <span className="font-medium">Session A</span>
                  <div className="space-y-2">
                    {tokensA?.breakdown.map((item, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between text-sm"
                      >
                        <span>{item.agentType}</span>
                        <span className="font-mono">
                          {formatTokens(item.total || 0)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Session B Tokens */}
                <div className="space-y-3">
                  <span className="font-medium">Session B</span>
                  <div className="space-y-2">
                    {tokensB?.breakdown.map((item, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between text-sm"
                      >
                        <span>{item.agentType}</span>
                        <span className="font-mono">
                          {formatTokens(item.total || 0)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Empty state */}
      {(!sessionA || !sessionB) && (
        <Card>
          <CardContent className="py-12 text-center">
            <ArrowLeftRight className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              Select two sessions above to compare them
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
