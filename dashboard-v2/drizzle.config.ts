import type { Config } from "drizzle-kit";
import path from "path";

// Resolve database path - uses environment variable or resolves relative path
const dbPath = process.env.DATABASE_URL ||
  path.resolve(__dirname, "..", "bazinga", "bazinga.db");

export default {
  schema: "./src/lib/db/schema.ts",
  out: "./drizzle",
  dialect: "sqlite",
  dbCredentials: {
    url: dbPath,
  },
} satisfies Config;
