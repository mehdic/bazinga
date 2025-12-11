# Specialization Loader Output Fix: Analysis

**Date:** 2025-12-11
**Context:** Skill outputs text directly, causing user-visible display and turn termination
**Decision:** Use Bash heredoc instead of text output
**Status:** ✅ IMPLEMENTED

---

## Problem Statement

When `specialization-loader` skill runs:
1. It outputs the specialization block as **text** (Claude's response)
2. This text is **visible to the user** (undesirable - internal orchestration data)
3. The turn **ends** after text output (no continuation to Task() calls)

**Root cause:** Skills that output text directly cause the conversation to show that text and end Claude's turn. Tool calls (Bash, etc.) return results that Claude can process and continue from.

**Comparison:**
| Mechanism | User sees it? | Turn continues? |
|-----------|---------------|-----------------|
| Text output | ✅ Yes | ❌ No |
| Tool call result | Can be summarized | ✅ Yes |

---

## Current Flow (Broken)

```
1. Orchestrator: Skill(specialization-loader)
2. Skill Claude: [reads templates, composes block]
3. Skill Claude: OUTPUT "[SPECIALIZATION_BLOCK_START]...block...[SPECIALIZATION_BLOCK_END]"
   └─> User sees this! Turn ends!
4. [Nothing happens - turn ended]
```

---

## Desired Flow

```
1. Orchestrator: Skill(specialization-loader)
2. Skill Claude: [reads templates, composes block]
3. Skill Claude: [saves block somewhere via tool call]
4. Skill Claude: Returns minimal confirmation
5. Orchestrator: [reads block from storage]
6. Orchestrator: Task() x N for developers
```

---

## Options Analysis

### Option A: Save to bazinga-db (NOT IMPLEMENTED - too complex)

**Change:** Skill saves block to DB, outputs minimal confirmation

**Implementation:**
1. Modify Step 7 to save full `spec_block` content (not just metadata)
2. Modify Step 8 to NOT output the block - just end after Bash call
3. Orchestrator reads block from DB when building Task() prompts

**Skill changes (Step 7):**
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-skill-output \
  "{session_id}" "specialization-loader" '{
    "group_id": "{group_id}",
    "spec_block": "{THE_FULL_BLOCK_ESCAPED}",
    "templates_used": [...],
    "token_count": N
  }'
```

**Skill changes (Step 8):**
```markdown
### Step 8: Complete

After saving to DB, your work is done. The Bash call above is your final action.
Do NOT output the block as text - it's already saved to DB.
```

**Orchestrator changes:**
```markdown
After Skill(specialization-loader) returns, read the block:
python3 bazinga_db.py get-skill-output "{session}" "specialization-loader" --group "{group}"
```

**Pros:**
- Uses existing DB infrastructure
- Block stored persistently (audit trail)
- Minimal new code
- Clean separation of concerns

**Cons:**
- Need to escape JSON properly (block may contain quotes, newlines)
- Extra DB query when building prompts

**Complexity:** Low (2-3 file changes)

---

### Option B: Save to temp file (NOT IMPLEMENTED)

**Change:** Skill writes block to file, orchestrator reads file

**Implementation:**
```bash
# Skill writes
cat > bazinga/temp/spec_{session}_{group}.md << 'SPECEOF'
{block content}
SPECEOF

# Orchestrator reads
cat bazinga/temp/spec_{session}_{group}.md
```

**Pros:**
- Very simple
- No JSON escaping issues
- Human-readable files

**Cons:**
- File cleanup needed
- Not as structured as DB
- Parallel groups may have race conditions

**Complexity:** Low

---

### Option C: Return block via environment variable (NOT IMPLEMENTED)

**Change:** Skill sets env var, orchestrator reads it

**Implementation:**
```bash
export SPEC_BLOCK_R2_INIT="..."
```

**Pros:**
- No file/DB overhead

**Cons:**
- Shell escaping nightmare
- Large blocks may exceed limits
- Doesn't persist across tool calls

**Complexity:** Medium (escaping issues)

---

### Option D: Inline specialization (remove skill) (NOT IMPLEMENTED)

**Change:** Orchestrator reads templates directly, no skill

**Pros:**
- Simplest flow
- No skill invocation overhead

**Cons:**
- Duplicates complex logic (version guards, token budgeting)
- Orchestrator template gets huge
- Loses modularity

**Complexity:** High (move all logic to orchestrator)

---

## Recommendation: Bash Heredoc (Simplest)

**Key Insight:** The problem is not WHERE data goes, but HOW it's returned:
- Text output → Turn ends, visible to user
- Tool call (Bash) → Turn continues, orchestrator extracts from result

**Solution:** Skill outputs via Bash heredoc instead of direct text.

**Rationale:**
1. **Minimal change** - Only SKILL.md Step 8 needs modification
2. **No DB changes** - Existing marker extraction still works
3. **No file storage** - Block stays in tool result
4. **Proven mechanism** - bazinga-db already works this way

---

## Implementation Plan (IMPLEMENTED)

### File 1: `.claude/skills/specialization-loader/SKILL.md`

**Step 8 changes:**
- Changed from "output text directly" to "call Bash with heredoc"
- Block content goes through Bash tool call
- Turn stays alive, orchestrator continues

```bash
cat << 'SPECBLOCK'
[SPECIALIZATION_BLOCK_START]
{block content}
[SPECIALIZATION_BLOCK_END]

Metadata:
- Group: {group_id}
...
SPECBLOCK
```

### No other files need changes

- Orchestrator already extracts blocks from skill output
- Same markers `[SPECIALIZATION_BLOCK_START]...[SPECIALIZATION_BLOCK_END]` work
- Just extracted from Bash tool result instead of text output

---

## JSON Escaping Strategy

The block contains markdown with quotes, newlines, code blocks. Options:

**A. Base64 encode:**
```bash
BLOCK_B64=$(echo "{block}" | base64 -w0)
# Save: {"spec_block_b64": "$BLOCK_B64"}
# Read: echo "$BLOCK_B64" | base64 -d
```

**B. Heredoc to file, then reference:**
```bash
cat > /tmp/spec_block.md << 'EOF'
{block}
EOF
BLOCK_HASH=$(md5sum /tmp/spec_block.md | cut -d' ' -f1)
# Save: {"spec_block_file": "/tmp/spec_block.md", "hash": "$BLOCK_HASH"}
```

**C. Let bazinga-db handle it:**
If bazinga-db's `save-skill-output` accepts a `--content-file` parameter like `save-reasoning` does, use that.

**Recommendation:** Option C if available, else Option A (base64).

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| JSON escaping breaks | Use base64 or file-based approach |
| DB query fails | Fallback to generic specialization |
| Multiple groups same spec | Save once, query returns same block |
| Large blocks | Base64 adds 33% overhead, still within limits |

---

## Success Criteria

1. ✅ Skill output NOT visible to user
2. ✅ Orchestrator continues to Task() after skill returns
3. ✅ Block correctly retrieved and used in prompts
4. ✅ Audit trail preserved in DB
5. ✅ Works for single and multiple group scenarios

---

## Questions for Review

1. Is bazinga-db's `save-skill-output` the right storage mechanism, or should we add a dedicated `save-spec-block` command?
2. Should we support querying multiple blocks at once (for efficiency)?
3. Is base64 encoding acceptable, or is there a cleaner approach?
