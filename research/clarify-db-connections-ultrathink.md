# Orchestrator Database Connections: Who Should Connect and Why It Fails

**Date:** 2025-12-12
**Context:** Orchestrator bypasses bazinga-db skill, uses inline SQL that fails
**Decision:** Pending
**Status:** Reviewed - Awaiting User Approval
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The BAZINGA orchestrator is using **direct database connections** via inline Python/sqlite3 commands instead of invoking the `bazinga-db` skill. This violates explicit rules and causes data corruption.

### Observed Failure (User-Provided Logs)

```
⏺ Bash(python3 -c "
      import sys…)
  ⎿  Error: Exit code 1
     Traceback (most recent call last):
       File "<string>", line 6, in <module>
     TypeError: __init__() missing 1 required positional argument: 'db_path'

⏺ Bash(sqlite3 bazinga/bazinga.db "SELECT id, session_id, group_id, status FROM task_groups..."
  ⎿  Error: in prepare, no such column: group_id
```

**Key observations:**
1. Orchestrator ran `python3 -c "import sqlite3..."` - **explicitly forbidden**
2. Orchestrator ran raw `sqlite3` commands - **explicitly forbidden**
3. Used wrong column name `group_id` (correct: `id`) - **proof the rule exists for good reason**
4. Multiple retry attempts with different approaches - **thrashing instead of following protocol**

### The Explicit Rule (Already Exists)

From `agents/orchestrator.md` lines 202-207:

```markdown
**🔴 CRITICAL: NEVER USE INLINE SQL**
- 🚫 **NEVER** write `python3 -c "import sqlite3..."` for database operations
- 🚫 **NEVER** write raw SQL queries (UPDATE, INSERT, SELECT)
- 🚫 **NEVER** directly access `bazinga/bazinga.db` with inline code
- ✅ **ALWAYS** use `Skill(command: "bazinga-db")` for ALL database operations
- **Why:** Inline SQL uses wrong column names (`group_id` vs `id`) and causes data loss
```

### The Design (Intended Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTENDED FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Orchestrator                                                   │
│      │                                                          │
│      ▼                                                          │
│  Skill(command: "bazinga-db")  ◄── CORRECT                     │
│      │                                                          │
│      ▼                                                          │
│  bazinga-db Skill                                               │
│      │ - Parses natural language request                        │
│      │ - Executes bazinga_db.py with correct args               │
│      │ - Uses proper column names                               │
│      │ - Returns formatted response                             │
│      │                                                          │
│      ▼                                                          │
│  bazinga_db.py (Python script)                                  │
│      │ - WAL mode for concurrency                               │
│      │ - Proper error handling                                  │
│      │ - Auto-path detection                                    │
│      │ - Validated column names                                 │
│      │                                                          │
│      ▼                                                          │
│  bazinga/bazinga.db (SQLite)                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         ACTUAL (BROKEN)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Orchestrator                                                   │
│      │                                                          │
│      ▼                                                          │
│  Bash(python3 -c "import sqlite3...")  ◄── WRONG               │
│      │                                                          │
│      ▼                                                          │
│  bazinga/bazinga.db (SQLite)                                    │
│      │ - Wrong column names (group_id vs id)                    │
│      │ - No WAL mode setup                                      │
│      │ - No error handling                                      │
│      │ - No path detection                                      │
│      │                                                          │
│      ▼                                                          │
│  ERROR: no such column: group_id                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Root Cause Analysis

### Why Does the Orchestrator Bypass the Skill?

**Hypothesis 1: Context Decay (Long Conversations)**
- After many messages, the orchestrator "forgets" the skill exists
- The rule is ~200 lines into a ~1900 line file
- Earlier patterns in context may override later rules

**Hypothesis 2: Implicit "Fix It" Instinct**
- When database operations fail, the orchestrator tries to "help"
- Instead of invoking skill and letting skill handle errors, it improvises
- Raw SQL feels "more direct" even though it's forbidden

**Hypothesis 3: Missing Enforcement Mechanism**
- The rule is instructional only - "NEVER do X"
- No structural barrier prevents inline SQL
- The model can choose to ignore instructions

