# Bash Heredoc Implementation Review

**Date:** 2025-12-11
**Context:** Review of the fix for specialization-loader skill output mechanism
**Status:** Implementation complete, seeking validation

---

## Problem Solved

When `specialization-loader` skill ran:
1. It output the specialization block as **text** (Claude's direct response)
2. This text was **visible to the user** (internal orchestration data leaked)
3. The turn **ended** after text output (orchestrator couldn't continue to Task() calls)

---

## Solution Implemented

Changed Step 8 of the skill from "output text directly" to "call Bash with heredoc":

**Before (broken):**
```
Skill composes block → Outputs as TEXT → Turn ends, visible to user
```

**After (fixed):**
```
Skill composes block → Calls Bash with heredoc → Turn continues, orchestrator extracts from tool result
```

---

## Key Insight

The difference between bazinga-db (which works) and specialization-loader (which was broken):

| Skill | Mechanism | Result |
|-------|-----------|--------|
| bazinga-db | Calls Bash tool with python script | Turn continues |
| specialization-loader (old) | Outputs text directly | Turn ends |
| specialization-loader (new) | Calls Bash with heredoc | Turn continues |

**Why:** Tool calls return results that Claude can process and continue from. Text output ends Claude's turn.

---

## Implementation Details

### SKILL.md Step 8 (Changed)

```markdown
### Step 8: Return Result via Bash

**🔴 CRITICAL: Use Bash to output the block, NOT direct text output.**

Direct text output ends your turn. Bash output keeps the turn alive so the orchestrator can continue.

**Use this Bash command to output your composed block:**

```bash
cat << 'SPECBLOCK'
[SPECIALIZATION_BLOCK_START]
{The composed markdown block - paste your composed content here}
[SPECIALIZATION_BLOCK_END]

Metadata:
- Group: {group_id}
- Templates: {count} loaded
- Tokens: {actual}/{budget}
- Identity: {short identity summary}
SPECBLOCK
```

**🔴 RULES:**
- ✅ Call `Bash` tool with the heredoc above as your ONLY action
- ✅ Replace `{...}` placeholders with actual values
- ❌ Do NOT output any text before or after the Bash call
- ❌ Do NOT say "I'll compose..." or narrate your process

**After the Bash call completes, your job is done.** The orchestrator extracts the block from the Bash output and continues to Task().
```

---

## Questions for Review

### 1. Is the mechanism sound?

Does calling Bash with a heredoc actually keep the turn alive? The assumption is:
- Text output = Claude's response = turn ends
- Tool call (Bash) = returns result = Claude can continue

Is this assumption correct in the Claude Code architecture?

### 2. Will the orchestrator correctly extract the block?

The orchestrator looks for `[SPECIALIZATION_BLOCK_START]...[SPECIALIZATION_BLOCK_END]` markers. Previously these were in text output, now they're in Bash tool result.

Does the orchestrator's extraction logic work with tool results the same as text?

### 3. Are there edge cases with heredoc?

The block content may contain:
- Markdown with backticks (code blocks)
- Special characters
- Quotes

Using `'SPECBLOCK'` (single-quoted delimiter) should prevent variable expansion. Are there other concerns?

### 4. What about the "ORCHESTRATOR: SPECIALIZATION BLOCK READY" instruction?

Previously the skill output included:
```
---
**ORCHESTRATOR: SPECIALIZATION BLOCK READY**

Extract and store the block between [SPECIALIZATION_BLOCK_START] and [SPECIALIZATION_BLOCK_END].
Continue to Turn 2 when ALL needed specialization blocks are collected.
```

This was removed in the new implementation. Is this okay, or does the orchestrator need this instruction to know what to do after receiving the block?

### 5. Parallel mode considerations

In parallel mode, the orchestrator may call the skill multiple times (for different specialization sets). Each call will result in a separate Bash output.

Does the orchestrator correctly:
- Collect all blocks before proceeding to Turn 2?
- Map each block to the correct group(s)?

### 6. Step 7 (DB logging) still happens before Step 8

The skill still logs metadata to DB in Step 7, then outputs the block via Bash in Step 8. Is this order correct? Should DB logging happen after Bash output?

---

## What Was NOT Changed

1. **Orchestrator templates** - No changes to phase_parallel.md or phase_simple.md
2. **Marker format** - Still uses `[SPECIALIZATION_BLOCK_START]...[SPECIALIZATION_BLOCK_END]`
3. **DB logging** - Step 7 still logs metadata to bazinga-db
4. **Block content structure** - Same markdown format

---

## Alternative Considered But Rejected

**DB storage approach:** Save block to DB, orchestrator reads from DB.

Rejected because:
- More complex (DB schema changes, JSON escaping)
- The simpler Bash heredoc approach solves the root cause directly
- No need to change WHERE data goes, just HOW it's returned

---

## Success Criteria

1. ✅ Skill outputs via Bash (not text)
2. ✅ Turn doesn't end after skill completes
3. ? Orchestrator extracts block from Bash result
4. ? Orchestrator continues to Task() calls
5. ? Works in both simple and parallel modes

Items 3-5 need runtime validation.

---

## Request for Reviewers

Please evaluate:
1. Is the mechanism fundamentally sound?
2. Are there hidden assumptions that might break?
3. What edge cases might cause problems?
4. Is any additional change needed to make this work?
