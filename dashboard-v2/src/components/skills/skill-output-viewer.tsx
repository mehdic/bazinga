"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn, formatRelativeTime } from "@/lib/utils";
import {
  Wand2,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Shield,
  TestTube,
  Search,
  FileCode,
  Copy,
  Check,
} from "lucide-react";

// SkillOutput matching actual database schema
interface SkillOutput {
  id: number;
  sessionId: string;
  timestamp: string | null;
  skillName: string;
  outputData: Record<string, unknown> | string;
}

interface SkillOutputViewerProps {
  outputs: SkillOutput[];
}

// Skill icons and colors
const SKILL_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  security_scan: { icon: Shield, color: "red", label: "Security Scan" },
  "security-scan": { icon: Shield, color: "red", label: "Security Scan" },
  test_coverage: { icon: TestTube, color: "green", label: "Test Coverage" },
  "test-coverage": { icon: TestTube, color: "green", label: "Test Coverage" },
  lint_check: { icon: FileCode, color: "yellow", label: "Lint Check" },
  "lint-check": { icon: FileCode, color: "yellow", label: "Lint Check" },
  codebase_analysis: { icon: Search, color: "blue", label: "Codebase Analysis" },
  "codebase-analysis": { icon: Search, color: "blue", label: "Codebase Analysis" },
};

function getSkillConfig(skillName: string) {
  return SKILL_CONFIG[skillName] || { icon: Wand2, color: "gray", label: skillName };
}

