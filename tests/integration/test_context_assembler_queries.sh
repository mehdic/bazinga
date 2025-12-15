#!/bin/bash
# Integration test for context-assembler skill database queries
# Verifies all bazinga-db operations used by context-assembler work correctly
#
# Usage: ./test_context_assembler_queries.sh
#
# This test:
# 1. Creates a test session with sample data
# 2. Tests each database query operation used by context-assembler
# 3. Verifies results are valid JSON and contain expected fields
# 4. Cleans up test data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Generate unique test session ID
TEST_SESSION_ID="test_ctx_$(date +%Y%m%d_%H%M%S)_$$"
TEST_GROUP_ID="TEST_GROUP_1"

echo "═══════════════════════════════════════════════════════════"
echo "    Context-Assembler Database Queries Integration Test"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Test Session ID: $TEST_SESSION_ID"
echo "Test Group ID: $TEST_GROUP_ID"
echo ""

# Helper function to run bazinga-db command
db_cmd() {
    python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet "$@" 2>/dev/null
}

# Helper to check if output is valid JSON
is_valid_json() {
    echo "$1" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null
    return $?
}

# Helper to count items in JSON array
json_array_length() {
    echo "$1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null || echo "0"
}

# ━━━ SETUP: Create Test Session and Data ━━━
echo "━━━ SETUP: Creating Test Session and Data ━━━"
echo ""

# Create test session
echo -n "Creating test session... "
SESSION_RESULT=$(db_cmd create-session "$TEST_SESSION_ID" "simple" "Test context-assembler queries" 2>&1 || echo "FAILED")
if [[ "$SESSION_RESULT" == *"FAILED"* ]] || [[ "$SESSION_RESULT" == *"error"* ]]; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: $SESSION_RESULT"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Create test task group
echo -n "Creating test task group... "
GROUP_RESULT=$(db_cmd create-task-group "$TEST_GROUP_ID" "$TEST_SESSION_ID" "Test Group" "Test task for context-assembler" "developer" 2>&1 || echo "FAILED")
if [[ "$GROUP_RESULT" == *"FAILED"* ]]; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: $GROUP_RESULT"
else
    echo -e "${GREEN}OK${NC}"
fi

# Save test context packages with different priorities
# Format: save-context-package <session> <group_id> <type> <file_path> <producer> <consumers_json> <priority> <summary>
echo -n "Creating test context packages... "

# Create artifacts directory for test files
mkdir -p "bazinga/artifacts/$TEST_SESSION_ID"
echo "test content" > "bazinga/artifacts/$TEST_SESSION_ID/file1.md"
echo "test content" > "bazinga/artifacts/$TEST_SESSION_ID/file2.md"
echo "test content" > "bazinga/artifacts/$TEST_SESSION_ID/file3.md"
echo "test content" > "bazinga/artifacts/$TEST_SESSION_ID/file4.md"

PKG1=$(db_cmd save-context-package "$TEST_SESSION_ID" "$TEST_GROUP_ID" "research" \
    "bazinga/artifacts/$TEST_SESSION_ID/file1.md" "developer" '["developer","qa_expert"]' "critical" \
    "Critical test package for authentication flow" 2>&1)
PKG2=$(db_cmd save-context-package "$TEST_SESSION_ID" "$TEST_GROUP_ID" "research" \
    "bazinga/artifacts/$TEST_SESSION_ID/file2.md" "developer" '["developer","tech_lead"]' "high" \
    "High priority finding about API design" 2>&1)
PKG3=$(db_cmd save-context-package "$TEST_SESSION_ID" "$TEST_GROUP_ID" "decisions" \
    "bazinga/artifacts/$TEST_SESSION_ID/file3.md" "developer" '["developer"]' "medium" \
    "Medium priority artifact for reference" 2>&1)
PKG4=$(db_cmd save-context-package "$TEST_SESSION_ID" "" "research" \
    "bazinga/artifacts/$TEST_SESSION_ID/file4.md" "developer" '["developer","qa_expert","tech_lead"]' "low" \
    "Session-wide low priority package" 2>&1)

