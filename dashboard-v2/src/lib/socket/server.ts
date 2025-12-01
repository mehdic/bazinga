// Socket.io server for real-time dashboard updates
// This runs as a separate process alongside the Next.js dev server

import { Server } from "socket.io";
import { createServer } from "http";
import path from "path";
import fs from "fs";

// Types for better-sqlite3 (imported dynamically to handle architecture mismatch)
type DatabaseInstance = {
  prepare: (sql: string) => {
    all: (...args: unknown[]) => unknown[];
    get: (...args: unknown[]) => unknown;
    run: (...args: unknown[]) => { changes: number; lastInsertRowid: bigint };
  };
  close: () => void;
  exec: (sql: string) => void;
  pragma: (pragma: string, options?: { simple?: boolean }) => unknown;
  transaction: <A extends unknown[], T>(fn: (...args: A) => T) => (...args: A) => T;
};
type DatabaseConstructor = new (path: string, options?: { readonly?: boolean }) => DatabaseInstance;

const PORT = process.env.SOCKET_PORT || 3001;

/**
 * Resolve database path robustly for both dev and bundled (dist) environments.
 * After esbuild bundles to dist/, __dirname changes from src/lib/socket to dist.
 */
function resolveDbPath(): string {
  // Environment variable takes precedence
  if (process.env.DATABASE_URL) {
    return process.env.DATABASE_URL;
  }

  // Candidate paths for different runtime scenarios
  const candidates = [
    // Running from dashboard-v2 root (dev): cwd = dashboard-v2, db at ../bazinga/bazinga.db
    path.resolve(process.cwd(), "..", "bazinga", "bazinga.db"),
    // Running from dist/socket-server.js (prod): __dirname = dist, db at ../bazinga/bazinga.db
    path.resolve(__dirname, "..", "bazinga", "bazinga.db"),
    // Running from src/lib/socket (ts-node dev): __dirname = src/lib/socket
    path.resolve(__dirname, "..", "..", "..", "..", "bazinga", "bazinga.db"),
    // Extra fallback: two levels up from dist
    path.resolve(__dirname, "..", "..", "bazinga", "bazinga.db"),
  ];

  // Find first existing path
  for (const p of candidates) {
    try {
      if (fs.existsSync(p)) {
        return p;
      }
    } catch {
      // Ignore access errors
    }
  }

  // Fallback to first candidate for error messages
  return candidates[0];
}

const DB_PATH = resolveDbPath();

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

// Reusable database connection (lazy initialization)
let _db: DatabaseInstance | null = null;
let _moduleLoadFailed = false;
let _DatabaseClass: DatabaseConstructor | null = null;

/**
 * Dynamically load better-sqlite3 to handle:
 * - Architecture mismatch (arm64 binary on x86_64 or vice versa)
 * - Module not found errors
 */
function loadDatabaseModule(): DatabaseConstructor | null {
  if (_moduleLoadFailed) return null;
  if (_DatabaseClass) return _DatabaseClass;

  try {
    // Use require() for dynamic loading - catches architecture mismatch errors
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    _DatabaseClass = require("better-sqlite3") as DatabaseConstructor;
    return _DatabaseClass;
  } catch (error) {
    // Classify error using error codes (preferred) with string fallback
    const err = error as NodeJS.ErrnoException;
    const code = err?.code;
    const msg = String(err?.message || error || "");

    // Determine if this is a permanent (sticky) failure or potentially transient
    const isModuleNotFound = code === "MODULE_NOT_FOUND" || msg.includes("Cannot find module");
    const isArchMismatch = code === "ERR_DLOPEN_FAILED" ||
      /incompatible architecture|Mach-O|ELF|wrong architecture|arm64.*x86_64|x86_64.*arm64/i.test(msg);

    // Only mark as permanently failed for architecture mismatches (not transient errors)
    if (isArchMismatch) {
      _moduleLoadFailed = true;
      console.warn(
        `Database module architecture mismatch detected.\n` +
        `The better-sqlite3 native binary was compiled for a different CPU architecture.\n` +
        `To fix: cd dashboard-v2 && npm rebuild better-sqlite3\n` +
        `Socket server will run without database access.`
      );
    } else if (isModuleNotFound) {
      // Module not found could be transient (npm install pending) - don't mark sticky
      console.warn(
        `Database module not found. Run: cd dashboard-v2 && npm install\n` +
        `Socket server will run without database access.`
      );
    } else {
      // Unknown error - log but allow retry
      console.warn(`Database module failed to load: ${error}`);
    }

    return null;
  }
}

function getDb(): DatabaseInstance | null {
  if (_db) return _db;
  if (_moduleLoadFailed) return null;

  const Database = loadDatabaseModule();
  if (!Database) return null;

  try {
    _db = new Database(DB_PATH, { readonly: true });
    return _db;
  } catch (error) {
    console.warn(`Database not available at ${DB_PATH}: ${error}`);
    return null;
  }
}

// Cleanup on exit
process.on("exit", () => {
  if (_db) _db.close();
});

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
    const db = getDb();
    if (!db) return; // Database not available yet

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

    // Check for session status changes (use end_time for completed sessions)
    // Note: sessions table has start_time, end_time, created_at - no updated_at
    const sessions = db
      .prepare(
        `SELECT session_id, status,
                COALESCE(end_time, start_time) as last_change
         FROM sessions
         WHERE COALESCE(end_time, start_time) > ?
         ORDER BY COALESCE(end_time, start_time) ASC`
      )
      .all(lastSessionUpdate || "1970-01-01") as Array<{
      session_id: string;
      status: string;
      last_change: string;
    }>;

    for (const session of sessions) {
      lastSessionUpdate = session.last_change;

      io.emit("event", {
        type: session.status === "completed" ? "session:completed" : "session:started",
        sessionId: session.session_id,
        status: session.status,
      } as SocketEvent);
    }
  } catch {
    // Database might be locked or unavailable - that's ok, retry next cycle
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
