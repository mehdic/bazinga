import type { BetterSQLite3Database } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";
import path from "path";
import { existsSync } from "fs";

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

// Drizzle function type (actual BetterSQLite3Database type imported above)
type DrizzleFunction = (client: DatabaseInstance, config: { schema: typeof schema }) => BetterSQLite3Database<typeof schema>;

// Lazy database initialization to avoid build-time and architecture errors
let _sqlite: DatabaseInstance | null = null;
let _db: BetterSQLite3Database<typeof schema> | null = null;
let _dbPath: string | null = null;  // Cache the resolved path (but allow re-resolution on reconnect)
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
        `Dashboard will run without database access.`
      );
    } else if (isModuleNotFound) {
      // Module not found could be transient (npm install pending) - don't mark sticky
      console.warn(
        `Database module not found. Run: cd dashboard-v2 && npm install\n` +
        `Dashboard will run without database access.`
      );
    } else {
      // Unknown error - log but allow retry
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
  // Try two locations:
  // 1. dashboard-v2/bazinga/bazinga.db (when running from dashboard-v2, e.g. tests)
  // 2. ../bazinga/bazinga.db (when running from root bazinga directory)
  const localPath = path.resolve(process.cwd(), "bazinga", "bazinga.db");
  if (existsSync(localPath)) {
    return localPath;
  }
  return path.resolve(process.cwd(), "..", "bazinga", "bazinga.db");
}

