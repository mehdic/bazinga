"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc/client";
import {
  LayoutDashboard,
  History,
  Activity,
  Settings,
  Zap,
  ChevronRight,
  ArrowLeftRight,
  Settings2,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Sessions", href: "/sessions", icon: History },
  { name: "Compare", href: "/sessions/compare", icon: ArrowLeftRight },
  { name: "Analytics", href: "/analytics", icon: Activity },
  { name: "Config", href: "/config", icon: Settings2 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: stats } = trpc.sessions.getStats.useQuery();
  const { data: sessions } = trpc.sessions.list.useQuery({ limit: 5 });

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <Zap className="h-6 w-6 text-primary" />
        <span className="text-xl font-bold">BAZINGA</span>
        <Badge variant="secondary" className="ml-auto">
          v2.0
        </Badge>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.name} href={item.href}>
              <Button
                variant={isActive ? "secondary" : "ghost"}
                className={cn("w-full justify-start", isActive && "bg-secondary")}
              >
                <item.icon className="mr-2 h-4 w-4" />
                {item.name}
              </Button>
            </Link>
          );
        })}
      </nav>

      {/* Recent Sessions */}
      <div className="border-t p-4">
        <h3 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
          Recent Sessions
        </h3>
        <ScrollArea className="h-48">
          <div className="space-y-1">
            {sessions?.sessions.map((session) => (
              <Link
                key={session.sessionId}
                href={`/sessions/${session.sessionId}`}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-between text-xs"
                >
                  <span className="flex items-center gap-2 truncate">
                    <span
                      className={cn(
                        "h-2 w-2 rounded-full",
                        session.status === "active" && "bg-green-500",
                        session.status === "completed" && "bg-blue-500",
                        session.status === "failed" && "bg-red-500"
                      )}
                    />
                    <span className="truncate">
                      #{session.sessionId.split("_").pop()?.slice(0, 6)}
                    </span>
                  </span>
                  <ChevronRight className="h-3 w-3 text-muted-foreground" />
                </Button>
              </Link>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Stats Footer */}
      {stats && (
        <div className="border-t p-4">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Active</span>
              <p className="font-semibold text-green-500">{stats.activeSessions}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Success</span>
              <p className="font-semibold">{stats.successRate.toFixed(0)}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
