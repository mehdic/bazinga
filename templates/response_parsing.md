# Agent Response Parsing for Capsule Construction

**Purpose:** Extract structured information from agent responses to construct compact capsules.

**Principle:** Best-effort parsing. If specific information is missing, use general descriptions. Never fail because data isn't in expected format.

---

## 🆕 CRP JSON Format (Primary)

**With Compact Return Protocol (CRP), all agents return a standardized JSON response:**

```json
{
  "status": "READY_FOR_QA",
  "summary": [
    "Implemented calculator module with 4 operations",
    "Created calculator.py, added 12 unit tests",
    "All tests passing, ready for QA review"
  ]
}
```

**Parsing CRP responses:**

1. **Parse JSON** - Response is pure JSON (no markdown wrapper)
2. **Extract status** - Direct field access: `response["status"]`
3. **Extract summary** - Array of 3 lines: `response["summary"]`
4. **Construct capsule** - Combine status + summary lines

**CRP Capsule Template:**

```
{emoji} Group {id} | {summary[0]} | {status} → {next_action}
```

**Example:**

```
🔨 Group A | Implemented calculator module with 4 operations | READY_FOR_QA → QA review
```

**Where to get full details:** Read the handoff file at `bazinga/artifacts/{session}/{group}/handoff_{agent}.json`

**The handoff file contains all details** (files changed, test counts, coverage, etc.) while the JSON response keeps orchestrator context minimal.

### CRP Status Codes by Agent

| Agent | Status Codes |
|-------|-------------|
| Developer | `READY_FOR_QA`, `READY_FOR_REVIEW`, `BLOCKED`, `PARTIAL`, `ESCALATE_SENIOR`, `NEEDS_TECH_LEAD_VALIDATION` |
| SSE | `READY_FOR_QA`, `READY_FOR_REVIEW`, `BLOCKED`, `PARTIAL`, `ROOT_CAUSE_FOUND`, `NEEDS_TECH_LEAD_VALIDATION` |
| QA Expert | `PASS`, `FAIL`, `FAIL_ESCALATE`, `BLOCKED`, `FLAKY`, `PARTIAL` |
| Tech Lead | `APPROVED`, `CHANGES_REQUESTED`, `SPAWN_INVESTIGATOR`, `UNBLOCKING_GUIDANCE`, `ESCALATE_TO_OPUS`, `ARCHITECTURAL_DECISION_MADE` |
| PM | `PLANNING_COMPLETE`, `CONTINUE`, `BAZINGA`, `INVESTIGATION_NEEDED`, `NEEDS_CLARIFICATION`, `INVESTIGATION_ONLY` |
| Investigator | `ROOT_CAUSE_FOUND`, `INVESTIGATION_INCOMPLETE`, `BLOCKED`, `EXHAUSTED`, `NEED_DEVELOPER_DIAGNOSTIC`, `HYPOTHESIS_ELIMINATED`, `NEED_MORE_ANALYSIS` |
| Requirements Engineer | `READY_FOR_REVIEW`, `BLOCKED`, `PARTIAL` |

### CRP Emoji Map

| Status Category | Emoji |
|-----------------|-------|
| Development complete | 🔨 |
| Tests passing | ✅ |
| Tests failing | ⚠️ |
| Approved | ✅ |
| Changes requested | ⚠️ |
| Blocked/Escalation | 🔬 |
| Planning | 📋 |
| BAZINGA | 🎉 |

---

## Fallback: Legacy Text Format

If response is NOT valid JSON (for backwards compatibility), fall back to text parsing below.

## General Parsing Strategy (Legacy Text)

1. **Read the full agent response** - Don't assume structure
2. **Extract key fields** - Look for status, summary, file mentions, metrics
3. **Scan for patterns** - File extensions (.py, .js), numbers (test counts, percentages)
4. **Construct capsule** - Use template with extracted data
5. **Fallback gracefully** - If data missing, use generic phrasing

---

## Developer Response Parsing

**Expected status values:**
- `READY_FOR_QA` - Implementation complete, has integration/E2E tests
- `READY_FOR_REVIEW` - Implementation complete, only unit tests or no tests
- `BLOCKED` - Cannot proceed without external help
- `PARTIAL` - Some work done, more needed (same-tier continuation)
- `ESCALATE_SENIOR` - Issue too complex, **immediate** Senior Software Engineer escalation

