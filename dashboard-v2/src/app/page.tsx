"use client";

import { StatsCards } from "@/components/dashboard/stats-cards";
import { ActiveSession } from "@/components/dashboard/active-session";
import { RecentSessions } from "@/components/dashboard/recent-sessions";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <StatsCards />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Active Session - Takes 1 column */}
        <div className="lg:col-span-1">
          <ActiveSession />
        </div>

        {/* Recent Sessions - Takes 2 columns */}
        <div className="lg:col-span-2">
          <RecentSessions />
        </div>
      </div>
    </div>
  );
}