**Hypothesis 4: Schema Mismatch Between Mental Model and Reality**
- Orchestrator "assumes" `group_id` is a column (intuitive name)
- Actual schema uses `id` as the column name
- Skill abstracts this away; inline SQL exposes the mismatch

**Hypothesis 5: Skill Invocation Syntax Confusion**
- Correct: `Skill(command: "bazinga-db")`
- Wrong: `Skill(skill: "bazinga-db")` (different parameter name!)
- If skill invocation fails silently, orchestrator may fall back to raw SQL

### Evidence Assessment

| Hypothesis | Evidence For | Evidence Against | Likelihood |
|------------|--------------|------------------|------------|
| Context Decay | Rule is deep in file (~line 200) | Runtime anchor exists at line 1 | Medium |
| Fix It Instinct | Logs show multiple retry approaches | Rule explicitly says "use skill" | High |
| Missing Enforcement | No pre-exec validation | Can't enforce in prompt-only system | High |
| Schema Mismatch | Error message proves wrong column | Skill would have correct column | Confirmed |
| Syntax Confusion | Two parameter names exist | No evidence of failed skill call | Low |

**Most Likely Root Cause:** Combination of Hypothesis 2 (Fix It Instinct) + Hypothesis 3 (No Enforcement)

When the orchestrator encounters a database task, it has two paths:
1. **Correct:** Invoke skill → Wait for result → Continue
2. **Incorrect:** Write inline SQL → Execute directly → Fail → Retry with different SQL

Path 2 feels "faster" and "more in control" but violates architecture.

---

## Why This Matters

### 1. Data Integrity Risk
- Inline SQL with wrong column names corrupts/loses data
- User logs show `group_id` used instead of `id`
- Task groups not updated correctly → orchestration state corrupted

### 2. Concurrency Issues
- Skill sets up WAL mode for concurrent access
- Inline SQL may not set WAL mode → lock contention
- Multiple agents could corrupt database

### 3. Maintenance Burden
- Schema changes require updating skill in ONE place
- Inline SQL scattered across orchestrator behavior requires updating EVERYWHERE
- Impossible to maintain

### 4. Audit Trail Loss
- Skill logs all operations with timestamps
- Inline SQL bypasses logging
- No record of what was changed

### 5. Error Recovery Failure
- Skill has proper error handling and recovery
- Inline SQL fails hard with cryptic Python errors
- Orchestrator thrashes instead of recovering gracefully

---

## Solution Options

### Option A: Strengthen Documentation (Low Effort, Low Confidence)

Add MORE rules to orchestrator.md:
- Move "NEVER INLINE SQL" to line 1
- Add to every section that mentions database
- Repeat in multiple places

**Pros:**
- Easy to implement
- No code changes

**Cons:**
- Already tried (rule exists at line 202)
- More rules don't guarantee compliance
- Context decay still applies

**Verdict:** Insufficient alone

### Option B: Pre-Execution Validation Hook (Medium Effort, Medium Confidence)

Create a Claude Code hook that blocks `python3 -c` and `sqlite3` commands:

```json
{
  "hooks": {
    "pre-tool-use": {
      "bash": {
        "block_patterns": [
          "python3 -c.*sqlite3",
          "sqlite3.*bazinga",
          "import sqlite3"
        ],
        "message": "❌ Inline SQL forbidden. Use Skill(command: \"bazinga-db\") instead."
      }
    }
  }
}
```

**Pros:**
- Hard enforcement - can't bypass
- Clear error message guides correct behavior
- Catches ANY inline SQL attempt

**Cons:**
- Requires hook implementation (does Claude Code support this?)
- May false-positive on legitimate uses
- External to orchestrator context

**Verdict:** Effective if hooks support pattern blocking

### Option C: Skill-First Architecture Enforcement (Medium Effort, High Confidence)

Modify orchestrator to ONLY have Skill and Task tools available (remove Bash for DB operations):

In orchestrator definition:
```markdown
**Your ONLY tools for state management:**
- ✅ Skill(command: "bazinga-db") - ALL database operations
- ❌ Bash - NOT available for database operations
```

