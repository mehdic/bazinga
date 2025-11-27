import Database from "better-sqlite3";
import { drizzle, BetterSQLite3Database } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";
import path from "path";

// Lazy database initialization to avoid build-time errors
let _sqlite: Database.Database | null = null;
let _db: BetterSQLite3Database<typeof schema> | null = null;
let _dbPath: string | null = null;

/**
 * Resolve database path at RUNTIME (not import time).
 * This is called lazily on first database access to avoid breaking builds.
 *
 * - In production: DATABASE_URL is required, throws clear error if missing
 * - In development: Falls back to relative path for convenience
 */
function resolveDatabasePath(): string {
  // If DATABASE_URL is set, use it directly
  if (process.env.DATABASE_URL) {
    return process.env.DATABASE_URL;
  }

  // In production, DATABASE_URL is required
  // NOTE: This check runs at RUNTIME, not build time
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "DATABASE_URL environment variable is required in production.\n" +
        "Set it in your deployment configuration or .env.local file.\n" +
        "Example: DATABASE_URL=/path/to/bazinga/bazinga.db\n\n" +
        "If using the start-dashboard.sh script, it will auto-detect the path."
    );
  }

  // Development fallback: look for database relative to project
  return path.resolve(process.cwd(), "..", "bazinga", "bazinga.db");
}

function getDatabase() {
  if (!_sqlite) {
    try {
      // Resolve path lazily on first access (not at import time)
      if (!_dbPath) {
        _dbPath = resolveDatabasePath();
      }
      _sqlite = new Database(_dbPath, { readonly: true });
      // Note: WAL mode not set - requires write access, but we're read-only
    } catch (error) {
      // During BUILD: return null (mock is ok for SSG)
      // Check Next.js build phase or general build indicators
      const isBuildPhase = process.env.NEXT_PHASE === 'phase-production-build' ||
                           process.env.NODE_ENV === 'production' && !process.env.DATABASE_URL;

      if (isBuildPhase) {
        console.warn(`Database not available during build at ${_dbPath}:`, error);
        return null;
      }

      // During RUNTIME: throw clear error (fail fast)
      throw new Error(
        `Database connection failed: ${error}\n` +
        `Path: ${_dbPath}\n` +
        `Ensure DATABASE_URL is set or the database file exists.`
      );
    }
  }
  return _sqlite;
}

function getDrizzle() {
  if (!_db) {
    const sqlite = getDatabase();
    if (sqlite) {
      _db = drizzle(sqlite, { schema });
    }
  }
  return _db;
}

// Export lazy-initialized db
export const db = new Proxy({} as BetterSQLite3Database<typeof schema>, {
  get(_, prop) {
    const drizzleDb = getDrizzle();
    if (!drizzleDb) {
      // Return a mock that returns empty results
      if (prop === "select") {
        return () => ({
          from: () => ({
            where: () => ({
              orderBy: () => ({
                limit: () => Promise.resolve([]),
                offset: () => Promise.resolve([]),
              }),
              limit: () => Promise.resolve([]),
            }),
            orderBy: () => ({
              limit: () => ({
                offset: () => Promise.resolve([]),
              }),
            }),
            limit: () => Promise.resolve([]),
            groupBy: () => Promise.resolve([]),
          }),
        });
      }
      return () => Promise.resolve([]);
    }
    return (drizzleDb as unknown as Record<string, unknown>)[prop as string];
  },
});

// Export for direct SQL queries if needed (also lazy)
export const sqlite = new Proxy({} as Database.Database, {
  get(_, prop) {
    const db = getDatabase();
    if (!db) return () => [];
    return (db as unknown as Record<string, unknown>)[prop as string];
  },
});