**Information to extract:**

1. **Status** - Scan for lines like:
   ```
   Status: READY_FOR_QA
   **Status:** READY_FOR_REVIEW
   ```

2. **Files modified/created** - Look for:
   ```
   - Created: file1.py, file2.js
   - Modified: config.py
   - Files created: [list]
   - Implemented in: file.py
   ```
   Also scan response text for file extensions: `.py`, `.js`, `.ts`, `.go`, etc.

3. **Tests added** - Look for:
   ```
   - Added 12 tests
   - Tests created: 15
   - Test count: N
   - Created test_*.py files
   ```
   Count mentions of `test` if specific number not found.

4. **Coverage** - Look for:
   ```
   - Coverage: 92%
   - Test coverage: 85.7%
   - 87% coverage
   ```
   Extract percentage if mentioned.

5. **Summary** - Look for:
   ```
   Summary: One sentence description
   **Summary:** Description
   ```
   Or use first substantial paragraph if no explicit summary.

**Capsule construction:**

```
🔨 Group {id} [{tier}/{model}] complete | {summary}, {file_count} files modified, {test_count} tests added ({coverage}% coverage) | {status} → {next_phase}
```

**Tier notation:** `[SSE]` for Senior Software Engineer, `[Dev]` for Developer. Bracket is optional for backward compatibility - omit if tier unavailable.

**Fallback logic:**

If missing:
- **Files**: Say "implementation complete" instead of listing files
- **Tests**: Say "with tests" or "no new tests" based on status
- **Coverage**: Omit coverage mention
- **Summary**: Use "Implementation complete" or extract from first paragraph
- **Tier/Model**: Omit bracket entirely (e.g., `🔨 Group A complete | ...`)

**Examples:**

Full data available:
```
🔨 Group A [SSE] complete | JWT auth implemented, 3 files created, 12 tests added (92% coverage) | No blockers → QA review
```

Minimal data (only status available):
```
🔨 Group B complete | Implementation complete | Ready → Tech Lead review
```

Files but no test count:
```
🔨 Group C [Dev] complete | Password reset in password_reset.py, with tests | Ready → QA testing
```

---

## QA Expert Response Parsing

**Expected status values:**
- `PASS` - All tests passed
- `FAIL` - Some tests failed (Level 1-2 challenges)
- `FAIL_ESCALATE` - Level 3+ challenge failures (security, chaos, behavioral) → SSE
- `BLOCKED` - Cannot run tests (environment issue, missing deps)
- `FLAKY` - Tests pass sometimes, fail sometimes → Tech Lead

**Information to extract:**

1. **Status/Recommendation** - Look for:
   ```
   Status: PASS
   Recommendation: APPROVE_FOR_REVIEW
   Status: FAIL
   ```

2. **Test results** - Look for:
   ```
   - 12/12 tests passed
   - Tests passed: 15
   - 3 failed, 12 passed
   - Unit Tests: 10/10 passed
   ```

3. **Coverage** - Same pattern as Developer

4. **Failures** - If failed, look for:
   ```
   Failed tests: [list]
   Failing: test_auth_edge_case, test_timeout
   ```

5. **Security/Quality mentions** - Look for:
   ```
   - security clear
   - no vulnerabilities
   - 0 security issues
   ```

**Capsule construction (PASS):**

```
✅ Group {id} tests passing | {passed}/{total} tests passed, {coverage}% coverage, {quality_signals} | Approved → Tech Lead review
```

**Capsule construction (FAIL):**

```
⚠️ Group {id} QA failed | {failed}/{total} tests failing ({failure_summary}) | Developer fixing → See artifacts/{session}/qa_failures.md
```

**Fallback logic:**

If missing:
- **Test counts**: Say "all tests passed" or "tests failed"
- **Coverage**: Omit
- **Failure details**: Say "N tests failing" without specifics
- **Quality signals**: Omit

**Examples:**

Full pass:
```
✅ Group A tests passing | 12/12 tests passed, 92% coverage, security clear | Approved → Tech Lead review
```

Minimal pass:
```
✅ Group B tests passing | All tests passed | Approved → Code review
```

