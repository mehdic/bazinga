# Tech Lead Code Review Feedback Loop: Iterative Improvement Protocol

**Date:** 2025-12-30
**Context:** User observed Tech Lead approves or rejects entirely, but doesn't provide actionable feedback that leads to code improvement. Current behavior is binary (APPROVED/CHANGES_REQUESTED) without a structured feedback loop.
**Decision:** Implement a categorized issue list with iterative feedback protocol
**Status:** Reviewed - Awaiting User Approval
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

### Current Behavior
The Tech Lead agent currently operates in a **binary approval mode**:
- **APPROVED**: Code passes review, routes to PM
- **CHANGES_REQUESTED**: Issues found, routes back to Developer

This creates two problems:

1. **All-or-Nothing Reviews**: Tech Lead can't distinguish between:
   - Critical security issues that MUST be fixed
   - Suggestions that would improve code but aren't blocking
   - Minor issues that are nice-to-have

2. **No Structured Feedback Loop**: When Developer receives CHANGES_REQUESTED:
   - Developer doesn't know which issues are mandatory vs optional
   - Developer can't communicate "I chose not to fix X because Y"
   - Tech Lead can't track which issues were addressed vs intentionally skipped
   - No mechanism to prevent endless loops of minor nitpicks

### Evidence from Codebase

**Tech Lead agent (agents/tech_lead.md lines 33-50):**
- Has severity taxonomy: BLOCKER, IMPORTANT, SUGGESTION, NIT, FYI
- Has review checklist: CRITICAL, HIGH, MEDIUM, LOW
- BUT: Only outputs APPROVED or CHANGES_REQUESTED (binary)
- Handoff file has `issues` array but no structured iteration protocol

**Transitions (workflow/transitions.json lines 116-128):**
```json
"CHANGES_REQUESTED": {
  "next_agent": "developer",
  "action": "respawn",
  "include_context": ["tl_feedback", "required_changes"],
  "escalation_check": true
}
```
- Developer gets feedback but no categorization of must-fix vs optional
- No mechanism for Developer to respond with fix status per issue

**Developer agent (agents/developer.md lines 1068-1079):**
- Section "If Implementing Feedback" mentions reading handoff file
- BUT: No structured protocol for responding to categorized issues
- No field in handoff file for "issues addressed" vs "issues skipped with reason"

---

## Proposed Solution: Iterative Code Review Protocol

### High-Level Design

```
Tech Lead Review → Categorized Issue List → Developer Response → Tech Lead Re-Review
                         ↓                         ↓
                   CRITICAL/HIGH           Addressed/Skipped+Reason
                   SUGGESTION              Addressed/Skipped
                   MINOR                   Addressed/Skipped
                         ↓                         ↓
              If CRITICAL exists →        Developer sends back
              CHANGES_REQUESTED           response per issue
                         ↓                         ↓
              If NO critical →            TL checks: All critical
              APPROVED (with notes)       resolved? → APPROVED
```

### Key Principles

1. **Critical Issues Block Approval**: Any CRITICAL/HIGH issue → CHANGES_REQUESTED
2. **Suggestions Are Optional**: Developer MAY fix if valuable, MAY skip with reason
3. **Minor Issues Are Best-Effort**: Developer fixes if easy, otherwise skips
4. **Developer Must Respond**: Explicit acknowledgment of each issue
5. **Max 2 Iterations**: After 2 rounds, escalate to PM or force decision
6. **No New Issues on Re-Review**: Tech Lead only checks if reported issues are fixed

### New Status Code: `CHANGES_REQUIRED`

To differentiate from the binary model, introduce nuance:

| Status | Meaning | Developer Action |
|--------|---------|------------------|
| `APPROVED` | No blocking issues | Proceed to PM |
| `APPROVED_WITH_NOTES` | Minor/suggestion issues only | Fix if easy, proceed to PM |
| `CHANGES_REQUIRED` | Critical/High issues exist | MUST address critical, respond to all |

**Why new status?** The existing `CHANGES_REQUESTED` is too generic. `CHANGES_REQUIRED` explicitly signals "critical issues must be fixed before approval."