**Pros:**
- Structural enforcement - can't use what doesn't exist
- Clear separation of concerns
- Aligns with existing architecture

**Cons:**
- Bash still needed for init commands (session ID, mkdir)
- Can't fully remove Bash, only restrict
- Model may still try forbidden patterns

**Verdict:** Partial - need selective Bash restriction

### Option D: Inline SQL → Skill Rewrite Pattern (High Effort, High Confidence)

When orchestrator generates inline SQL, intercept and rewrite to skill invocation:

```
Detected: python3 -c "import sqlite3; UPDATE task_groups..."
Rewritten to: Skill(command: "bazinga-db")
Request: "update task group R2-INIT status to completed for session bazinga_20251211_112743"
```

**Pros:**
- Transparently fixes behavior
- No orchestrator changes needed
- Catches all inline SQL

**Cons:**
- Complex implementation
- May misinterpret SQL intent
- Adds latency

**Verdict:** Over-engineered for this problem

### Option E: Mandatory Skill Checkpoint (Medium Effort, High Confidence)

Add explicit checkpoint BEFORE any database operation:

```markdown
### §Database Operation Checkpoint (MANDATORY)

Before ANY database-related action:

1. **STOP** - Am I about to write SQL or Python database code?
2. **CHECK** - Is this in the Bash Allowlist? (NO database ops are)
3. **REDIRECT** - Use Skill(command: "bazinga-db") instead

**Self-check phrase:** "Database operations go through skill, NEVER inline."
```

**Pros:**
- Explicit decision point
- Self-reminder pattern (proven effective for role drift)
- No external tooling needed

**Cons:**
- Still relies on model following instructions
- May be skipped under time pressure

**Verdict:** Good complement to other solutions

---

## Recommended Solution: Combined Approach

### Layer 1: Move Rule to Top + Runtime Anchor (Documentation)

Move the "NEVER INLINE SQL" rule to the top of orchestrator.md, right after the existing runtime anchor:

```markdown
<!--
🚨 RUNTIME ENFORCEMENT ANCHOR 🚨

If you find yourself about to:
- Run a git command → STOP → Spawn Developer
- Call an external API → STOP → Spawn Investigator
- Analyze logs/output → STOP → Spawn appropriate agent
- Read code files → STOP → Spawn agent to read
- **ACCESS DATABASE → STOP → Use Skill(command: "bazinga-db")**  ← ADD THIS

The ONLY exception is the explicit ALLOWLIST in §Bash Command Allowlist.

This comment exists because role drift is the #1 orchestrator failure mode.
-->
```

### Layer 2: Add to Bash Allowlist as EXPLICIT FORBIDDEN

In §Bash Command Allowlist:

```markdown
**Explicitly FORBIDDEN (use bazinga-db skill instead):**
- `python3 -c "import sqlite3..."` → Skill(command: "bazinga-db")
- `sqlite3 bazinga/bazinga.db ...` → Skill(command: "bazinga-db")
- `python3 .claude/skills/bazinga-db/scripts/bazinga_db.py` → Skill(command: "bazinga-db")
- ANY direct database access → Skill(command: "bazinga-db")
```

### Layer 3: Add Database Checkpoint Before State Operations

In orchestrator's database operation sections (Steps 0, 1, 2A, 2B):

```markdown
**§Database Checkpoint:** Before this operation, verify you are using `Skill(command: "bazinga-db")`, NOT inline SQL.
```

### Layer 4: Skill Error Handling Guidance

Add to bazinga-db skill documentation:

```markdown
### If Skill Invocation Fails

If `Skill(command: "bazinga-db")` returns an error:

1. ✅ DO: Retry the skill invocation with clearer request
2. ✅ DO: Check session_id and parameters are correct
3. ✅ DO: Output error capsule and STOP if persistent failure
4. ❌ DO NOT: Fall back to inline SQL
5. ❌ DO NOT: Try raw Python/sqlite3 commands
6. ❌ DO NOT: Attempt to "fix" the database directly

**The skill is the ONLY authorized database interface. If it fails, the operation fails.**
```

---

## Implementation Plan