Fail with details:
```
⚠️ Group C QA failed | 3/15 tests failing (auth edge cases) | Developer fixing → See artifacts/bazinga_123/qa_failures.md
```

Fail minimal:
```
⚠️ Group A QA failed | Tests failing | Developer fixing
```

---

## Tech Lead Response Parsing

**Expected status values:**
- `APPROVED` - Code quality approved
- `CHANGES_REQUESTED` - Issues need fixing
- `SPAWN_INVESTIGATOR` - Complex problem needs investigation
- `UNBLOCKING_GUIDANCE` - Provided guidance for blocked developer

**Information to extract:**

1. **Decision** - Look for:
   ```
   Decision: APPROVED
   **Decision:** CHANGES_REQUESTED
   Status: APPROVED
   ```

2. **Security issues** - Look for:
   ```
   - Security: 0 issues
   - 1 high severity issue
   - security clear
   - Security scan: 2 medium issues found
   ```

3. **Lint issues** - Look for:
   ```
   - Lint: 0 issues
   - 3 lint errors
   - Code quality: 5 warnings
   ```

4. **Coverage** - Same pattern

5. **Reason** - Look for:
   ```
   Reason: Quality is excellent
   **Reason:** SQL injection vulnerability
   ```

**Capsule construction (APPROVED):**

```
✅ Group {id} approved | {quality_summary} | Complete ({completed}/{total} groups)
```

**Capsule construction (CHANGES_REQUESTED):**

```
⚠️ Group {id} needs revision | {issue_summary} | Fixes required → Developer
```

**Capsule construction (ESCALATE):**

```
🔬 Group {id} complexity detected | {escalation_reason} | Escalating to Opus → Tech Lead (Rev {N})
```

**Capsule construction (INVESTIGATION):**

```
🔬 Group {id} investigation needed | {complex_issue} | Spawning Investigator for deep analysis
```

**Quality summary construction:**

Combine available info:
- Security: "Security clear" OR "N security issues found"
- Lint: "0 lint issues" OR "N lint issues"
- Coverage: "coverage {N}%"
- Architecture: "architecture solid" if mentioned

**Examples:**

Full approval:
```
✅ Group A approved | Security clear, 0 lint issues, architecture solid | Complete (1/3 groups)
```

Minimal approval:
```
✅ Group B approved | Code quality approved | Complete (2/3 groups)
```

Changes needed:
```
⚠️ Group C needs revision | 1 high security issue (SQL injection) + 3 lint errors | Fixes required → Developer
```

Minimal changes:
```
⚠️ Group A needs revision | Code quality issues found | Developer fixing
```

Investigation:
```
🔬 Group C investigation needed | Intermittent test failures with unclear root cause | Spawning Investigator
```

---

## PM Response Parsing

**PRIORITY: Check for Investigation Answers FIRST**

**If PM response contains "## Investigation Answers" section:**

Extract investigation findings to show user BEFORE planning capsule:

**Extraction pattern:**
```
Look for section: ## Investigation Answers
Extract all question-answer pairs
Format: Question → Answer → Evidence
```

**Capsule construction (investigation results):**
```
📊 Investigation results | {findings_summary} | Details: {details}
```

**Example extraction:**
```
PM response contains:
## Investigation Answers
**Question:** How many E2E tests exist?
**Answer:** Found 83 E2E tests in 5 files (30 passing, 53 skipped)
**Evidence:** npm test output

Orchestrator outputs:
📊 Investigation results | Found 83 E2E tests in 5 files | 30 passing, 53 skipped
```

**Fallback:** If investigation section exists but formatting unclear, extract key findings from the section and summarize.

---

**Expected status values:**
- `PLANNING_COMPLETE` - Initial planning done, ready to start execution
- `BAZINGA` - Work complete, all requirements met
- `CONTINUE` - More work needed
- `NEEDS_CLARIFICATION` - User input required
- `INVESTIGATION_ONLY` - Only questions answered, no implementation requested
- `INVESTIGATION_NEEDED` - Blocked by unclear root cause, need investigator

**Information to extract:**

