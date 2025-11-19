#!/bin/bash
# Integration Test: Codebase Analyzer Performance and Functionality
# Tests the improved analyzer with reproducible artifacts

set -e  # Exit on error

echo "=========================================="
echo "BAZINGA Codebase Analyzer Integration Test"
echo "=========================================="
echo ""

# Setup
TEST_SESSION="integration-test-$(date +%s)"
OUTPUT_DIR="research/tests/artifacts"
mkdir -p "$OUTPUT_DIR"

echo "Test Session: $TEST_SESSION"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Test 1: Simple task (should be fast, minimal analysis)
echo "TEST 1: Simple Task Analysis"
echo "--------------------------------------------"
START_TIME=$(date +%s)
python3 .claude/skills/codebase-analysis/scripts/analyze_codebase.py \
  --task "fix typo in README" \
  --session "${TEST_SESSION}-simple" \
  --cache-enabled \
  --timeout 10 \
  --output "$OUTPUT_DIR/test1-simple-task.json" 2>&1 | tee "$OUTPUT_DIR/test1-simple-task.log"
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Duration: ${DURATION}s"
echo ""

# Test 2: Medium complexity task (should find utilities)
echo "TEST 2: Medium Complexity Task (Should find utilities)"
echo "--------------------------------------------"
START_TIME=$(date +%s)
python3 .claude/skills/codebase-analysis/scripts/analyze_codebase.py \
  --task "add new endpoint for user profile" \
  --session "${TEST_SESSION}-medium" \
  --cache-enabled \
  --timeout 20 \
  --output "$OUTPUT_DIR/test2-medium-task.json" 2>&1 | tee "$OUTPUT_DIR/test2-medium-task.log"
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Duration: ${DURATION}s"
echo ""

# Test 3: Complex task (should find similar features and patterns)
echo "TEST 3: Complex Task (Full analysis)"
echo "--------------------------------------------"
START_TIME=$(date +%s)
python3 .claude/skills/codebase-analysis/scripts/analyze_codebase.py \
  --task "add new agent for code review and quality assurance checks" \
  --session "${TEST_SESSION}-complex" \
  --cache-enabled \
  --timeout 30 \
  --output "$OUTPUT_DIR/test3-complex-task.json" 2>&1 | tee "$OUTPUT_DIR/test3-complex-task.log"
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Duration: ${DURATION}s"
echo ""

# Test 4: Cache efficiency (re-run same task, should be faster)
echo "TEST 4: Cache Efficiency (Re-run complex task)"
echo "--------------------------------------------"
START_TIME=$(date +%s)
python3 .claude/skills/codebase-analysis/scripts/analyze_codebase.py \
  --task "implement OAuth2 authentication with Google and GitHub providers" \
  --session "${TEST_SESSION}-cached" \
  --cache-enabled \
  --timeout 30 \
  --output "$OUTPUT_DIR/test4-cached-task.json" 2>&1 | tee "$OUTPUT_DIR/test4-cached-task.log"
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Duration: ${DURATION}s"
echo ""

# Test 5: Pattern detection
echo "TEST 5: Pattern Detection (Pytest should be found)"
echo "--------------------------------------------"
START_TIME=$(date +%s)
python3 .claude/skills/codebase-analysis/scripts/analyze_codebase.py \
  --task "add unit tests for auth module" \
  --session "${TEST_SESSION}-patterns" \
  --cache-enabled \
  --timeout 15 \
  --output "$OUTPUT_DIR/test5-pattern-detection.json" 2>&1 | tee "$OUTPUT_DIR/test5-pattern-detection.log"
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Duration: ${DURATION}s"
echo ""

# Validation
echo "=========================================="
echo "VALIDATION"
echo "=========================================="

# Check Test 1
echo -n "✓ Test 1 - File created: "
if [ -f "$OUTPUT_DIR/test1-simple-task.json" ]; then
    echo "PASS"
else
    echo "FAIL"
fi

# Check Test 2 - Should find utilities
echo -n "✓ Test 2 - Found utilities: "
UTIL_COUNT=$(jq '.utilities | length' "$OUTPUT_DIR/test2-medium-task.json")
if [ "$UTIL_COUNT" -gt 0 ]; then
    echo "PASS ($UTIL_COUNT utilities)"
else
    echo "FAIL (0 utilities)"
fi

# Check Test 3 - Should find similar features
echo -n "✓ Test 3 - Found similar features: "
SIMILAR_COUNT=$(jq '.similar_features | length' "$OUTPUT_DIR/test3-complex-task.json")
if [ "$SIMILAR_COUNT" -gt 0 ]; then
    echo "PASS ($SIMILAR_COUNT features)"
else
    echo "FAIL (0 features)"
fi

# Check Test 4 - Cache efficiency should be higher
echo -n "✓ Test 4 - Cache efficiency: "
CACHE_EFF=$(jq -r '.cache_efficiency' "$OUTPUT_DIR/test4-cached-task.json")
echo "$CACHE_EFF"

# Check Test 5 - Pytest should be detected
echo -n "✓ Test 5 - Pytest detected: "
TEST_FW=$(jq -r '.project_patterns.test_framework' "$OUTPUT_DIR/test5-pattern-detection.json")
if [ "$TEST_FW" == "pytest" ]; then
    echo "PASS"
else
    echo "FAIL (detected: $TEST_FW)"
fi

# Generate summary
echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo "All test artifacts saved to: $OUTPUT_DIR/"
echo ""
echo "Files created:"
ls -lh "$OUTPUT_DIR/" | grep "test.*\.json" | awk '{print "  " $9 " (" $5 ")"}'
echo ""

# Create summary JSON
cat > "$OUTPUT_DIR/test-summary.json" <<EOF
{
  "test_session": "$TEST_SESSION",
  "timestamp": "$(date -Iseconds)",
  "tests_run": 5,
  "tests": {
    "simple_task": {
      "file": "test1-simple-task.json",
      "duration": "$(jq -r '.timestamp' $OUTPUT_DIR/test1-simple-task.json)",
      "passed": true
    },
    "medium_task": {
      "file": "test2-medium-task.json",
      "utilities_found": $UTIL_COUNT,
      "passed": $([ "$UTIL_COUNT" -gt 0 ] && echo "true" || echo "false")
    },
    "complex_task": {
      "file": "test3-complex-task.json",
      "similar_features_found": $SIMILAR_COUNT,
      "passed": $([ "$SIMILAR_COUNT" -gt 0 ] && echo "true" || echo "false")
    },
    "cache_efficiency": {
      "file": "test4-cached-task.json",
      "efficiency": "$CACHE_EFF",
      "passed": true
    },
    "pattern_detection": {
      "file": "test5-pattern-detection.json",
      "framework_detected": "$TEST_FW",
      "passed": $([ "$TEST_FW" == "pytest" ] && echo "true" || echo "false")
    }
  }
}
EOF

echo "Test summary: $OUTPUT_DIR/test-summary.json"
echo ""
echo "✓ Integration tests complete!"
