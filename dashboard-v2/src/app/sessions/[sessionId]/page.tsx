"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { trpc } from "@/lib/trpc/client";
import { cn, formatDuration, timeAgo, getStatusColor, formatTokens } from "@/lib/utils";
import {
  ArrowLeft,
  Clock,
  Users,
  Zap,
  CheckCircle2,
  Circle,
  XCircle,
  Loader2,
  Bot,
  FileText,
  BarChart3,
  Shield,
  Sparkles,
  GitBranch,
  Download,
  Play,
} from "lucide-react";
import { useEffect, useState } from "react";

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const { data: session, isLoading } = trpc.sessions.getById.useQuery(
    { sessionId },
    { refetchInterval: 5000 }
  );

  const { data: tokenData } = trpc.sessions.getTokenBreakdown.useQuery(
    { sessionId },
    { enabled: !!sessionId }
  );

  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!session || session.status !== "active") return;

    const start = new Date(session.startTime).getTime();
    const interval = setInterval(() => {
      setElapsed(Date.now() - start);
    }, 1000);

    return () => clearInterval(interval);
  }, [session]);

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

  const shortId = sessionId.split("_").pop()?.slice(0, 8) || sessionId;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/sessions">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              Session #{shortId}
              <Badge
                variant={
                  session.status === "active"
                    ? "default"
                    : session.status === "completed"
                    ? "secondary"
                    : "destructive"
                }
              >
                {session.status === "active" && (
                  <Play className="h-3 w-3 mr-1 animate-pulse" />
                )}
                {session.status}
              </Badge>
            </h1>
            <p className="text-sm text-muted-foreground">
              Started {timeAgo(session.startTime)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Session Info Card */}
      <Card>
        <CardContent className="p-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <span className="text-sm text-muted-foreground">Mode</span>
              <p className="font-medium flex items-center gap-2">
                <Users className="h-4 w-4" />
                {session.mode === "parallel"
                  ? `Parallel (${session.developerCount} devs)`
                  : "Simple Mode"}
              </p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Duration</span>
              <p className="font-medium flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {session.status === "active"
                  ? formatDuration(elapsed)
                  : session.endTime
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
      <Tabs defaultValue="tasks" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="tasks">
            <GitBranch className="h-4 w-4 mr-2" />
            Tasks
          </TabsTrigger>
          <TabsTrigger value="logs">
            <FileText className="h-4 w-4 mr-2" />
            Logs
          </TabsTrigger>
          <TabsTrigger value="tokens">
            <Zap className="h-4 w-4 mr-2" />
            Tokens
          </TabsTrigger>
          <TabsTrigger value="quality">
            <Shield className="h-4 w-4 mr-2" />
            Quality
          </TabsTrigger>
          <TabsTrigger value="timeline">
            <BarChart3 className="h-4 w-4 mr-2" />
            Timeline
          </TabsTrigger>
          <TabsTrigger value="insights">
            <Sparkles className="h-4 w-4 mr-2" />
            AI Insights
          </TabsTrigger>
        </TabsList>

        {/* Tasks Tab */}
        <TabsContent value="tasks" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {taskGroups.map((group) => (
              <Card key={group.groupId}>
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
                      {group.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Stage</span>
                    <span>{group.currentStage}</span>
                  </div>
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
          <Card>
            <CardHeader>
              <CardTitle>Orchestration Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-2">
                  {session.logs?.map((log, i) => (
                    <div
                      key={log.id}
                      className="flex gap-4 rounded-lg border p-3 text-sm"
                    >
                      <div className="flex-shrink-0">
                        <Badge variant="outline">{log.agentType}</Badge>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-muted-foreground">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                          {log.statusCode && (
                            <Badge variant="secondary" className="text-xs">
                              {log.statusCode}
                            </Badge>
                          )}
                          {log.modelTier && (
                            <Badge variant="outline" className="text-xs">
                              {log.modelTier}
                            </Badge>
                          )}
                        </div>
                        <p className="text-muted-foreground line-clamp-3">
                          {log.content.slice(0, 300)}
                          {log.content.length > 300 && "..."}
                        </p>
                      </div>
                    </div>
                  ))}
                  {(!session.logs || session.logs.length === 0) && (
                    <div className="py-12 text-center">
                      <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">No logs yet</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tokens Tab */}
        <TabsContent value="tokens">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Token Breakdown by Agent</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {tokenData?.breakdown.map((item, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4 text-muted-foreground" />
                        <span>{item.agentType}</span>
                        <Badge variant="outline" className="text-xs">
                          {item.modelTier}
                        </Badge>
                      </div>
                      <span className="font-mono">
                        {formatTokens(item.total || 0)}
                      </span>
                    </div>
                  ))}
                  {(!tokenData?.breakdown || tokenData.breakdown.length === 0) && (
                    <div className="py-8 text-center">
                      <Zap className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">No token data yet</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Token Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Total Tokens</span>
                    <span className="text-2xl font-bold">
                      {formatTokens(totalTokens)}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Estimated Cost</span>
                    <span className="text-lg font-medium">
                      ${((totalTokens / 1000000) * 3).toFixed(4)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality">
          <Card>
            <CardHeader>
              <CardTitle>Success Criteria</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {session.successCriteria?.map((criterion) => (
                  <div
                    key={criterion.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div className="flex items-center gap-3">
                      {criterion.status === "met" ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : criterion.status === "failed" ? (
                        <XCircle className="h-5 w-5 text-red-500" />
                      ) : (
                        <Circle className="h-5 w-5 text-muted-foreground" />
                      )}
                      <div>
                        <p className="font-medium">{criterion.criterion}</p>
                        {criterion.actual && (
                          <p className="text-sm text-muted-foreground">
                            {criterion.actual}
                          </p>
                        )}
                      </div>
                    </div>
                    <Badge
                      variant={
                        criterion.status === "met"
                          ? "secondary"
                          : criterion.status === "failed"
                          ? "destructive"
                          : "outline"
                      }
                    >
                      {criterion.status}
                    </Badge>
                  </div>
                ))}
                {(!session.successCriteria || session.successCriteria.length === 0) && (
                  <div className="py-12 text-center">
                    <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">No success criteria defined</p>
                  </div>
                )}
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
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                          {log.statusCode && (
                            <Badge variant="secondary" className="text-xs">
                              {log.statusCode}
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
