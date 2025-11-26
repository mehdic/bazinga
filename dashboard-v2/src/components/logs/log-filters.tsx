"use client";

import { useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Search, X, Filter, FileText } from "lucide-react";

// Agent types for filtering
const AGENT_TYPES = ["pm", "developer", "qa_expert", "tech_lead", "orchestrator", "investigator"];
const MODEL_TIERS = ["opus", "sonnet", "haiku"];

interface LogEntry {
  id: number;
  agentType: string;
  statusCode: string | null;
  content: string;
  timestamp: string;
  modelTier: string | null;
}

interface LogFiltersProps {
  logs: LogEntry[];
}

export function LogFilters({ logs }: LogFiltersProps) {
  const [search, setSearch] = useState("");
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);

  // Filter logs based on search and selections
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

      // Model filter
      if (
        selectedModels.length > 0 &&
        log.modelTier &&
        !selectedModels.includes(log.modelTier)
      ) {
        return false;
      }

      return true;
    });
  }, [logs, search, selectedAgents, selectedModels]);

  const toggleAgent = (agent: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agent) ? prev.filter((a) => a !== agent) : [...prev, agent]
    );
  };

  const toggleModel = (model: string) => {
    setSelectedModels((prev) =>
      prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]
    );
  };

  const clearFilters = () => {
    setSearch("");
    setSelectedAgents([]);
    setSelectedModels([]);
  };

  const hasFilters = search || selectedAgents.length > 0 || selectedModels.length > 0;

  // Get unique agents and models from logs
  const availableAgents = [...new Set(logs.map((l) => l.agentType))];
  const availableModels = [...new Set(logs.map((l) => l.modelTier).filter(Boolean))] as string[];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Orchestration Logs</CardTitle>
          <Badge variant="outline">
            {filteredLogs.length} of {logs.length}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search and Filters */}
        <div className="space-y-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search in logs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
            {search && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2"
                onClick={() => setSearch("")}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap gap-2">
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <Filter className="h-4 w-4" />
              Agents:
            </div>
            {availableAgents.map((agent) => (
              <Badge
                key={agent}
                variant={selectedAgents.includes(agent) ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => toggleAgent(agent)}
              >
                {agent}
              </Badge>
            ))}
          </div>

          {availableModels.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Filter className="h-4 w-4" />
                Models:
              </div>
              {availableModels.map((model) => (
                <Badge
                  key={model}
                  variant={selectedModels.includes(model) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => toggleModel(model)}
                >
                  {model}
                </Badge>
              ))}
            </div>
          )}

          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-1" />
              Clear filters
            </Button>
          )}
        </div>

        {/* Log Entries */}
        <ScrollArea className="h-[500px]">
          <div className="space-y-2">
            {filteredLogs.map((log) => (
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
                      <Badge
                        variant={
                          log.statusCode === "BLOCKED" || log.statusCode === "FAILED"
                            ? "destructive"
                            : "secondary"
                        }
                        className="text-xs"
                      >
                        {log.statusCode}
                      </Badge>
                    )}
                    {log.modelTier && (
                      <Badge variant="outline" className="text-xs">
                        {log.modelTier}
                      </Badge>
                    )}
                  </div>
                  <p className="text-muted-foreground">
                    {search ? (
                      <HighlightText text={log.content.slice(0, 300)} search={search} />
                    ) : (
                      <>
                        {log.content.slice(0, 300)}
                        {log.content.length > 300 && "..."}
                      </>
                    )}
                  </p>
                </div>
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

// Helper component to highlight search matches
function HighlightText({ text, search }: { text: string; search: string }) {
  if (!search) return <>{text}</>;

  const parts = text.split(new RegExp(`(${search})`, "gi"));

  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === search.toLowerCase() ? (
          <mark key={i} className="bg-yellow-500/30 rounded px-0.5">
            {part}
          </mark>
        ) : (
          part
        )
      )}
      {text.length > 300 && "..."}
    </>
  );
}
