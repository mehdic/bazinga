import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

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

export function timeAgo(date: Date | string): string {
  const now = new Date();
  const then = new Date(date);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return then.toLocaleDateString();
}
