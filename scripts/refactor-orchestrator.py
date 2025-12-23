#!/usr/bin/env python3
"""
Refactor orchestrator.md to reduce size while preserving all functionality.
This script performs surgical replacements of verbose sections with template references.
"""

import re
from pathlib import Path


def replace_parsing_section(content: str) -> str:
    """Replace the response parsing section with a concise template reference."""

    # Find the start and end of the parsing section
    start_pattern = r'## 📊 Agent Response Parsing for Capsule Construction\n\n\*\*Purpose:\*\* Extract structured information'
    end_pattern = r'Example: "Developer Group A complete \| Implementation finished \| Ready for review"\n```\n\n---\n'

    match = re.search(f'{start_pattern}.*?{end_pattern}', content, re.DOTALL)

    if not match:
        print("⚠️  Could not find parsing section")
        return content

    replacement = '''## 📊 Agent Response Parsing for Capsule Construction

**Complete parsing guide:** `bazinga/templates/response_parsing.md`

**Quick Reference:**

For each agent type, extract:
- **Developer**: Status (READY_FOR_QA/REVIEW/BLOCKED/PARTIAL), files, tests, coverage
- **QA Expert**: Status (PASS/FAIL/PARTIAL), test results, failures, quality signals
- **Tech Lead**: Decision (APPROVED/CHANGES_REQUESTED/ESCALATE/INVESTIGATION), security/lint issues
- **PM**: Status (BAZINGA/CONTINUE/CLARIFY), mode decision, task groups
- **Investigator**: Status (ROOT_CAUSE_FOUND/NEED_DIAGNOSTIC/etc.), hypotheses

**Parsing principle:** Best-effort extraction with fallbacks. Never fail on missing data.

**Capsule templates (examples):**
```
🔨 Developer: Group {id} complete | {summary}, {files}, {tests} ({coverage}%) | {status} → {next}
✅ QA: Group {id} passing | {passed}/{total} tests, {coverage}%, {quality} | → Tech Lead
✅ Tech Lead: Group {id} approved | {quality_summary} | Complete ({N}/{total} groups)
📋 PM: Planning complete | {mode}: {groups} | Starting development
```

**Detailed extraction patterns, fallback strategies, and complete examples:** See `bazinga/templates/response_parsing.md`

---
'''

    content = content[:match.start()] + replacement + content[match.end():]
    print(f"✓ Replaced parsing section (saved ~{match.end() - match.start() - len(replacement)} chars)")

    return content


def replace_simple_mode_prompt_building(content: str) -> str:
    """Replace verbose Simple Mode prompt building with concise template reference."""

    # Find the prompt building section
    start_marker = "### 🔴 MANDATORY DEVELOPER PROMPT BUILDING - NO SHORTCUTS ALLOWED"
    end_marker = "**AFTER spawning:**"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("⚠️  Could not find Simple Mode prompt building section")
        return content

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print("⚠️  Could not find end of Simple Mode prompt building section")
        return content

    replacement = '''### 🔴 MANDATORY DEVELOPER PROMPT BUILDING - NO SHORTCUTS ALLOWED

**Follow the prompt building guide:** `bazinga/templates/prompt_building.md`

**Required sections for developer prompt:**
1. ✓ Session ID (from Step 0)
2. ✓ Role definition + Group assignment ("main") + Mode ("Simple")
3. ✓ Task description from PM
4. ✓ Testing framework (from testing_config.json)
5. ✓ Mandatory skills (from skills_config.json where status="mandatory")
6. ✓ Optional skills (from skills_config.json where status="optional")
7. ✓ MANDATORY WORKFLOW with Skill() invocations
8. ✓ Report format

**Validation checklist before spawning:**
- [ ] "Skill(command:" appears once per mandatory skill
- [ ] Testing mode from testing_config.json included
- [ ] MANDATORY WORKFLOW section present
- [ ] Report format specified

See `bazinga/templates/prompt_building.md` for complete instructions.
See `agents/developer.md` for full agent definition.

'''

    old_section = content[start_idx:end_idx]
    content = content[:start_idx] + replacement + content[end_idx:]
    print(f"✓ Replaced Simple Mode prompt building (saved ~{len(old_section) - len(replacement)} chars)")

    return content


