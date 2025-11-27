"use client";

import { useSocketStore } from "@/lib/socket/client";

/**
 * Smart refetch interval that adapts based on WebSocket connection status.
 *
 * When socket is connected:
 *   - Returns `false` (no polling) - socket events trigger cache invalidation
 *   - Real-time updates via WebSocket
 *
 * When socket is disconnected:
 *   - Returns polling interval as fallback
 *   - Ensures data stays fresh even without real-time connection
 *
 * @param fallbackInterval - Polling interval (ms) when socket disconnected. Default: 10000
 * @returns Object with refetchInterval and connection status
 */
export function useSmartRefetch(fallbackInterval: number = 10000) {
  const isConnected = useSocketStore((state) => state.isConnected);

  return {
    // When connected, disable polling (socket events handle updates)
    // When disconnected, use fallback polling interval
    refetchInterval: isConnected ? false : fallbackInterval,
    isConnected,
  };
}

/**
 * Get refetch interval for use in query options.
 * Simpler version that just returns the interval value.
 *
 * @param fallbackInterval - Polling interval (ms) when socket disconnected
 * @returns refetchInterval value (false or number)
 */
export function useRefetchInterval(fallbackInterval: number = 10000): false | number {
  const isConnected = useSocketStore((state) => state.isConnected);
  return isConnected ? false : fallbackInterval;
}
