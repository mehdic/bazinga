"use client";

import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { trpc } from "@/lib/trpc/client";
import { useSocket } from "@/lib/socket/client";
import { useRefetchInterval } from "@/lib/hooks/use-smart-refetch";
import { NotificationDropdown } from "@/components/notifications/notification-dropdown";
import {
  Moon,
  Sun,
  RefreshCw,
  Wifi,
  WifiOff,
  Loader2,
} from "lucide-react";
import { useState } from "react";

interface HeaderProps {
  title?: string;
}

export function Header({ title = "Dashboard" }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const { isConnected } = useSocket();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const utils = trpc.useUtils();

  // Smart refetch: no polling when socket connected, 5s fallback when disconnected
  const refetchInterval = useRefetchInterval(5000);

  const { data: activeSession } = trpc.sessions.getActive.useQuery(undefined, {
    refetchInterval,
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await utils.sessions.invalidate();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold">{title}</h1>
        {activeSession && (
          <Badge variant="default" className="animate-pulse bg-green-500">
            Active Session
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-2">
        {/* Connection Status */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className="relative cursor-default">
              {isConnected ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {isConnected ? "Real-time updates active" : "Connecting to real-time server..."}
          </TooltipContent>
        </Tooltip>

        {/* Refresh */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              {isRefreshing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>Refresh data</TooltipContent>
        </Tooltip>

        {/* Notifications */}
        <NotificationDropdown />

        {/* Theme Toggle */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </TooltipContent>
        </Tooltip>
      </div>
    </header>
  );
}