def replace_parallel_mode_prompt_building(content: str) -> str:
    """Replace verbose Parallel Mode prompt building with reference to Simple Mode."""

    # Find the prompt building section for parallel mode
    start_marker = "### 🔴 MANDATORY DEVELOPER PROMPT BUILDING (PARALLEL MODE) - NO SHORTCUTS"
    end_marker = "**AFTER receiving ALL developer responses:**"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("⚠️  Could not find Parallel Mode prompt building section")
        return content

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print("⚠️  Could not find end of Parallel Mode prompt building section")
        return content

    replacement = '''### 🔴 MANDATORY DEVELOPER PROMPT BUILDING (PARALLEL MODE) - NO SHORTCUTS

**Follow the SAME process as Simple Mode (Step 2A.1)** with these group-specific adaptations:

**For EACH group (A, B, C, D), build prompt with:**
1. ✓ Session ID (from Step 0)
2. ✓ Group assignment (specific group ID: A, B, C, D) + Mode ("Parallel")
3. ✓ **Group-specific branch name**
4. ✓ **Group-specific task description** from PM
5. ✓ Testing framework + Mandatory/Optional skills (same as Simple Mode)
6. ✓ MANDATORY WORKFLOW (same as Simple Mode, but with group branch)
7. ✓ Report format

**Validation checklist (for EACH group):**
- [ ] "Skill(command:" appears once per mandatory skill
- [ ] Testing mode from testing_config.json included
- [ ] MANDATORY WORKFLOW section present
- [ ] Group-specific branch name included
- [ ] Report format specified

**IMPORTANT:** Build prompts for ALL groups BEFORE spawning any.

See `bazinga/templates/prompt_building.md` for detailed instructions.

'''

    old_section = content[start_idx:end_idx]
    content = content[:start_idx] + replacement + content[end_idx:]
    print(f"✓ Replaced Parallel Mode prompt building (saved ~{len(old_section) - len(replacement)} chars)")

    return content


def consolidate_phase_2b_duplication(content: str) -> str:
    """Consolidate Phase 2B workflow duplication with reference to Phase 2A."""

    # Find the section about routing each group independently
    start_marker = "### Step 2B.3-2B.7: Route Each Group Independently"
    # Find the next major section (Step 2B.8)
    end_marker = "### Step 2B.8: Spawn PM When All Groups Complete"

    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("⚠️  Could not find Phase 2B routing section")
        return content

    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print("⚠️  Could not find end of Phase 2B routing section")
        return content

    replacement = '''### Step 2B.3-2B.7: Route Each Group Independently

**Critical difference from Simple Mode:** Each group flows through the workflow INDEPENDENTLY and CONCURRENTLY.

**For EACH group, execute the SAME workflow as Phase 2A (Steps 2A.3 through 2A.7):**

| Phase 2A Step | Phase 2B Equivalent | Notes |
|---------------|---------------------|-------|
| 2A.3: Route Developer Response | 2B.3 | Check this group's developer status |
| 2A.4: Spawn QA Expert | 2B.4 | Use this group's files only |
| 2A.5: Route QA Response | 2B.5 | Check this group's QA status |
| 2A.6: Spawn Tech Lead | 2B.6 | Use this group's context only |
| 2A.6b: Investigation Loop | 2B.6b | Same investigation process |
| 2A.6c: Tech Lead Validation | 2B.6c | Validate this group's investigation |
| 2A.7: Route Tech Lead Response | 2B.7 | Check this group's approval |

**Group-specific adaptations:**
- Replace "main" with group ID (A, B, C, D)
- Use group-specific branch name
- Use group-specific files list
- Track group status independently in database
- Log with agent_id: `{role}_group_{X}`

**Workflow execution:** Process groups concurrently but track each independently.

**Prompt building:** Use the same process as Step 2A.4 (QA), 2A.6 (Tech Lead), but substitute group-specific files and context.

**When ALL groups reach "complete" status → Proceed to Step 2B.8**

'''

    old_section = content[start_idx:end_idx]
    content = content[:start_idx] + replacement + content[end_idx:]
    print(f"✓ Consolidated Phase 2B duplication (saved ~{len(old_section) - len(replacement)} chars)")

    return content


def main():
    orchestrator_path = Path("agents/orchestrator.md")

    if not orchestrator_path.exists():
        print(f"❌ File not found: {orchestrator_path}")
        return 1

    print("Reading orchestrator.md...")
    content = orchestrator_path.read_text()
    original_size = len(content)
    original_lines = content.count('\n')

    print(f"Original: {original_lines} lines, {original_size} chars")
    print()

    # Phase 1: Replace parsing section (already done, but keeping for completeness)
    print("Phase 1: Replacing response parsing section...")
    content = replace_parsing_section(content)
    print()

    # Phase 2: High-Impact Refactorings
    print("Phase 2: Replacing Simple Mode prompt building...")
    content = replace_simple_mode_prompt_building(content)
    print()

    print("Phase 3: Replacing Parallel Mode prompt building...")
    content = replace_parallel_mode_prompt_building(content)
    print()

    print("Phase 4: Consolidating Phase 2B duplication...")
    content = consolidate_phase_2b_duplication(content)
    print()

    # Calculate savings
    new_size = len(content)
    new_lines = content.count('\n')
    saved_lines = original_lines - new_lines
    saved_chars = original_size - new_size

    print("=" * 60)
    print(f"Result: {new_lines} lines, {new_size} chars")
    print(f"Saved: {saved_lines} lines ({saved_lines/original_lines*100:.1f}%)")
    print(f"Saved: {saved_chars} chars ({saved_chars/original_size*100:.1f}%)")
    print(f"Estimated tokens: ~{new_size // 4}")
    print("=" * 60)

    # Write back
    print()
    print("Writing refactored orchestrator.md...")
    orchestrator_path.write_text(content)
    print("✓ Done!")

    return 0


if __name__ == "__main__":
    exit(main())
