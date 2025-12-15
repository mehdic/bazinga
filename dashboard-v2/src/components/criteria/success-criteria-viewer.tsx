"use client";

import { trpc } from "@/lib/trpc/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle2, Clock, XCircle, Target, FileCheck } from "lucide-react";

interface SuccessCriteriaViewerProps {
  sessionId: string;
}

const STATUS_CONFIG = {
  met: {
    icon: CheckCircle2,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/30",
    label: "Met",
  },
  pending: {
    icon: Clock,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    label: "Pending",
  },
  failed: {
    icon: XCircle,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    label: "Failed",
  },
};

export function SuccessCriteriaViewer({ sessionId }: SuccessCriteriaViewerProps) {
  const { data: criteria, isLoading } = trpc.sessions.getSuccessCriteria.useQuery({ sessionId });
  const { data: summary } = trpc.sessions.getCriteriaSummary.useQuery({ sessionId });

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

  if (!criteria || criteria.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No success criteria defined for this session</p>
        </CardContent>
      </Card>
    );
  }

  const progressPercent = summary
    ? Math.round((summary.met / summary.total) * 100)
    : 0;

  // Group criteria by category
  const byCategory = criteria.reduce((acc, c) => {
    const category = c.category || "General";
    if (!acc[category]) acc[category] = [];
    acc[category].push(c);
    return acc;
  }, {} as Record<string, typeof criteria>);

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <FileCheck className="h-4 w-4" />
            Completion Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-2xl font-bold">{progressPercent}%</p>
                <p className="text-sm text-muted-foreground">
                  {summary?.met || 0} of {summary?.total || 0} criteria met
                </p>
              </div>
              <div className="flex gap-4">
                <div className="text-center">
                  <p className="text-lg font-semibold text-green-500">{summary?.met || 0}</p>
                  <p className="text-xs text-muted-foreground">Met</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-yellow-500">{summary?.pending || 0}</p>
                  <p className="text-xs text-muted-foreground">Pending</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-red-500">{summary?.failed || 0}</p>
                  <p className="text-xs text-muted-foreground">Failed</p>
                </div>
              </div>
            </div>
            <Progress value={progressPercent} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Criteria by Category */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Criteria Details</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[400px]">
            <div className="divide-y divide-border">
              {Object.entries(byCategory).map(([category, items]) => (
                <div key={category} className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="outline">{category}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {items.filter((i) => i.status === "met").length}/{items.length} complete
                    </span>
                  </div>
                  <div className="space-y-2">
                    {items.map((item) => {
                      const status = item.status as keyof typeof STATUS_CONFIG || "pending";
                      const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
                      const Icon = config.icon;

                      return (
                        <div
                          key={item.id}
                          className={`p-3 rounded-lg border ${config.bgColor} ${config.borderColor}`}
                        >
                          <div className="flex items-start gap-3">
                            <Icon className={`h-5 w-5 mt-0.5 ${config.color}`} />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium">{item.criterion}</p>
                              {item.evidence && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Evidence: {item.evidence}
                                </p>
                              )}
                              {item.verifiedAt && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Verified: {new Date(item.verifiedAt).toLocaleString()}
                                  {item.verifiedBy && ` by ${item.verifiedBy}`}
                                </p>
                              )}
                            </div>
                            <Badge
                              variant="secondary"
                              className={`${config.bgColor} ${config.color} shrink-0`}
                            >
                              {config.label}
                            </Badge>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
