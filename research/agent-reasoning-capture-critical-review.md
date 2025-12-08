# Agent Reasoning Capture: Critical Implementation Review

**Date:** 2025-12-08
**Context:** Post-implementation review of Agent Reasoning Capture feature
**Decision:** Identify flaws, logic gaps, and improvement opportunities
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## What Was Implemented

### Phase 1: Database Schema
- `agent_reasoning` table with columns: session_id, group_id, agent_type, agent_id, iteration, reasoning_phase, confidence_level, content, references, redacted, timestamp
- Migration v8 in init_db.py

### Phase 2: CLI Commands
- `save-reasoning` - Store agent reasoning with auto-secret redaction
- `get-reasoning` - Query with filters (agent_type, phase, group_id, limit)
- `reasoning-timeline` - Chronological progression of all reasoning
- `check-mandatory-phases` - Verify understanding + completion phases exist

### Phase 3: Agent Prompts
- All 7 agents updated with reasoning documentation instructions
- Mandatory phases: understanding, completion
- Optional phases: approach, decisions, risks, blockers, pivot

### Phase 4: Orchestrator Integration
- Reasoning context query after context packages (Simple + Parallel modes)
- Tech Lead gets developer-specific reasoning for code reviews
- Investigator gets reasoning-timeline for investigation context

---

## Critical Analysis: Identified Flaws

### 1. SECRET REDACTION IS INCOMPLETE (SEVERITY: HIGH)

**Evidence from testing:**
```
Input: "Found API key sk-abc123def456xyz789 in config. Using JWT_SECRET=mysupersecretkey"
Output: "Found API key sk-abc123def456xyz789 in config. Using JWT_SECRET_REDACTED"
```

**Problem:** The `sk-abc123def456xyz789` API key was NOT redacted. Only `KEY=value` patterns are caught.

**Missing patterns:**
- `sk-*` (OpenAI API keys)
- `pk_*`, `sk_*` (Stripe keys)
- `ghp_*`, `gho_*` (GitHub tokens)
- `AKIA*` (AWS access keys)
- Bearer tokens in headers
- Base64-encoded credentials

**Risk:** Agents could inadvertently log real API keys to the database, creating a security exposure.

**Fix needed:** Expand regex patterns in `redact_secrets()` function.

---

### 2. MANDATORY PHASE CHECK IS NEVER ENFORCED (SEVERITY: HIGH)

**Current state:** `check-mandatory-phases` command exists but is NEVER called in the orchestrator workflow.

**Agent prompts say:**
> "You MUST document reasoning for phases: understanding (mandatory), completion (mandatory)"

**But:** This is purely advisory. There's no enforcement mechanism.

**Problem flow:**
1. Developer spawned
2. Developer does work, reports READY_FOR_QA
3. Orchestrator routes to QA
4. **NO CHECK** if Developer actually documented understanding + completion

**Result:** Agents can skip reasoning documentation entirely with zero consequences.

**Fix needed:** Add `check-mandatory-phases` call before routing to next workflow step. But this creates a new question: What happens if check fails? Block workflow? Spawn retry?

---

### 3. NO REASONING CONTENT SIZE LIMITS (SEVERITY: MEDIUM)

**Current:** `content` column is TEXT with no size limit.

**Risk scenario:**
1. Agent saves verbose 10KB reasoning entry
2. Next agent queries reasoning, gets 10KB in prompt
3. That agent saves even more verbose response
4. Reasoning balloons over iterations

**Impact:** Context bloat, increased token costs, potential prompt truncation.

**Fix needed:**
- Add `content_length` constraint (e.g., max 2000 chars)
- Or: Truncate at query time with `--max-chars` flag

---

### 4. TECH LEAD DEVELOPER QUERY IS AMBIGUOUS (SEVERITY: MEDIUM)

**Current query:**
```bash
get-reasoning "{session_id}" "{group_id}" --agent_type developer --limit 3
```

**Problem:** What if work was done by SSE (Senior Software Engineer) or RE (Requirements Engineer)?

