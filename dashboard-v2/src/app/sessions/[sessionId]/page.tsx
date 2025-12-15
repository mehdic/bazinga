"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { trpc } from "@/lib/trpc/client";
import { cn, formatDuration, formatTokens } from "@/lib/utils";
import {
  ArrowLeft,
  Clock,
  Users,
  Zap,
  XCircle,
  Bot,
  FileText,
  BarChart3,
  Shield,
  Sparkles,
  GitBranch,
  Play,
  Workflow,
  Wand2,
  Brain,
  Target,
} from "lucide-react";
import { useEffect, useState } from "react";
import { TokenCharts } from "@/components/charts/token-charts";
import { StateMachine } from "@/components/workflow/state-machine";
import { LogFilters } from "@/components/logs/log-filters";
import { SessionReplay } from "@/components/replay/session-replay";
import { SkillOutputViewer } from "@/components/skills/skill-output-viewer";
import { SessionHeader } from "@/components/session/session-header";
import { useRefetchInterval } from "@/lib/hooks/use-smart-refetch";
import { ReasoningViewer } from "@/components/reasoning/reasoning-viewer";
import { SuccessCriteriaViewer } from "@/components/criteria/success-criteria-viewer";

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  // Smart refetch: no polling when socket connected, 5s fallback when disconnected
  const refetchInterval = useRefetchInterval(5000);

  const { data: session, isLoading } = trpc.sessions.getById.useQuery(
    { sessionId },
    { enabled: !!sessionId, refetchInterval }
  );

  const { data: tokenData } = trpc.sessions.getTokenBreakdown.useQuery(
    { sessionId },
    { enabled: !!sessionId }
  );

  const { data: skillOutputs } = trpc.sessions.getSkillOutputs.useQuery(
    { sessionId },
    { enabled: !!sessionId }
  );

  const { data: capabilities } = trpc.sessions.getCapabilities.useQuery();

  const [elapsed, setElapsed] = useState(0);

  // Extract specific properties to avoid re-running effect on any session change
  const sessionStatus = session?.status;
  const sessionStartTime = session?.startTime;

  useEffect(() => {
    if (sessionStatus !== "active" || !sessionStartTime) return;

    const start = new Date(sessionStartTime).getTime();
    // Set initial elapsed immediately to avoid hydration flash
    setElapsed(Date.now() - start);

    const interval = setInterval(() => {
      setElapsed(Date.now() - start);
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionStatus, sessionStartTime]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <XCircle className="h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-lg font-medium">Session not found</h2>
        <p className="text-sm text-muted-foreground mb-4">
          The session you&apos;re looking for doesn&apos;t exist.
        </p>
        <Link href="/sessions">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Sessions
          </Button>
        </Link>
      </div>
    );
  }

  const taskGroups = session.taskGroups || [];
  const completedGroups = taskGroups.filter((g) => g.status === "completed").length;
  const progress = taskGroups.length > 0 ? (completedGroups / taskGroups.length) * 100 : 0;
  const totalTokens = tokenData?.breakdown.reduce((sum, b) => sum + (b.total || 0), 0) || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <SessionHeader
        sessionId={session.sessionId}
        status={session.status}
        startTime={session.startTime}
        mode={session.mode}
        originalRequirements={session.originalRequirements}
        logs={session.logs?.map((log) => ({
          id: log.id,
          agentType: log.agentType,
          content: log.content,
          timestamp: log.timestamp,
        }))}
        taskGroups={session.taskGroups?.map((group) => ({
          id: group.id,
          name: group.name,
          status: group.status,
          revisionCount: group.revisionCount,
          assignedTo: group.assignedTo,
          complexity: group.complexity,
        }))}
        tokenUsage={session.tokenUsage?.map((usage) => ({
          agentType: usage.agentType,
          tokensEstimated: usage.tokensEstimated,
          timestamp: usage.timestamp,
        }))}
        endTime={session.endTime}
      />

      {/* Session Info Card */}
      <Card>
        <CardContent className="p-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <span className="text-sm text-muted-foreground">Mode</span>
              <p className="font-medium flex items-center gap-2">
                <Users className="h-4 w-4" />
                {session.mode === "parallel" ? "Parallel Mode" : "Simple Mode"}
              </p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Duration</span>
              <p className="font-medium flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {session.status === "active"
                  ? formatDuration(elapsed)
                  : session.endTime && session.startTime
                  ? formatDuration(
                      new Date(session.endTime).getTime() -
                        new Date(session.startTime).getTime()
                    )
                  : "Unknown"}
              </p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Total Tokens</span>
              <p className="font-medium flex items-center gap-2">
                <Zap className="h-4 w-4" />
                {formatTokens(totalTokens)}
              </p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Progress</span>
              <div className="flex items-center gap-2">
                <Progress value={progress} className="h-2 flex-1" />
                <span className="text-sm font-medium">{progress.toFixed(0)}%</span>
              </div>
            </div>
          </div>

          {session.originalRequirements && (
            <>
              <Separator className="my-4" />
              <div>
                <span className="text-sm text-muted-foreground">Requirements</span>
                <p className="mt-1">{session.originalRequirements}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="workflow" className="space-y-4">
        <TabsList className="flex flex-wrap gap-1">
          <TabsTrigger value="workflow">
            <Workflow className="h-4 w-4 mr-1" />
            Workflow
          </TabsTrigger>
          <TabsTrigger value="replay">
            <Play className="h-4 w-4 mr-1" />
            Replay
          </TabsTrigger>
          <TabsTrigger value="tasks">
            <GitBranch className="h-4 w-4 mr-1" />
            Tasks
          </TabsTrigger>
          <TabsTrigger value="logs">
            <FileText className="h-4 w-4 mr-1" />
            Logs
          </TabsTrigger>
          {capabilities?.hasReasoningColumns && (
            <TabsTrigger value="reasoning">
              <Brain className="h-4 w-4 mr-1" />
              Reasoning
            </TabsTrigger>
          )}
          {capabilities?.hasSuccessCriteria && (
            <TabsTrigger value="criteria">
              <Target className="h-4 w-4 mr-1" />
              Criteria
            </TabsTrigger>
          )}
          <TabsTrigger value="tokens">
            <Zap className="h-4 w-4 mr-1" />
            Tokens
          </TabsTrigger>
          <TabsTrigger value="skills">
            <Wand2 className="h-4 w-4 mr-1" />
            Skills
          </TabsTrigger>
          <TabsTrigger value="quality">
            <Shield className="h-4 w-4 mr-1" />
            Quality
          </TabsTrigger>
          <TabsTrigger value="timeline">
            <BarChart3 className="h-4 w-4 mr-1" />
            Timeline
          </TabsTrigger>
          <TabsTrigger value="insights">
            <Sparkles className="h-4 w-4 mr-1" />
            Insights
          </TabsTrigger>
        </TabsList>

        {/* Workflow Tab */}
        <TabsContent value="workflow">
          <Card>
            <CardHeader>
              <CardTitle>Orchestration Workflow</CardTitle>
            </CardHeader>
            <CardContent>
              <StateMachine
                logs={session.logs || []}
                taskGroups={taskGroups}
                sessionStatus={session.status}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Replay Tab */}
        <TabsContent value="replay">
          <SessionReplay
            logs={session.logs || []}
            sessionStatus={session.status}
          />
        </TabsContent>

        {/* Tasks Tab */}
        <TabsContent value="tasks" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {taskGroups.map((group) => (
              <Card key={group.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{group.name}</CardTitle>
                    <Badge
                      variant={
                        group.status === "completed"
                          ? "secondary"
                          : group.status === "failed"
                          ? "destructive"
                          : "outline"
                      }
                    >
                      {group.status || "pending"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Revisions</span>
                    <span
                      className={cn(
                        (group.revisionCount ?? 0) > 1 && "text-yellow-500",
                        (group.revisionCount ?? 0) > 2 && "text-red-500"
                      )}
                    >
                      {group.revisionCount ?? 0}
                    </span>
                  </div>
                  {group.assignedTo && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Assigned</span>
                      <span className="flex items-center gap-1">
                        <Bot className="h-3 w-3" />
                        {group.assignedTo}
                      </span>
                    </div>
                  )}
                  {group.complexity && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Complexity</span>
                      <span>{group.complexity}/10</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
          {taskGroups.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <GitBranch className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">No task groups yet</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs">
          <LogFilters logs={session.logs || []} />
        </TabsContent>

        {/* Reasoning Tab (v8+) */}
        {capabilities?.hasReasoningColumns && (
          <TabsContent value="reasoning">
            <ReasoningViewer sessionId={sessionId} />
          </TabsContent>
        )}

        {/* Success Criteria Tab (v4+) */}
        {capabilities?.hasSuccessCriteria && (
          <TabsContent value="criteria">
            <SuccessCriteriaViewer sessionId={sessionId} />
          </TabsContent>
        )}

        {/* Tokens Tab */}
        <TabsContent value="tokens">
          <div className="space-y-4">
            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Total Tokens</div>
                  <div className="text-2xl font-bold">{formatTokens(totalTokens)}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Estimated Cost</div>
                  <div className="text-2xl font-bold">
                    ${((totalTokens / 1000000) * 3).toFixed(4)}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Est. at $3/1M tokens
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Avg per Agent</div>
                  <div className="text-2xl font-bold">
                    {tokenData?.breakdown && tokenData.breakdown.length > 0
                      ? formatTokens(Math.round(totalTokens / tokenData.breakdown.length))
                      : "0"}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Charts */}
            {tokenData?.breakdown && tokenData?.timeline ? (
              <TokenCharts
                breakdown={tokenData.breakdown}
                timeline={tokenData.timeline}
              />
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <Zap className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No token data yet</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Skills Tab */}
        <TabsContent value="skills">
          <SkillOutputViewer outputs={skillOutputs || []} />
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality">
          <Card>
            <CardHeader>
              <CardTitle>Quality Checks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="py-12 text-center">
                <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  Quality metrics from skill outputs will appear here
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Check the Skills tab for detailed analysis results
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline">
          <Card>
            <CardHeader>
              <CardTitle>Agent Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />
                <div className="space-y-4 pl-10">
                  {session.logs?.slice(0, 20).map((log, i) => (
                    <div key={log.id} className="relative">
                      <div
                        className={cn(
                          "absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-background",
                          log.agentType === "pm" && "bg-purple-500",
                          log.agentType === "developer" && "bg-blue-500",
                          log.agentType === "qa_expert" && "bg-green-500",
                          log.agentType === "tech_lead" && "bg-orange-500",
                          log.agentType === "orchestrator" && "bg-gray-500"
                        )}
                      />
                      <div className="text-sm">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium">{log.agentType}</span>
                          <span className="text-xs text-muted-foreground">
                            {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "Unknown"}
                          </span>
                          {log.iteration != null && (
                            <Badge variant="secondary" className="text-xs">
                              Iter #{log.iteration}
                            </Badge>
                          )}
                        </div>
                        <p className="text-muted-foreground line-clamp-2">
                          {log.content.slice(0, 150)}...
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {(!session.logs || session.logs.length === 0) && (
                <div className="py-12 text-center">
                  <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No timeline data yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Insights Tab */}
        <TabsContent value="insights">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                AI-Powered Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="rounded-lg border p-4">
                  <h3 className="font-medium mb-2">Session Summary</h3>
                  <p className="text-sm text-muted-foreground">
                    This session is running in {session.mode} mode with{" "}
                    {taskGroups.length} task groups. Currently {completedGroups} groups
                    are completed ({progress.toFixed(0)}% progress).
                    {session.status === "active" &&
                      " The session is still actively processing."}
                  </p>
                </div>

                {taskGroups.some((g) => (g.revisionCount ?? 0) > 1) && (
                  <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4">
                    <h3 className="font-medium text-yellow-500 mb-2">
                      Revision Pattern Detected
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Some task groups have multiple revisions. Consider reviewing the
                      requirements clarity or adding validation checkpoints.
                    </p>
                  </div>
                )}

                <div className="rounded-lg border p-4">
                  <h3 className="font-medium mb-2">Recommendations</h3>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    {taskGroups.length > 4 && (
                      <li className="flex items-start gap-2">
                        <span>•</span>
                        Consider breaking down large sessions into smaller batches
                      </li>
                    )}
                    {totalTokens > 50000 && (
                      <li className="flex items-start gap-2">
                        <span>•</span>
                        High token usage detected - review prompts for optimization
                      </li>
                    )}
                    <li className="flex items-start gap-2">
                      <span>•</span>
                      Monitor QA results for potential patterns in failures
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
