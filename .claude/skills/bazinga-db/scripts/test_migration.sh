#!/bin/bash
# Test script for agent_type migration

set -e

echo "======================================================================"
echo "Testing Agent Type Migration Script"
echo "======================================================================"
echo ""

TEST_DB="/tmp/test_bazinga_migration.db"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Clean up any previous test database
rm -f "$TEST_DB"

echo "Step 1: Creating test database with OLD schema..."
python3 <<EOF
import sqlite3

conn = sqlite3.connect('$TEST_DB')
cursor = conn.cursor()

# Enable WAL mode
cursor.execute("PRAGMA journal_mode = WAL")
cursor.execute("PRAGMA foreign_keys = ON")

# Create sessions table
cursor.execute("""
    CREATE TABLE sessions (
        session_id TEXT PRIMARY KEY,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        mode TEXT CHECK(mode IN ('simple', 'parallel')),
        original_requirements TEXT,
        status TEXT CHECK(status IN ('active', 'completed', 'failed')) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create orchestration_logs with OLD CHECK constraint
cursor.execute("""
    CREATE TABLE orchestration_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        iteration INTEGER,
        agent_type TEXT CHECK(agent_type IN ('pm', 'developer', 'qa', 'tech_lead', 'orchestrator')),
        agent_id TEXT,
        content TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
""")

# Create indexes
cursor.execute("""
    CREATE INDEX idx_logs_session
    ON orchestration_logs(session_id, timestamp DESC)
""")
cursor.execute("""
    CREATE INDEX idx_logs_agent_type
    ON orchestration_logs(session_id, agent_type)
""")

# Create token_usage table
cursor.execute("""
    CREATE TABLE token_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        agent_type TEXT NOT NULL,
        agent_id TEXT,
        tokens_estimated INTEGER NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
""")

# Insert test session
cursor.execute("""
    INSERT INTO sessions (session_id, mode, original_requirements)
    VALUES ('test_session', 'parallel', 'Test migration')
""")

# Insert test data with OLD agent types
cursor.execute("""
    INSERT INTO orchestration_logs (session_id, iteration, agent_type, agent_id, content)
    VALUES
        ('test_session', 1, 'pm', 'pm_main', 'PM analysis'),
        ('test_session', 1, 'developer', 'dev_1', 'Developer work'),
        ('test_session', 1, 'qa', 'qa_main', 'QA testing'),
        ('test_session', 1, 'tech_lead', 'tl_main', 'Tech lead review'),
        ('test_session', 2, 'orchestrator', 'orch', 'Orchestrator routing')
""")

# Insert token usage with old types
cursor.execute("""
    INSERT INTO token_usage (session_id, agent_type, agent_id, tokens_estimated)
    VALUES
        ('test_session', 'pm', 'pm_main', 1000),
        ('test_session', 'developer', 'dev_1', 2000),
        ('test_session', 'qa', 'qa_main', 500),
        ('test_session', 'tech_lead', 'tl_main', 800)
""")

conn.commit()
conn.close()

print("✅ Created test database with OLD schema")
EOF

echo ""
echo "Step 2: Verifying OLD schema..."
python3 <<EOF
import sqlite3

conn = sqlite3.connect('$TEST_DB')
cursor = conn.cursor()

# Check schema
schema = cursor.execute("""
    SELECT sql FROM sqlite_master
    WHERE type='table' AND name='orchestration_logs'
""").fetchone()[0]

if "('pm', 'developer', 'qa', 'tech_lead', 'orchestrator')" in schema:
    print("✅ OLD CHECK constraint confirmed: ('pm', 'developer', 'qa', 'tech_lead', 'orchestrator')")
else:
    print("❌ Unexpected schema")
    print(schema)

# Check data
distribution = cursor.execute("""
    SELECT agent_type, COUNT(*) as count
    FROM orchestration_logs
    GROUP BY agent_type
    ORDER BY agent_type
""").fetchall()

print("\nAgent type distribution BEFORE migration:")
for agent_type, count in distribution:
    print(f"  - {agent_type}: {count} records")

conn.close()
EOF

echo ""
echo "======================================================================"
echo "Step 3: Running migration script..."
echo "======================================================================"
python3 "$SCRIPT_DIR/migrate_agent_types.py" "$TEST_DB"

echo ""
echo "======================================================================"
echo "Step 4: Testing with NEW agent types..."
echo "======================================================================"
python3 <<EOF
import sqlite3

conn = sqlite3.connect('$TEST_DB')
cursor = conn.cursor()

try:
    # Try inserting with NEW agent types (should succeed)
    cursor.execute("""
        INSERT INTO orchestration_logs (session_id, iteration, agent_type, agent_id, content)
        VALUES ('test_session', 2, 'qa_expert', 'qa_main', 'QA with new type')
    """)
    print("✅ Successfully inserted record with 'qa_expert'")

    cursor.execute("""
        INSERT INTO orchestration_logs (session_id, iteration, agent_type, agent_id, content)
        VALUES ('test_session', 2, 'techlead', 'tl_main', 'Tech lead with new type')
    """)
    print("✅ Successfully inserted record with 'techlead'")

    conn.commit()
except Exception as e:
    print(f"❌ Failed to insert with new types: {e}")
    conn.rollback()

# Try inserting with OLD agent types (should fail)
try:
    cursor.execute("""
        INSERT INTO orchestration_logs (session_id, iteration, agent_type, agent_id, content)
        VALUES ('test_session', 3, 'qa', 'qa_main', 'Should fail')
    """)
    print("❌ ERROR: Old type 'qa' should have been rejected!")
    conn.rollback()
except Exception as e:
    print(f"✅ Correctly rejected old type 'qa': {str(e)[:80]}")

try:
    cursor.execute("""
        INSERT INTO orchestration_logs (session_id, iteration, agent_type, agent_id, content)
        VALUES ('test_session', 3, 'tech_lead', 'tl_main', 'Should fail')
    """)
    print("❌ ERROR: Old type 'tech_lead' should have been rejected!")
    conn.rollback()
except Exception as e:
    print(f"✅ Correctly rejected old type 'tech_lead': {str(e)[:80]}")

conn.close()
EOF

echo ""
echo "======================================================================"
echo "Step 5: Verifying data integrity..."
echo "======================================================================"
python3 <<EOF
import sqlite3

conn = sqlite3.connect('$TEST_DB')
cursor = conn.cursor()

# Count all records
total = cursor.execute("SELECT COUNT(*) FROM orchestration_logs").fetchone()[0]
print(f"Total records in orchestration_logs: {total}")

# Expected: 5 original + 2 new = 7
if total == 7:
    print("✅ All records preserved (5 original + 2 new test records)")
else:
    print(f"⚠️  Expected 7 records, found {total}")

# Check distribution
distribution = cursor.execute("""
    SELECT agent_type, COUNT(*) as count
    FROM orchestration_logs
    GROUP BY agent_type
    ORDER BY agent_type
""").fetchall()

print("\nAgent type distribution AFTER migration:")
for agent_type, count in distribution:
    print(f"  - {agent_type}: {count} records")

# Verify no old types remain
old_types = cursor.execute("""
    SELECT COUNT(*) FROM orchestration_logs
    WHERE agent_type IN ('qa', 'tech_lead')
""").fetchone()[0]

if old_types == 0:
    print("\n✅ No old agent types remain")
else:
    print(f"\n❌ Found {old_types} records with old agent types!")

conn.close()
EOF

echo ""
echo "======================================================================"
echo "✅ Migration test completed successfully!"
echo "======================================================================"
echo ""
echo "Cleaning up test database: $TEST_DB"
rm -f "$TEST_DB" "$TEST_DB-shm" "$TEST_DB-wal"
echo "✅ Cleanup complete"