| Step | File | Change | Priority |
|------|------|--------|----------|
| 1 | agents/orchestrator.md | Add DATABASE line to runtime anchor | High |
| 2 | agents/orchestrator.md | Add database commands to FORBIDDEN list in Bash Allowlist | High |
| 3 | agents/orchestrator.md | Add §Database Checkpoint references at Steps 0, 1, 2A, 2B | Medium |
| 4 | .claude/skills/bazinga-db/SKILL.md | Add "If Skill Invocation Fails" section | Medium |
| 5 | .claude/claude.md | Add reminder about bazinga-db skill usage | Low |

### Estimated Impact

- **Lines added:** ~30
- **Lines modified:** ~10
- **Files affected:** 3
- **Risk:** Low (documentation-only changes)

---

## Critical Analysis

### Pros

1. **Addresses root cause** - Makes rule more prominent and explicit
2. **Low risk** - Documentation changes only, no code
3. **Consistent with existing patterns** - Uses same approach as role drift prevention
4. **Immediate effect** - New orchestrations will see updated rules
5. **Layered defense** - Multiple checkpoints increase compliance

### Cons

1. **Still relies on model compliance** - No hard enforcement
2. **Documentation bloat** - Orchestrator.md already near size limit
3. **May not prevent all cases** - Determined model could still bypass
4. **Doesn't fix existing sessions** - Only helps future orchestrations

### Risks

1. **Over-documentation** - Too many rules may cause cognitive overload
2. **Rule fatigue** - Model may "tune out" repeated warnings
3. **False sense of security** - May think problem is solved when it's not

### Verdict

**Recommended for implementation** with monitoring. This is the pragmatic solution given:
- Can't modify Claude Code to add hard enforcement
- Documentation-based prevention has worked for other role drift cases
- Low implementation effort, low risk
- Can iterate based on observed compliance

---

## Alternative Considered: Hard Enforcement via Code

**Why not modify bazinga_db.py to be the ONLY database interface?**

The Python script already exists and works correctly. The problem is the orchestrator choosing NOT to use it. We cannot modify the orchestrator's tool availability at runtime - it has access to Bash, and Bash can run sqlite3.

**True hard enforcement would require:**
- Claude Code hooks that intercept Bash commands (uncertain if supported)
- Sandboxing that blocks sqlite3 binary access (too restrictive)
- Removing Bash entirely (breaks init commands)

None of these are practical within current constraints.

---

## Success Metrics

After implementation, monitor for:

1. **Zero inline SQL commands** in next 10 orchestration sessions
2. **All database ops via skill** - grep logs for `Skill(command: "bazinga-db")`
3. **No `sqlite3` or `python3 -c` errors** in orchestrator output
4. **Correct column names used** - no "no such column: group_id" errors

---

## Summary

| Question | Answer |
|----------|--------|
| Who SHOULD connect to DB? | `bazinga-db` skill (via bazinga_db.py) |
| Who IS connecting to DB? | Orchestrator via inline SQL (WRONG) |
| Why does this happen? | "Fix it" instinct + no hard enforcement |
| How to fix? | Multi-layer documentation reinforcement |
| Can we hard-enforce? | Not with current tooling |
| Is this normal? | No - it's a known anti-pattern |

---

## Multi-LLM Review Integration

### Reviewer
- OpenAI GPT-5 (Gemini skipped)

### Critical Feedback Summary

GPT-5 raised several valid concerns about the documentation-only approach:

1. **"Enforcement is mostly documentation-based"** - Moving rules and adding reminders won't reliably prevent inline SQL. The same "fix-it instinct" can recur.

2. **"Assumes Bash Allowlist is enforced"** - The allowlist exists in docs, not in code. Without a code-level gate, the orchestrator can still run any Bash command.

3. **"Ambiguous skill invocation contract"** - bazinga-db relies on natural-language requests which can misparse. No deterministic API contract.

4. **"Risk of context bloat"** - Adding more verbiage to an already huge orchestrator prompt can worsen context decay.

5. **"No remediation for corrupted DB state"** - No detection or repair for sessions where inline SQL wrote incorrect data.

### LLM Suggested Changes Requiring Approval