1. **Status** - Look for:
   ```
   ## PM Status: PLANNING_COMPLETE
   ## PM Status: INVESTIGATION_NEEDED
   Status: BAZINGA
   **PM Status:** CONTINUE
   PM Status: NEEDS_CLARIFICATION
   **Status:** INVESTIGATION_ONLY
   ```

   **Note:** `PLANNING_COMPLETE` is PM's initial response after analyzing requirements. It includes mode decision and task groups.
   **Note:** `INVESTIGATION_NEEDED` means PM is blocked by unclear root cause - orchestrator should spawn Investigator.

2. **Mode decision** (initial PM spawn) - Look for:
   ```
   Mode: SIMPLE
   Execution Mode: PARALLEL
   Decision: Parallel mode with 3 developers
   ```

3. **Task groups** (initial PM spawn) - Look for:
   ```
   Group A: JWT Authentication
   Task Groups:
     - Group A: ...
     - Group B: ...
   ```

4. **Clarification question** - Look for:
   ```
   Question: Should we use Stripe test mode?
   Blocker Type: Missing External Data
   ```

**Capsule construction (PLANNING_COMPLETE - complex multi-phase):**

```markdown
📋 **Execution Plan Ready**

**Mode:** {mode} ({N} concurrent developers)
**Tasks:** {task_count} across {phase_count} phases

**Phases:**
> Phase 1: {phase_name} - Groups {ids}
> Phase 2: {phase_name} - Groups {ids}

**Success Criteria:** {criteria_summary}

Starting Phase 1...
```

**Capsule construction (PLANNING_COMPLETE - simple):**

```
📋 Planning complete | Single-group: {task_summary} | Starting development
```

**Capsule construction (mode decision - legacy/fallback):**

```
📋 Planning complete | {N} parallel groups: {group_summaries} | Starting development → Groups {list}
```

**Capsule construction (BAZINGA):**

```
✅ BAZINGA - Orchestration Complete!
[Show final report]
```

### PM BAZINGA Completion Summary Parsing

When PM sends BAZINGA, extract the Completion Summary section:

**Look for:**
```
### Completion Summary
- Completed_Items: [N]
- Total_Items: [M]
- Completion_Percentage: [X]%
- Deferred_Items: [list]
```

**Validation before accepting:**
1. Completed_Items == Total_Items (100% required)
2. Deferred_Items is empty `[]`
3. Completion_Percentage == 100%

**Exception:** If user approved scope reduction (logged via `save-event <session_id> scope_change '<payload>'`), validate against `approved_scope` instead.

**If validation fails:**
- DO NOT accept BAZINGA
- Invoke validator: `Skill(command: "bazinga-validator")`
- Validator will provide detailed rejection reason

**If Completion Summary is missing:**
- Flag as incomplete BAZINGA format
- Validator will query original scope from database

**Capsule construction (CONTINUE):**

```
📋 PM check | {assessment} | {feedback} → {next_action}
```

**Capsule construction (CLARIFICATION):**

```
⚠️ PM needs clarification | {blocker_type}: {question_summary} | Awaiting response (auto-proceed with fallback in 5 min)
```

**Capsule construction (INVESTIGATION_NEEDED):**

```
🔬 Investigation needed | {problem_summary} | Spawning Investigator
```

**Fallback logic:**

If mode/groups not clear, scan for keywords:
- "parallel" → parallel mode
- "simple" → simple mode
- Count group mentions (Group A, Group B, etc.)

**Examples:**

Mode decision:
```
📋 Planning complete | 3 parallel groups: JWT auth (5 files), User reg (3 files), Password reset (4 files) | Starting development → Groups A, B, C
```

Simple mode:
```
📋 Planning complete | Single-group execution: Implement user authentication | Starting development
```

Clarification:
```
⚠️ PM needs clarification | Missing external data: Should we use Stripe test mode or production? | Awaiting response
```

---

## Investigator Response Parsing

**Expected status values:**
- `ROOT_CAUSE_FOUND` - Problem identified, routes to Tech Lead for validation
- `INVESTIGATION_INCOMPLETE` - Max iterations reached without definitive answer
- `BLOCKED` - External blocker prevents investigation
- `EXHAUSTED` - All hypotheses eliminated, need new theories
- `NEED_DEVELOPER_DIAGNOSTIC` - Need code instrumentation (internal loop)
- `HYPOTHESIS_ELIMINATED` - Ruled out a theory (internal loop)
- `NEED_MORE_ANALYSIS` - Continuing investigation (internal loop)

**Information to extract:**

