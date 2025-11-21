# Claude Code Skill Fix Manual

**Version:** 1.0
**Date:** November 2025
**Author:** Claude (Sonnet 4.5)
**Purpose:** Comprehensive guide to fix Claude Code skills that are written as documentation instead of executable instructions

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Root Cause Analysis](#root-cause-analysis)
3. [The Correct Pattern](#the-correct-pattern)
4. [Required Components](#required-components)
5. [Step-by-Step Fix Process](#step-by-step-fix-process)
6. [Before/After Examples](#beforeafter-examples)
7. [Validation Process](#validation-process)
8. [Common Pitfalls](#common-pitfalls)
9. [Fix Checklist](#fix-checklist)

---

## Problem Statement

### Symptoms

When you encounter a Claude Code skill with these characteristics, it needs to be fixed:

- ❌ **Documentation style:** Written as a user manual or reference guide
- ❌ **Shows raw commands:** Contains bash/python command examples for humans to copy-paste
- ❌ **Missing version:** No `version` field in YAML frontmatter
- ❌ **No invocation guidance:** No "When to Invoke" section
- ❌ **No examples:** No concrete scenarios showing expected input/output
- ❌ **Too long:** Often 300-500+ lines of detailed implementation logic
- ❌ **Wrong framing:** Says "This skill does X" instead of "You are the X skill"

### Example of Broken Pattern

```markdown
---
name: test-coverage
description: "Run coverage analysis"
allowed-tools: [Bash, Read, Write]
---

# Test Coverage Skill

## How to Use

### Step 1: Detect Language

Check for these files:
- Python: requirements.txt, pyproject.toml
- JavaScript: package.json

### Step 2: Run Coverage

**For Python:**
```bash
pytest --cov=. --cov-report=json
```

**For JavaScript:**
```bash
npm test -- --coverage
```
```

**Problem:** This is a manual showing bash commands, not instructions for the skill instance to execute autonomously.

---

## Root Cause Analysis

### How Skills Actually Work

1. **Skills are Claude instances** - When invoked, a new Claude instance runs with the SKILL.md as its instructions
2. **They have allowed-tools** - The skill can only use tools specified in `allowed-tools` (e.g., Bash, Read, Write)
3. **They execute autonomously** - The skill reads SKILL.md and executes the instructions using its allowed tools
4. **They return results** - The skill returns a message to the calling agent (PM, Tech Lead, Developer, etc.)

### The Misunderstanding

**WRONG:** SKILL.md is documentation for OTHER agents showing them what bash commands to run

**CORRECT:** SKILL.md contains instructions FOR the skill instance on how to execute its task using its allowed tools

### The Key Insight

Most skills already have **pre-built scripts** (bash, python) in their directory that contain all the implementation logic (260-446 lines). The SKILL.md should simply instruct the skill instance to:

1. Call the existing script
2. Read the generated report
3. Return a summary

---

## The Correct Pattern

### Structure Overview

```markdown
---
name: skill-name
description: "What the skill does and when to use it"
version: 1.0.0
allowed-tools: [Bash, Read]
---

# Skill Name Skill

You are the skill-name skill. [Brief description of purpose]

## When to Invoke This Skill

**Invoke this skill when:**
- [Condition 1]
- [Condition 2]

**Do NOT invoke when:**
- [Exclusion 1]
- [Exclusion 2]

---

## Your Task

When invoked:
1. Execute the [skill-name] script
2. Read the generated report
3. Return a summary to the calling agent

---

## Step 1: Execute Script

Use the **Bash** tool to run the pre-built script:

```bash
bash .claude/skills/skill-name/script-name.sh
# OR
python3 .claude/skills/skill-name/script-name.py
```

This script will:
- [What it does - bullet points]
- Generate `bazinga/output-file.json`

---

## Step 2: Read Generated Report

Use the **Read** tool to read:

```bash
bazinga/output-file.json
```

Extract key information:
- `field1` - Description
- `field2` - Description

---

## Step 3: Return Summary

Return a concise summary to the calling agent:

```
[Expected output format]
```

---

## Example Invocation

**Scenario 1: [Description]**

Input: [What triggered the skill]

Expected output:
```
[Actual output example]
```

**Scenario 2: [Another scenario]**

Input: [What triggered the skill]

Expected output:
```
[Actual output example]
```

---

## Error Handling

**If [error condition]:**
- [What to do]

---

## Notes

- [Additional context]
- [Script details]
```

### Key Characteristics

- **Length:** 150-250 lines (down from 300-500+)
- **Focus:** Calling scripts, not implementing logic
- **Framing:** "You are the X skill" (instructions FOR the skill)
- **Tools:** Usually just `[Bash, Read]` (scripts handle everything)
- **Examples:** Concrete scenarios with expected output
- **Version:** Always include `version: 1.0.0`

---

## Required Components

### 1. YAML Frontmatter

```yaml
---
name: skill-name              # Required: lowercase-with-hyphens, max 64 chars
description: "Brief desc"      # Required: max 1024 chars, describes when to use
version: 1.0.0                # Required: semantic versioning
allowed-tools: [Bash, Read]   # Required: tools the skill can use
---
```

**Allowed YAML fields:**
- `name` (required)
- `description` (required)
- `version` (optional but recommended)
- `allowed-tools` (required)
- `license` (optional)
- `metadata` (optional)
- `dependencies` (optional)

### 2. "When to Invoke" Section

```markdown
## When to Invoke This Skill

**Invoke this skill when:**
- [Specific condition 1]
- [Specific condition 2]
- [Specific condition 3]

**Do NOT invoke when:**
- [Exclusion condition 1]
- [Exclusion condition 2]
```

**Purpose:** Helps Claude (the calling agent) decide when to use this skill.

**Tips:**
- Be specific about triggers
- Include both positive (when to use) and negative (when NOT to use) conditions
- Think about the agent's context (PM, Tech Lead, Developer)

### 3. Example Invocation Scenarios

```markdown
## Example Invocation

**Scenario 1: [Realistic scenario name]**

Input: [What the calling agent said or did]

Expected output:
```
[Exact output the skill should return]
```
```

**Why this matters:**
- Shows the skill what success looks like
- Helps Claude understand expected behavior
- Provides concrete examples vs abstract instructions

**Best practices:**
- Include 2-3 scenarios
- Show both success and failure cases
- Use realistic data (not placeholder text)
- Show exact output format

### 4. Script Location

The skill should call scripts in its own directory:

```bash
# Bash script
bash .claude/skills/skill-name/script-name.sh

# Python script
python3 .claude/skills/skill-name/script-name.py
```

**Check the skill directory first:**

```bash
ls -la .claude/skills/skill-name/
```

Common script names:
- `coverage.sh` / `coverage.ps1` (test-coverage)
- `scan.sh` / `scan.ps1` (security-scan)
- `lint.sh` / `lint.ps1` (lint-check)
- `check.py` (db-migration-check)
- `analyze.py` (codebase-analysis)

---

## Step-by-Step Fix Process

### Step 1: Read Current SKILL.md

```bash
Read: .claude/skills/skill-name/SKILL.md
```

**Identify:**
1. What scripts exist in the skill directory
2. Current description in YAML frontmatter
3. What the skill is supposed to do
4. What output file it generates

### Step 2: Check for Existing Scripts

```bash
ls -la .claude/skills/skill-name/
```

**Look for:**
- `.sh` files (bash scripts for Linux/Mac)
- `.ps1` files (PowerShell scripts for Windows)
- `.py` files (Python scripts)

**Check script size:**

```bash
wc -l .claude/skills/skill-name/*.sh
```

Large scripts (200+ lines) indicate the implementation logic is already there.

### Step 3: Test the Script (Optional)

```bash
bash .claude/skills/skill-name/script-name.sh --help
# OR
python3 .claude/skills/skill-name/script-name.py --help
```

**Check:**
- What parameters it needs
- What output file it generates
- Where it writes the output (usually `bazinga/`)

### Step 4: Create "When to Invoke" Section

**Think about:**
- Who calls this skill? (PM, Tech Lead, Developer, Orchestrator)
- What triggers its invocation? (code review, deployment, testing)
- When should it NOT be invoked? (emergencies, no data available)

**Template:**

```markdown
## When to Invoke This Skill

**Invoke this skill when:**
- [Primary use case]
- [Secondary use case]
- [Tertiary use case]

**Do NOT invoke when:**
- [Exclusion 1]
- [Exclusion 2]
```

### Step 5: Write Example Scenarios

**Create 2-3 realistic scenarios:**

1. **Success scenario** - Everything works as expected
2. **Edge case scenario** - Partial results, warnings
3. **Error scenario** - What happens when it fails

**Template:**

```markdown
## Example Invocation

**Scenario 1: [Descriptive Name]**

Input: [What triggered the skill - be specific]

Expected output:
```
[Actual output the skill should produce]
```

**Scenario 2: [Another Scenario]**

Input: [Different trigger]

Expected output:
```
[Different output]
```
```

### Step 6: Write the New SKILL.md

Use this template:

```markdown
---
name: skill-name
description: "[Copy from current SKILL.md description]"
version: 1.0.0
allowed-tools: [Bash, Read]
---

# [Skill Name] Skill

You are the [skill-name] skill. When invoked, you [brief description].

## When to Invoke This Skill

**Invoke this skill when:**
- [Condition 1]
- [Condition 2]

**Do NOT invoke when:**
- [Exclusion 1]
- [Exclusion 2]

---

## Your Task

When invoked:
1. Execute the [script-name] script
2. Read the generated report
3. Return a summary to the calling agent

---

## Step 1: Execute [Script Type] Script

Use the **Bash** tool to run the pre-built script:

```bash
bash .claude/skills/skill-name/script-name.sh
# OR
python3 .claude/skills/skill-name/script-name.py [--args if needed]
```

This script will:
- [What it does - list key operations]
- Generate `bazinga/output-file.json`

---

## Step 2: Read Generated Report

Use the **Read** tool to read:

```bash
bazinga/output-file.json
```

Extract key information:
- `field1` - What it contains
- `field2` - What it contains
- `field3` - What it contains

---

## Step 3: Return Summary

Return a concise summary to the calling agent:

```
[Expected Summary Format]
- Key metric 1: {value}
- Key metric 2: {value}

{If issues found:}
Issues:
- {issue 1}
- {issue 2}

Details saved to: bazinga/output-file.json
```

---

## Example Invocation

**Scenario 1: [Realistic Scenario Name]**

Input: [What triggered it]

Expected output:
```
[Exact output]
```

**Scenario 2: [Another Scenario]**

Input: [What triggered it]

Expected output:
```
[Exact output]
```

---

## Error Handling

**If [error condition]:**
- [What to do]
- [How to fix]

**If [another error]:**
- [What to do]
- [How to fix]

---

## Notes

- The script handles all [implementation detail]
- Supports both bash (Linux/Mac) and PowerShell (Windows)
- [Any other relevant context]
```

### Step 7: Validate the Fixed Skill

```bash
python3 scripts/validate_skills.py
```

**Check for:**
- ✅ All required YAML fields present
- ✅ Description under 1024 characters
- ✅ Name is lowercase with hyphens
- ✅ No unexpected YAML properties

### Step 8: Commit the Fix

```bash
git add .claude/skills/skill-name/SKILL.md
git commit -m "feat(skills): Rewrite [skill-name] to use existing scripts + add metadata

Changes:
- Added version: 1.0.0
- Added 'When to Invoke' section
- Added example invocation scenarios
- Simplified to 3 steps: execute script → read report → return summary
- Removed detailed implementation logic (now in scripts)
- Reduced allowed-tools to [Bash, Read]

All validation passing ✅"
```

---

## Before/After Examples

### Example 1: test-coverage

**BEFORE (Wrong - 231 lines):**

```markdown
---
name: test-coverage
description: "Generate test coverage reports..."
allowed-tools: [Bash, Read, Write]
---

# Test Coverage Analysis Skill

You are the test-coverage skill...

## Step 1: Detect Project Language

Use the **Read** tool to check for language indicators:

**Python:**
- Check for: `requirements.txt`, `pyproject.toml`...

**JavaScript:**
- Check for: `package.json`...

## Step 2: Run Coverage Analysis

### For Python:
```bash
pytest --cov=. --cov-report=json --cov-report=term-missing
```

### For JavaScript:
```bash
npm test -- --coverage --coverageReporters=json
```

[... 200 more lines of detailed implementation ...]
```

**AFTER (Correct - 143 lines):**

```markdown
---
name: test-coverage
description: "Generate test coverage reports..."
version: 1.0.0
allowed-tools: [Bash, Read]
---

# Test Coverage Analysis Skill

You are the test-coverage skill...

## When to Invoke This Skill

**Invoke this skill when:**
- Tech Lead is reviewing test files
- Before approving code changes or pull requests
- Developer claims "added tests"

**Do NOT invoke when:**
- No tests exist in the project
- Just viewing code (not reviewing for approval)

---

## Your Task

When invoked:
1. Execute the test coverage script
2. Read the generated coverage report
3. Return a summary to the calling agent

---

## Step 1: Execute Coverage Script

Use the **Bash** tool to run the pre-built coverage script:

```bash
bash .claude/skills/test-coverage/coverage.sh
```

This script will:
- Detect project language (Python, JavaScript, Go, Java)
- Auto-install required tools if needed
- Run coverage analysis
- Generate `bazinga/coverage_report.json`

---

## Step 2: Read Generated Report

Use the **Read** tool to read:

```bash
bazinga/coverage_report.json
```

Extract key information:
- `overall_coverage` - Total line coverage percentage
- `files_below_threshold` - Files with coverage < 80%

---

## Step 3: Return Summary

Return a concise summary:

```
Test Coverage Report:
- Overall coverage: {percentage}%
- Files below 80% threshold: {count}

Details saved to: bazinga/coverage_report.json
```

---

## Example Invocation

**Scenario: Reviewing PR with New Tests**

Input: Tech Lead reviewing PR #123 with new auth tests

Expected output:
```
Test Coverage Report:
- Overall coverage: 78%
- Files below 80% threshold: 2 files
- Critical areas with low coverage:
  - auth.py: 68% coverage
  - payment.py: 52% coverage

Details saved to: bazinga/coverage_report.json
```

---

## Error Handling

**If coverage tool not installed:**
- Script attempts auto-installation
- Falls back gracefully if installation fails

---

## Notes

- The script (260+ lines) handles all language detection
- Supports both bash (Linux/Mac) and PowerShell (Windows)
```

**Changes:**
- ✅ Reduced from 231 → 143 lines (38% reduction)
- ✅ Added `version: 1.0.0`
- ✅ Added "When to Invoke" section
- ✅ Added example invocation scenario
- ✅ Calls existing `coverage.sh` script instead of showing bash commands
- ✅ Reduced `allowed-tools` from `[Bash, Read, Write]` → `[Bash, Read]`

---

### Example 2: security-scan

**BEFORE (Wrong - 210 lines):**

Shows detailed instructions for running bandit, npm audit, gosec for each language with specific command-line flags.

**AFTER (Correct - 168 lines):**

Calls `scan.sh` script (446 lines), focuses on when to invoke, example scenarios, and return format.

**Key improvements:**
- ✅ Script handles all tool selection and execution
- ✅ Clear "When to Invoke" guidance
- ✅ Two example scenarios (basic mode, advanced mode)
- ✅ Reduced complexity by 20%

---

## Validation Process

### Automated Validation

Use the validation script:

```bash
python3 scripts/validate_skills.py
```

This checks:
- ✅ YAML frontmatter is valid
- ✅ Required fields present (`name`, `description`)
- ✅ No unexpected properties
- ✅ Name format (lowercase, hyphens, max 64 chars)
- ✅ Description length (max 1024 chars)
- ✅ allowed-tools contains valid tools

### Manual Checks

**Read the SKILL.md and verify:**

1. **Framing:** Does it say "You are the X skill"? ✅
2. **Script calling:** Does it call existing scripts instead of showing bash commands? ✅
3. **When to Invoke:** Does it have clear invocation guidance? ✅
4. **Examples:** Does it have 2-3 concrete scenarios? ✅
5. **Length:** Is it under 250 lines? ✅
6. **Version:** Does it have `version: 1.0.0`? ✅
7. **Tools:** Are allowed-tools minimal (usually `[Bash, Read]`)? ✅

### Test the Skill (Optional)

You can test manually by invoking it:

```bash
# Create a test scenario
cd /path/to/project

# Call the script directly to verify it works
bash .claude/skills/skill-name/script-name.sh

# Check the output
cat bazinga/output-file.json
```

---

## Common Pitfalls

### Pitfall 1: Including Implementation Logic

**WRONG:**
```markdown
## Step 2: Run Coverage

For Python, first check if pytest-cov is installed:
```bash
pip list | grep pytest-cov
```

If not installed, install it:
```bash
pip install pytest-cov
```

Then run coverage:
```bash
pytest --cov=. --cov-report=json
```
```

**RIGHT:**
```markdown
## Step 1: Execute Coverage Script

Use the **Bash** tool:

```bash
bash .claude/skills/test-coverage/coverage.sh
```

This script will:
- Detect language
- Install tools if needed
- Run coverage
- Generate report
```

### Pitfall 2: Forgetting "When to Invoke"

**WRONG:** Jump straight to instructions without context

**RIGHT:** Always include "When to Invoke This Skill" section so Claude knows when to use it

### Pitfall 3: No Example Scenarios

**WRONG:** Abstract descriptions without concrete examples

**RIGHT:** Show 2-3 realistic scenarios with exact expected output

### Pitfall 4: Wrong Framing

**WRONG:** "This skill provides coverage analysis..."

**RIGHT:** "You are the test-coverage skill. When invoked, you run coverage analysis..."

### Pitfall 5: Too Many allowed-tools

**WRONG:** `allowed-tools: [Bash, Read, Write, Grep, Edit]`

**RIGHT:** `allowed-tools: [Bash, Read]` (let the script do the work)

### Pitfall 6: Missing Version

**WRONG:** No `version` in YAML frontmatter

**RIGHT:** Always include `version: 1.0.0`

---

## Fix Checklist

Use this checklist when fixing a skill:

### Pre-Fix
- [ ] Read current SKILL.md completely
- [ ] List all scripts in skill directory
- [ ] Check script sizes (indicate complexity)
- [ ] Identify what output file the skill generates
- [ ] Note current description in YAML

### YAML Frontmatter
- [ ] `name` is present and valid (lowercase-hyphens, max 64 chars)
- [ ] `description` is present and under 1024 chars
- [ ] Added `version: 1.0.0`
- [ ] `allowed-tools` is minimal (usually `[Bash, Read]`)
- [ ] No unexpected YAML properties

### Structure
- [ ] Starts with "You are the X skill" framing
- [ ] Has "When to Invoke This Skill" section
- [ ] Has "Your Task" overview (3 steps)
- [ ] Step 1: Execute script (shows bash command to call script)
- [ ] Step 2: Read report (shows coordination file to read)
- [ ] Step 3: Return summary (shows expected format)
- [ ] Has "Example Invocation" section with 2-3 scenarios
- [ ] Has "Error Handling" section
- [ ] Has "Notes" section
- [ ] Total length < 250 lines

### Content Quality
- [ ] Calls existing scripts (not raw bash commands)
- [ ] Shows what the script does (bulleted list)
- [ ] Shows what fields to extract from report
- [ ] Shows expected summary format
- [ ] Example scenarios use realistic data
- [ ] Example scenarios show exact expected output
- [ ] "When to Invoke" has 3+ invoke conditions
- [ ] "When to Invoke" has 2+ exclusion conditions

### Validation
- [ ] Run `python3 scripts/validate_skills.py` - all pass
- [ ] Manual review of SKILL.md structure
- [ ] Length reduction achieved (ideally 30-50% shorter)
- [ ] Script is called in Step 1 (not raw commands)

### Commit
- [ ] Git add changed SKILL.md
- [ ] Commit with descriptive message
- [ ] Include version bump in commit message
- [ ] Push to remote

---

## Summary

**The fundamental principle:**

> **Skills are Claude instances that execute instructions autonomously using their allowed tools.**
>
> **SKILL.md should contain instructions FOR the skill, not documentation ABOUT the skill.**

**The three-step pattern:**

1. **Execute script** (using Bash tool)
2. **Read report** (using Read tool)
3. **Return summary** (formatted output)

**Required additions:**

- `version: 1.0.0` in YAML
- "When to Invoke" section
- Example invocation scenarios

**Key insight:**

Most skills already have battle-tested scripts (200-500 lines) in their directory. The SKILL.md should simply instruct the skill instance to call these scripts, not duplicate their implementation logic.

---

## Reference

**Official Documentation:**
- https://docs.claude.com/en/docs/claude-code/skills
- https://support.claude.com/en/articles/12512198-how-to-create-custom-skills

**Allowed YAML Properties:**
- `name` (required)
- `description` (required)
- `version` (optional)
- `allowed-tools` (required)
- `license` (optional)
- `metadata` (optional)
- `dependencies` (optional)

**Common allowed-tools:**
- `Bash` - Execute bash commands
- `Read` - Read files
- `Write` - Write files
- `Grep` - Search in files
- `Edit` - Edit files
- `Glob` - Find files by pattern

**Typical skill structure:**
```
.claude/skills/skill-name/
├── SKILL.md                 # Instructions FOR the skill
├── script-name.sh           # Implementation (bash)
├── script-name.ps1          # Implementation (PowerShell)
├── script-name.py           # Implementation (Python)
└── references/              # Optional reference docs
    ├── schema.md
    └── examples.md
```

---

**End of Manual**

*Use this manual to fix any Claude Code skill that follows the broken documentation pattern.*
