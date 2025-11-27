"use client";

import { useEffect } from "react";
import { useSocketStore, SocketEvent } from "@/lib/socket/client";
import { trpc } from "@/lib/trpc/client";

/**
 * Hook that syncs socket events with tRPC query cache.
 *
 * When socket events arrive, this invalidates the relevant queries
 * so they refetch with fresh data. This enables real-time updates
 * without polling when the socket is connected.
 *
 * Should be used once at the app level (in providers.tsx).
 */
export function useSocketQuerySync() {
  const registerEventCallback = useSocketStore(
    (state) => state.registerEventCallback
  );
  const utils = trpc.useUtils();

  useEffect(() => {
    const handleEvent = (event: SocketEvent) => {
      // Invalidate relevant queries based on event type
      switch (event.type) {
        case "session:started":
          // New session - refresh session list and active session
          utils.sessions.list.invalidate();
          utils.sessions.getActive.invalidate();
          utils.sessions.getStats.invalidate();
          break;

        case "session:completed":
        case "bazinga":
          // Session finished - refresh everything related to sessions
          utils.sessions.list.invalidate();
          utils.sessions.getActive.invalidate();
          utils.sessions.getStats.invalidate();
          utils.sessions.getById.invalidate({ sessionId: event.sessionId });
          utils.sessions.getAgentMetrics.invalidate();
          break;

        case "agent:spawned":
        case "agent:completed":
          // Agent activity - refresh session details
          utils.sessions.getById.invalidate({ sessionId: event.sessionId });
          utils.sessions.getActive.invalidate();
          break;

        case "log:added":
          // New log - refresh session details and token breakdown
          utils.sessions.getById.invalidate({ sessionId: event.sessionId });
          utils.sessions.getTokenBreakdown.invalidate({
            sessionId: event.sessionId,
          });
          break;

        case "group:updated":
          // Task group status change - refresh session details
          utils.sessions.getById.invalidate({ sessionId: event.sessionId });
          break;
      }
    };

    // Register callback and get cleanup function
    const unregister = registerEventCallback(handleEvent);

    // Cleanup on unmount
    return unregister;
  }, [registerEventCallback, utils]);
}
