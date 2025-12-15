"use client";

import { useState } from "react";
import { trpc } from "@/lib/trpc/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Brain, ChevronDown, ChevronUp, Eye, EyeOff, FileText, Loader2 } from "lucide-react";

const PAGE_SIZE = 50;

interface ReasoningViewerProps {
  sessionId: string;
}

const PHASES = [
  { value: "all", label: "All Phases" },
  { value: "understanding", label: "Understanding" },
  { value: "approach", label: "Approach" },
  { value: "decisions", label: "Decisions" },
  { value: "risks", label: "Risks" },
  { value: "blockers", label: "Blockers" },
  { value: "pivot", label: "Pivot" },
  { value: "completion", label: "Completion" },
];

const CONFIDENCE_COLORS = {
  high: "bg-green-500/20 text-green-400 border-green-500/50",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
  low: "bg-red-500/20 text-red-400 border-red-500/50",
};

const PHASE_COLORS: Record<string, string> = {
  understanding: "bg-blue-500/20 text-blue-400",
  approach: "bg-purple-500/20 text-purple-400",
  decisions: "bg-green-500/20 text-green-400",
  risks: "bg-orange-500/20 text-orange-400",
  blockers: "bg-red-500/20 text-red-400",
  pivot: "bg-yellow-500/20 text-yellow-400",
  completion: "bg-emerald-500/20 text-emerald-400",
};

export function ReasoningViewer({ sessionId }: ReasoningViewerProps) {
  const [phase, setPhase] = useState<string>("all");
  const [agentType, setAgentType] = useState<string>("all");
  const [confidenceLevel, setConfidenceLevel] = useState<"all" | "high" | "medium" | "low">("all");
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [showRedacted, setShowRedacted] = useState<Set<number>>(new Set());
  const [offset, setOffset] = useState(0);

  const { data: summary } = trpc.sessions.getReasoningSummary.useQuery({ sessionId });
  const { data: reasoningData, isLoading, isFetching } = trpc.sessions.getReasoning.useQuery({
    sessionId,
    phase: phase === "all" ? undefined : phase,
    agentType: agentType === "all" ? undefined : agentType,
    confidenceLevel,
    limit: PAGE_SIZE,
    offset,
  });

  // Reset offset when filters change
  const handleFilterChange = (setter: (value: string) => void, value: string) => {
    setter(value);
    setOffset(0);
  };

  const agents = summary?.byAgent ? Object.keys(summary.byAgent) : [];

  const toggleExpanded = (id: number) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  const toggleShowRedacted = (id: number) => {
    const newShow = new Set(showRedacted);
    if (newShow.has(id)) {
      newShow.delete(id);
    } else {
      newShow.add(id);
    }
    setShowRedacted(newShow);
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-muted rounded w-1/4" />
            <div className="h-20 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const logs = reasoningData?.logs || [];

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      {summary && summary.totalEntries > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{summary.totalEntries}</div>
              <div className="text-sm text-muted-foreground">Total Entries</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{Object.keys(summary.byAgent).length}</div>
              <div className="text-sm text-muted-foreground">Agents</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-400">
                {summary.byConfidence?.high || 0}
              </div>
              <div className="text-sm text-muted-foreground">High Confidence</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-yellow-400">{summary.redactedCount}</div>
              <div className="text-sm text-muted-foreground">Redacted</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Select value={phase} onValueChange={(v) => handleFilterChange(setPhase, v)}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Phase" />
              </SelectTrigger>
              <SelectContent>
                {PHASES.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={agentType} onValueChange={(v) => handleFilterChange(setAgentType, v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Agent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Agents</SelectItem>
                {agents.map((agent) => (
                  <SelectItem key={agent} value={agent}>
                    {agent.replace(/_/g, " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={confidenceLevel}
              onValueChange={(v) => {
                setConfidenceLevel(v as typeof confidenceLevel);
                setOffset(0);
              }}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Confidence" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Reasoning Entries */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center justify-between">
            <span>
              Reasoning Entries ({offset + 1}-{Math.min(offset + logs.length, reasoningData?.total || 0)} of {reasoningData?.total || 0})
            </span>
            {isFetching && <Loader2 className="h-4 w-4 animate-spin" />}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {logs.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground">
              No reasoning entries found for the selected filters
            </div>
          ) : (
            <ScrollArea className="h-[500px]">
              <div className="divide-y divide-border">
                {logs.map((log) => (
                  <div key={log.id} className="p-4 hover:bg-muted/50">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          {log.agentType?.replace(/_/g, " ")}
                        </Badge>
                        {log.reasoningPhase && (
                          <Badge
                            variant="secondary"
                            className={PHASE_COLORS[log.reasoningPhase] || ""}
                          >
                            {log.reasoningPhase}
                          </Badge>
                        )}
                        {log.confidenceLevel && (
                          <Badge
                            variant="outline"
                            className={
                              CONFIDENCE_COLORS[log.confidenceLevel as keyof typeof CONFIDENCE_COLORS] || ""
                            }
                          >
                            {log.confidenceLevel}
                          </Badge>
                        )}
                        {log.redacted && (
                          <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500">
                            Redacted
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {log.timestamp
                            ? new Date(log.timestamp).toLocaleTimeString()
                            : ""}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleExpanded(log.id)}
                        >
                          {expandedIds.has(log.id) ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>

                    {/* Content */}
                    {log.redacted && !showRedacted.has(log.id) ? (
                      <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-md">
                        <div className="flex items-center justify-between">
                          <span className="text-yellow-500 text-sm">
                            Content redacted for security
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleShowRedacted(log.id)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Show
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div
                        className={`text-sm ${
                          expandedIds.has(log.id) ? "" : "line-clamp-3"
                        }`}
                      >
                        <pre className="whitespace-pre-wrap font-sans">{log.content}</pre>
                      </div>
                    )}

                    {/* Show redaction toggle if showing redacted content */}
                    {log.redacted && showRedacted.has(log.id) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-2"
                        onClick={() => toggleShowRedacted(log.id)}
                      >
                        <EyeOff className="h-4 w-4 mr-1" />
                        Hide
                      </Button>
                    )}

                    {/* References */}
                    {expandedIds.has(log.id) &&
                      log.references &&
                      log.references.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border">
                          <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            Files Referenced
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {log.references.map((ref: string, idx: number) => (
                              <Badge key={idx} variant="outline" className="font-mono text-xs">
                                {ref}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                    {/* Group ID */}
                    {expandedIds.has(log.id) && log.groupId && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        Task Group: <span className="font-mono">{log.groupId}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          {/* Pagination Controls */}
          {logs.length > 0 && (
            <div className="flex items-center justify-between p-4 border-t border-border">
              <div className="text-sm text-muted-foreground">
                Page {Math.floor(offset / PAGE_SIZE) + 1} of {Math.ceil((reasoningData?.total || 0) / PAGE_SIZE)}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  disabled={offset === 0 || isFetching}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  disabled={!reasoningData?.hasMore || isFetching}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