function JsonViewer({ data, depth = 0 }: { data: unknown; depth?: number }) {
  const [collapsed, setCollapsed] = useState(depth > 2);

  if (typeof data !== "object" || data === null) {
    if (typeof data === "string") {
      return <span className="text-green-500">&quot;{data}&quot;</span>;
    }
    if (typeof data === "number") {
      return <span className="text-blue-500">{data}</span>;
    }
    if (typeof data === "boolean") {
      return <span className="text-purple-500">{data ? "true" : "false"}</span>;
    }
    return <span className="text-muted-foreground">null</span>;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-muted-foreground">[]</span>;
    return (
      <div className="pl-4">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
        >
          {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          <span className="text-xs">[{data.length} items]</span>
        </button>
        {!collapsed && (
          <div className="border-l border-border pl-2 ml-1 mt-1 space-y-1">
            {data.map((item, i) => (
              <div key={i} className="flex">
                <span className="text-muted-foreground text-xs mr-2">{i}:</span>
                <JsonViewer data={item} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  const entries = Object.entries(data);
  if (entries.length === 0) return <span className="text-muted-foreground">{"{}"}</span>;

  return (
    <div className="pl-4">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
      >
        {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        <span className="text-xs">{"{...}"}</span>
      </button>
      {!collapsed && (
        <div className="border-l border-border pl-2 ml-1 mt-1 space-y-1">
          {entries.map(([key, value]) => (
            <div key={key} className="flex flex-wrap">
              <span className="text-cyan-500 text-sm mr-1">{key}:</span>
              <JsonViewer data={value} depth={depth + 1} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SkillCard({ output }: { output: SkillOutput }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const config = getSkillConfig(output.skillName);
  const Icon = config.icon;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(
      typeof output.outputData === "string"
        ? output.outputData
        : JSON.stringify(output.outputData, null, 2)
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Try to extract summary info from common skill output formats
  const getSummary = () => {
    if (typeof output.outputData !== "object" || !output.outputData) return null;
    const data = output.outputData as Record<string, unknown>;

    // Security scan summary
    if ("vulnerabilities" in data || "issues" in data) {
      const issues = (data.vulnerabilities || data.issues) as unknown[];
      const severity = data.severity as string;
      return {
        type: "security",
        count: Array.isArray(issues) ? issues.length : 0,
        severity,
      };
    }

    // Test coverage summary
    if ("coverage" in data || "coveragePercent" in data) {
      return {
        type: "coverage",
        percent: (data.coverage || data.coveragePercent) as number,
      };
    }

    // Lint check summary
    if ("errors" in data || "warnings" in data) {
      return {
        type: "lint",
        errors: (data.errors as unknown[] | undefined)?.length || (data.errorCount as number) || 0,
        warnings: (data.warnings as unknown[] | undefined)?.length || (data.warningCount as number) || 0,
      };
    }

    return null;
  };

  const summary = getSummary();

  return (
    <Card className="overflow-hidden">
      <CardHeader
        className="p-4 cursor-pointer hover:bg-accent/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex h-10 w-10 items-center justify-center rounded-lg",
                config.color === "red" && "bg-red-500/10",
                config.color === "green" && "bg-green-500/10",
                config.color === "yellow" && "bg-yellow-500/10",
                config.color === "blue" && "bg-blue-500/10",
                config.color === "gray" && "bg-muted"
              )}
            >
              <Icon
                className={cn(
                  "h-5 w-5",
                  config.color === "red" && "text-red-500",
                  config.color === "green" && "text-green-500",
                  config.color === "yellow" && "text-yellow-500",
                  config.color === "blue" && "text-blue-500",
                  config.color === "gray" && "text-muted-foreground"
                )}
              />
            </div>
            <div>
              <CardTitle className="text-base">{config.label}</CardTitle>
              <p className="text-xs text-muted-foreground">
                {output.timestamp ? formatRelativeTime(new Date(output.timestamp)) : "Unknown time"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Summary badges */}
            {summary?.type === "security" && "count" in summary && (
              <Badge
                variant={(summary.count ?? 0) > 0 ? "destructive" : "secondary"}
                className="gap-1"
              >
                {(summary.count ?? 0) > 0 ? (
                  <AlertTriangle className="h-3 w-3" />
                ) : (
                  <CheckCircle className="h-3 w-3" />
                )}
                {summary.count ?? 0} issues
              </Badge>
            )}
            {summary?.type === "coverage" && "percent" in summary && (
              <Badge
                variant={(summary.percent ?? 0) >= 80 ? "secondary" : "outline"}
                className={cn((summary.percent ?? 0) >= 80 && "bg-green-500/20 text-green-500")}
              >
                {summary.percent ?? 0}% coverage
              </Badge>
            )}
            {summary?.type === "lint" && "errors" in summary && (
              <>
                {(summary.errors ?? 0) > 0 && (
                  <Badge variant="destructive" className="gap-1">
                    <XCircle className="h-3 w-3" />
                    {summary.errors ?? 0} errors
                  </Badge>
                )}
                {(summary.warnings ?? 0) > 0 && (
                  <Badge variant="outline" className="gap-1 text-yellow-500">
                    <AlertTriangle className="h-3 w-3" />
                    {summary.warnings ?? 0} warnings
                  </Badge>
                )}
                {(summary.errors ?? 0) === 0 && (summary.warnings ?? 0) === 0 && (
                  <Badge variant="secondary" className="gap-1 bg-green-500/20 text-green-500">
                    <CheckCircle className="h-3 w-3" />
                    Clean
                  </Badge>
                )}
              </>
            )}
            {expanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="p-4 pt-0">
          <Separator className="mb-4" />
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Output Data</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-7 px-2 text-xs"
            >
              {copied ? (
                <Check className="h-3 w-3 mr-1" />
              ) : (
                <Copy className="h-3 w-3 mr-1" />
              )}
              {copied ? "Copied" : "Copy"}
            </Button>
          </div>
          <div className="rounded-lg border bg-muted/50 p-3 overflow-x-auto max-h-96 overflow-y-auto">
            <pre className="text-xs font-mono">
              <JsonViewer data={output.outputData} />
            </pre>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export function SkillOutputViewer({ outputs }: SkillOutputViewerProps) {
  if (outputs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Wand2 className="h-12 w-12 mb-4 opacity-50" />
        <p className="text-lg font-medium">No skill outputs</p>
        <p className="text-sm">Skills like security scans and test coverage will appear here</p>
      </div>
    );
  }

  // Group by skill name
  const groupedOutputs = outputs.reduce((acc, output) => {
    const key = output.skillName;
    if (!acc[key]) acc[key] = [];
    acc[key].push(output);
    return acc;
  }, {} as Record<string, SkillOutput[]>);

  return (
    <div className="space-y-4">
      {Object.entries(groupedOutputs).map(([skillName, skillOutputs]) => (
        <div key={skillName} className="space-y-2">
          {skillOutputs.map((output) => (
            <SkillCard key={output.id} output={output} />
          ))}
        </div>
      ))}
    </div>
  );
}
