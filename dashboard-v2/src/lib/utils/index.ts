import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Shared agent color palette - hex values for charts (Recharts)
export const AGENT_COLORS_HEX: Record<string, string> = {
  pm: "#8b5cf6",           // purple
  developer: "#3b82f6",    // blue
  qa_expert: "#22c55e",    // green
  tech_lead: "#f97316",    // orange
  orchestrator: "#6b7280", // gray
  investigator: "#ec4899", // pink
  senior_engineer: "#14b8a6", // teal
};

// Shared agent color palette - Tailwind classes for UI components
export const AGENT_COLORS_TW: Record<string, string> = {
  pm: "bg-purple-500",
  developer: "bg-blue-500",
  qa_expert: "bg-green-500",
  tech_lead: "bg-orange-500",
  orchestrator: "bg-gray-500",
  investigator: "bg-pink-500",
  senior_engineer: "bg-teal-500",
};

export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  }
  return `${seconds}s`;
}

export function formatTokens(tokens: number): string {
  if (tokens >= 1000000) {
    return `${(tokens / 1000000).toFixed(1)}M`;
  }
  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(1)}K`;
  }
  return tokens.toString();
}

export function formatCost(tokens: number, modelTier: string = "sonnet"): string {
  // Approximate costs per 1M tokens (input + output average)
  const costs: Record<string, number> = {
    haiku: 0.25,
    sonnet: 3.0,
    opus: 15.0,
  };
  const costPerMillion = costs[modelTier] || costs.sonnet;
  const cost = (tokens / 1000000) * costPerMillion;
  return `$${cost.toFixed(4)}`;
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case "active":
    case "in_progress":
    case "running":
      return "text-green-500";
    case "completed":
    case "success":
    case "bazinga":
    case "pass":
    case "approved":
      return "text-blue-500";
    case "failed":
    case "error":
    case "fail":
      return "text-red-500";
    case "pending":
    case "waiting":
      return "text-yellow-500";
    default:
      return "text-muted-foreground";
  }
}

export function getStatusBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  switch (status.toLowerCase()) {
    case "active":
    case "in_progress":
    case "running":
      return "default";
    case "completed":
    case "success":
    case "bazinga":
      return "secondary";
    case "failed":
    case "error":
      return "destructive";
    default:
      return "outline";
  }
}

export function timeAgo(date: Date | string | null | undefined): string {
  if (!date) return "Unknown";
  const now = new Date();
  const then = new Date(date);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return then.toLocaleDateString();
}

export function formatRelativeTime(date: Date | string | null | undefined): string {
  if (!date) return "Unknown";
  const now = new Date();
  const then = new Date(date);
  const diff = now.getTime() - then.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  if (days < 7) return `${days} day${days === 1 ? "" : "s"} ago`;
  return then.toLocaleDateString();
}