### Issue Classification (Tech Lead Output)

```json
{
  "issues": [
    {
      "id": "TL-001",
      "severity": "CRITICAL",  // CRITICAL, HIGH, SUGGESTION, MINOR
      "blocking": true,        // true for CRITICAL/HIGH, false for others
      "title": "SQL Injection Vulnerability",
      "location": "src/api/users.py:45",
      "problem": "User input directly interpolated into SQL query",
      "fix": "Use parameterized query: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
      "why": "Allows attackers to execute arbitrary SQL commands"
    },
    {
      "id": "TL-002",
      "severity": "SUGGESTION",
      "blocking": false,
      "title": "Consider adding rate limiting",
      "location": "src/api/auth.py:23",
      "problem": "Login endpoint has no rate limiting",
      "fix": "Add @limiter.limit('10 per minute') decorator",
      "why": "Would prevent brute force attacks"
    }
  ],
  "summary": {
    "critical": 1,
    "high": 0,
    "suggestion": 1,
    "minor": 0,
    "blocking_count": 1  // Issues that MUST be fixed
  }
}
```

### Developer Response Protocol

```json
{
  "issue_responses": [
    {
      "issue_id": "TL-001",
      "action": "FIXED",
      "details": "Changed to parameterized query on line 45"
    },
    {
      "issue_id": "TL-002",
      "action": "DEFERRED",  // FIXED, DEFERRED, REJECTED
      "reason": "Rate limiting requires Redis which is not in scope for MVP. Logged as tech debt TD-042.",
      "tech_debt_id": "TD-042"
    }
  ],
  "summary": {
    "fixed": 1,
    "deferred": 1,
    "rejected": 0,
    "blocking_resolved": 1  // All blocking issues resolved
  }
}
```

**Action Types:**
- `FIXED`: Issue was addressed in the code
- `DEFERRED`: Issue is valid but will be addressed later (tech debt)
- `REJECTED`: Developer disagrees with the issue (requires justification)

**Rule**: Blocking issues (`severity: CRITICAL/HIGH`) can only be `FIXED` or `REJECTED` with strong justification. `DEFERRED` not allowed for blocking issues.

### Tech Lead Re-Review Protocol

On re-review, Tech Lead:

1. **Reads Developer's issue_responses**
2. **Validates FIXED items**: Confirms code actually implements the fix
3. **Reviews REJECTED items**:
   - If justification is valid → Accept
   - If justification is weak → Re-flag as blocking
4. **Does NOT raise new issues**: Only validates previously reported issues
5. **Decision**:
   - All blocking resolved (or validly rejected) → `APPROVED`
   - Any blocking unresolved → `CHANGES_REQUIRED` (max 2 iterations)

### Iteration Limit

```
Iteration 1: Initial review → Issues found
Iteration 2: Developer fixes → Re-review
Iteration 3: If still blocked → ESCALATE to PM

PM Decision:
- Force approve with tech debt
- Reject the implementation entirely
- Request different approach
```

**Why limit?** Prevents endless loop of nitpicks. After 2 iterations, either issues are resolved or there's a fundamental disagreement that PM must arbitrate.

---

## Implementation Details

### 1. Tech Lead Agent Changes (agents/tech_lead.md)

**Add new section after "Comment Severity Taxonomy":**

```markdown
## Issue Classification for Feedback Loop

When reviewing code, classify ALL issues into:

| Severity | Blocking? | Developer Must... |
|----------|-----------|-------------------|
| CRITICAL | YES | Fix or provide strong justification to reject |
| HIGH | YES | Fix or provide strong justification to reject |
| SUGGESTION | NO | Consider fixing if valuable, may skip with reason |
| MINOR | NO | Fix if easy (<5 min), otherwise skip |

### Issue Output Format

For EACH issue, provide:
- `id`: Unique identifier (TL-001, TL-002, etc.)
- `severity`: CRITICAL/HIGH/SUGGESTION/MINOR
- `blocking`: true if CRITICAL/HIGH, false otherwise
- `title`: Brief description
- `location`: File:line
- `problem`: What's wrong
- `fix`: How to fix it (be specific!)
- `why`: Why this matters

### Decision Logic

```
IF blocking_count > 0:
  status = "CHANGES_REQUIRED"
  next = Developer
