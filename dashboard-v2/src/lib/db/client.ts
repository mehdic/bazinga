import type { BetterSQLite3Database } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";
import path from "path";

// Types for better-sqlite3 (imported dynamically to handle architecture mismatch)
type DatabaseInstance = {
  prepare: (sql: string) => {
    all: (...args: unknown[]) => unknown[];
    get: (...args: unknown[]) => unknown;
    run: (...args: unknown[]) => { changes: number; lastInsertRowid: number | bigint };
  };
  close: () => void;
  exec: (sql: string) => void;
  pragma: (pragma: string, options?: { simple?: boolean }) => unknown;
  transaction: <T>(fn: () => T) => () => T;
};
type DatabaseConstructor = new (path: string, options?: { readonly?: boolean }) => DatabaseInstance;

// Drizzle function type (actual BetterSQLite3Database type imported above)
type DrizzleFunction = (client: DatabaseInstance, config: { schema: typeof schema }) => BetterSQLite3Database<typeof schema>;

// Lazy database initialization to avoid build-time and architecture errors
let _sqlite: DatabaseInstance | null = null;
let _db: BetterSQLite3Database<typeof schema> | null = null;
let _dbPath: string | null = null;
let _moduleLoadFailed = false;
let _DatabaseClass: DatabaseConstructor | null = null;
let _drizzle: DrizzleFunction | null = null;

/**
 * Dynamically load better-sqlite3 AND drizzle-orm to handle:
 * - Build-time errors (module not available during SSG)
 * - Architecture mismatch (arm64 binary on x86_64 or vice versa)
 *
 * NOTE: drizzle-orm/better-sqlite3 statically imports better-sqlite3,
 * so we must load it dynamically too to catch architecture errors.
 */
function loadDatabaseModules(): { Database: DatabaseConstructor; drizzle: DrizzleFunction } | null {
  if (_moduleLoadFailed) return null;
  if (_DatabaseClass && _drizzle) return { Database: _DatabaseClass, drizzle: _drizzle };

  try {
    // Use require() for dynamic loading - catches architecture mismatch errors
    // Must load better-sqlite3 first to catch errors before drizzle tries to import it
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    _DatabaseClass = require("better-sqlite3") as DatabaseConstructor;
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const drizzleModule = require("drizzle-orm/better-sqlite3") as { drizzle: DrizzleFunction };
    _drizzle = drizzleModule.drizzle;
    return { Database: _DatabaseClass, drizzle: _drizzle };
  } catch (error) {
    _moduleLoadFailed = true;
    const errorMessage = String(error);

    // Detect architecture mismatch
    if (errorMessage.includes("incompatible architecture") ||
        errorMessage.includes("arm64") ||
        errorMessage.includes("x86_64")) {
      console.warn(
        `Database module architecture mismatch detected.\n` +
        `The better-sqlite3 native binary was compiled for a different CPU architecture.\n` +
        `To fix: cd dashboard-v2 && npm rebuild better-sqlite3\n` +
        `Dashboard will run without database access.`
      );
    } else if (errorMessage.includes("Cannot find module")) {
      console.warn(
        `Database module not found. Run: cd dashboard-v2 && npm install\n` +
        `Dashboard will run without database access.`
      );
    } else {
      console.warn(`Database module failed to load: ${error}`);
    }

    return null;
  }
}

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

function getDatabase(): DatabaseInstance | null {
  if (_sqlite) return _sqlite;
  if (_moduleLoadFailed) return null;

  // First, try to load the modules
  const modules = loadDatabaseModules();
  if (!modules) return null;

  try {
    // Resolve path lazily on first access (not at import time)
    if (!_dbPath) {
      _dbPath = resolveDatabasePath();
    }
    _sqlite = new modules.Database(_dbPath, { readonly: true });
    // Note: WAL mode not set - requires write access, but we're read-only
    return _sqlite;
  } catch (error) {
    // If database file doesn't exist, return null (allows build to succeed)
    // The mock proxy will return empty results during build/SSG
    const errorMessage = String(error);
    if (errorMessage.includes("SQLITE_CANTOPEN") ||
        errorMessage.includes("unable to open database") ||
        errorMessage.includes("no such file")) {
      console.warn(`Database not available at ${_dbPath}: ${error}`);
      return null;
    }

    // For other errors (permissions, corruption, etc.), log and continue
    console.warn(
      `Database connection failed: ${error}\n` +
      `Path: ${_dbPath}\n` +
      `Dashboard will run without database access.`
    );
    return null;
  }
}

function getDrizzle(): BetterSQLite3Database<typeof schema> | null {
  if (_db) return _db;
  if (_moduleLoadFailed) return null;

  const sqlite = getDatabase();
  if (!sqlite) return null;

  // drizzle is already loaded by loadDatabaseModules()
  if (_drizzle) {
    _db = _drizzle(sqlite, { schema });
    return _db;
  }
  return null;
}

// Export lazy-initialized db with mock fallback
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
export const sqlite = new Proxy({} as DatabaseInstance, {
  get(_, prop) {
    const db = getDatabase();
    if (!db) return () => [];
    return (db as unknown as Record<string, unknown>)[prop as string];
  },
});