**The query filters `agent_type = 'developer'` which will MISS:**
- `senior_software_engineer` reasoning (escalation cases)
- `requirements_engineer` reasoning (research tasks)

**Result:** Tech Lead reviews code but lacks reasoning from the actual implementer.

**Fix needed:** Query all implementation agents: `--agent_type developer,senior_software_engineer,requirements_engineer`

---

### 5. REASONING TIMELINE CAN OVERWHELM INVESTIGATOR (SEVERITY: MEDIUM)

**Current:** Investigator gets full `reasoning-timeline` for group.

**Problem scenario:**
- Complex parallel workflow with 4 groups
- Each group has 5 agents with 3 reasoning entries each
- Investigator investigating Group A issue
- Timeline returns 60 entries (potentially 30KB+ of content)

**Impact:** Investigator prompt bloated with irrelevant reasoning from other groups.

**Fix needed:** Filter timeline by relevance:
- Same group only: `--group_id {group_id}` (already supported)
- Or: Time window: `--since "1 hour ago"`
- Or: Only blockers/pivots: `--phase blockers,pivot`

---

### 6. NO VALIDATION OF REASONING QUALITY (SEVERITY: MEDIUM)

**Current:** Agents self-report reasoning content and confidence.

**Problem:** An agent could save:
```
Phase: understanding
Confidence: high
Content: "I understand the task"
```

**This passes all checks** but provides zero useful reasoning.

**No enforcement of:**
- Minimum content length
- Actual analysis in content
- Confidence justification

**Result:** Feature becomes checkbox compliance rather than genuine reasoning capture.

**Fix needed:** Either:
- Minimum content length (200+ chars)
- Required keywords/structure
- Or accept this as acceptable limitation (documentation is advisory)

---

### 7. PHASE ORDERING NOT ENFORCED (SEVERITY: LOW)

**Expected flow:** understanding → approach → decisions → risks → completion

**Current:** Agents can save phases in any order.

**Problem:** An agent could save `completion` before `understanding`.

**Impact:** Reasoning timeline could show illogical progression.

**Assessment:** Probably acceptable. Agents may iterate and understanding may evolve. Strict ordering could be too restrictive.

---

### 8. REFERENCES FIELD UNUSED (SEVERITY: LOW)

**Schema has:** `references JSON` column
**CLI accepts:** `--references JSON` parameter
**Agent prompts:** Never mention references

**Current state:** Field exists but has no defined usage pattern.