ELSE IF suggestion_count + minor_count > 0:
  status = "APPROVED_WITH_NOTES"
  next = PM (Developer may optionally address notes)
ELSE:
  status = "APPROVED"
  next = PM
```
```

**Modify handoff file format (lines 1069-1128):**

```json
{
  "issues": [...],  // Existing but enhanced with id, blocking fields
  "issue_summary": {
    "critical": N,
    "high": N,
    "suggestion": N,
    "minor": N,
    "blocking_count": N
  },
  "iteration": 1,  // NEW: Track review iteration
  "max_iterations": 2,  // NEW: Loop limit
  "prior_issues_resolved": [...],  // NEW: Issues from prior iteration that are now fixed
  "new_issues_this_iteration": [...]  // NEW: Only on first iteration
}
```

### 2. Developer Agent Changes (agents/developer.md)

**Add new section "Responding to Tech Lead Feedback":**

```markdown
## Responding to Tech Lead Feedback

When you receive CHANGES_REQUIRED from Tech Lead, you MUST:

### 1. Read the Issue List

```bash
cat bazinga/artifacts/{SESSION_ID}/{GROUP_ID}/handoff_tech_lead.json | jq '.issues'
```

### 2. Address Each Issue

For EACH issue in the list:

**BLOCKING issues (CRITICAL/HIGH):**
- You MUST either FIX or REJECT with strong justification
- DEFERRED is NOT allowed for blocking issues
- If you REJECT, explain WHY the issue is not valid

**NON-BLOCKING issues (SUGGESTION/MINOR):**
- Fix if valuable and effort is reasonable
- Skip if not valuable or too much effort
- No justification required for skipping

### 3. Document Your Responses

In your handoff file, include:

```json
{
  "issue_responses": [
    {
      "issue_id": "TL-001",
      "action": "FIXED",  // FIXED, DEFERRED, REJECTED
      "details": "What you did to fix it",
      "commit": "abc123"  // Optional: commit hash
    }
  ],
  "blocking_summary": {
    "total_blocking": N,
    "fixed": N,
    "rejected_with_reason": N,
    "unaddressed": 0  // MUST be 0 to proceed
  }
}
```

### 4. Rejection Rules

You may REJECT a blocking issue ONLY if:
- The issue is based on incorrect understanding of requirements
- The suggested fix would break other functionality
- The issue is a false positive from automated scan
- There's a better alternative fix (document it)

Weak reasons (NOT acceptable):
- "Too hard" → Then escalate, don't reject
- "Takes too long" → Log as tech debt if truly out of scope
- "I disagree" → Provide technical reasoning
```

### 3. Transitions Changes (workflow/transitions.json)

**Add new status:**

```json
"tech_lead": {
  "APPROVED": {
    "next_agent": "developer",
    "action": "spawn_merge",
    "then": "check_phase",
    "include_context": ["approval_notes"]
  },
  "APPROVED_WITH_NOTES": {
    "next_agent": "developer",
    "action": "spawn_merge",
    "then": "check_phase",
    "include_context": ["approval_notes", "optional_improvements"]
  },
  "CHANGES_REQUIRED": {
    "next_agent": "developer",
    "action": "respawn",
    "include_context": ["tl_feedback", "issue_list", "blocking_issues"],
    "iteration_check": true,
    "max_iterations": 2
  },
  "CHANGES_REQUESTED": {
    "_deprecated": "Use CHANGES_REQUIRED instead",
    "_alias_to": "CHANGES_REQUIRED"
  }
}
```

**Add iteration check rule:**

```json
"_special_rules": {
  "iteration_limit": {
    "description": "After max_iterations, escalate to PM instead of looping",
    "affected_statuses": ["CHANGES_REQUIRED"],
    "max_iterations": 2,
    "escalation_action": {
      "next_agent": "project_manager",
      "include_context": ["iteration_history", "unresolved_issues", "escalation_reason"]
    }
  }
}
```

