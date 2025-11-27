"use client";

import React from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { timeAgo, getStatusBadgeVariant } from "@/lib/utils";
import type { Session } from "@/types";
import {
  Clock,
  Users,
  ChevronRight,
  Play,
  CheckCircle2,
  XCircle,
} from "lucide-react";

interface SessionCardProps {
  session: Session;
  showDetails?: boolean;
}

export function SessionCard({ session, showDetails = false }: SessionCardProps) {
  const statusIcon: Record<string, React.ReactNode> = {
    active: <Play className="h-3 w-3" />,
    completed: <CheckCircle2 className="h-3 w-3" />,
    failed: <XCircle className="h-3 w-3" />,
  };

  const shortId = session.sessionId.split("_").pop()?.slice(0, 8) || session.sessionId;

  return (
    <Card className="transition-colors hover:bg-accent/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">
            <span className="text-muted-foreground">#</span>
            {shortId}
          </CardTitle>
          <Badge variant={getStatusBadgeVariant(session.status || "pending")}>
            <span className="mr-1">{statusIcon[session.status || ""] || null}</span>
            {session.status || "pending"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Requirements preview */}
        {session.originalRequirements && (
          <p className="line-clamp-2 text-sm text-muted-foreground">
            {session.originalRequirements}
          </p>
        )}

        {/* Meta info */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {timeAgo(session.startTime)}
          </span>
          <span className="flex items-center gap-1 capitalize">
            <Users className="h-3 w-3" />
            {session.mode || "unknown"}
          </span>
        </div>

        {/* Progress bar for active sessions */}
        {session.status === "active" && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Progress</span>
              <span>In progress...</span>
            </div>
            <Progress value={undefined} className="h-1" />
          </div>
        )}

        {/* View details link */}
        <Link href={`/sessions/${session.sessionId}`}>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            View Details
            <ChevronRight className="h-4 w-4" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
