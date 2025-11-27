"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc/client";
import { SessionCard } from "@/components/dashboard/session-card";
import {
  History,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";

type StatusFilter = "all" | "active" | "completed" | "failed";

export default function SessionsPage() {
  const [status, setStatus] = useState<StatusFilter>("all");
  const [page, setPage] = useState(0);
  const limit = 12;

  const { data, isLoading, isFetching } = trpc.sessions.list.useQuery({
    limit,
    offset: page * limit,
    status,
  });

  const statusFilters: { label: string; value: StatusFilter; color: string }[] = [
    { label: "All", value: "all", color: "default" },
    { label: "Active", value: "active", color: "success" },
    { label: "Completed", value: "completed", color: "info" },
    { label: "Failed", value: "failed", color: "destructive" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <History className="h-6 w-6" />
            Sessions
          </h1>
          <p className="text-muted-foreground">
            Browse and analyze all orchestration sessions
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isFetching && !isLoading && (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="flex items-center gap-4 p-4">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <div className="flex gap-2">
            {statusFilters.map((filter) => (
              <Button
                key={filter.value}
                variant={status === filter.value ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setStatus(filter.value);
                  setPage(0);
                }}
              >
                {filter.label}
                {data && filter.value === "all" && (
                  <Badge variant="secondary" className="ml-2">
                    {data.total}
                  </Badge>
                )}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sessions Grid */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[...Array(8)].map((_, i) => (
            <Card key={i} className="h-48 animate-pulse">
              <CardContent className="p-6">
                <div className="space-y-3">
                  <div className="h-4 w-24 rounded bg-muted" />
                  <div className="h-12 rounded bg-muted" />
                  <div className="h-4 w-32 rounded bg-muted" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : data?.sessions.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <History className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">No sessions found</h3>
            <p className="text-sm text-muted-foreground">
              {status === "all"
                ? "Start your first orchestration to see sessions here."
                : `No ${status} sessions found.`}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {data?.sessions.map((session) => (
            <SessionCard key={session.sessionId} session={session} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total > limit && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {page * limit + 1}-{Math.min((page + 1) * limit, data.total)} of{" "}
            {data.total} sessions
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={!data.hasMore}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
