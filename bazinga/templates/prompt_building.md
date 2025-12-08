# Agent Prompt Building Guide

## Overview
Agent prompts are dynamically built by reading configuration files and appending sections based on what's enabled.

## Configuration Files to Read

### 1. Skills Configuration
```bash
cat bazinga/skills_config.json
```

Check which advanced skills are mandatory for each agent:
- `developer.codebase-analysis` - "mandatory" / "optional" / "disabled"
- `developer.test-pattern-analysis`
- `developer.api-contract-validation`
- `developer.db-migration-check`
- `developer.lint-check`
- `qa_expert.pattern-miner`
- `qa_expert.quality-dashboard`
- `pm.velocity-tracker`

### 2. Testing Configuration
```bash
cat bazinga/testing_config.json
```

Extract key settings:
- `testing_mode` - "full" / "minimal" / "disabled"
- `testing_enabled` - true/false
- `qa_workflow.enable_qa_expert` - true/false
- `pre_commit_validation.lint_check` - true/false
- `pre_commit_validation.unit_tests` - true/false
- `pre_commit_validation.build_check` - true/false

## Prompt Structure

### Base Prompt
Always start with agent role and context:
```
You are a {AGENT_TYPE} in a Claude Code Multi-Agent Dev Team.

**GROUP:** {group_id}
**MODE:** {Simple|Parallel}

{code_context - if applicable}

**REQUIREMENTS:**
{task details from PM}
{user's original requirements}
```

### Testing Framework Section
Add based on `testing_config.json`:

```
**TESTING FRAMEWORK CONFIGURATION:**
**Mode:** {testing_mode}
**QA Expert:** {qa_expert_enabled}

{IF testing_mode == "disabled"}
⚠️  **TESTING FRAMEWORK DISABLED (Prototyping Mode)**
- Only lint checks required
- No test implementation needed
- Route directly to Tech Lead (skip QA)
{ENDIF}

{IF testing_mode == "minimal"}
📋 **MINIMAL TESTING MODE (Fast Development)**
- Lint checks + unit tests required
- No integration/contract/E2E tests needed
- Route directly to Tech Lead (skip QA Expert)
{ENDIF}

{IF testing_mode == "full"}
✅ **FULL TESTING MODE (Production Quality)**
- All test types may be required
- QA Expert will review if integration tests exist
- Route to QA Expert if integration tests, else Tech Lead
{ENDIF}

**Pre-Commit Validation Requirements:**
- Lint Check: {lint_check_required}
- Unit Tests: {unit_tests_required}
- Build Check: {build_check_required}
```

### Specialization Block Section (Skill-Based)

**Purpose:** Inject composed technology-specific patterns via specialization-loader skill.

**Prerequisites:**
- `bazinga/skills_config.json` has `specializations.enabled: true`
- Agent type is in `specializations.enabled_agents`
- Task group has assigned specializations (non-empty array)

**Step 1: Check if enabled**

Read `bazinga/skills_config.json`:
- If `specializations.enabled` is false → skip
- If agent type not in `enabled_agents` → skip

**Step 2: Query specializations from database**

```
bazinga-db, get task groups for session [session_id]
specializations = task_group["specializations"]  # JSON array or null
```

If null or empty → skip specialization loading.

**Step 3: Invoke specialization-loader skill**

**🔴 CRITICAL: TWO SEPARATE ACTIONS** (the Skill tool reads context from conversation, not parameters)

**Action 3a: Output context as text FIRST (not in tool call):**
```text
Session ID: {session_id}
Group ID: {group_id}
Agent Type: {developer|senior_software_engineer|qa_expert|tech_lead|requirements_engineer|investigator}
Model: {haiku|sonnet|opus}
Specialization Paths: {JSON array from Step 2}
```

**Action 3b: THEN invoke the skill:**
```
Skill(command: "specialization-loader")
```

The skill reads the context you output above and returns the composed block.

**Step 4: Extract and prepend composed block**

The skill returns a composed block with markers:
```
[SPECIALIZATION_BLOCK_START]
{composed markdown}
[SPECIALIZATION_BLOCK_END]
```

Extract content and prepend to agent prompt:

