import type { Config } from "drizzle-kit";
import path from "path";

// Resolve database path - uses environment variable or resolves relative path
// Using process.cwd() for ESM compatibility (__dirname is not available in ESM)
const dbPath = process.env.DATABASE_URL ||
  path.resolve(process.cwd(), "..", "bazinga", "bazinga.db");

// Normalize path for drizzle-kit (requires file: prefix for SQLite)
const normalizedUrl = dbPath.startsWith("file:") ? dbPath : `file:${dbPath}`;

export default {
  schema: "./src/lib/db/schema.ts",
  out: "./drizzle",
  dialect: "sqlite",
  dbCredentials: {
    url: normalizedUrl,
  },
} satisfies Config;
