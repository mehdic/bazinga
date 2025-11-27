"use client";

import { useEffect, useRef, useCallback } from "react";
import { useSocketStore, SocketEvent } from "@/lib/socket/client";
import { trpc } from "@/lib/trpc/client";

// Debounce delay in milliseconds - batches rapid events
const DEBOUNCE_DELAY = 200;

// Track which invalidations are pending per session
interface PendingInvalidations {
  sessionDetails: Set<string>; // sessionIds needing getById refresh
  tokenBreakdown: Set<string>; // sessionIds needing token refresh
  globalQueries: boolean; // list, stats, active, metrics
}

/**
 * Hook that syncs socket events with tRPC query cache.
 *
 * Features:
 * - Debounces rapid events (200ms window) to prevent API spam
 * - Batches invalidations by session ID
 * - Handles reconnection by refreshing all queries
 *
 * Should be used once at the app level (in providers.tsx).
 */
export function useSocketQuerySync() {
  const registerEventCallback = useSocketStore(
    (state) => state.registerEventCallback
  );
  const isConnected = useSocketStore((state) => state.isConnected);
  const wasConnectedRef = useRef(false);
  const utils = trpc.useUtils();

  // Track pending invalidations for debouncing
  const pendingRef = useRef<PendingInvalidations>({
    sessionDetails: new Set(),
    tokenBreakdown: new Set(),
    globalQueries: false,
  });
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Flush all pending invalidations
  const flushInvalidations = useCallback(() => {
    const pending = pendingRef.current;

    // Invalidate global queries if flagged
    if (pending.globalQueries) {
      utils.sessions.list.invalidate();
      utils.sessions.getActive.invalidate();
      utils.sessions.getStats.invalidate();
      utils.sessions.getAgentMetrics.invalidate();
    }

    // Invalidate session-specific queries
    pending.sessionDetails.forEach((sessionId) => {
      utils.sessions.getById.invalidate({ sessionId });
    });

    pending.tokenBreakdown.forEach((sessionId) => {
      utils.sessions.getTokenBreakdown.invalidate({ sessionId });
    });

    // Reset pending state
    pendingRef.current = {
      sessionDetails: new Set(),
      tokenBreakdown: new Set(),
      globalQueries: false,
    };
  }, [utils]);

  // Schedule debounced flush
  const scheduleFlush = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(flushInvalidations, DEBOUNCE_DELAY);
  }, [flushInvalidations]);

  // Handle reconnection - refresh everything
  useEffect(() => {
    // On reconnect (was disconnected, now connected), refresh all queries
    if (isConnected && !wasConnectedRef.current) {
      // Small delay to let socket stabilize
      const timer = setTimeout(() => {
        utils.sessions.list.invalidate();
        utils.sessions.getActive.invalidate();
        utils.sessions.getStats.invalidate();
        utils.sessions.getAgentMetrics.invalidate();
      }, 500);

      return () => clearTimeout(timer);
    }
    wasConnectedRef.current = isConnected;
  }, [isConnected, utils]);

  useEffect(() => {
    const handleEvent = (event: SocketEvent) => {
      const pending = pendingRef.current;

      // Queue invalidations based on event type
      switch (event.type) {
        case "session:started":
          // New session - refresh global queries
          pending.globalQueries = true;
          break;

        case "session:completed":
        case "bazinga":
          // Session finished - refresh everything
          pending.globalQueries = true;
          pending.sessionDetails.add(event.sessionId);
          break;

        case "agent:spawned":
        case "agent:completed":
          // Agent activity - refresh session details
          pending.sessionDetails.add(event.sessionId);
          pending.globalQueries = true; // For active session badge
          break;

        case "log:added":
          // New log - refresh session details and tokens
          pending.sessionDetails.add(event.sessionId);
          pending.tokenBreakdown.add(event.sessionId);
          break;

        case "group:updated":
          // Task group status change - refresh session details
          pending.sessionDetails.add(event.sessionId);
          break;
      }

      // Schedule debounced flush
      scheduleFlush();
    };

    // Register callback and get cleanup function
    const unregister = registerEventCallback(handleEvent);

    // Cleanup on unmount
    return () => {
      unregister();
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [registerEventCallback, scheduleFlush]);
}