```markdown
## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates (tests must pass)
> - Routing and status requirements (READY_FOR_QA, etc.)
> - Pre-commit quality checks (lint, build)
> - Core agent workflow rules

For this session, your identity is enhanced:

**{Composed Identity String}**
(e.g., "You are a Java 8 Backend API Developer specialized in Spring Boot 2.7.")

Your expertise includes:
- {Key point 1}
- {Key point 2}
- {Key point 3}

### Patterns to Apply
{Condensed patterns - version-aware, within token budget}

### Patterns to Avoid
{Anti-patterns as bullet list}

### Verification Checklist
{If token budget allows}
```

**Step 5: Fallback behavior**

| Scenario | Action |
|----------|--------|
| specializations.enabled = false | Skip entirely |
| Agent type not in enabled_agents | Skip entirely |
| No specializations in DB | Skip entirely (graceful degradation) |
| Skill invocation fails | Log warning, spawn without specialization |

**Token budget (per-model):**

| Model | Soft Limit | Hard Limit |
|-------|------------|------------|
| haiku | 600 | 900 |
| sonnet | 1200 | 1800 |
| opus | 1600 | 2400 |

The skill handles token budgeting, version guards, and content trimming.
Orchestrator receives composed block ready for injection.

---

### Advanced Skills Section
IF any advanced skills are mandatory, add:

```
═══════════════════════════════════════════
⚡ ADVANCED SKILLS ACTIVE
═══════════════════════════════════════════

You have access to the following Skills:

{FOR each mandatory skill, reference its SKILL.md file}

Example:
1. **Codebase Analysis Skill**: Run BEFORE coding
   Skill(command: "codebase-analysis")
   See: .claude/skills/codebase-analysis/SKILL.md for details

2. **Test Pattern Analysis Skill**: Run BEFORE writing tests
   Skill(command: "test-pattern-analysis")
   See: .claude/skills/test-pattern-analysis/SKILL.md for details

USE THESE SKILLS for better implementation quality!
═══════════════════════════════════════════
```

### Mandatory Workflow Section
Build workflow steps based on enabled skills:

```
**MANDATORY WORKFLOW:**

BEFORE Implementing:
1. Review codebase context above
{IF codebase_analysis_mandatory}
2. INVOKE Codebase Analysis Skill (MANDATORY)
   Skill(command: "codebase-analysis")
{ENDIF}

During Implementation:
3. Implement the COMPLETE solution
4. Write unit tests
{IF test_pattern_analysis_mandatory}
5. INVOKE Test Pattern Analysis Skill (MANDATORY)
   Skill(command: "test-pattern-analysis")
{ENDIF}

BEFORE Reporting READY_FOR_QA:
6. Run ALL unit tests - MUST pass 100%
{IF lint_check_mandatory}
7. INVOKE lint-check Skill (MANDATORY)
   Skill(command: "lint-check")
{ENDIF}
8. Run build check - MUST succeed
{IF api_contract_validation_mandatory AND api_changes}
9. INVOKE API Contract Validation (MANDATORY)
   Skill(command: "api-contract-validation")
{ENDIF}
{IF db_migration_check_mandatory AND migration_changes}
10. INVOKE DB Migration Check (MANDATORY)
    Skill(command: "db-migration-check")
{ENDIF}

ONLY THEN:
11. Commit to branch: {branch_name}
12. Report: READY_FOR_QA
```

### Report Format
End with expected output format (see message_templates.md for standard formats)

## Key Principles

1. **Read configs first** - Don't guess what's enabled
2. **Only add sections for mandatory skills** - Skip optional/disabled
3. **Reference skill files** - Don't duplicate their documentation
4. **Keep it concise** - Agent gets the full SKILL.md when they invoke
5. **Clear workflow** - Agent knows exactly what steps to take

## Summary

**Instead of:** 250 lines of IF/ELSE pseudo-code showing every permutation
**Do this:** Read 2 config files, append 3-4 sections based on what's enabled

The agent prompt should be:
- Role definition (who they are)
- Context (what they're working on)
- Configuration (testing mode, skills available)
- Workflow (steps to follow)
- Output format (how to report back)

That's it. Keep it simple.