#### Change 1: Bash Policy Guard Script (exec_guard.sh)

**Current:** Orchestrator uses Bash directly with documented allowlist (not enforced)
**Proposed:** All Bash calls go through `bazinga/scripts/exec_guard.sh` which:
- Enforces allowlist via regex matching
- Rejects sqlite3/python3 -c with sqlite3
- Logs violations to bazinga-db as `role_violation` events
- Exits non-zero on forbidden patterns

**Impact:** Creates real code-level enforcement; requires script creation + orchestrator doc update

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 2: Deterministic Skill API

**Current:** Skill invoked via natural language: `Skill(command: "bazinga-db")` then freeform prose
**Proposed:** Require explicit subcommand format: `Skill(command: "bazinga-db save-state <session> <type> '<json>'")`

**Impact:** More reliable parsing; requires updating SKILL.md and all orchestrator examples

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 3: DB Health-Check Subcommand

**Current:** No schema validation at session start
**Proposed:** Add `health-check` subcommand that:
- Runs `PRAGMA integrity_check`
- Verifies correct column names exist
- Ensures WAL mode enabled
- Reports issues clearly

**Impact:** Catches corrupted DB early; requires Python code addition to bazinga_db.py

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 4: Compatibility View for Safety

**Current:** Inline SQL using wrong column name (`group_id`) fails hard
**Proposed:** Create temporary safety net view:
```sql
CREATE VIEW task_groups_compat AS
SELECT id AS group_id, id, session_id, name, status, ... FROM task_groups;
```

**Impact:** Reduces damage from stray inline SQL; not a substitute for policy, just a fallback

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 5: Reduce Bash Surface Area

**Current:** Bash used for: session-id, mkdir, file checks, dashboard start, build baseline
**Proposed:** Move session-id and mkdir to bazinga-db subcommands:
- `bazinga-db init-session` (generates ID + creates dirs)
- Keep only `build-baseline.sh` as allowed Bash

**Impact:** Near-zero Bash surface; requires Python code + skill doc updates

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 6: Skill Failure Playbook

**Current:** No explicit guidance on what to do when skill fails
**Proposed:** Add explicit playbook:
- 1 retry with 2s backoff
- If still failing, STOP with single error capsule
- NEVER fall back to inline SQL

**Impact:** Documentation only; prevents thrashing behavior

**Do you approve this change?** [Yes/No/Modify]

---

### Consensus Points (Incorporated Without Approval)

These are low-risk improvements that align with existing patterns:

1. ✅ **Keep docs lean** - Don't add paragraphs, add pointers to enforcement mechanisms
2. ✅ **Single high-visibility banner** - Move rule to runtime anchor at top
3. ✅ **Log violations** - Use existing `save-event` with `role_violation` subtype

### Rejected LLM Suggestions (With Reasoning)

1. ❌ **Periodic policy-validator skill at phase boundaries** - Too invasive for now; monitoring via logs is sufficient
2. ❌ **PATH hardening to remove sqlite3** - Not practical in Claude Code environment
3. ❌ **E2E tests for Bash blocking** - Good idea but out of scope for this fix

---

## Revised Implementation Plan (Pending Approvals)

| Step | Change | Approval Needed | Priority |
|------|--------|-----------------|----------|
| 1 | Move rule to runtime anchor | No | High |
| 2 | Create exec_guard.sh | Yes (Change 1) | High |
| 3 | Update skill to deterministic API | Yes (Change 2) | Medium |
| 4 | Add health-check subcommand | Yes (Change 3) | Medium |
| 5 | Create compat view | Yes (Change 4) | Low |
| 6 | Move session-id/mkdir to skill | Yes (Change 5) | Low |
| 7 | Add failure playbook | Yes (Change 6) | Medium |

---

## References

- `agents/orchestrator.md` lines 202-207 (existing rule)
- `.claude/skills/bazinga-db/SKILL.md` (skill definition)
- `.claude/skills/bazinga-db/references/schema.md` (correct column names)
- `research/orchestrator-role-drift-prevention.md` (related role drift analysis)
- User-provided failure logs (2025-12-12)
- OpenAI GPT-5 review (2025-12-12)
