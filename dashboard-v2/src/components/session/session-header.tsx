"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Download, Play } from "lucide-react";
import { timeAgo } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  exportToJSON,
  exportSessionLogs,
  exportTokenUsage,
  type ExportableSession,
} from "@/lib/utils/export";

interface SessionHeaderProps {
  sessionId: string;
  status: string | null;
  startTime: string | null;
  mode: string | null;
  originalRequirements: string | null;
  logs?: ExportableSession["logs"];
  taskGroups?: ExportableSession["taskGroups"];
  tokenUsage?: ExportableSession["tokenUsage"];
  endTime: string | null;
}

export function SessionHeader({
  sessionId,
  status,
  startTime,
  mode,
  originalRequirements,
  logs,
  taskGroups,
  tokenUsage,
  endTime,
}: SessionHeaderProps) {
  const shortId = sessionId.split("_").pop()?.slice(0, 8) || sessionId;

  return (
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
                status === "active"
                  ? "default"
                  : status === "completed"
                  ? "secondary"
                  : "destructive"
              }
            >
              {status === "active" && (
                <Play className="h-3 w-3 mr-1 animate-pulse" />
              )}
              {status}
            </Badge>
          </h1>
          <p className="text-sm text-muted-foreground">
            Started {timeAgo(startTime)}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Export Options</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() =>
                exportToJSON({
                  sessionId,
                  status,
                  mode,
                  startTime,
                  endTime,
                  originalRequirements,
                  logs,
                  taskGroups,
                  tokenUsage,
                })
              }
            >
              Full Session (JSON)
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => exportSessionLogs(logs, sessionId)}
              disabled={!logs?.length}
            >
              Logs Only (CSV)
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => exportTokenUsage(tokenUsage, sessionId)}
              disabled={!tokenUsage?.length}
            >
              Token Usage (CSV)
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
