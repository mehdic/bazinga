import Database from "better-sqlite3";
import { drizzle, BetterSQLite3Database } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";
import path from "path";

// Database path resolution with production validation
function resolveDatabasePath(): string {
  // If DATABASE_URL is set, use it directly
  if (process.env.DATABASE_URL) {
    return process.env.DATABASE_URL;
  }

  // In production, DATABASE_URL is required
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

const DB_PATH = resolveDatabasePath();

// Lazy database initialization to avoid build-time errors
let _sqlite: Database.Database | null = null;
let _db: BetterSQLite3Database<typeof schema> | null = null;

function getDatabase() {
  if (!_sqlite) {
    try {
      _sqlite = new Database(DB_PATH, { readonly: true });
      // Note: WAL mode not set - requires write access, but we're read-only
    } catch (error) {
      // During build time or when database doesn't exist, return a mock
      console.warn(`Database not available at ${DB_PATH}:`, error);
      return null;
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
