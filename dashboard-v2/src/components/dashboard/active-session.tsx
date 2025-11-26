"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { trpc } from "@/lib/trpc/client";
import { cn, formatDuration } from "@/lib/utils";
import {
  Play,
  Users,
  Clock,
  ChevronRight,
  Bot,
  CheckCircle2,
  Circle,
  Loader2,
} from "lucide-react";
import { useEffect, useState } from "react";

export function ActiveSession() {
  const { data: session, isLoading } = trpc.sessions.getById.useQuery(
    { sessionId: "" },
    { enabled: false }
  );

  const { data: activeSession } = trpc.sessions.getActive.useQuery(undefined, {
    refetchInterval: 3000,
  });

  const { data: fullSession } = trpc.sessions.getById.useQuery(
    { sessionId: activeSession?.sessionId || "" },
    { enabled: !!activeSession?.sessionId, refetchInterval: 3000 }
  );

  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!activeSession) return;

    const start = new Date(activeSession.startTime).getTime();
    const interval = setInterval(() => {
      setElapsed(Date.now() - start);
    }, 1000);

    return () => clearInterval(interval);
  }, [activeSession]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="h-6 w-32 animate-pulse rounded bg-muted" />
        </CardHeader>
        <CardContent>
          <div className="h-32 animate-pulse rounded bg-muted" />
        </CardContent>
      </Card>
    );
  }

  if (!activeSession) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Circle className="h-4 w-4 text-muted-foreground" />
            No Active Session
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Start a new orchestration to see real-time progress here.
          </p>
        </CardContent>
      </Card>
    );
  }

  const taskGroups = fullSession?.taskGroups || [];
  const completedGroups = taskGroups.filter((g) => g.status === "completed").length;
  const progress = taskGroups.length > 0 ? (completedGroups / taskGroups.length) * 100 : 0;

  return (
    <Card className="border-primary/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Play className="h-4 w-4 text-green-500 animate-pulse" />
            Active Session
          </CardTitle>
          <Badge variant="success" className="animate-pulse">
            Running
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Session ID and Mode */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            #{activeSession.sessionId.split("_").pop()?.slice(0, 8)}
          </span>
          <span className="flex items-center gap-1">
            <Users className="h-3 w-3" />
            {activeSession.mode === "parallel"
              ? `Parallel (${activeSession.developerCount} devs)`
              : "Simple Mode"}
          </span>
        </div>

        {/* Requirements */}
        {activeSession.originalRequirements && (
          <p className="text-sm line-clamp-2">
            {activeSession.originalRequirements}
          </p>
        )}

        <Separator />

        {/* Task Groups Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Task Groups</span>
            <span>
              {completedGroups}/{taskGroups.length} completed
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Task Group List */}
        {taskGroups.length > 0 && (
          <div className="space-y-1">
            {taskGroups.slice(0, 4).map((group) => (
              <div
                key={group.groupId}
                className="flex items-center justify-between text-xs"
              >
                <span className="flex items-center gap-2">
                  {group.status === "completed" ? (
                    <CheckCircle2 className="h-3 w-3 text-green-500" />
                  ) : group.status === "in_progress" ? (
                    <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />
                  ) : (
                    <Circle className="h-3 w-3 text-muted-foreground" />
                  )}
                  {group.name}
                </span>
                <Badge variant="outline" className="text-[10px]">
                  {group.currentStage}
                </Badge>
              </div>
            ))}
            {taskGroups.length > 4 && (
              <span className="text-xs text-muted-foreground">
                +{taskGroups.length - 4} more groups
              </span>
            )}
          </div>
        )}

        <Separator />

        {/* Elapsed Time */}
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-1 text-muted-foreground">
            <Clock className="h-3 w-3" />
            Elapsed
          </span>
          <span className="font-mono">{formatDuration(elapsed)}</span>
        </div>

        {/* View Details */}
        <Link href={`/sessions/${activeSession.sessionId}`}>
          <Button className="w-full" size="sm">
            View Live Details
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
