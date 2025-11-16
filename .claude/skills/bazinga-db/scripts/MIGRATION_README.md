# Agent Type Migration Script

## Problem

The BAZINGA database had an inconsistency between the database CHECK constraint and the Python code validation for `agent_type` values.

### Symptoms

You may see these errors when trying to log tech lead or QA interactions:

```
Error: Failed to log techlead interaction: CHECK constraint failed:
agent_type IN ('pm', 'developer', 'qa', 'tech_lead', 'orchestrator')
```

Or when trying alternative naming:

```
Error: Invalid agent_type: tech_lead
```

### Root Cause

**Old database schema** used:
- `'qa'` for QA Expert
- `'tech_lead'` for Tech Lead

**Current codebase** uses (correct):
- `'qa_expert'` for QA Expert
- `'techlead'` for Tech Lead

This mismatch means:
1. The orchestrator tries to log with `'techlead'` → database rejects it (expects `'tech_lead'`)
2. You try `'tech_lead'` → Python validation rejects it (expects `'techlead'`)

## Solution

Run the migration script to align your database with the codebase:

```bash
python3 migrate_agent_types.py /path/to/bazinga.db
```

### What it does

1. **Updates existing data:**
   - Changes all `'qa'` → `'qa_expert'` in `orchestration_logs`
   - Changes all `'tech_lead'` → `'techlead'` in `orchestration_logs`
   - Updates `token_usage` table similarly

2. **Updates schema:**
   - Recreates `orchestration_logs` table with correct CHECK constraint
   - New constraint: `('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator')`

3. **Preserves data:**
   - All existing logs are copied to the new table
   - All indexes are recreated
   - No data loss

### Example Output

```
Migrating database: /home/user/bazinga/bazinga/bazinga.db

Step 1: Migrating existing data in orchestration_logs...
  - Updated 12 'qa' → 'qa_expert' records
  - Updated 8 'tech_lead' → 'techlead' records

Step 2: Recreating table with correct CHECK constraint...
  - Created new table with correct CHECK constraint
  - Copied 145 records to new table
  - Dropped old table
  - Renamed new table to orchestration_logs

Step 3: Recreating indexes...
  - Recreated indexes

Step 4: Checking token_usage table...
  - Updated 5 'qa' → 'qa_expert' in token_usage
  - Updated 3 'tech_lead' → 'techlead' in token_usage

✅ Migration completed successfully!

Summary:
  - orchestration_logs: 20 records updated
  - token_usage: 8 records updated
  - CHECK constraint updated to: ('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator')

============================================================
Verification
============================================================
✅ CHECK constraint is correct
✅ No old agent_type values found

Current agent_type distribution:
  - pm: 45 records
  - developer: 67 records
  - qa_expert: 12 records
  - techlead: 8 records
  - orchestrator: 13 records

============================================================
Migration complete! Database is now consistent with codebase.
============================================================
```

## Verification

After migration, these commands should work:

```bash
# Log tech lead interaction (should succeed)
python3 bazinga_db.py --db /path/to/bazinga.db log-interaction \
  "session_123" \
  "techlead" \
  "Code review complete. All checks passed." \
  1 \
  "techlead_main"

# Log QA interaction (should succeed)
python3 bazinga_db.py --db /path/to/bazinga.db log-interaction \
  "session_123" \
  "qa_expert" \
  "All tests passed. No regressions found." \
  1 \
  "qa_main"
```

## Backup (Optional but Recommended)

Before running the migration, you can backup your database:

```bash
cp /path/to/bazinga.db /path/to/bazinga.db.backup
```

To restore if needed:

```bash
cp /path/to/bazinga.db.backup /path/to/bazinga.db
```

## Agent Type Reference

The correct agent types to use in all BAZINGA operations:

| Agent | Correct Type | ❌ Don't Use |
|-------|--------------|-------------|
| **Project Manager** | `pm` | - |
| **Developer** | `developer` | `dev` |
| **QA Expert** | `qa_expert` | `qa`, `qa_engineer` |
| **Tech Lead** | `techlead` | `tech_lead`, `tl` |
| **Orchestrator** | `orchestrator` | `orch` |

## When to Run This Migration

Run this migration if:
- ✅ You see CHECK constraint errors mentioning `'tech_lead'` or `'qa'`
- ✅ You have an existing database from before January 2025
- ✅ Your database was created with an older schema

You don't need to run this if:
- ❌ You just initialized a new database with `init_db.py` (already correct)
- ❌ You don't have any existing data in your database

## Safe to Run Multiple Times?

Yes! The script is idempotent. If you run it multiple times:
- Records already using `'qa_expert'` won't change
- Records already using `'techlead'` won't change
- The CHECK constraint will be recreated (no harm)

## Questions?

See the main [INTEGRATION_GUIDE.md](../INTEGRATION_GUIDE.md) for more details on database operations.
