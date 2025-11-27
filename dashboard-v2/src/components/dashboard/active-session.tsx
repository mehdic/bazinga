"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { trpc } from "@/lib/trpc/client";
import { formatDuration } from "@/lib/utils";
import { useRefetchInterval } from "@/lib/hooks/use-smart-refetch";
import {
  Play,
  Users,
  Clock,
  ChevronRight,
  CheckCircle2,
  Circle,
  Loader2,
} from "lucide-react";
import { useEffect, useState } from "react";

export function ActiveSession() {
  // Smart refetch: no polling when socket connected, 3s fallback when disconnected
  const refetchInterval = useRefetchInterval(3000);

  // Use getActive query for loading state (not a disabled query)
  const { data: activeSession, isLoading: isActiveLoading } = trpc.sessions.getActive.useQuery(undefined, {
    refetchInterval,
  });

  const { data: fullSession } = trpc.sessions.getById.useQuery(
    { sessionId: activeSession?.sessionId || "" },
    { enabled: !!activeSession?.sessionId, refetchInterval }
  );

  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!activeSession || !activeSession.startTime) return;

    const start = new Date(activeSession.startTime).getTime();
    const interval = setInterval(() => {
      setElapsed(Date.now() - start);
    }, 1000);

    return () => clearInterval(interval);
  }, [activeSession]);

  if (isActiveLoading) {
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
  const totalGroups = taskGroups.length;
  // Weight progress: completed=100%, in_progress/running=50%, pending=0%
  const progressValue = totalGroups > 0
    ? taskGroups.reduce((acc, g) => {
        if (g.status === "completed") return acc + 100;
        if (g.status === "in_progress" || g.status === "running") return acc + 50;
        return acc;
      }, 0) / totalGroups
    : 0;
  const completedGroups = taskGroups.filter((g) => g.status === "completed").length;

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
          <span className="flex items-center gap-1 capitalize">
            <Users className="h-3 w-3" />
            {activeSession.mode || "unknown"} mode
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
          <Progress value={progressValue} className="h-2" />
        </div>

        {/* Task Group List */}
        {taskGroups.length > 0 && (
          <div className="space-y-1">
            {taskGroups.slice(0, 4).map((group) => (
              <div
                key={group.id}
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
                  {group.assignedTo || "pending"}
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