function getDatabase(): DatabaseInstance | null {
  if (_moduleLoadFailed) return null;

  // Always recalculate the path (in case database appears after server startup)
  const currentPath = resolveDatabasePath();

  // If we have a cached connection, verify the path is still the same
  if (_sqlite) {
    if (currentPath === _dbPath) {
      return _sqlite;
    }
    // Path changed (e.g., database now exists in a different location)
    // Close old connection and open new one
    try {
      _sqlite.close();
    } catch {
      // Already closed, that's fine
    }
    _sqlite = null;
    _db = null;  // Clear drizzle cache too since underlying database changed
  }

  // First, try to load the modules
  const modules = loadDatabaseModules();
  if (!modules) return null;

  try {
    _dbPath = currentPath;  // Always update _dbPath with current resolution
    // In development/test, allow write access (may be needed for tests seeding data)
    // In production, use read-only mode (set via DATABASE_URL or environment)
    const isReadOnly = process.env.NODE_ENV === "production" && !process.env.DATABASE_URL?.startsWith("file:");
    _sqlite = new modules.Database(_dbPath, { readonly: isReadOnly });
    return _sqlite;
  } catch (error) {
    // If database file doesn't exist, return null (allows build to succeed)
    // The mock proxy will return empty results during build/SSG
    const errorMessage = String(error);
    if (errorMessage.includes("SQLITE_CANTOPEN") ||
        errorMessage.includes("unable to open database") ||
        errorMessage.includes("no such file")) {
      // This is expected during initial server startup before database is created
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
  if (_moduleLoadFailed) return null;

  // If we have a cached drizzle instance, check if underlying database changed
  if (_db && _sqlite) {
    // If getDatabase() returns a different instance, our drizzle is stale
    const currentSqlite = getDatabase();
    if (currentSqlite && currentSqlite === _sqlite) {
      return _db;  // Same database connection, safe to return cached drizzle
    }
    // Database changed (or closed), clear stale drizzle instance
    _db = null;
  }

  const sqlite = getDatabase();
  if (!sqlite) return null;

  // drizzle is already loaded by loadDatabaseModules()
  if (_drizzle) {
    _db = _drizzle(sqlite, { schema });
    return _db;
  }
  return null;
}

// Shape-accurate NOOP for Drizzle query builder chains
// Supports any order of chaining: db.select().from().where().orderBy().limit().offset()
// Returns itself for builder methods, empty results for terminal methods
const createNoopQueryBuilder = (): unknown => {
  const builder: Record<string, unknown> = {};

  // Terminal methods - return empty results
  // Includes promise-like methods (then/catch/finally) for thenable compatibility
  const terminals = {
    all: () => [],
    get: () => undefined,
    execute: () => Promise.resolve([]),
    then: (resolve: (value: unknown[]) => void) => Promise.resolve([]).then(resolve),
    catch: (reject: (reason: unknown) => void) => Promise.resolve([]).catch(reject),
    finally: (cb: () => void) => Promise.resolve([]).finally(cb),
  };

  // Builder methods - return self for continued chaining
  const chainMethods = [
    "from", "where", "orderBy", "groupBy", "having",
    "limit", "offset", "leftJoin", "rightJoin", "innerJoin",
    "fullJoin", "as", "distinct", "for",
  ];

  // Assign terminal methods
  Object.assign(builder, terminals);

  // Assign chain methods (return builder for any arguments)
  for (const method of chainMethods) {
    builder[method] = () => builder;
  }

  return builder;
};

// NOOP query object for db.query.<table>.findMany/findFirst patterns
const NOOP_QUERY = new Proxy({}, {
  get: () => ({
    findMany: () => Promise.resolve([]),
    findFirst: () => Promise.resolve(undefined),
    findUnique: () => Promise.resolve(undefined),
  }),
});

// NOOP DML result for run() calls - matches better-sqlite3 RunResult shape
// Note: Using BigInt(0) instead of 0n for ES target compatibility
const NOOP_RUN_RESULT = { changes: 0, lastInsertRowid: BigInt(0) };

// NOOP Drizzle-like object for when DB is unavailable
// Note: transaction passes NOOP_DRIZZLE as tx so (tx) => tx.select()... works
// DML chains support: returning(), execute(), and run() for complete compatibility
const NOOP_DRIZZLE: Record<string, unknown> = {
  select: () => createNoopQueryBuilder(),
  insert: () => ({
    values: () => ({
      returning: () => [],
      execute: () => Promise.resolve([]),
      run: () => NOOP_RUN_RESULT,
    }),
  }),
  update: () => ({
    set: () => ({
      where: () => ({
        returning: () => [],
        execute: () => Promise.resolve([]),
        run: () => NOOP_RUN_RESULT,
      }),
    }),
  }),
  delete: () => ({
    where: () => ({
      returning: () => [],
      execute: () => Promise.resolve([]),
      run: () => NOOP_RUN_RESULT,
    }),
  }),
  transaction: <T>(fn: (tx: unknown) => T) => fn(NOOP_DRIZZLE),
  query: NOOP_QUERY,
};

// Export lazy-initialized db with mock fallback
export const db = new Proxy({} as BetterSQLite3Database<typeof schema>, {
  get(_, prop) {
    const drizzleDb = getDrizzle();
    if (!drizzleDb) {
      // Return shape-accurate NOOP to prevent crashes during method chaining
      const noopValue = (NOOP_DRIZZLE as Record<string, unknown>)[prop as string];
      if (noopValue !== undefined) {
        return noopValue;
      }
      // Fallback for unknown properties
      return () => Promise.resolve([]);
    }
    return (drizzleDb as unknown as Record<string, unknown>)[prop as string];
  },
});

// Shape-accurate no-ops for sqlite fallback (prevents crashes)
const NOOP_STATEMENT = {
  all: () => [],
  get: () => undefined,
  run: () => ({ changes: 0, lastInsertRowid: BigInt(0) }),
};

const NOOP_SQLITE: DatabaseInstance = {
  prepare: () => NOOP_STATEMENT,
  close: () => {},
  exec: () => {},
  pragma: () => undefined,
  transaction: <A extends unknown[], T>(fn: (...args: A) => T) => (...args: A) => fn(...args),
};

// Export for direct SQL queries if needed (also lazy)
export const sqlite = new Proxy({} as DatabaseInstance, {
  get(_, prop) {
    const db = getDatabase();
    if (!db) {
      // Return shape-accurate no-ops to prevent crashes like [].all()
      return (NOOP_SQLITE as unknown as Record<string, unknown>)[prop as string];
    }
    return (db as unknown as Record<string, unknown>)[prop as string];
  },
});
