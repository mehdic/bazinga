"use client";

import { useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Search, X, Filter, FileText } from "lucide-react";

// Log entry matching actual database schema
interface LogEntry {
  id: number;
  agentType: string;
  content: string;
  timestamp: string | null;
  iteration: number | null;
  agentId: string | null;
}

interface LogFiltersProps {
  logs: LogEntry[];
}

export function LogFilters({ logs }: LogFiltersProps) {
  const [search, setSearch] = useState("");
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      // Search filter
      if (search && !log.content.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }

      // Agent filter
      if (selectedAgents.length > 0 && !selectedAgents.includes(log.agentType)) {
        return false;
      }

      return true;
    });
  }, [logs, search, selectedAgents]);

  const toggleAgent = (agent: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agent) ? prev.filter((a) => a !== agent) : [...prev, agent]
    );
  };

  const clearFilters = () => {
    setSearch("");
    setSelectedAgents([]);
  };

  const hasFilters = search || selectedAgents.length > 0;

  // Get unique agents from logs
  const availableAgents = Array.from(new Set(logs.map((l) => l.agentType)));

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Orchestration Logs</CardTitle>
          <Badge variant="outline">
            {filteredLogs.length} of {logs.length} logs
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search & Filters */}
        <div className="flex flex-col gap-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search logs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>

          {/* Agent Filters */}
          <div className="flex flex-wrap gap-2">
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Filter className="h-3 w-3" /> Agents:
            </span>
            {availableAgents.map((agent) => (
              <Button
                key={agent}
                variant={selectedAgents.includes(agent) ? "default" : "outline"}
                size="sm"
                onClick={() => toggleAgent(agent)}
                className="h-6 px-2 text-xs"
              >
                {agent}
              </Button>
            ))}
          </div>

          {hasFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="w-fit text-xs"
            >
              <X className="h-3 w-3 mr-1" /> Clear filters
            </Button>
          )}
        </div>

        {/* Log List */}
        <ScrollArea className="h-[500px]">
          <div className="space-y-2 pr-4">
            {filteredLogs.map((log) => (
              <div
                key={log.id}
                className="rounded-lg border bg-card p-3 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="secondary"
                      className={cn(
                        log.agentType === "pm" && "bg-purple-500/20 text-purple-500",
                        log.agentType === "developer" && "bg-blue-500/20 text-blue-500",
                        log.agentType === "qa_expert" && "bg-green-500/20 text-green-500",
                        log.agentType === "tech_lead" && "bg-orange-500/20 text-orange-500",
                        log.agentType === "orchestrator" && "bg-gray-500/20"
                      )}
                    >
                      {log.agentType}
                    </Badge>
                    {log.agentId && (
                      <span className="text-xs text-muted-foreground">
                        {log.agentId}
                      </span>
                    )}
                    {log.iteration != null && (
                      <span className="text-xs text-muted-foreground">
                        Iter #{log.iteration}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {log.timestamp
                      ? new Date(log.timestamp).toLocaleTimeString()
                      : "Unknown time"}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-4 whitespace-pre-wrap">
                  {log.content}
                </p>
              </div>
            ))}

            {filteredLogs.length === 0 && (
              <div className="py-12 text-center">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  {hasFilters ? "No logs match your filters" : "No logs yet"}
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