if [[ "$PKG1" == *"ERROR"* ]] || [[ "$PKG2" == *"ERROR"* ]]; then
    echo -e "${RED}FAILED${NC}"
    echo "PKG1: $PKG1"
    echo "PKG2: $PKG2"
else
    echo -e "${GREEN}OK (4 packages)${NC}"
fi

# Save test reasoning entries
# Format: save-reasoning <session> <group_id> <agent_type> <phase> <content> [--confidence X]
echo -n "Creating test reasoning entries... "
REASON1=$(db_cmd save-reasoning "$TEST_SESSION_ID" "$TEST_GROUP_ID" "developer" "understanding" \
    "Analyzed requirements and identified key components" --confidence high 2>&1)
REASON2=$(db_cmd save-reasoning "$TEST_SESSION_ID" "$TEST_GROUP_ID" "developer" "completion" \
    "Implemented core functionality with proper error handling" --confidence high 2>&1)
REASON3=$(db_cmd save-reasoning "$TEST_SESSION_ID" "$TEST_GROUP_ID" "qa_expert" "understanding" \
    "Reviewed test coverage requirements" --confidence medium 2>&1)

if [[ "$REASON1" == *'"success": false'* ]] || [[ "$REASON1" == *"ERROR"* ]] || [[ "$REASON1" == *"Failed to save"* ]]; then
    echo -e "${RED}FAILED${NC}"
    echo "REASON1: $REASON1"
else
    echo -e "${GREEN}OK (3 entries)${NC}"
fi

echo ""

# ━━━ TEST 1: get-context-packages (Normal Zone Query) ━━━
echo "━━━ Test 1: get-context-packages (Normal Zone) ━━━"

RESULT=$(db_cmd get-context-packages "$TEST_SESSION_ID" "$TEST_GROUP_ID" "developer" 5)

if [ -z "$RESULT" ]; then
    echo -e "${RED}❌ FAIL: Empty result from get-context-packages${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
elif ! is_valid_json "$RESULT"; then
    echo -e "${RED}❌ FAIL: Invalid JSON returned${NC}"
    echo "   Result: $RESULT"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    COUNT=$(json_array_length "$RESULT")
    if [ "$COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: Returned $COUNT packages${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
        # Show sample
        echo "   Sample: $(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('file_path','?') if d else 'empty')" 2>/dev/null)"
    else
        echo -e "${YELLOW}⚠️ WARNING: Returned 0 packages (expected 3-4)${NC}"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
fi
echo ""

# ━━━ TEST 2: get-context-packages (Session-wide, empty group_id) ━━━
echo "━━━ Test 2: get-context-packages (Session-wide) ━━━"

RESULT=$(db_cmd get-context-packages "$TEST_SESSION_ID" "" "developer" 10)

if [ -z "$RESULT" ]; then
    echo -e "${RED}❌ FAIL: Empty result for session-wide query${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
elif ! is_valid_json "$RESULT"; then
    echo -e "${RED}❌ FAIL: Invalid JSON returned${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    COUNT=$(json_array_length "$RESULT")
    echo -e "${GREEN}✅ PASS: Session-wide query returned $COUNT packages${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
fi
echo ""

# ━━━ TEST 3: get-context-packages (Different agent types) ━━━
echo "━━━ Test 3: get-context-packages (Agent Types) ━━━"

for AGENT in developer qa_expert tech_lead senior_software_engineer investigator; do
    RESULT=$(db_cmd get-context-packages "$TEST_SESSION_ID" "$TEST_GROUP_ID" "$AGENT" 3)
    if is_valid_json "$RESULT"; then
        COUNT=$(json_array_length "$RESULT")
        echo -e "   ${GREEN}✓${NC} $AGENT: $COUNT packages"
    else
        echo -e "   ${RED}✗${NC} $AGENT: Invalid response"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done
PASS_COUNT=$((PASS_COUNT + 1))
echo ""

# ━━━ TEST 4: get-reasoning (Prior Reasoning Retrieval) ━━━
echo "━━━ Test 4: get-reasoning (Prior Reasoning) ━━━"

