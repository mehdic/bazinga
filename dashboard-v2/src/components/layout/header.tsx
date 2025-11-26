"use client";

import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc/client";
import {
  Bell,
  Moon,
  Sun,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useState, useEffect } from "react";

interface HeaderProps {
  title?: string;
}

export function Header({ title = "Dashboard" }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const [isConnected, setIsConnected] = useState(true);
  const utils = trpc.useUtils();

  const { data: activeSession } = trpc.sessions.getActive.useQuery(undefined, {
    refetchInterval: 5000,
  });

  const handleRefresh = () => {
    utils.sessions.invalidate();
  };

  // Simulate connection status (would be WebSocket in production)
  useEffect(() => {
    const interval = setInterval(() => {
      setIsConnected(true);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold">{title}</h1>
        {activeSession && (
          <Badge variant="success" className="animate-pulse">
            Active Session
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-2">
        {/* Connection Status */}
        <Button variant="ghost" size="icon" className="relative">
          {isConnected ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-500" />
          )}
        </Button>

        {/* Refresh */}
        <Button variant="ghost" size="icon" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4" />
        </Button>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          {activeSession && (
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-primary" />
          )}
        </Button>

        {/* Theme Toggle */}
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
      </div>
    </header>
  );
}
