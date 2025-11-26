import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";
import path from "path";

// Database path - points to existing bazinga.db
const DB_PATH = process.env.DATABASE_URL || path.join(process.cwd(), "..", "bazinga", "bazinga.db");

// Create database connection
const sqlite = new Database(DB_PATH, { readonly: true });
sqlite.pragma("journal_mode = WAL");

// Create drizzle instance with schema
export const db = drizzle(sqlite, { schema });

// Export for direct SQL queries if needed
export { sqlite };