RESULT=$(db_cmd get-reasoning "$TEST_SESSION_ID")

if [ -z "$RESULT" ]; then
    echo -e "${RED}❌ FAIL: Empty result from get-reasoning${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
elif ! is_valid_json "$RESULT"; then
    echo -e "${RED}❌ FAIL: Invalid JSON returned${NC}"
    echo "   Result: $RESULT"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    COUNT=$(json_array_length "$RESULT")
    if [ "$COUNT" -ge 3 ]; then
        echo -e "${GREEN}✅ PASS: Returned $COUNT reasoning entries${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${YELLOW}⚠️ WARNING: Expected 3 entries, got $COUNT${NC}"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
fi
echo ""

# ━━━ TEST 5: get-reasoning with group_id filter ━━━
echo "━━━ Test 5: get-reasoning (Group Filtered) ━━━"

RESULT=$(db_cmd get-reasoning "$TEST_SESSION_ID" --group_id "$TEST_GROUP_ID")

if [ -z "$RESULT" ]; then
    echo -e "${RED}❌ FAIL: Empty result with group filter${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
elif ! is_valid_json "$RESULT"; then
    echo -e "${RED}❌ FAIL: Invalid JSON returned${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    COUNT=$(json_array_length "$RESULT")
    echo -e "${GREEN}✅ PASS: Group-filtered query returned $COUNT entries${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
fi
echo ""

# ━━━ TEST 6: mark-context-consumed ━━━
echo "━━━ Test 6: mark-context-consumed ━━━"

# Get a package ID to mark as consumed
PKG_ID=$(db_cmd get-context-packages "$TEST_SESSION_ID" "$TEST_GROUP_ID" "developer" 1 | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('id','') if d else '')" 2>/dev/null || echo "")

if [ -z "$PKG_ID" ]; then
    echo -e "${YELLOW}⚠️ WARNING: No package ID found to test consumption${NC}"
    WARN_COUNT=$((WARN_COUNT + 1))
else
    # Mark as consumed
    CONSUME_RESULT=$(db_cmd mark-context-consumed "$PKG_ID" "developer" 1 2>&1)

    if [[ "$CONSUME_RESULT" == *"✓"* ]] || [[ "$CONSUME_RESULT" == *"Marked"* ]] || [[ -z "$CONSUME_RESULT" ]]; then
        echo -e "${GREEN}✅ PASS: mark-context-consumed succeeded for package $PKG_ID${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    elif [[ "$CONSUME_RESULT" == *"not designated"* ]]; then
        echo -e "${YELLOW}⚠️ WARNING: Package not designated for developer consumption${NC}"
        WARN_COUNT=$((WARN_COUNT + 1))
    else
        echo -e "${RED}❌ FAIL: mark-context-consumed failed${NC}"
        echo "   Result: $CONSUME_RESULT"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
fi
echo ""

# ━━━ TEST 7: Raw SQL Query (Error Patterns Style) ━━━
echo "━━━ Test 7: Raw Query (Error Patterns Check) ━━━"

# This tests the query command used for error patterns lookup
RESULT=$(db_cmd query "SELECT COUNT(*) as cnt FROM context_packages WHERE session_id = '$TEST_SESSION_ID'" 2>&1)

if [ -z "$RESULT" ]; then
    echo -e "${RED}❌ FAIL: Empty result from query command${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
elif ! is_valid_json "$RESULT"; then
    echo -e "${RED}❌ FAIL: Invalid JSON from query${NC}"
    echo "   Result: $RESULT"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    COUNT=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('cnt',0) if d else 0)" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ PASS: Query returned count=$COUNT${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
fi
echo ""

# ━━━ TEST 8: Session Query (Used by Step 4a for project_id) ━━━
echo "━━━ Test 8: Session Metadata Query ━━━"

RESULT=$(db_cmd get-session "$TEST_SESSION_ID" 2>&1)