### 4. Orchestrator Changes

**Update routing logic for re-review:**

```markdown
### Tech Lead Re-Review Detection

When spawning Tech Lead after Developer fix:

1. Check if this is a re-review (iteration > 1)
2. If re-review, include in prompt:
   - Prior issue list
   - Developer's issue_responses
   - Instruction: "Only validate previously reported issues. Do NOT raise new issues."

3. If iteration >= max_iterations:
   - Route to PM instead of Developer
   - PM decides: force approve, reject, or request new approach
```

### 5. New Database Fields (bazinga-db schema)

```sql
-- Add to task_groups table
ALTER TABLE task_groups ADD COLUMN review_iteration INTEGER DEFAULT 0;
ALTER TABLE task_groups ADD COLUMN review_max_iterations INTEGER DEFAULT 2;

-- New table for issue tracking
CREATE TABLE IF NOT EXISTS review_issues (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  group_id TEXT NOT NULL,
  issue_id TEXT NOT NULL,  -- TL-001, TL-002, etc.
  iteration INTEGER NOT NULL,
  severity TEXT NOT NULL,  -- CRITICAL, HIGH, SUGGESTION, MINOR
  blocking BOOLEAN NOT NULL,
  title TEXT NOT NULL,
  location TEXT,
  problem TEXT,
  fix_suggestion TEXT,
  why_important TEXT,
  developer_action TEXT,  -- FIXED, DEFERRED, REJECTED, PENDING
  developer_response TEXT,
  resolved BOOLEAN DEFAULT FALSE,
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

---

## Workflow Diagrams

### Happy Path (No Critical Issues)

```
Tech Lead Review
      │
      ▼
  ┌─────────────────┐
  │ Issues found:   │
  │ - 0 CRITICAL    │
  │ - 0 HIGH        │
  │ - 2 SUGGESTION  │
  │ - 1 MINOR       │
  └────────┬────────┘
           │
           ▼
  APPROVED_WITH_NOTES
           │
           ▼
  Developer (merge task)
  - MAY address notes
  - Proceeds to PM
```

### Standard Feedback Loop

```
Tech Lead Review (Iteration 1)
      │
      ▼
  ┌─────────────────┐
  │ Issues found:   │
  │ - 1 CRITICAL    │
  │ - 1 HIGH        │
  │ - 2 SUGGESTION  │
  └────────┬────────┘
           │
           ▼
  CHANGES_REQUIRED
           │
           ▼
  Developer
  - FIXES TL-001 (critical)
  - FIXES TL-002 (high)
  - DEFERS TL-003 (suggestion)
  - SKIPS TL-004 (suggestion)
           │
           ▼
  Tech Lead Re-Review (Iteration 2)
  - Validates TL-001: Fixed ✓
  - Validates TL-002: Fixed ✓
  - Notes TL-003 deferred (OK)
  - Notes TL-004 skipped (OK)
           │
           ▼
  APPROVED
```

### Developer Rejects Issue

```
Tech Lead Review
      │
      ▼
  TL-001: CRITICAL - "SQL injection"
           │
           ▼
  CHANGES_REQUIRED
           │
           ▼
  Developer Response:
  "REJECTED - This is a false positive.
   The input comes from internal service,
   not user input. See auth_service.py:12
   for validation."
           │
           ▼
  Tech Lead Re-Review
  - Reviews rejection reasoning
  - Confirms: input IS validated upstream
  - Accepts rejection
           │
           ▼
  APPROVED
```

### Iteration Limit Reached

```
Tech Lead Review (Iteration 1)
  - TL-001: CRITICAL
           │
           ▼
  Developer: FIXED
           │
           ▼
  Tech Lead Re-Review (Iteration 2)
  - TL-001: Still broken
           │
           ▼
  CHANGES_REQUIRED (iteration 2 of 2)
           │
           ▼
  Developer: FIXED (again)
           │
           ▼
  Tech Lead Re-Review (Iteration 3)
  - TL-001: STILL broken
           │
           ▼
  Iteration limit reached!
           │
           ▼
  → Route to PM
  PM Decision:
  - Force approve with tech debt?
  - Reject implementation?
  - Request SSE escalation?
