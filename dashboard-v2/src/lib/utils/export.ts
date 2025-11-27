// Export utilities for session data
// Updated to match actual database schema

export interface ExportableSession {
  sessionId: string;
  status: string | null;
  mode: string | null;
  startTime: string | null;
  endTime: string | null;
  originalRequirements: string | null;
  logs?: Array<{
    id: number;
    agentType: string;
    content: string;
    timestamp: string | null;
  }>;
  taskGroups?: Array<{
    id: string;
    name: string;
    status: string | null;
    revisionCount: number | null;
    assignedTo: string | null;
    complexity: number | null;
  }>;
  tokenUsage?: Array<{
    agentType: string;
    tokensEstimated: number;
    timestamp: string | null;
  }>;
}

export function exportToJSON(session: ExportableSession, filename?: string) {
  const data = JSON.stringify(session, null, 2);
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename || `session-${session.sessionId}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function exportToCSV(
  data: Record<string, unknown>[],
  filename: string
) {
  if (data.length === 0) return;

  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(","),
    ...data.map((row) =>
      headers
        .map((header) => {
          const value = row[header];
          // Escape quotes and wrap in quotes if contains comma
          const stringValue = String(value ?? "");
          if (stringValue.includes(",") || stringValue.includes('"') || stringValue.includes("\n")) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(",")
    ),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function exportSessionLogs(
  logs: ExportableSession["logs"],
  sessionId: string
) {
  if (!logs || logs.length === 0) return;

  const csvData = logs.map((log) => ({
    timestamp: log.timestamp || "",
    agentType: log.agentType,
    content: log.content.slice(0, 500), // Truncate for CSV
  }));

  exportToCSV(csvData, `session-${sessionId}-logs.csv`);
}

export function exportTokenUsage(
  tokens: ExportableSession["tokenUsage"],
  sessionId: string
) {
  if (!tokens || tokens.length === 0) return;

  const csvData = tokens.map((token) => ({
    timestamp: token.timestamp || "",
    agentType: token.agentType,
    tokensEstimated: token.tokensEstimated,
  }));

  exportToCSV(csvData, `session-${sessionId}-tokens.csv`);
}