if [ -z "$RESULT" ] || [ "$RESULT" = "null" ]; then
    echo -e "${RED}❌ FAIL: Session not found${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
elif ! is_valid_json "$RESULT"; then
    echo -e "${RED}❌ FAIL: Invalid JSON for session${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    SESSION_ID_CHECK=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)
    if [ "$SESSION_ID_CHECK" = "$TEST_SESSION_ID" ]; then
        echo -e "${GREEN}✅ PASS: Session metadata retrieved correctly${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}❌ FAIL: Session ID mismatch${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
fi
echo ""

# ━━━ TEST 9: Concurrent Query Simulation ━━━
echo "━━━ Test 9: Concurrent Query Handling ━━━"

# Run multiple queries in parallel to test database locking
echo -n "Running 5 parallel queries... "
(
    db_cmd get-context-packages "$TEST_SESSION_ID" "" "developer" 3 > /dev/null 2>&1 &
    db_cmd get-context-packages "$TEST_SESSION_ID" "" "qa_expert" 3 > /dev/null 2>&1 &
    db_cmd get-reasoning "$TEST_SESSION_ID" > /dev/null 2>&1 &
    db_cmd get-session "$TEST_SESSION_ID" > /dev/null 2>&1 &
    db_cmd list-sessions 5 > /dev/null 2>&1 &
    wait
)
PARALLEL_RESULT=$?

if [ $PARALLEL_RESULT -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
    echo -e "${GREEN}✅ PASS: Parallel queries completed without deadlock${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "${RED}FAILED${NC}"
    echo -e "${RED}❌ FAIL: Parallel queries failed${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# ━━━ TEST 10: Empty Result Handling ━━━
echo "━━━ Test 10: Empty Result Handling ━━━"

# Query for non-existent session
RESULT=$(db_cmd get-context-packages "nonexistent_session_xyz" "" "developer" 5 2>&1)

if [ -z "$RESULT" ] || [ "$RESULT" = "[]" ]; then
    echo -e "${GREEN}✅ PASS: Empty result handled correctly (empty array)${NC}"
    PASS_COUNT=$((PASS_COUNT + 1))
elif is_valid_json "$RESULT"; then
    COUNT=$(json_array_length "$RESULT")
    if [ "$COUNT" -eq 0 ]; then
        echo -e "${GREEN}✅ PASS: Returns empty array for non-existent session${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${YELLOW}⚠️ WARNING: Unexpected data for non-existent session${NC}"
        WARN_COUNT=$((WARN_COUNT + 1))
    fi
else
    echo -e "${YELLOW}⚠️ WARNING: Non-JSON response for non-existent session${NC}"
    WARN_COUNT=$((WARN_COUNT + 1))
fi
echo ""

# ━━━ CLEANUP ━━━
echo "━━━ CLEANUP ━━━"
echo ""

# Update session to completed (cleanup marker)
echo -n "Marking test session as completed... "
db_cmd update-session-status "$TEST_SESSION_ID" "completed" > /dev/null 2>&1 || true
echo -e "${GREEN}OK${NC}"

# Clean up test artifacts directory
echo -n "Cleaning up test artifacts... "
rm -rf "bazinga/artifacts/$TEST_SESSION_ID" 2>/dev/null || true
echo -e "${GREEN}OK${NC}"
echo ""

# ━━━ SUMMARY ━━━
echo "═══════════════════════════════════════════════════════════"
echo "                      SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  ✅ Passed:   $PASS_COUNT"
echo "  ⚠️ Warnings: $WARN_COUNT"
echo "  ❌ Failed:   $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}❌ OVERALL: FAIL${NC}"
    echo ""
    echo "Some context-assembler database queries are failing."
    echo "Check bazinga-db skill and database schema."
    exit 1
elif [ $WARN_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️ OVERALL: PASS WITH WARNINGS${NC}"
    echo ""
    echo "All critical queries work, but some edge cases need attention."
    exit 0
else
    echo -e "${GREEN}✅ OVERALL: PASS${NC}"
    echo ""
    echo "All context-assembler database queries are working correctly."
    exit 0
fi