```

---

## Risk Analysis

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Endless loops | High | Hard limit of 2 iterations, then PM escalation |
| Developer rejects everything | Medium | Orchestrator tracks rejection rate; >50% triggers PM review |
| Tech Lead raises new issues on re-review | Medium | Explicit instruction: "Only validate prior issues" |
| Increased latency | Low | Most issues resolved in 1-2 iterations |
| Developer confusion | Low | Clear documentation with examples |
| Backwards compatibility | Low | Keep `CHANGES_REQUESTED` as alias to `CHANGES_REQUIRED` |

### Non-Blocking Approval Safeguard

To prevent abuse where Developer skips all suggestions:

```
IF iteration == 1 AND developer_skipped_all_suggestions:
  Tech Lead notes in re-review: "All suggestions skipped"
  PM will see this in completion report
  Not blocking, but visible for audit
```

---

## Migration Plan

### Phase 1: Schema & Transitions (Non-Breaking)
1. Add `review_issues` table to database
2. Add `review_iteration` field to task_groups
3. Add `APPROVED_WITH_NOTES` and `CHANGES_REQUIRED` to transitions
4. Keep `CHANGES_REQUESTED` as alias (backwards compatible)

### Phase 2: Tech Lead Updates
1. Update Tech Lead agent to output enhanced issue format
2. Add iteration tracking to handoff file
3. Add re-review instructions for iteration > 1

### Phase 3: Developer Updates
1. Add "Responding to Tech Lead Feedback" section
2. Add issue_responses to handoff file format
3. Add validation for blocking issue handling

### Phase 4: Orchestrator Updates
1. Update prompt-builder to include iteration context
2. Add iteration check before spawning Tech Lead
3. Add PM escalation route for iteration limit

### Phase 5: Validation
1. Integration test: Standard feedback loop
2. Integration test: Developer rejection
3. Integration test: Iteration limit escalation
4. Integration test: APPROVED_WITH_NOTES path

---

## Alternatives Considered

### Alternative 1: Keep Binary APPROVED/CHANGES_REQUESTED
**Pros:** Simpler, no migration
**Cons:** Doesn't solve the problem, Tech Lead remains "pompous"
**Verdict:** Rejected - doesn't address user's concern

### Alternative 2: Tech Lead Directly Edits Code
**Pros:** No back-and-forth
**Cons:** Violates agent separation, Tech Lead is reviewer not implementer
**Verdict:** Rejected - architectural violation

### Alternative 3: Auto-Apply Suggestions via Skill
**Pros:** Faster resolution
**Cons:** Developer loses agency, may introduce bugs
**Verdict:** Rejected - risky and overcomplicates

### Alternative 4: Single "Improvement Pass" Status
**Pros:** Simpler than full protocol
**Cons:** Doesn't distinguish critical from optional
**Verdict:** Partially adopted - APPROVED_WITH_NOTES handles this

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Reviews with actionable feedback | ~30% | >90% |
| Average iterations per group | Unknown | <1.5 |
| Developer confusion (escalations due to unclear feedback) | Unknown | <5% |
| Critical issues missed on approval | Unknown | 0% |
| Time to approval (with issues) | Unknown | <2 iterations |

---

## Decision Rationale

This design balances several concerns:

1. **Code Quality**: Critical issues MUST be fixed (blocking)
2. **Developer Agency**: Suggestions can be deferred with reason
3. **Efficiency**: Loop limit prevents endless nitpicking
4. **Accountability**: All decisions tracked in database
5. **Backwards Compatibility**: Old status codes still work
6. **Simplicity**: Re-review only checks prior issues

The iteration limit of 2 was chosen because:
- 1 iteration = Tech Lead may have missed context Developer provides
- 2 iterations = Genuine disagreement, PM should arbitrate
- 3+ iterations = Likely fundamental issue, not worth more cycles

---

## References

- `agents/tech_lead.md` - Current Tech Lead implementation
- `agents/developer.md` - Current Developer implementation
- `workflow/transitions.json` - Current state machine
- `docs/TECH_DEBT_GUIDE.md` - Tech debt logging patterns
- User feedback: "Tech Lead is pompous - just approves or rejects without helping improve"

---

## Additional Enhancement: Deep Analysis Mode

### Trigger "Ultrathink" for Tech Lead Reviews

To ensure Tech Lead performs thorough analysis rather than superficial reviews:

**Add to Tech Lead prompt (agents/tech_lead.md):**

```markdown
## 🧠 Deep Analysis Mode (MANDATORY)

