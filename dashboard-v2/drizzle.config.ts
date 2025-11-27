import type { Config } from "drizzle-kit";
import path from "path";

// Resolve database path - uses environment variable or resolves relative path
// Using process.cwd() for ESM compatibility (__dirname is not available in ESM)
const dbPath = process.env.DATABASE_URL ||
  path.resolve(process.cwd(), "..", "bazinga", "bazinga.db");

export default {
  schema: "./src/lib/db/schema.ts",
  out: "./drizzle",
  dialect: "sqlite",
  dbCredentials: {
    url: dbPath,
  },
} satisfies Config;
