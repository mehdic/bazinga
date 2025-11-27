// Socket.io server for real-time dashboard updates
// This runs as a separate process alongside the Next.js dev server

import { Server } from "socket.io";
import { createServer } from "http";
import Database from "better-sqlite3";
import path from "path";

const PORT = process.env.SOCKET_PORT || 3001;
const DB_PATH = process.env.DATABASE_URL || path.join(process.cwd(), "..", "bazinga", "bazinga.db");

// Event types
export type SocketEvent =
  | { type: "session:started"; sessionId: string; requirements: string }
  | { type: "session:completed"; sessionId: string; status: string }
  | { type: "agent:spawned"; sessionId: string; agentType: string; groupId?: string }
  | { type: "agent:completed"; sessionId: string; agentType: string; statusCode: string }
  | { type: "log:added"; sessionId: string; logId: number; agentType: string; content: string }
  | { type: "group:updated"; sessionId: string; groupId: string; status: string }
  | { type: "bazinga"; sessionId: string };

// Create HTTP server for Socket.io
const httpServer = createServer();

// Create Socket.io server
const io = new Server(httpServer, {
  cors: {
    origin: ["http://localhost:3000", "http://127.0.0.1:3000"],
    methods: ["GET", "POST"],
  },
});

// Track connected clients
let connectedClients = 0;

// Database polling state
let lastLogId = 0;
let lastSessionUpdate = "";

io.on("connection", (socket) => {
  connectedClients++;
  console.log(`Client connected. Total: ${connectedClients}`);

  // Send connection confirmation
  socket.emit("connected", { timestamp: new Date().toISOString() });

  // Handle subscription to specific session
  socket.on("subscribe:session", (sessionId: string) => {
    socket.join(`session:${sessionId}`);
    console.log(`Client subscribed to session: ${sessionId}`);
  });

  socket.on("unsubscribe:session", (sessionId: string) => {
    socket.leave(`session:${sessionId}`);
  });

  socket.on("disconnect", () => {
    connectedClients--;
    console.log(`Client disconnected. Total: ${connectedClients}`);
  });
});

// Poll database for changes and emit events
function pollDatabase() {
  try {
    const db = new Database(DB_PATH, { readonly: true });

    // Check for new logs
    const newLogs = db
      .prepare(
        `SELECT id, session_id, agent_type, content, timestamp
         FROM orchestration_logs
         WHERE id > ?
         ORDER BY id ASC
         LIMIT 50`
      )
      .all(lastLogId) as Array<{
      id: number;
      session_id: string;
      agent_type: string;
      content: string;
      timestamp: string;
    }>;

    for (const log of newLogs) {
      lastLogId = Math.max(lastLogId, log.id);

      // Emit to session room
      io.to(`session:${log.session_id}`).emit("event", {
        type: "log:added",
        sessionId: log.session_id,
        logId: log.id,
        agentType: log.agent_type,
        content: log.content.slice(0, 200),
      } as SocketEvent);

      // Emit to all clients for global notifications
      io.emit("log", {
        sessionId: log.session_id,
        agentType: log.agent_type,
        timestamp: log.timestamp,
      });

      // Check for BAZINGA
      if (log.content.includes("BAZINGA")) {
        io.emit("event", {
          type: "bazinga",
          sessionId: log.session_id,
        } as SocketEvent);
      }
    }

    // Check for session status changes
    const sessions = db
      .prepare(
        `SELECT session_id, status, updated_at
         FROM sessions
         WHERE updated_at > ?
         ORDER BY updated_at ASC`
      )
      .all(lastSessionUpdate || "1970-01-01") as Array<{
      session_id: string;
      status: string;
      updated_at: string;
    }>;

    for (const session of sessions) {
      lastSessionUpdate = session.updated_at;

      io.emit("event", {
        type: session.status === "completed" ? "session:completed" : "session:started",
        sessionId: session.session_id,
        status: session.status,
      } as SocketEvent);
    }

    db.close();
  } catch (error) {
    // Database might not exist yet or be locked - that's ok
  }
}

// Start polling every 2 seconds
setInterval(pollDatabase, 2000);

// Start server
httpServer.listen(PORT, () => {
  console.log(`Socket.io server running on port ${PORT}`);
});

// Export for programmatic use
export { io, httpServer };