**Options:**
- Remove it (YAGNI - You Aren't Gonna Need It)
- Define use case (e.g., link to code locations, related reasoning entries)
- Document as "reserved for future use"

---

### 9. DUPLICATE LOGIC IN TEMPLATES (SEVERITY: LOW)

**phase_simple.md and phase_parallel.md both have:**
- Reasoning context query section
- Routing rules table
- Prompt section format

**Problem:** If we update the format in one, must remember to update the other.

**Current approach:** Parallel mode says "see Simple Mode §Reasoning Context Routing Rules" but still has its own copy.

**Fix options:**
- Extract to shared template file
- Or: Accept duplication (templates are meant to be standalone)

---

### 10. CLI INTEGRATION IS FRAGILE (SEVERITY: LOW)

**Current:** Orchestrator templates embed raw CLI commands:
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-reasoning ...
```

**Problem:** If CLI interface changes (parameter names, output format), templates silently break.

**Current mitigations:**
- CLI is versioned with database
- `--quiet` flag ensures consistent JSON output

**Acceptable risk:** CLI is internal, changes would be coordinated.

---

## Decision Logic Flow Analysis

### Happy Path ✅
```
Developer spawned
  ↓ saves understanding reasoning
  ↓ implements feature
  ↓ saves completion reasoning
  ↓ reports READY_FOR_QA
Orchestrator routes to QA
  ↓ QA queries reasoning context (gets dev's understanding + completion)
  ↓ QA validates with context
  ↓ saves own reasoning
  ↓ reports PASS
Orchestrator routes to Tech Lead
  ↓ TL queries developer reasoning specifically
  ↓ TL reviews with WHY context
  ↓ reports APPROVED
```

**This works well when agents cooperate.**

### Failure Paths ⚠️

**Path A: Agent skips reasoning documentation**
```
Developer spawned
  ↓ implements feature (no reasoning saved)
  ↓ reports READY_FOR_QA
Orchestrator routes to QA
  ↓ QA queries reasoning context (returns empty)
  ↓ QA proceeds without context
  ↓ (no degradation, just less context)
```
**Assessment:** Graceful degradation. Feature value reduced but not blocked.

**Path B: Database/CLI failure**
```
Developer spawned
  ↓ saves reasoning (DB write fails silently?)
  ↓ reports READY_FOR_QA
Orchestrator routes to QA
  ↓ QA queries reasoning (CLI error)
  ↓ Template says "proceed without reasoning (non-blocking)"
  ↓ QA proceeds
```
**Assessment:** Need to verify CLI error handling. Does it exit 0 on DB errors?

**Path C: Reasoning query returns stale data**
```
Developer spawned (iteration 1)
  ↓ saves understanding reasoning
  ↓ fails, iteration 2 spawned
Developer (iteration 2)
  ↓ queries reasoning
  ↓ gets iteration 1's reasoning (stale, from failed attempt)
  ↓ may repeat failed approach
```
**Assessment:** Need iteration filtering. Query should prefer latest iteration.

---

## Comparison to Original Design

### Original research document proposed:
1. ✅ Database table for reasoning storage
2. ✅ CLI commands for save/get/timeline/check
3. ✅ Agent prompts with phase instructions
4. ✅ Orchestrator context injection
5. ❌ Pre-commit hooks for reasoning validation (not implemented)
6. ❌ Dashboard visualization (not implemented)
7. ❌ Reasoning quality scoring (not implemented)

### Scope decisions made:
- Focused on core capture + retrieval
- Deferred validation/enforcement
- Deferred visualization

**Reasonable MVP scope.**

---

## Recommendations

### Priority 1: Fix Critical Issues
1. **Expand secret redaction patterns** - Add common API key prefixes
2. **Fix Tech Lead query** - Include all implementation agents, not just "developer"

### Priority 2: Add Enforcement Options
3. **Optional phase check** - Add flag to orchestrator: `enforce_mandatory_phases: true|false`
4. **Content size limits** - Either at save time or query time

### Priority 3: Future Improvements
5. **Iteration filtering** - Query latest iteration's reasoning by default
6. **Reasoning dashboard** - Visualize reasoning flow in dashboard-v2
7. **Quality heuristics** - Warn on suspiciously short reasoning content

---

## Verdict

**Overall Assessment:** The implementation is a solid MVP with known limitations.

### Strengths ✅
- Clean database schema
- Flexible CLI interface
- Non-blocking integration (graceful degradation)
- Secret redaction (partial)

### Weaknesses ⚠️
- Secret redaction incomplete
- No enforcement mechanism
- Tech Lead query too narrow
- No content size limits

### Risks 🔴
- Security exposure from incomplete secret redaction
- Feature may be ignored without enforcement
- Context bloat over time

### Recommendation
1. **Ship as-is** for immediate value
2. **Fix secret redaction** in next iteration (security)
3. **Fix Tech Lead query** in next iteration (functionality)
4. **Consider enforcement** based on observed usage

---

## Multi-LLM Review Integration

*Pending external review from OpenAI GPT-5 and Google Gemini 3 Pro Preview*

---

## References

- Original design: `research/agent-reasoning-capture-ultrathink.md`
- Implementation commits: `a35bd87`, `4c53da0`, `7d6f8cd`
- CLI source: `.claude/skills/bazinga-db/scripts/bazinga_db.py`
- Templates: `bazinga/templates/orchestrator/phase_simple.md`, `phase_parallel.md`
