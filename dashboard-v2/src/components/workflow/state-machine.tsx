"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  User,
  Code,
  TestTube,
  GitPullRequest,
  CheckCircle,
  Circle,
  ArrowRight,
  Loader2,
  XCircle,
  Sparkles,
} from "lucide-react";

// Agent types in workflow order
const WORKFLOW_STAGES = [
  { id: "pm", label: "Project Manager", icon: User, color: "purple" },
  { id: "developer", label: "Developer", icon: Code, color: "blue" },
  { id: "qa_expert", label: "QA Expert", icon: TestTube, color: "green" },
  { id: "tech_lead", label: "Tech Lead", icon: GitPullRequest, color: "orange" },
] as const;

interface LogEntry {
  id: number;
  agentType: string;
  statusCode: string | null;
  timestamp: string;
}

interface TaskGroup {
  groupId: string;
  name: string | null;
  status: string;
  currentStage: string | null;
  assignedTo: string | null;
}

interface StateMachineProps {
  logs: LogEntry[];
  taskGroups: TaskGroup[];
  sessionStatus: string;
}

export function StateMachine({ logs, taskGroups, sessionStatus }: StateMachineProps) {
  // Determine current stage from most recent log
  const currentStage = useMemo(() => {
    if (!logs || logs.length === 0) return null;
    const sortedLogs = [...logs].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    return sortedLogs[0]?.agentType || null;
  }, [logs]);

  // Get stage status based on logs
  const getStageStatus = (stageId: string) => {
    const stageLogs = logs.filter((l) => l.agentType === stageId);
    if (stageLogs.length === 0) return "pending";

    const latestLog = stageLogs.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )[0];

    if (latestLog.statusCode === "BLOCKED" || latestLog.statusCode === "FAILED") {
      return "failed";
    }

    // If this is the current stage and session is active, it's in progress
    if (stageId === currentStage && sessionStatus === "active") {
      return "active";
    }

    // Check if there are later stages that have logs
    const stageIndex = WORKFLOW_STAGES.findIndex((s) => s.id === stageId);
    const laterStages = WORKFLOW_STAGES.slice(stageIndex + 1);
    const hasLaterStageLogs = laterStages.some((s) =>
      logs.some((l) => l.agentType === s.id)
    );

    if (hasLaterStageLogs) {
      return "completed";
    }

    return stageId === currentStage ? "active" : "completed";
  };

  // Count iterations through the workflow
  const iterationCount = useMemo(() => {
    const pmLogs = logs.filter((l) => l.agentType === "pm");
    return Math.max(1, pmLogs.length);
  }, [logs]);

  return (
    <div className="space-y-6">
      {/* Main Workflow Diagram */}
      <div className="relative">
        {/* Progress Line */}
        <div className="absolute left-0 right-0 top-1/2 h-1 -translate-y-1/2 bg-muted rounded-full" />

        {/* Stages */}
        <div className="relative flex justify-between">
          {WORKFLOW_STAGES.map((stage, index) => {
            const status = getStageStatus(stage.id);
            const Icon = stage.icon;

            return (
              <div key={stage.id} className="flex flex-col items-center">
                {/* Stage Node */}
                <div
                  className={cn(
                    "relative z-10 flex h-16 w-16 items-center justify-center rounded-full border-4 transition-all",
                    status === "completed" && "border-green-500 bg-green-500/10",
                    status === "active" && "border-primary bg-primary/10 animate-pulse",
                    status === "failed" && "border-red-500 bg-red-500/10",
                    status === "pending" && "border-muted bg-muted"
                  )}
                >
                  {status === "active" ? (
                    <Loader2
                      className={cn("h-6 w-6 animate-spin", `text-${stage.color}-500`)}
                    />
                  ) : status === "completed" ? (
                    <CheckCircle className="h-6 w-6 text-green-500" />
                  ) : status === "failed" ? (
                    <XCircle className="h-6 w-6 text-red-500" />
                  ) : (
                    <Icon className="h-6 w-6 text-muted-foreground" />
                  )}
                </div>

                {/* Stage Label */}
                <div className="mt-3 text-center">
                  <p className="text-sm font-medium">{stage.label}</p>
                  <Badge
                    variant={
                      status === "completed"
                        ? "secondary"
                        : status === "active"
                        ? "default"
                        : status === "failed"
                        ? "destructive"
                        : "outline"
                    }
                    className="mt-1"
                  >
                    {status}
                  </Badge>
                </div>

                {/* Arrow */}
                {index < WORKFLOW_STAGES.length - 1 && (
                  <ArrowRight
                    className={cn(
                      "absolute right-[-50%] top-[32px] h-6 w-6 translate-x-1/2",
                      getStageStatus(WORKFLOW_STAGES[index + 1].id) !== "pending"
                        ? "text-green-500"
                        : "text-muted-foreground"
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Workflow Loop Indicator */}
      <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4" />
          <span>
            Iteration {iterationCount}
            {iterationCount > 1 && " (revision cycle)"}
          </span>
        </div>
        {sessionStatus === "completed" && (
          <Badge variant="secondary" className="bg-green-500/10 text-green-500">
            BAZINGA Complete
          </Badge>
        )}
      </div>

      {/* Task Groups State */}
      {taskGroups.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">
            Task Group States
          </h4>
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
            {taskGroups.map((group) => {
              const stageInfo = WORKFLOW_STAGES.find(
                (s) => s.id === group.currentStage
              );
              const StageIcon = stageInfo?.icon || Circle;

              return (
                <div
                  key={group.groupId}
                  className="flex items-center gap-3 rounded-lg border p-3"
                >
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full",
                      group.status === "completed" && "bg-green-500/10",
                      group.status === "in_progress" && "bg-blue-500/10",
                      group.status === "failed" && "bg-red-500/10"
                    )}
                  >
                    <StageIcon
                      className={cn(
                        "h-4 w-4",
                        group.status === "completed" && "text-green-500",
                        group.status === "in_progress" && "text-blue-500",
                        group.status === "failed" && "text-red-500"
                      )}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {group.name || group.groupId.slice(-8)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {group.currentStage || "Pending"} • {group.assignedTo || "Unassigned"}
                    </p>
                  </div>
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
              );
            })}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-full border-2 border-muted" />
          <span>Pending</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-full border-2 border-primary bg-primary/10" />
          <span>Active</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-full border-2 border-green-500 bg-green-500/10" />
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-full border-2 border-red-500 bg-red-500/10" />
          <span>Failed/Blocked</span>
        </div>
      </div>
    </div>
  );
}