Before making ANY review decision, you MUST engage in thorough analysis:

### Think Deeply About:

1. **Security Implications**
   - What could an attacker do with this code?
   - Are there injection vectors? Auth bypasses? Data leaks?
   - What happens with malformed input?

2. **Edge Cases**
   - What happens at boundaries? (0, -1, MAX_INT, empty string)
   - What if dependencies fail? (network, DB, file system)
   - What if called twice? Concurrently? Out of order?

3. **Future Maintenance**
   - Will a new developer understand this in 6 months?
   - Are there hidden dependencies that could break?
   - Is the abstraction level appropriate?

4. **Performance Under Load**
   - What happens with 10x, 100x, 1000x data?
   - Are there N+1 queries? Unbounded loops?
   - Memory usage patterns?

5. **Integration Points**
   - How does this interact with existing code?
   - Are API contracts maintained?
   - Are there backward compatibility concerns?

### Evidence-Based Findings

For EACH issue you identify:
- Show the exact code that's problematic
- Explain the attack vector or failure mode
- Provide a concrete fix example
- Estimate severity based on actual impact

**Do NOT rush through reviews.** Quality review prevents costly bugs.
```

**Why This Matters:**
- Current Tech Lead may be doing shallow reviews (approve/reject without depth)
- "Ultrathink" approach ensures each review considers multiple dimensions
- Produces actionable feedback instead of vague rejections
- Justifies the use of Opus model for Tech Lead (high-capability for complex reasoning)

**Implementation Note:** This section should be placed prominently in the Tech Lead agent file, ideally before the workflow section, to ensure it's read before any review begins.

---

## Next Steps

1. Get external LLM reviews (OpenAI + Gemini)
2. Integrate feedback
3. Present to user for approval
4. Implement if approved

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (Gemini skipped - ENABLE_GEMINI=false)
**Date:** 2025-12-30

### Consensus Points (Accepted and Incorporated)

#### 1. ✅ Phased Rollout is Critical
**OpenAI:** "Start with richer structured issues and Dev responses under the existing CHANGES_REQUESTED status... Only then extend statuses and DB schema."

**Incorporated:** Revised migration plan to three phases:
- **Phase 0:** No new statuses, richer handoff structure only
- **Phase 1:** APPROVED_WITH_NOTES as alias
- **Phase 2:** DB schema extension via bazinga-db skill

#### 2. ✅ "No New Issues on Re-Review" is Unsafe
**OpenAI:** "Prohibiting new issues in re-review can hide critical vulnerabilities discovered later."

**Incorporated:** Changed rule to:
> "Do not add new NON-BLOCKING issues in re-review. If new CRITICAL/HIGH is discovered, you MUST flag it. Provide concise rationale to prevent nitpick loops."

#### 3. ✅ PM Cannot Force-Approve Blocking Issues
**OpenAI:** "PM's spec explicitly forbids declaring success with test failures or security vulnerabilities. For critical issues, PM must not BAZINGA."

**Incorporated:** Removed "force approve with tech debt" option. PM escalation options are now:
- Re-plan tasks (split work, different approach)
- Escalate to SSE for complex fixes
- Reject implementation and restart
- Request user decision (if scope reduction needed)

#### 4. ✅ Severity Taxonomy Unification
**OpenAI:** "This creates ambiguity. One taxonomy must be canonical."

**Incorporated:** Single taxonomy:
```
CRITICAL/HIGH → blocking: true (must fix)
MEDIUM/LOW → blocking: false (optional)

