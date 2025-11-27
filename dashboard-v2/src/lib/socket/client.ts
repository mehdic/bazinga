"use client";

import { io, Socket } from "socket.io-client";
import { create } from "zustand";
import { useEffect } from "react";

// Socket event types (matching server)
export type SocketEvent =
  | { type: "session:started"; sessionId: string; requirements?: string }
  | { type: "session:completed"; sessionId: string; status: string }
  | { type: "agent:spawned"; sessionId: string; agentType: string; groupId?: string }
  | { type: "agent:completed"; sessionId: string; agentType: string; statusCode: string }
  | { type: "log:added"; sessionId: string; logId: number; agentType: string; content: string }
  | { type: "group:updated"; sessionId: string; groupId: string; status: string }
  | { type: "bazinga"; sessionId: string };

// Notification type for UI
export interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: Date;
  sessionId?: string;
  read: boolean;
}

// Event listener callback type for query invalidation
type EventCallback = (event: SocketEvent) => void;

// Socket store with Zustand
interface SocketState {
  socket: Socket | null;
  isConnected: boolean;
  notifications: Notification[];
  recentEvents: SocketEvent[];
  eventCallbacks: Set<EventCallback>;
  connect: () => void;
  disconnect: () => void;
  subscribeToSession: (sessionId: string) => void;
  unsubscribeFromSession: (sessionId: string) => void;
  addNotification: (notification: Omit<Notification, "id" | "timestamp" | "read">) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;
  registerEventCallback: (callback: EventCallback) => () => void;
}

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:3001";

export const useSocketStore = create<SocketState>((set, get) => ({
  socket: null,
  isConnected: false,
  notifications: [],
  recentEvents: [],
  eventCallbacks: new Set(),

  connect: () => {
    const existingSocket = get().socket;
    if (existingSocket?.connected) return;

    const socket = io(SOCKET_URL, {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socket.on("connect", () => {
      set({ isConnected: true });
      console.log("Socket connected");
    });

    socket.on("disconnect", () => {
      set({ isConnected: false });
      console.log("Socket disconnected");
    });

    socket.on("connect_error", (error) => {
      console.log("Socket connection error:", error.message);
      set({ isConnected: false });
    });

    // Handle events from server
    socket.on("event", (event: SocketEvent) => {
      const { addNotification, recentEvents, eventCallbacks } = get();

      // Add to recent events (keep last 50)
      set({
        recentEvents: [event, ...recentEvents.slice(0, 49)],
      });

      // Notify all registered callbacks (for query invalidation)
      eventCallbacks.forEach((callback) => {
        try {
          callback(event);
        } catch (e) {
          console.error("Error in socket event callback:", e);
        }
      });

      // Create notifications for important events
      switch (event.type) {
        case "session:started":
          addNotification({
            type: "info",
            title: "Session Started",
            message: `New orchestration session: ${event.sessionId.slice(-8)}`,
            sessionId: event.sessionId,
          });
          break;

        case "session:completed":
          addNotification({
            type: event.status === "completed" ? "success" : "warning",
            title: "Session Completed",
            message: `Session ${event.sessionId.slice(-8)} finished with status: ${event.status}`,
            sessionId: event.sessionId,
          });
          break;

        case "bazinga":
          addNotification({
            type: "success",
            title: "BAZINGA!",
            message: `Session ${event.sessionId.slice(-8)} completed successfully!`,
            sessionId: event.sessionId,
          });
          // Could trigger browser notification here
          if (typeof window !== "undefined" && Notification.permission === "granted") {
            new Notification("BAZINGA!", {
              body: `Session completed successfully`,
              icon: "/favicon.ico",
            });
          }
          break;

        case "agent:completed":
          if (event.statusCode === "BLOCKED" || event.statusCode === "FAILED") {
            addNotification({
              type: "warning",
              title: `${event.agentType} ${event.statusCode}`,
              message: `Agent reported ${event.statusCode} status`,
              sessionId: event.sessionId,
            });
          }
          break;
      }
    });

    // Handle log events (lighter weight)
    socket.on("log", (data: { sessionId: string; agentType: string; timestamp: string }) => {
      // Could update a "latest activity" indicator
    });

    set({ socket });
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.disconnect();
      set({ socket: null, isConnected: false });
    }
  },

  subscribeToSession: (sessionId: string) => {
    const { socket } = get();
    if (socket?.connected) {
      socket.emit("subscribe:session", sessionId);
    }
  },

  unsubscribeFromSession: (sessionId: string) => {
    const { socket } = get();
    if (socket?.connected) {
      socket.emit("unsubscribe:session", sessionId);
    }
  },

  addNotification: (notification) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    set((state) => ({
      notifications: [
        {
          ...notification,
          id,
          timestamp: new Date(),
          read: false,
        },
        ...state.notifications.slice(0, 49), // Keep last 50
      ],
    }));
  },

  markNotificationRead: (id: string) => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    }));
  },

  clearNotifications: () => {
    set({ notifications: [] });
  },

  registerEventCallback: (callback: EventCallback) => {
    set((state) => {
      const newCallbacks = new Set(state.eventCallbacks);
      newCallbacks.add(callback);
      return { eventCallbacks: newCallbacks };
    });

    // Return unregister function
    return () => {
      set((state) => {
        const newCallbacks = new Set(state.eventCallbacks);
        newCallbacks.delete(callback);
        return { eventCallbacks: newCallbacks };
      });
    };
  },
}));

// Hook for auto-connecting on mount
export function useSocket() {
  const { connect, isConnected, notifications, recentEvents } = useSocketStore();

  // Connect on mount using useEffect (proper React pattern)
  // This prevents duplicate connections from React 18 double renders
  useEffect(() => {
    if (!useSocketStore.getState().socket) {
      connect();
    }
  }, [connect]);

  return { isConnected, notifications, recentEvents };
}

// Hook for subscribing to a specific session
export function useSessionSocket(sessionId: string | null) {
  const { subscribeToSession, unsubscribeFromSession, recentEvents } =
    useSocketStore();

  // Filter events for this session
  const sessionEvents = sessionId
    ? recentEvents.filter(
        (e) => "sessionId" in e && e.sessionId === sessionId
      )
    : [];

  return {
    subscribe: () => sessionId && subscribeToSession(sessionId),
    unsubscribe: () => sessionId && unsubscribeFromSession(sessionId),
    events: sessionEvents,
  };
}
