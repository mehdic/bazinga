/**
 * Schema Capability Detection
 *
 * Detects which schema features are available in the connected database.
 * Enables graceful degradation when connecting to older databases.
 *
 * CRITICAL: Uses raw `sqlite` connection (better-sqlite3), NOT Drizzle `db`.
 * Drizzle doesn't have db.all() - that's a better-sqlite3 method.
 *
 * See: research/dashboard-schema-fixes-ultrathink.md
 */

import { sqlite } from "./client";
import type { SchemaCapabilities } from "@/types";

// Cache capabilities to avoid repeated probes
let cachedCapabilities: SchemaCapabilities | null = null;

/**
 * Validate identifier to prevent SQL injection
 * Only allows alphanumeric and underscore, must start with letter/underscore
 */
function isValidIdentifier(name: string): boolean {
  return /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name);
}

/**
 * Probe if a table exists in the database
 * Uses raw sqlite.prepare().all() - NOT Drizzle
 */
function probeTable(tableName: string): boolean {
  if (!isValidIdentifier(tableName)) {
    return false;
  }
  try {
    const stmt = sqlite.prepare(
      `SELECT name FROM sqlite_master WHERE type='table' AND name=?`
    );
    const result = stmt.all(tableName) as { name: string }[];
    return result.length > 0;
  } catch {
    return false;
  }
}

/**
 * Probe if a column exists in a table
 * Uses sqlite.pragma() for PRAGMA queries - safer than raw SQL
 */
function probeColumn(tableName: string, columnName: string): boolean {
  if (!isValidIdentifier(tableName) || !isValidIdentifier(columnName)) {
    return false;
  }
  try {
    // sqlite.pragma() is the proper way to execute PRAGMA in better-sqlite3
    // NOTE: NOOP_SQLITE.pragma() returns undefined, so we must handle that case
    const columns = sqlite.pragma(`table_info(${tableName})`) as { name: string }[] | undefined;
    if (!columns || !Array.isArray(columns)) {
      return false;
    }
    return columns.some((col) => col.name === columnName);
  } catch {
    return false;
  }
}

/**
 * Get the current schema version from the database
 * Uses raw sqlite.prepare().all() - NOT Drizzle
 */
function getSchemaVersion(): number {
  try {
    const stmt = sqlite.prepare(
      `SELECT version FROM schema_version ORDER BY version DESC LIMIT 1`
    );
    const result = stmt.all() as { version: number }[];
    return result.length > 0 ? result[0].version : 0;
  } catch {
    // Table doesn't exist or other error
    return 0;
  }
}

/**
 * Detect all schema capabilities
 * NOTE: All probes are synchronous (better-sqlite3 is sync)
 */
export function detectCapabilities(): SchemaCapabilities {
  // Return cached if available
  if (cachedCapabilities) {
    return cachedCapabilities;
  }

  // Run all probes (synchronous with better-sqlite3)
  const schemaVersion = getSchemaVersion();
  const hasReasoningColumns = probeColumn("orchestration_logs", "log_type");
  const hasEventColumns = probeColumn("orchestration_logs", "event_subtype");
  const hasSuccessCriteria = probeTable("success_criteria");
  const hasContextPackages = probeTable("context_packages");
  const hasTaskGroupExtensions = probeColumn("task_groups", "specializations");
  const hasSkillOutputExtensions = probeColumn("skill_outputs", "agent_type");
  const hasErrorPatterns = probeTable("error_patterns");
  const hasDevelopmentPlans = probeTable("development_plans");

  cachedCapabilities = {
    schemaVersion,
    hasReasoningColumns,
    hasEventColumns,
    hasSuccessCriteria,
    hasContextPackages,
    hasTaskGroupExtensions,
    hasSkillOutputExtensions,
    hasContextEngineering: hasErrorPatterns,
    hasDevelopmentPlans,
  };

  return cachedCapabilities;
}

/**
 * Clear the capability cache (useful for testing or after schema migrations)
 */
export function clearCapabilityCache(): void {
  cachedCapabilities = null;
}

/**
 * Get cached capabilities (returns null if not yet detected)
 */
export function getCachedCapabilities(): SchemaCapabilities | null {
  return cachedCapabilities;
}
