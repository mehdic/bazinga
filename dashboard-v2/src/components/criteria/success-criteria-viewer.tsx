"use client";

import { trpc } from "@/lib/trpc/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle2, Clock, XCircle, AlertTriangle, Target, FileCheck } from "lucide-react";

interface SuccessCriteriaViewerProps {
  sessionId: string;
}

// Status config matching actual DB values: 'pending' | 'met' | 'blocked' | 'failed'
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
  blocked: {
    icon: AlertTriangle,
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/30",
    label: "Blocked",
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

  // Guard against division by zero when total is 0
  const progressPercent = summary && summary.total > 0
    ? Math.round((summary.met / summary.total) * 100)
    : 0;

  // Separate required and optional criteria
  // requiredForCompletion is INTEGER (0/1/null). Default in DB is 1.
  // null should be treated as required (default behavior)
  const requiredCriteria = criteria.filter((c) => c.requiredForCompletion !== 0);
  const optionalCriteria = criteria.filter((c) => c.requiredForCompletion === 0);

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
                  <p className="text-lg font-semibold text-orange-500">{summary?.blocked || 0}</p>
                  <p className="text-xs text-muted-foreground">Blocked</p>
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

      {/* Criteria Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Criteria Details</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[400px]">
            <div className="divide-y divide-border">
              {/* Required Criteria */}
              {requiredCriteria.length > 0 && (
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/30">
                      Required
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {requiredCriteria.filter((i) => i.status === "met").length}/{requiredCriteria.length} complete
                    </span>
                  </div>
                  <div className="space-y-2">
                    {requiredCriteria.map((item) => (
                      <CriterionItem key={item.id} item={item} />
                    ))}
                  </div>
                </div>
              )}

              {/* Optional Criteria */}
              {optionalCriteria.length > 0 && (
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="outline" className="bg-gray-500/10 text-gray-500 border-gray-500/30">
                      Optional
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {optionalCriteria.filter((i) => i.status === "met").length}/{optionalCriteria.length} complete
                    </span>
                  </div>
                  <div className="space-y-2">
                    {optionalCriteria.map((item) => (
                      <CriterionItem key={item.id} item={item} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

interface CriterionItemProps {
  item: {
    id: number;
    criterion: string;
    status: string | null;
    actual: string | null;
    evidence: string | null;
    requiredForCompletion: number | null; // BOOLEAN as INTEGER (0/1/null)
    updatedAt: string | null;
  };
}

function CriterionItem({ item }: CriterionItemProps) {
  const status = (item.status as keyof typeof STATUS_CONFIG) || "pending";
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;

  return (
    <div className={`p-3 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
      <div className="flex items-start gap-3">
        <Icon className={`h-5 w-5 mt-0.5 ${config.color}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{item.criterion}</p>
          {item.actual && (
            <p className="text-xs text-muted-foreground mt-1">
              <span className="font-medium">Actual:</span> {item.actual}
            </p>
          )}
          {item.evidence && (
            <p className="text-xs text-muted-foreground mt-1">
              <span className="font-medium">Evidence:</span> {item.evidence}
            </p>
          )}
          {item.updatedAt && (
            <p className="text-xs text-muted-foreground mt-1">
              Updated: {new Date(item.updatedAt).toLocaleString()}
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
}