1. **Status** - Same pattern as other agents

2. **Root cause** - Look for:
   ```
   Root Cause: Race condition in async flow
   **Root Cause:** Memory leak in cache
   ```

3. **Hypothesis** - Look for:
   ```
   Hypothesis Being Tested: Database connection timeout
   Testing: Race condition theory
   ```

4. **Diagnostic request** - Look for what Developer needs to add

**Capsule construction varies by status - use templates from investigation messages already defined.**

---

## Best Practices for Parsing

### 1. Scan Multiple Patterns

Don't rely on exact format. Look for variations:
```python
# Instead of expecting exactly "Status: READY_FOR_QA"
# Scan for any of:
- "Status: READY_FOR_QA"
- "**Status:** READY_FOR_QA"
- "Status READY_FOR_QA"
- "ready for QA" (case insensitive)
```

### 2. Extract from Natural Text

If structured fields missing, scan the prose:
```
Response: "I've implemented JWT authentication in auth_middleware.py
and token_validator.py, added 12 comprehensive tests achieving 92% coverage."

Extract:
- Files: auth_middleware.py, token_validator.py (2 files)
- Tests: 12
- Coverage: 92%
- Topic: JWT authentication
```

### 3. Use Defaults

Always have fallback values:
```
files = extract_files(response) OR "implementation complete"
tests = extract_test_count(response) OR "with tests" if has_tests else ""
coverage = extract_coverage(response) OR None
```

### 4. Prioritize Clarity

If unsure, use clear generic phrasing:
```
Good: "Group A complete | Implementation finished | Ready → QA"
Bad:  "Group A complete | ??? | ??? → ???"
```

### 5. Link to Artifacts for Details

When information is too detailed or missing:
```
⚠️ Multiple issues found → See artifacts/bazinga_123/techlead_review.md
```

---

## Parsing Workflow Summary

For each agent response:

1. **Identify agent type** (Developer, QA, Tech Lead, PM, Investigator)
2. **Extract status** (required - determines next routing)
3. **Scan for key metrics** (files, tests, coverage, issues)
4. **Look for summary/description** (topic, what was done)
5. **Select capsule template** based on agent type + status
6. **Fill template** with extracted data
7. **Apply fallbacks** for missing data
8. **Output capsule** to user

**If extraction fails completely:** Output a minimal but clear capsule:
```
[Agent type] {id} {status_word} | {generic_description} | {next_action}

Example: "Developer Group A complete | Implementation finished | Ready for review"
```

---

## Developer (Merge Task) Response Parsing

**Context:** After Tech Lead approves a group, a Developer is spawned with a merge task (not implementation).

**Expected status values:**
- `MERGE_SUCCESS` - Feature branch merged to initial branch, tests pass
- `MERGE_CONFLICT` - Git merge conflicts encountered
- `MERGE_TEST_FAILURE` - Merge succeeded but tests failed

**Information to extract:**

1. **Status** - Look for:
   ```
   Status: MERGE_SUCCESS
   **Status:** MERGE_CONFLICT
   MERGE_TEST_FAILURE
   ```

2. **Conflict files** (if MERGE_CONFLICT) - Look for:
   ```
   Conflicting files: file1.py, file2.js
   Conflicts in: [list]
   ```

3. **Test failures** (if MERGE_TEST_FAILURE) - Look for:
   ```
   Failed tests: test_name, test_name2
   Failures: [list]
   ```

4. **Files changed** - Look for merge summary

**Capsule construction (MERGE_SUCCESS):**

```
✅ Group {id} merged | {feature_branch} → {initial_branch} | Tests passing → PM check
```

**Capsule construction (MERGE_CONFLICT):**

```
⚠️ Group {id} merge conflict | {conflict_files} | Developer fixing → Retry merge
```

**Capsule construction (MERGE_TEST_FAILURE):**

```
⚠️ Group {id} merge failed tests | {test_failures} | Developer fixing → Retry merge
```

**Examples:**

Successful merge:
```
✅ Group A merged | feature/jwt-auth → main | Tests passing → PM check
```

Conflict:
```
⚠️ Group B merge conflict | auth.py, config.py | Developer fixing → Retry merge
```

Test failure:
```
⚠️ Group C merge failed tests | test_auth_integration, test_login | Developer fixing → Retry merge
```