Mapping from old terms:
- BLOCKER → CRITICAL
- IMPORTANT → HIGH
- SUGGESTION → MEDIUM
- NIT → LOW
```

#### 5. ✅ Issue ID Collision Prevention
**OpenAI:** "TL-001 style IDs risk collision across groups/iterations."

**Incorporated:** Deterministic namespacing:
```
issue_id = "TL-{group_id}-{iteration}-{seq}"
Example: TL-AUTH-1-001, TL-AUTH-2-001
```

#### 6. ✅ DB Changes Must Use bazinga-db Skill
**OpenAI:** "Direct SQL migrations aren't allowed; bazinga-db skill must be extended."

**Incorporated:** Phase 2 explicitly extends bazinga-db skill rather than inline SQL.

#### 7. ✅ Validator Must Check Unresolved Blocking Issues
**OpenAI:** "If unresolved blocking issues exist, validator should reject PM's BAZINGA."

**Incorporated:** Added validator check in Phase 0.

### Additional Improvements from Review

#### 8. ✅ Keep CHANGES_REQUESTED Initially
**OpenAI:** "Do not introduce CHANGES_REQUIRED yet; normalize it to CHANGES_REQUESTED for backward compatibility."

**Incorporated:** Phase 0 uses existing CHANGES_REQUESTED. CHANGES_REQUIRED deferred to future phase if needed.

#### 9. ✅ Developer Fix Patches
**OpenAI:** "Encourage TL to include optional fix_patch (unified diff) for common/trivial fixes."

**Incorporated:** Added optional `fix_patch` field to issue format.

#### 10. ✅ Integration Test Requirements
**OpenAI:** Specific E2E test scenarios listed.

**Incorporated:** Added to Phase 0 validation section.

### Rejected Suggestions (With Reasoning)

None rejected - all OpenAI feedback was valid and has been incorporated.

---

## Revised Migration Plan (Post-Review)

### Phase 0: Safe Rollout (No New Statuses, No DB Schema Changes)

**Goal:** Implement richer feedback structure without breaking existing workflow.

#### Tech Lead Changes

1. **Add "Issue Classification for Feedback Loop" section:**
   ```markdown
   ## Issue Classification for Feedback Loop

   Classify ALL issues with:
   - id: "TL-{GROUP_ID}-{ITERATION}-{SEQ}" (e.g., TL-AUTH-1-001)
   - severity: CRITICAL/HIGH/MEDIUM/LOW
   - blocking: true (CRITICAL/HIGH) or false (MEDIUM/LOW)
   - title, location, problem, fix, why
   - fix_patch: (optional) unified diff for simple fixes
   ```

2. **Add "Re-review Protocol" section:**
   ```markdown
   ## Re-review Protocol

   On re-review (iteration > 1):
   1. Read Developer's issue_responses
   2. Validate FIXED items: confirm fix is correct
   3. Review REJECTED items: accept if reasoning is valid
   4. You MAY raise new CRITICAL/HIGH issues if discovered
   5. Do NOT add new MEDIUM/LOW issues (prevents nitpick loops)
   ```

3. **Handoff file enhancement:**
   ```json
   {
     "issues": [...],
     "issue_summary": {
       "critical": N, "high": N, "medium": N, "low": N,
       "blocking_count": N
     },
     "iteration": 1,
     "prior_issues_resolved": [],
     "new_blocking_issues": []
   }
   ```

#### Developer Changes

1. **Add "Responding to Tech Lead Feedback" section:**
   ```markdown
   ## Responding to Tech Lead Feedback

   For EACH issue:
   - BLOCKING (CRITICAL/HIGH): FIXED or REJECTED with strong justification
   - NON-BLOCKING (MEDIUM/LOW): FIXED, DEFERRED, or skipped

   DEFERRED not allowed for blocking issues.
   REJECTED requires technical reasoning (not "too hard").
   ```

2. **Handoff file enhancement:**
   ```json
   {
     "issue_responses": [
       {
         "issue_id": "TL-AUTH-1-001",
         "action": "FIXED",
         "details": "Changed to parameterized query",
         "commit": "abc123"
       }
     ],
     "blocking_summary": {
       "total_blocking": N,
       "fixed": N,
       "rejected_with_reason": N,
       "unaddressed": 0
     }
   }
   ```

#### Orchestrator Changes

1. **Use existing CHANGES_REQUESTED transitions** (no new status codes)

2. **Iteration tracking via stuck detection:**
   - Track review_attempts per group (existing mechanism)
   - After 2 TL→Dev→TL loops, route to PM with iteration_history

3. **Prompt-builder updates:**
   - Include prior TL issues and dev responses in TL re-review spawns
   - Add instruction: "validate prior issues; only raise new CRITICAL/HIGH"

#### Validator Changes

1. **Add blocking issue check:**
   - Read latest TL handoff and latest Dev response
   - If any blocking issues remain unresolved → REJECT BAZINGA
   - Message: "Unresolved blocking review issues: [list]"

#### Integration Tests

1. Single-loop approval (no issues)
2. Single-loop approval with notes (non-blocking only)
3. Two-loop CHANGES_REQUESTED path then approval
4. Re-review with new CRITICAL issue raised
5. Iteration limit escalates to PM
6. Validator rejects with unresolved blocking issues

### Phase 1: Controlled Status Extensions (Optional)

**Goal:** Add APPROVED_WITH_NOTES for clearer signaling.

1. **Transitions:**
   - Add `APPROVED_WITH_NOTES` as alias of `APPROVED`
   - Router treats it identically to APPROVED

2. **Agent markers:**
   - Add APPROVED_WITH_NOTES to tech_lead markers

3. **Tech Lead:**
   - Emit APPROVED_WITH_NOTES when blocking_count == 0 and notes exist

### Phase 2: Persistence and Analytics

**Goal:** Full database integration and metrics.

1. **Extend bazinga-db skill:**
   - `save-review-issues {session_id} {group_id} {iteration} {issues_json}`
   - `save-issue-responses {session_id} {group_id} {responses_json}`
   - `get-unresolved-blocking {session_id} {group_id}`
   - `get-review-metrics {session_id}`

2. **Metrics to track:**
   - Average iterations to approval
   - Unresolved blocking counts
   - Rejection ratio of blocking issues
   - Suggestion adoption rate

---

## Updated Risk Analysis (Post-Review)

| Risk | Mitigation |
|------|------------|
| Workflow breakage from new statuses | Phase 0 uses existing CHANGES_REQUESTED |
| Re-review blind spots | Allow new CRITICAL/HIGH issues on re-review |
| PM bypass of security concerns | PM cannot force-approve; must re-plan or escalate |
| DB changes via inline SQL | All changes via bazinga-db skill extension |
| Issue ID collisions | Deterministic namespacing: TL-{group}-{iter}-{seq} |
| Validator not enforcing | Add blocking issue check to validator |

---

## Confidence Assessment

| Phase | Confidence | Notes |
|-------|------------|-------|
| Phase 0 | **High** | Uses existing statuses, minimal breakage risk |
| Phase 1 | **Medium** | Requires router/parser updates |
| Phase 2 | **Medium** | Requires bazinga-db skill extension |

---

## Summary of Changes from Original Plan

1. **Removed CHANGES_REQUIRED status** (stay with CHANGES_REQUESTED for now)
2. **Allowed new CRITICAL/HIGH issues on re-review** (safety)
3. **Removed PM force-approve option** (respects PM Golden Rules)
4. **Unified severity taxonomy** (CRITICAL/HIGH/MEDIUM/LOW only)
5. **Deterministic issue IDs** (prevent collisions)
6. **All DB changes via bazinga-db** (no inline SQL)
7. **Phased rollout** (Phase 0 safe, Phase 1-2 incremental)
8. **Validator integration** (block BAZINGA with unresolved issues)

The core value proposition remains: **Tech Lead provides categorized, actionable feedback, and Developer responds with explicit acknowledgment of each issue.**
