import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Code, Github } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export interface PlatformBadgeProps {
  platform: string | null | undefined;
  showIcon?: boolean;
  className?: string;
}

export function PlatformBadge({ platform, showIcon = true, className }: PlatformBadgeProps) {
  // Handle null/undefined/empty platform (legacy sessions)
  const normalizedPlatform = platform?.toLowerCase() || "claude-code";

  // Determine badge variant and display text
  const isClaude = normalizedPlatform === "claude-code" || normalizedPlatform === "claude";
  const isCopilot = normalizedPlatform === "copilot";

  const variant = isClaude ? "info" : isCopilot ? "secondary" : "outline";
  const displayText = isClaude ? "Claude Code" : isCopilot ? "Copilot" : "Unknown";
  const Icon = isClaude ? Code : Github;
  const tooltipText = isClaude
    ? "Session created on Claude Code"
    : isCopilot
    ? "Session created on GitHub Copilot"
    : "Unknown platform";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant={variant} className={className}>
            {showIcon && <Icon className="mr-1 h-3 w-3" />}
            {displayText}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltipText}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
