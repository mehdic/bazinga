# Claude Code Skills: Complete Implementation Guide

**Version:** 1.0.0
**Date:** 2025-11-19
**Source:** Mikhail Shilkov's Technical Deep-Dive + BAZINGA Implementation Experience
**Purpose:** Single source of truth for creating, updating, and invoking skills

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [SKILL.md Format](#skillmd-format)
4. [Skill Tool Definition](#skill-tool-definition)
5. [Invocation Syntax](#invocation-syntax)
6. [Runtime Behavior](#runtime-behavior)
7. [Best Practices](#best-practices)
8. [Common Patterns](#common-patterns)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

---

## Overview

**What are Skills?**

Skills are self-contained capability packages that extend Claude's abilities with specialized knowledge, workflows, or tool integrations. They combine:
- **Instructions** (SKILL.md) - What Claude reads when the skill is invoked
- **Scripts** - Executable code (Python, Bash, etc.)
- **Resources** - Templates, data files, configurations

**Key Characteristics:**
- **Model-invoked** - Claude decides when to use them (unlike slash commands which are user-invoked)
- **Inline execution** - Run within the main conversation, not as separate processes
- **On-demand loading** - Only loaded when invoked, keeping main prompt lean
- **Project or user-scoped** - Can be machine-wide or project-specific

---

## Directory Structure

### Standard Layout

```
.claude/skills/
├── skill-name/
│   ├── SKILL.md           # Required: Skill definition and instructions
│   ├── scripts/           # Optional: Executable scripts
│   │   ├── main_script.py
│   │   └── helper.sh
│   ├── resources/         # Optional: Templates and data
│   │   ├── template.json
│   │   └── config.yaml
│   └── references/        # Optional: Additional documentation
│       └── usage.md
```

### Naming Conventions

**Skill directory:**
- Use kebab-case: `codebase-analysis`, `lint-check`, `api-contract-validation`
- Be descriptive but concise
- Avoid special characters except hyphens

**SKILL.md:**
- Must be exactly `SKILL.md` (uppercase, no variations)
- Required in every skill directory

**Subfolders:**
- `scripts/` - For executable code
- `resources/` - For templates and data
- `references/` - For additional documentation (not loaded by skill instance)

---

## SKILL.md Format

### Structure

```markdown
---
version: 1.0.0
name: skill-name
description: Brief description that tells Claude when to use this skill
author: Team/Person Name
tags: [category1, category2]
allowed-tools: [Bash, Read]
---

# Skill Name

You are the skill-name skill. Your role is to [describe role].

## When to Invoke This Skill

- Condition 1
- Condition 2
- Condition 3

## Your Task

When invoked with [parameters], you must:

### Step 1: [Action]

[Detailed instructions]

### Step 2: [Action]

[Detailed instructions]

### Step 3: [Action]

[Detailed instructions]

## Example Invocation

[Concrete examples with input/output]

---

**For detailed documentation:** See references/usage.md
```

### Frontmatter Fields

**Required:**
- `version`: Semantic version (e.g., `1.0.0`)
- `name`: Identifier used to invoke the skill (must match directory name)
- `description`: Tells Claude when to use this skill (appears in `<available_skills>`)

**Optional:**
- `author`: Who created/maintains the skill
- `tags`: Categorization tags
- `allowed-tools`: Tools the skill instance can use (e.g., `[Bash, Read]`)

### Content Guidelines

**✅ DO:**
- Write instructions FOR the skill instance (second person: "You are...")
- Call existing scripts rather than implementing logic inline
- Include concrete examples with actual input/output
- Keep it focused (150-250 lines is ideal)
- Use clear section headers
- Provide step-by-step workflows

**❌ DON'T:**
- Write documentation ABOUT the skill (for humans)
- Show raw bash commands for humans to copy
- Include verbose implementation details
- Create skills without version numbers
- Skip "When to Invoke" section
- Mix documentation with instructions

**Remember:** SKILL.md is read BY the skill instance (Claude), not by humans. Write actionable instructions, not reference documentation.

---

## Skill Tool Definition

### Tool Structure

Claude Code provides a `Skill` tool with this input schema:

```typescript
{
  "name": "Skill",
  "description": "Execute a skill...",
  "input_schema": {
    "type": "object",
    "properties": {
      "command": {
        "type": "string",
        "description": "The skill name (no arguments). E.g., \"pdf\" or \"xlsx\""
      }
    },
    "required": ["command"]
  }
}
```

**Key Points:**
- Parameter name is `command`, NOT `skill`
- Only accepts skill name (no additional arguments)
- Skill name must match the `name` field in SKILL.md frontmatter

### Available Skills Section

The tool description contains an embedded `<available_skills>` section:

```xml
<available_skills>
<skill>
<name>skill-name</name>
<description>Brief description from SKILL.md frontmatter</description>
<location>user|project</location>
</skill>
</available_skills>
```

Claude uses this to determine which skills exist and when to invoke them.

---

## Invocation Syntax

### Correct Invocation

**Simple name:**
```
Skill(command: "skill-name")
```

**Fully qualified name:**
```
Skill(command: "namespace:skill-name")
```

**Examples:**
```python
# Invoke codebase-analysis skill
Skill(command: "codebase-analysis")

# Invoke lint-check skill
Skill(command: "lint-check")

# Invoke bazinga-db skill
Skill(command: "bazinga-db")

# Fully qualified (if namespace exists)
Skill(command: "ms-office-suite:pdf")
```

### Common Mistakes

**❌ WRONG:**
```python
Skill(skill: "codebase-analysis")     # Wrong parameter name
Skill(name: "lint-check")             # Wrong parameter name
Skill("api-validation")               # Missing parameter name
Skill(command: "lint-check", args="--strict")  # No args parameter exists
```

**✅ CORRECT:**
```python
Skill(command: "codebase-analysis")   # Correct
Skill(command: "lint-check")          # Correct
Skill(command: "api-validation")      # Correct
```

### Detection

To verify correct syntax in agent files:

```bash
# Find all Skill invocations
grep "Skill(" agents/*.md

# Should all show "Skill(command:"
# If you see "Skill(skill:" or "Skill(name:", that's a bug
```

---

## Runtime Behavior

### Invocation Flow

1. **Claude decides to invoke skill** (based on description in `<available_skills>`)
2. **Tool call:** `Skill(command: "skill-name")`
3. **System responds with:**
   - `tool_result` confirmation
   - Command message: `"skill-name is running..."`
   - Base path: `/path/to/.claude/skills/skill-name/`
   - SKILL.md body content (without frontmatter)
4. **Claude reads instructions** from SKILL.md body
5. **Claude executes workflow** described in SKILL.md
6. **Claude returns result** to caller

### Key Behaviors

**Inline execution:**
- Skills run within the main conversation
- No separate process or sub-agent spawned
- Skill instance is just Claude reading different instructions

**Context preservation:**
- Conversation history visible to skill
- Can reference earlier messages
- State maintained across skill execution

**Tool availability:**
- Skill has access to tools specified in `allowed-tools` frontmatter
- Can call Bash, Read, Edit, etc. (if allowed)
- Can invoke other skills if needed

**Output:**
- Skills typically write to files (reports, artifacts)
- Return summary to caller via text response
- Full details saved to output file for later reading

---

## Best Practices

### Design Principles

1. **Self-contained:** Skills should be independent modules
2. **Script-based:** Complex logic goes in scripts, not SKILL.md
3. **Clear interface:** Well-defined inputs/outputs
4. **Documented:** Include usage examples
5. **Versioned:** Use semantic versioning
6. **Focused:** One clear purpose per skill

### Directory Organization

**For simple skills:**
```
skill-name/
├── SKILL.md
└── scripts/
    └── main.py
```

**For complex skills:**
```
skill-name/
├── SKILL.md
├── scripts/
│   ├── main_logic.py
│   ├── helper.py
│   └── validator.sh
├── resources/
│   ├── template.json
│   └── config.yaml
└── references/
    └── usage.md        # Detailed docs for humans
```

### SKILL.md Length Guidelines

| Lines | Assessment | Action |
|-------|------------|--------|
| <100 | Too brief | Add examples and details |
| 100-150 | Good | Optimal length |
| 150-250 | Acceptable | Consider moving content to references/ |
| >250 | Too verbose | Must move content to references/ |

**Comparison with BAZINGA skills:**
- `codebase-analysis`: 88 lines ✅
- `bazinga-db`: ~120 lines ✅
- `lint-check`: ~110 lines ✅

### Script Invocation Pattern

**In SKILL.md:**
```markdown
### Step 1: Execute Analysis

```bash
python3 .claude/skills/skill-name/scripts/analyze.py \
  --input "$INPUT_FILE" \
  --output "$OUTPUT_FILE" \
  --session "$SESSION_ID"
```

### Step 2: Read Results

```bash
cat "$OUTPUT_FILE"
```

### Step 3: Return Summary

[Format and return findings to caller]
```

**Benefits:**
- Logic in scripts (testable, maintainable)
- Instructions in SKILL.md (clear workflow)
- Separation of concerns

### Cross-Platform Script Invocation

For skills that use shell/PowerShell wrapper scripts (not just Python), document both options:

**In SKILL.md:**
```markdown
## Step 1: Execute Script

Use the **Bash** tool to run the pre-built script.

**On Unix/macOS:**
```bash
bash .claude/skills/skill-name/scripts/script.sh
```

**On Windows (PowerShell):**
```powershell
pwsh .claude/skills/skill-name/scripts/script.ps1
```

> **Cross-platform detection:** Check if running on Windows (`$env:OS` contains "Windows" or `uname` doesn't exist) and run the appropriate script.
```

**File Structure:**
```
skill-name/
├── SKILL.md
└── scripts/
    ├── script.sh      # Unix/macOS version
    └── script.ps1     # Windows version
```

**Guidelines:**
- Both scripts must produce identical outputs
- Use `scripts/` subdirectory (not skill root)
- Scripts should be functionally equivalent
- CLI installs correct version based on platform selection

---

## Common Patterns

### Pattern 1: Analysis Skill

**Purpose:** Analyze codebase/data and generate report

**Structure:**
```
skill-name/
├── SKILL.md
└── scripts/
    ├── analyze.py      # Main analysis logic
    ├── parser.py       # Parse input
    └── reporter.py     # Format output
```

**SKILL.md workflow:**
1. Run analysis script
2. Read output file
3. Return summary

**Example:** `codebase-analysis`, `test-coverage`, `security-scan`

### Pattern 2: Validation Skill

**Purpose:** Validate code/config and report issues

**Structure:**
```
skill-name/
├── SKILL.md
├── scripts/
│   └── validate.py
└── resources/
    └── rules.yaml      # Validation rules
```

**SKILL.md workflow:**
1. Run validation script
2. Read validation report
3. Return issues found

**Example:** `lint-check`, `api-contract-validation`, `db-migration-check`

### Pattern 3: Database Skill

**Purpose:** Persist/retrieve orchestration state

**Structure:**
```
skill-name/
├── SKILL.md
└── scripts/
    ├── db_ops.py       # Database operations
    └── schema.sql      # Schema definition
```

**SKILL.md workflow:**
1. Parse request (save/get/update)
2. Execute database operation
3. Return success/data

**Example:** `bazinga-db`

### Pattern 4: Reporting Skill

**Purpose:** Aggregate metrics and generate dashboard

**Structure:**
```
skill-name/
├── SKILL.md
├── scripts/
│   ├── collect.py
│   └── visualize.py
└── resources/
    └── dashboard.html
```

**SKILL.md workflow:**
1. Collect metrics
2. Generate visualizations
3. Write dashboard file
4. Return summary

**Example:** `quality-dashboard`, `velocity-tracker`

---

## Troubleshooting

### Issue: Skill Not Found

**Symptoms:**
- Error: "Skill 'skill-name' not found"
- Skill not appearing in `<available_skills>`

**Causes:**
- SKILL.md missing or misnamed
- Frontmatter `name` doesn't match directory name
- Directory not in `.claude/skills/`

**Solution:**
```bash
# Verify structure
ls -la .claude/skills/skill-name/SKILL.md

# Check frontmatter name
grep "^name:" .claude/skills/skill-name/SKILL.md
```

### Issue: Skill Invocation Fails

**Symptoms:**
- Tool call doesn't execute
- No response from skill

**Causes:**
- Wrong parameter name (using `skill:` instead of `command:`)
- Skill name typo
- Skill already running (can't invoke twice)

**Solution:**
```bash
# Verify invocation syntax
grep "Skill(" agents/your-agent.md

# Should see: Skill(command: "...")
# NOT: Skill(skill: "...")
```

### Issue: Script Not Found

**Symptoms:**
- Bash error: "No such file or directory"
- Python error: "ModuleNotFoundError"

**Causes:**
- Incorrect path in SKILL.md
- Script not executable
- Working directory assumption wrong

**Solution:**
```markdown
# Always use absolute path from skill root
python3 .claude/skills/skill-name/scripts/analyze.py

# NOT relative:
python3 scripts/analyze.py  # May fail depending on CWD
```

### Issue: Skill Too Verbose

**Symptoms:**
- SKILL.md >250 lines
- Takes long time to load
- Difficult to maintain

**Solution:**
1. Move detailed documentation to `references/usage.md`
2. Keep only actionable instructions in SKILL.md
3. Reference the documentation file at end of SKILL.md

**Example:**
```markdown
---

**For detailed documentation:** `.claude/skills/skill-name/references/usage.md`
```

---

## Examples

### Example 1: Simple Analysis Skill

**Directory:** `.claude/skills/file-counter/`

**SKILL.md:**
```markdown
---
version: 1.0.0
name: file-counter
description: Count files by type and generate report
author: BAZINGA Team
allowed-tools: [Bash, Read]
---

# File Counter Skill

You are the file-counter skill. Count files by extension and report statistics.

## When to Invoke This Skill

- Need to understand codebase file distribution
- Planning refactoring or migration
- Generating project metrics

## Your Task

### Step 1: Run Analysis

```bash
python3 .claude/skills/file-counter/scripts/count.py \
  --output bazinga/file_counts.json
```

### Step 2: Read Results

```bash
cat bazinga/file_counts.json
```

### Step 3: Return Summary

Report:
- Total files by extension
- Largest file types
- Any unusual patterns

Example: "Found 234 Python files (.py), 156 JavaScript files (.js), 89 Markdown files (.md)"
```

### Example 2: Validation Skill

**Directory:** `.claude/skills/json-validator/`

**SKILL.md:**
```markdown
---
version: 1.0.0
name: json-validator
description: Validate JSON files against schemas
author: BAZINGA Team
allowed-tools: [Bash, Read]
---

# JSON Validator Skill

You are the json-validator skill. Validate JSON files and report errors.

## When to Invoke This Skill

- Before committing JSON configuration changes
- When modifying API contracts
- Debugging JSON parse errors

## Your Task

### Step 1: Run Validation

```bash
python3 .claude/skills/json-validator/scripts/validate.py \
  --file "$TARGET_FILE" \
  --schema "$SCHEMA_FILE" \
  --output bazinga/validation_report.json
```

### Step 2: Check Results

```bash
cat bazinga/validation_report.json | jq '.errors | length'
```

### Step 3: Return Report

If errors > 0:
- List each error with line number
- Show expected vs actual format
- Suggest fixes

If errors == 0:
- Confirm validation passed
- Report file size and structure
```

---

## Reference: BAZINGA Skill Comparison

### Well-Structured Skills in This Project

| Skill | Lines | Structure | Notes |
|-------|-------|-----------|-------|
| `codebase-analysis` | 88 | Perfect ✅ | Moved verbose content to references/ |
| `bazinga-db` | ~120 | Good ✅ | Focused on DB operations |
| `lint-check` | ~110 | Good ✅ | Clear workflow |
| `security-scan` | ~264 | Acceptable ✅ | Dual-mode (basic/advanced) |
| `test-coverage` | ~140 | Good ✅ | Cross-platform support |
| `api-contract-validation` | ~95 | Good ✅ | Well-documented |

### Lessons from BAZINGA

1. **Template vs. runtime context:**
   - Use `"template": true` flag for unprocessed templates
   - Use `"fallback": true` flag for emergency minimal contexts
   - Check both flags in developer workflow

2. **Session isolation:**
   - Output files: Session-isolated (`bazinga/artifacts/{session}/skills/`)
   - Cache: Global with session-keyed names (for cross-session benefits)

3. **Parameter naming:**
   - Always use `command` parameter for Skill tool
   - Bug introduced when using `skill` parameter (commit c05ee0e)
   - Verify with: `grep "Skill(" agents/*.md`

4. **Documentation separation:**
   - SKILL.md: Instructions for skill instance (<100 lines ideal)
   - references/usage.md: Documentation for humans (any length)

5. **Dual-mode pattern:**
   - Implement only when time savings >20 seconds
   - Control via environment variable (`SECURITY_SCAN_MODE`)
   - Example: security-scan (basic: 5-10s, advanced: 30-60s)
   - Progressive escalation: revision 0-1 → basic, revision 2+ → advanced

6. **Hybrid invocation approach:**
   - Permanent instructions in agent file (prevents memory drift)
   - Dynamic MANDATORY injection by orchestrator (prevents skipping)
   - Pattern: `read(agent_file) + append(mandatory_instructions) + spawn()`

### BAZINGA-Specific Implementation History

For detailed implementation history, architectural decisions, and lessons learned from specific skills:

**See:** `research/skills-implementation-summary.md`

Contains:
- Implementation details of security-scan, test-coverage, lint-check
- Hybrid invocation approach rationale
- Progressive analysis ladder
- Dual-mode evaluation and decisions
- Cross-platform support patterns
- Future enhancement proposals

---

## Skill Creation Checklist

Before committing a new skill:

- [ ] Directory in `.claude/skills/skill-name/`
- [ ] SKILL.md exists with required frontmatter
- [ ] `version` field present (semantic versioning)
- [ ] `name` matches directory name
- [ ] `description` clear and concise
- [ ] "When to Invoke" section included
- [ ] "Your Task" workflow with concrete steps
- [ ] Example invocation scenarios
- [ ] Scripts in `scripts/` subdirectory (if applicable)
- [ ] SKILL.md length reasonable (<250 lines)
- [ ] Verbose content moved to `references/` (if needed)
- [ ] All Skill invocations use `command` parameter
- [ ] Tested invocation from relevant agent
- [ ] Documentation updated (this guide if needed)

---

## Updates and Maintenance

**When to update this guide:**
- New skill patterns discovered
- Claude Code tool definition changes
- Best practices evolve
- Common issues identified

**Version history:**
- v1.0.0 (2025-11-19): Initial comprehensive guide based on Mikhail Shilkov's deep-dive + BAZINGA experience

**Maintained by:** BAZINGA Team

**Related documents:**
- `research/skill-fix-manual.md` - Step-by-step fixing guide for broken skills
- `research/skill-parameter-verification.md` - Investigation of command vs skill parameter
- `.claude/skills/codebase-analysis/references/usage.md` - Example of references/ pattern

---

**This is the single source of truth for skill implementation in this project. Always consult this guide before creating, updating, or invoking skills.**
