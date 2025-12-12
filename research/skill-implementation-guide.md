# Claude Code Skills: Complete Implementation Guide

**Version:** 2.0.0
**Date:** 2025-12-12
**Sources:**
- Mikhail Shilkov's Technical Deep-Dive (mikhail.io)
- Lee Han Chung's Skills Deep Dive (leehanchung.github.io)
- Official Claude Code Documentation (code.claude.com/docs/en/skills)
- BAZINGA Implementation Experience

**Purpose:** Single source of truth for creating, updating, and invoking skills

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [SKILL.md Format](#skillmd-format)
5. [Frontmatter Fields Reference](#frontmatter-fields-reference)
6. [Skill Tool Definition](#skill-tool-definition)
7. [Invocation Methods](#invocation-methods)
8. [Runtime Behavior & Execution Flow](#runtime-behavior--execution-flow)
9. [Discovery and Loading](#discovery-and-loading)
10. [Tool Permissions](#tool-permissions)
11. [Common Patterns](#common-patterns)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)
14. [Examples](#examples)
15. [Skill Creation Checklist](#skill-creation-checklist)
16. [BAZINGA-Specific Notes](#bazinga-specific-notes)

---

## Overview

### What Are Skills?

Skills are **prompt-based conversation and execution context modifiers** that extend Claude's capabilities through specialized instruction injection. They are NOT executable code—they expand into detailed prompts that prepare Claude to solve specific problem types.

**Key insight from Mikhail Shilkov:**
> "Skills aren't separate processes, sub-agents, or external tools: they're injected instructions that guide Claude's behavior within the main conversation."

### Key Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Model-invoked** | Claude autonomously decides when to use them (unlike slash commands which are user-invoked) |
| **Inline execution** | Run within the main conversation, not as separate processes |
| **On-demand loading** | Only loaded when invoked, keeping main prompt lean |
| **Project or user-scoped** | Can be machine-wide (`~/.claude/skills/`) or project-specific (`.claude/skills/`) |
| **Temporary modification** | Behavior only affects current interaction; conversation returns to normal after completion |

### Skills vs. Other Extensions

| Aspect | Skills | Slash Commands | MCP Servers |
|--------|--------|----------------|-------------|
| Invocation | Model decides | User types `/command` | Model calls tool |
| Execution | Prompt expansion | Prompt expansion | External process |
| Purpose | Guide workflows | Pre-defined prompts | New tools/resources |
| Return | Context modification | Direct execution | Tool results |

### What Skills Combine

- **Instructions** (SKILL.md) - What Claude reads when invoked
- **Scripts** - Executable code (Python, Bash, etc.) Claude can run
- **Resources** - Templates, data files, configurations
- **References** - Additional documentation for detailed guidance

---

## Architecture

### Three-Tier Information Disclosure

Skills use a progressive disclosure model:

1. **Frontmatter** (Tier 1) - Minimal metadata shown in skill list
   - Name, description, location
   - ~50-200 characters per skill

2. **SKILL.md Body** (Tier 2) - Full instructions loaded on invocation
   - Comprehensive but focused guidance
   - ~500-5,000 words

3. **Resources/References** (Tier 3) - Helper assets loaded on-demand
   - Scripts, templates, detailed docs
   - Any length

### Meta-Tool Architecture

Claude Code provides a `Skill` meta-tool that manages all individual skills. This tool:
- Appears in Claude's tools array alongside Read, Write, Bash, etc.
- Contains a dynamically-generated `<available_skills>` section
- Uses natural language understanding (not algorithmic matching) for skill selection

### Design Philosophy

> "What makes this design clever is that it achieves on-demand prompt expansion without modifying the core system prompt. Skills are executable knowledge packages that Claude loads only when needed, extending capabilities while keeping the main prompt lean." — Mikhail Shilkov

---

## Directory Structure

### Storage Locations

| Location | Scope | Use Case |
|----------|-------|----------|
| `~/.claude/skills/` | Personal | Available across all projects |
| `.claude/skills/` | Project | Checked into git, shared with team |
| Plugin-bundled | Plugin | Automatically available when plugin installed |

Skills load from these sources in order, with later sources able to override earlier ones.

### Standard Layout

```
.claude/skills/
├── skill-name/
│   ├── SKILL.md           # Required: Skill definition and instructions
│   ├── scripts/           # Optional: Executable scripts
│   │   ├── main_script.py
│   │   └── helper.sh
│   ├── resources/         # Optional: Templates and data (loaded into context)
│   │   ├── template.json
│   │   └── config.yaml
│   ├── references/        # Optional: Additional documentation (loaded into context)
│   │   └── usage.md
│   └── assets/            # Optional: Binary files (referenced by path only)
│       └── template.html
```

### Directory Purposes

| Directory | Purpose | Context Loaded? |
|-----------|---------|-----------------|
| `scripts/` | Executable code (Python, Bash) | No - executed via Bash tool |
| `resources/` | Templates, configs, schemas | Yes - via Read tool |
| `references/` | Detailed documentation | Yes - via Read tool |
| `assets/` | Binary files, images | No - referenced by path only |

### Naming Conventions

**Skill directory:**
- Use kebab-case: `codebase-analysis`, `lint-check`, `api-contract-validation`
- Lowercase letters, numbers, hyphens only
- Maximum 64 characters
- Be descriptive but concise

**SKILL.md:**
- Must be exactly `SKILL.md` (uppercase)
- Required in every skill directory
- No variations allowed

---

## SKILL.md Format

### Complete Structure

```markdown
---
name: skill-name
description: Brief description that tells Claude when to use this skill. Use when [trigger].
version: 1.0.0
author: Team/Person Name
tags: [category1, category2]
allowed-tools: [Bash, Read, Write]
---

# Skill Title

You are the skill-name skill. Your role is to [describe role].

## Overview

[1-2 sentence purpose statement]

## Prerequisites

[Dependencies, requirements, setup needed]

## When to Invoke This Skill

- Condition 1
- Condition 2
- Condition 3

## Your Task

When invoked, you must:

### Step 1: [Action]

[Detailed instructions with code blocks]

### Step 2: [Action]

[Detailed instructions]

### Step 3: [Action]

[Detailed instructions]

## Output Format

[Expected output structure]

## Error Handling

[How to handle failures]

## Example Invocation

[Concrete examples with input/output]

---

**For detailed documentation:** See references/usage.md
```

### Content Guidelines

**✅ DO:**
- Write instructions FOR the skill instance (second person: "You are...")
- Use imperative language ("Analyze code for...", "Extract text from...")
- Call existing scripts rather than implementing logic inline
- Include concrete examples with actual input/output
- Keep focused (under 500 lines for optimal performance, max 5,000 words)
- Use clear section headers
- Use `{baseDir}` for paths, never hardcode absolute paths
- Reference external files rather than embedding everything
- Provide step-by-step workflows

**❌ DON'T:**
- Write documentation ABOUT the skill (for humans)
- Show raw bash commands for humans to copy
- Include verbose implementation details
- Create skills without version numbers
- Skip "When to Invoke" section
- Mix documentation with instructions
- Exceed 5,000 words (context overflow risk)
- Hardcode absolute paths

**Remember:** SKILL.md is read BY the skill instance (Claude), not by humans. Write actionable instructions, not reference documentation.

---

## Frontmatter Fields Reference

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Identifier used to invoke the skill. Must match directory name. Lowercase letters, numbers, hyphens only. Max 64 chars. | `codebase-analysis` |
| `description` | Brief summary that tells Claude when to invoke. Primary selection signal. Include triggers! Max 1024 chars. | `"Analyze codebase patterns. Use when reviewing architecture."` |

### Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| `version` | Semantic version for tracking | `1.0.0` |
| `author` | Who created/maintains the skill | `BAZINGA Team` |
| `tags` | Categorization tags | `[analysis, security]` |
| `allowed-tools` | Tools skill can use without asking | `[Bash, Read, Write]` |
| `license` | License information | `MIT` |
| `model` | Override model selection | `claude-opus-4-20250514` or `inherit` |
| `disable-model-invocation` | Prevents automatic invocation; requires `/skill-name` | `true` |
| `mode` | Categorizes as mode command (special UI section) | `true` |

### Description Best Practices

The `description` field is **critical** for discoverability. Include BOTH:
1. What the skill does
2. When to use it (trigger terms)

**Good examples:**
```yaml
# ✅ Specific with trigger
description: "Extract text from PDFs, fill forms, merge documents. Use when working with PDF files."

# ✅ Clear purpose and trigger
description: "Analyze codebase for patterns, dependencies, and architecture. Use when reviewing code structure."

# ✅ Action-oriented
description: "Run security vulnerability scans on code changes. Use before approving PRs."
```

**Bad examples:**
```yaml
# ❌ Too vague
description: "Helps with documents"

# ❌ No trigger
description: "Processes files"

# ❌ Too generic
description: "For data analysis"
```

### Deprecated/Undocumented Fields

⚠️ **`when_to_use`**: Appears in some codebases but is **undocumented and potentially deprecated**. Rely on detailed `description` instead.

---

## Skill Tool Definition

### Tool Schema

Claude Code provides a `Skill` tool with this input schema:

```typescript
{
  "name": "Skill",
  "description": "Execute a skill within the main conversation...",
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

### Critical Points

| Point | Detail |
|-------|--------|
| Parameter name | `command` (NOT `skill` or `name`) |
| Parameter value | Skill name only, no arguments |
| Skill name | Must match `name` field in SKILL.md frontmatter |
| Namespace syntax | `namespace:skill-name` for fully qualified names |

### Available Skills Section

The tool description contains an embedded `<available_skills>` section, dynamically generated:

```xml
<available_skills>
<skill>
<name>codebase-analysis</name>
<description>Analyze codebase for patterns and architecture. Use when reviewing code.</description>
<location>project</location>
</skill>
<skill>
<name>pdf</name>
<description>Extract text from PDF documents. Use when processing PDFs.</description>
<location>user</location>
</skill>
</available_skills>
```

Claude reads this list and uses natural language understanding to match user intent—**there is no algorithmic skill selection at the code level**.

### Token Budget

The available skills list is subject to a **15,000-character token budget** by default. Keep descriptions concise to avoid truncation.

---

## Invocation Methods

### Automatic Invocation (Model-Invoked)

Claude reads skill descriptions in the Skill tool and autonomously invokes matching skills based on user intent.

**How it works:**
1. User makes a request
2. Claude reads available skills list
3. Claude decides if a skill matches the intent
4. Claude calls `Skill(command: "skill-name")`

### Manual Invocation

Users can explicitly invoke skills via:
- `/skill-name` syntax
- When `disable-model-invocation: true` is set

### Correct Invocation Syntax

**Simple name:**
```python
Skill(command: "skill-name")
```

**Fully qualified name (with namespace):**
```python
Skill(command: "ms-office-suite:pdf")
```

**Examples:**
```python
# Invoke codebase-analysis skill
Skill(command: "codebase-analysis")

# Invoke lint-check skill
Skill(command: "lint-check")

# Invoke bazinga-db skill
Skill(command: "bazinga-db")
```

### Common Mistakes

```python
# ❌ WRONG - Wrong parameter name
Skill(skill: "codebase-analysis")
Skill(name: "lint-check")

# ❌ WRONG - Missing parameter name
Skill("api-validation")

# ❌ WRONG - No args parameter exists
Skill(command: "lint-check", args="--strict")

# ✅ CORRECT
Skill(command: "codebase-analysis")
```

### Verification

To verify correct syntax in agent files:
```bash
# Find all Skill invocations
grep "Skill(" agents/*.md

# Should all show "Skill(command:"
# If you see "Skill(skill:" or "Skill(name:", that's a bug
```

---

## Runtime Behavior & Execution Flow

### Complete Invocation Flow

1. **User Request** - User asks something that matches a skill's purpose

2. **Claude Decision** - Claude reads `<available_skills>` and decides to invoke

3. **Tool Call** - Claude calls `Skill(command: "skill-name")`

4. **System Response** - The system returns:
   - `tool_result` confirmation
   - **Message 1** (`isMeta: false`): Metadata for user transparency
     - `<command-message>The "skill-name" skill is loading</command-message>`
   - **Message 2** (`isMeta: true`, hidden from UI): Full skill instructions
     - Base path: `/path/to/.claude/skills/skill-name/`
     - SKILL.md body content (without frontmatter)

5. **Execution** - Claude reads instructions and executes workflow

6. **Completion** - Claude returns result; context reverts to normal

### Dual-Channel Communication

Skills use the `isMeta` flag for dual-channel messaging:

| Channel | `isMeta` | Content | Purpose |
|---------|----------|---------|---------|
| User-visible | `false` | Minimal metadata (~50-200 chars) | Transparency |
| Claude-only | `true` | Full instructions (~500-5,000 words) | Guidance |

This separation prevents information overload in the UI while providing Claude with comprehensive instructions.

### Key Behaviors

**Inline execution:**
- Skills run within the main conversation
- No separate process or sub-agent spawned
- Skill instance is just Claude reading different instructions

**Context preservation:**
- Conversation history visible to skill
- Can reference earlier messages
- State maintained across skill execution

**Context modification (temporary):**
- Pre-approved tools in `allowed-tools` active during execution
- Model override active if specified
- **All modifications revert after skill completes**

**Output patterns:**
- Skills typically write to files (reports, artifacts)
- Return summary to caller via text response
- Full details saved to output file for later reading

---

## Discovery and Loading

### Discovery Process

Skills load from multiple sources (scanned in order):
1. User settings: `~/.claude/skills/`
2. Project settings: `.claude/skills/`
3. Plugin-provided skills
4. Built-in skills

The system **dynamically generates** the available skills list for each API request.

### Progressive Disclosure

Information reveals in stages:

1. **Initial**: Show only skill name and description (minimal context)
2. **Selection**: Load full SKILL.md after Claude/user chooses
3. **Execution**: Load helper assets, references, scripts on-demand

This prevents context bloat while maintaining discoverability.

### Viewing Available Skills

**Ask Claude:**
```
What Skills are available?
List all available Skills
```

**Inspect filesystem:**
```bash
ls ~/.claude/skills/
ls .claude/skills/
cat .claude/skills/my-skill/SKILL.md
```

---

## Tool Permissions

### The `allowed-tools` Field

Use `allowed-tools` to define which tools the skill can use **without user approval**:

```yaml
# File operations only
allowed-tools: [Read, Write, Edit, Glob, Grep]

# Read-only skill
allowed-tools: [Read, Grep, Glob]

# Multiple tools
allowed-tools: [Bash, Read, Write]
```

### Advanced: Command-Scoped Permissions

You can scope Bash permissions to specific commands:

```yaml
# Only git commands
allowed-tools: "Bash(git status:*),Bash(git diff:*),Read"

# Only npm commands
allowed-tools: "Bash(npm:*),Read,Write"
```

### Security Principle

**Principle of least privilege:** Only include tools your skill actually needs.

```yaml
# ✅ Good - minimal permissions for read-only skill
allowed-tools: [Read, Grep, Glob]

# ⚠️ Overpermissioned - only needs Read
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
```

### Permission Scoping

Tool permissions are **scoped to skill execution only**. When the skill completes, permissions revert to normal session defaults.

---

## Common Patterns

### Pattern 1: Script Automation

**Purpose:** Offload computational tasks to Python/Bash scripts

**Structure:**
```
skill-name/
├── SKILL.md
└── scripts/
    ├── analyze.py
    └── helper.sh
```

**SKILL.md pattern:**
```markdown
### Step 1: Execute Analysis

```bash
python3 .claude/skills/skill-name/scripts/analyze.py \
  --input "$INPUT_FILE" \
  --output "$OUTPUT_FILE"
```

### Step 2: Read Results

```bash
cat "$OUTPUT_FILE"
```
```

### Pattern 2: Read-Process-Write

**Purpose:** File transformation and data processing

**Flow:**
1. Read source file(s)
2. Process/transform content
3. Write output file(s)

### Pattern 3: Search-Analyze-Report

**Purpose:** Codebase analysis and pattern detection

**Flow:**
1. Search codebase (Grep, Glob)
2. Analyze findings
3. Generate report

**Examples:** `codebase-analysis`, `security-scan`

### Pattern 4: Validation

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

**Examples:** `lint-check`, `api-contract-validation`

### Pattern 5: Database Operations

**Purpose:** Persist/retrieve orchestration state

**Flow:**
1. Parse request (save/get/update)
2. Execute database operation
3. Return success/data

**Example:** `bazinga-db`

### Pattern 6: Template-Based Generation

**Purpose:** Create structured outputs from templates

**Structure:**
```
skill-name/
├── SKILL.md
└── assets/
    └── template.html
```

### Pattern 7: Wizard-Style Workflows

**Purpose:** Complex processes requiring user input

**Flow:**
1. Present options
2. Gather user choices
3. Execute based on selections

### Pattern 8: Context Aggregation

**Purpose:** Combining information from multiple sources

**Flow:**
1. Gather data from multiple files/APIs
2. Synthesize findings
3. Present unified view

### Pattern 9: Iterative Refinement

**Purpose:** Multiple analysis passes with increasing depth

**Flow:**
1. Initial quick scan
2. Deeper analysis of flagged items
3. Final detailed report

---

## Best Practices

### Design Principles

1. **Self-contained** - Skills should be independent modules
2. **Script-based** - Complex logic goes in scripts, not SKILL.md
3. **Clear interface** - Well-defined inputs/outputs
4. **Documented** - Include usage examples
5. **Versioned** - Use semantic versioning
6. **Focused** - One clear purpose per skill ("PDF form filling" not "Document processing")

### SKILL.md Length Guidelines

**Official guidance from [Claude Code Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):**

> "Keep SKILL.md body under **500 lines** for optimal performance."

This is a **soft guideline**, not a hard requirement. There is no mandatory length limit.

| Lines | Assessment | Action |
|-------|------------|--------|
| <100 | Brief | May need more examples/details for complex skills |
| 100-300 | Good | Well-balanced for most skills |
| 300-500 | Acceptable | Consider progressive disclosure if approaching 500 |
| >500 | Soft limit | Split content into separate files for optimal performance |

**Key principles:**
- Use **progressive disclosure** - SKILL.md acts as overview/table of contents
- Create supporting files (`reference.md`, `examples.md`) for detailed content
- Claude loads supporting files only when needed, maintaining token efficiency
- No hard limit exists; focus on organization over arbitrary line counts

**Maximum:** Keep under 5,000 words to avoid context overflow (model limit, not skill-specific).

### Directory Organization

**Simple skill:**
```
skill-name/
├── SKILL.md
└── scripts/
    └── main.py
```

**Complex skill:**
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
├── references/
│   └── usage.md        # Detailed docs
└── assets/
    └── report.html     # Binary/template files
```

### Script Invocation

**Always use full paths from skill root:**
```markdown
### Step 1: Execute Script

```bash
python3 .claude/skills/skill-name/scripts/analyze.py \
  --input "$INPUT" \
  --output "$OUTPUT"
```
```

**Never use relative paths:**
```bash
# ❌ May fail depending on CWD
python3 scripts/analyze.py

# ✅ Always works
python3 .claude/skills/skill-name/scripts/analyze.py
```

### Cross-Platform Scripts

For skills needing shell/PowerShell wrappers:

```
skill-name/
├── SKILL.md
└── scripts/
    ├── script.sh       # Unix/macOS
    └── script.ps1      # Windows
```

**In SKILL.md:**
```markdown
## Step 1: Execute Script

**On Unix/macOS:**
```bash
bash .claude/skills/skill-name/scripts/script.sh
```

**On Windows (PowerShell):**
```powershell
pwsh .claude/skills/skill-name/scripts/script.ps1
```
```

**Guidelines:**
- Both scripts must produce identical outputs
- Scripts should be functionally equivalent
- Test on both platforms when possible

### Team Sharing

1. Create project skill in `.claude/skills/`
2. Commit to git: `git add .claude/skills/`
3. Push to repository
4. Team members get skills after `git pull`

### Version History

Optionally track versions in SKILL.md:

```markdown
## Version History

- v2.0.0 (2025-10-01): Breaking changes to output format
- v1.1.0 (2025-09-15): Added validation step
- v1.0.0 (2025-09-01): Initial release
```

---

## Troubleshooting

### Issue: Skill Not Found

**Symptoms:**
- Error: "Skill 'skill-name' not found"
- Skill not appearing in `<available_skills>`

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| SKILL.md missing/misnamed | Check file exists: `ls .claude/skills/skill-name/SKILL.md` |
| Frontmatter `name` mismatch | Ensure `name:` matches directory name |
| Wrong directory location | Must be in `.claude/skills/` or `~/.claude/skills/` |
| Invalid YAML syntax | No tabs, correct indentation, valid structure |

**Diagnostic:**
```bash
# Verify structure
ls -la .claude/skills/skill-name/SKILL.md

# Check frontmatter name
grep "^name:" .claude/skills/skill-name/SKILL.md

# View debug info
claude --debug
```

### Issue: Skill Invocation Fails

**Symptoms:**
- Tool call doesn't execute
- No response from skill

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Wrong parameter name | Use `command:` not `skill:` or `name:` |
| Skill name typo | Check spelling matches frontmatter `name` |
| Skill already running | Can't invoke same skill twice simultaneously |

**Verification:**
```bash
# Check invocation syntax in code
grep "Skill(" agents/*.md

# Should see: Skill(command: "...")
# NOT: Skill(skill: "...")
```

### Issue: Claude Doesn't Auto-Invoke

**Symptoms:**
- Claude doesn't use skill when expected
- Must manually invoke with `/skill-name`

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Vague description | Add specific trigger terms: "Use when..." |
| Too generic | Make description more specific |
| Conflicts with other skills | Use distinct trigger terms |
| `disable-model-invocation: true` | Remove or change to `false` |

### Issue: Script Not Found

**Symptoms:**
- Bash error: "No such file or directory"
- Python error: "ModuleNotFoundError"

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Wrong path in SKILL.md | Use full path from skill root |
| Script not executable | `chmod +x scripts/*.py` |
| Wrong path separator | Use Unix-style: `scripts/helper.py` not `scripts\helper.py` |

**Always use:**
```bash
# ✅ Full path from skill root
python3 .claude/skills/skill-name/scripts/analyze.py

# ❌ Relative path (may fail)
python3 scripts/analyze.py
```

### Issue: Skill Too Verbose

**Symptoms:**
- SKILL.md >500 lines
- Takes long time to load
- Context overflow

**Solution:**
1. Move detailed documentation to `references/usage.md`
2. Keep only actionable instructions in SKILL.md
3. Reference the documentation file at end

```markdown
---

**For detailed documentation:** See `.claude/skills/skill-name/references/usage.md`
```

### Issue: Dependencies Missing

**Symptoms:**
- Import errors
- Command not found

**Solution:**
- Document dependencies in SKILL.md Prerequisites section
- Users must install via `pip`, `npm`, etc. in their environment

### Issue: Multiple Skills Conflict

**Symptoms:**
- Wrong skill invoked
- Unpredictable behavior

**Solution:**
- Use distinct trigger terms in descriptions
- Avoid generic language like "for data analysis"
- Make each skill's purpose unambiguous

---

## Examples

### Example 1: Simple Analysis Skill

**Directory:** `.claude/skills/file-counter/`

**SKILL.md:**
```markdown
---
name: file-counter
description: Count files by type and generate statistics. Use when analyzing project composition.
version: 1.0.0
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
find . -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn > /tmp/file_counts.txt
```

### Step 2: Read Results

```bash
cat /tmp/file_counts.txt
```

### Step 3: Return Summary

Report:
- Total files by extension
- Largest file types
- Any unusual patterns

Example: "Found 234 Python files (.py), 156 JavaScript files (.js), 89 Markdown files (.md)"
```

### Example 2: Validation Skill with Tool Restrictions

**Directory:** `.claude/skills/json-validator/`

**SKILL.md:**
```markdown
---
name: json-validator
description: Validate JSON files against schemas. Use when verifying config or API contracts.
version: 1.0.0
author: BAZINGA Team
allowed-tools: [Read, Grep, Glob]
---

# JSON Validator Skill

You are the json-validator skill. Validate JSON files and report errors.

## When to Invoke This Skill

- Before committing JSON configuration changes
- When modifying API contracts
- Debugging JSON parse errors

## Your Task

### Step 1: Find JSON Files

```bash
# Find all JSON files in current directory
ls *.json 2>/dev/null || echo "No JSON files in current directory"
```

### Step 2: Validate Each File

For each JSON file:
1. Read the file content
2. Check for syntax errors
3. Validate structure

### Step 3: Return Report

If errors found:
- List each error with line number
- Show expected vs actual format
- Suggest fixes

If no errors:
- Confirm validation passed
- Report file size and structure
```

### Example 3: Complex Multi-File Skill

**Directory:** `.claude/skills/security-scan/`

**Structure:**
```
security-scan/
├── SKILL.md
├── scripts/
│   ├── scan.py
│   └── report.py
├── resources/
│   └── vulnerability_patterns.yaml
└── references/
    └── usage.md
```

**SKILL.md:**
```markdown
---
name: security-scan
description: Run security vulnerability scans on code. Use when reviewing PRs or before deployment.
version: 2.0.0
author: BAZINGA Team
allowed-tools: [Bash, Read, Write, Grep]
tags: [security, analysis]
---

# Security Scan Skill

You are the security-scan skill. Analyze code for vulnerabilities.

## Overview

Detect SQL injection, XSS, hardcoded secrets, insecure dependencies.

## Prerequisites

- Python 3.8+
- Optional: semgrep, bandit for enhanced scanning

## When to Invoke This Skill

- Before approving PRs
- After significant code changes
- Pre-deployment security checks

## Your Task

### Step 1: Execute Scan

```bash
python3 .claude/skills/security-scan/scripts/scan.py \
  --target "$TARGET_DIR" \
  --output bazinga/security_report.json
```

### Step 2: Read Results

```bash
cat bazinga/security_report.json
```

### Step 3: Return Summary

Report:
- Critical/High/Medium issues count
- Top vulnerabilities with locations
- Recommended fixes

---

**For detailed documentation:** See references/usage.md
```

### Example 4: Skill with Disabled Auto-Invocation

```yaml
---
name: database-migrate
description: Run database migrations. Manual invocation only - use /database-migrate.
version: 1.0.0
disable-model-invocation: true
allowed-tools: [Bash]
---

# Database Migration Skill

[Instructions...]
```

This skill won't auto-invoke; users must explicitly type `/database-migrate`.

---

## Skill Creation Checklist

Before committing a new skill:

### Structure
- [ ] Directory in `.claude/skills/skill-name/` (or `~/.claude/skills/`)
- [ ] SKILL.md exists with exact filename (uppercase)
- [ ] Scripts in `scripts/` subdirectory (if applicable)
- [ ] Resources in `resources/` (if applicable)
- [ ] Verbose content moved to `references/` (if needed)

### Frontmatter
- [ ] `name` field present and matches directory name
- [ ] `description` clear, concise, includes trigger terms
- [ ] `version` field present (semantic versioning)
- [ ] `allowed-tools` scoped to minimum needed
- [ ] No tabs in YAML (spaces only)

### Content
- [ ] "When to Invoke" section included
- [ ] "Your Task" workflow with concrete steps
- [ ] Example invocation scenarios
- [ ] Script paths use full path from skill root
- [ ] Under 500 lines for optimal performance (100-300 is typical)
- [ ] Under 5,000 words total

### Testing
- [ ] Manual invocation works: `/skill-name`
- [ ] Auto-invocation triggers correctly
- [ ] Scripts execute without errors
- [ ] All tool permissions work
- [ ] Cross-platform (if applicable)

### Code Quality
- [ ] All Skill invocations use `command` parameter
- [ ] No hardcoded absolute paths (use `{baseDir}`)
- [ ] Dependencies documented in Prerequisites

---

## BAZINGA-Specific Notes

### Well-Structured Skills in This Project

| Skill | Lines | Structure | Notes |
|-------|-------|-----------|-------|
| `codebase-analysis` | 88 | Perfect ✅ | Moved verbose content to references/ |
| `bazinga-db` | ~120 | Good ✅ | Focused on DB operations |
| `lint-check` | ~110 | Good ✅ | Clear workflow |
| `security-scan` | ~264 | Acceptable ✅ | Dual-mode (basic/advanced) |
| `test-coverage` | ~140 | Good ✅ | Cross-platform support |
| `api-contract-validation` | ~95 | Good ✅ | Well-documented |

### Lessons Learned

1. **Template vs. runtime context:**
   - Use `"template": true` flag for unprocessed templates
   - Use `"fallback": true` flag for emergency minimal contexts
   - Check both flags in developer workflow

2. **Session isolation:**
   - Output files: Session-isolated (`bazinga/artifacts/{session}/skills/`)
   - Cache: Global with session-keyed names (for cross-session benefits)

3. **Parameter naming bug:**
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

### Related Documents

- `research/skill-fix-manual.md` - Step-by-step fixing guide for broken skills
- `research/skills-implementation-summary.md` - BAZINGA implementation history
- `.claude/skills/codebase-analysis/references/usage.md` - Example of references/ pattern

---

## Updates and Maintenance

**When to update this guide:**
- New skill patterns discovered
- Claude Code tool definition changes
- Best practices evolve
- Common issues identified

**Version history:**
- v2.0.0 (2025-12-12): Comprehensive integration of Mikhail Shilkov, Lee Han Chung, and official Claude Code documentation
- v1.0.0 (2025-11-19): Initial guide based on Mikhail Shilkov's deep-dive + BAZINGA experience

**Maintained by:** BAZINGA Team

---

## Quick Reference Card

```
SKILL LOCATION:      .claude/skills/skill-name/SKILL.md
                     ~/.claude/skills/skill-name/SKILL.md

INVOCATION:          Skill(command: "skill-name")
                     NOT: Skill(skill: "...") ❌

FRONTMATTER:         ---
                     name: skill-name        (required, match directory)
                     description: ...        (required, include triggers)
                     version: 1.0.0          (recommended)
                     allowed-tools: [...]    (optional, scope narrowly)
                     ---

IDEAL LENGTH:        100-250 lines, <5000 words

SCRIPT PATHS:        .claude/skills/skill-name/scripts/main.py
                     NOT: scripts/main.py ❌

VERIFY SYNTAX:       grep "Skill(command" agents/*.md ✅
                     grep "Skill(skill" agents/*.md ❌
```

---

**This is the single source of truth for skill implementation. Always consult this guide before creating, updating, or invoking skills.**
