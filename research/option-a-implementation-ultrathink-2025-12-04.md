# Option A: Full Specialization Implementation (Ultrathink)

**Date:** 2025-12-04
**Context:** Implementing complete specialization system with token budgeting, composed identity, and advisory wrapper
**Decision:** Pending user validation
**Status:** Implemented with fixes pending
**Reviewed by:** Codex (2025-12-04)

---

## Executive Summary

This document details the full implementation of dynamic agent specializations (Option A from the audit). It integrates all discussed features from research documents while preserving the existing Tech Stack Scout agent and PM assignment workflow.

**Key deliverables:**
1. **specialization-loader skill** - Reads templates, composes identity, enforces token budget
2. **Token budget enforcement** - 1200 soft / 1800 hard limit with intelligent trimming
3. **Composed identity** - "You are a Java 8 Backend API Developer specialized in Spring Boot 2.7"
4. **Advisory wrapper** - Replaces "MANDATORY" with supplementary guidance
5. **Version guards** - Templates adapt to detected project versions
6. **Config flags** - Enable/disable, token limits, mode settings

---

## What Stays (Already Implemented)

These components remain unchanged:

| Component | File | Status |
|-----------|------|--------|
| Tech Stack Scout | `agents/tech_stack_scout.md` | 90% - Keep as-is |
| PM Assignment | `agents/project_manager.md` | 100% - Keep as-is |
| DB Schema v7 | `bazinga-db skill` | 100% - Keep as-is |
| 72 Templates | `templates/specializations/` | Need version guards |
| project_context.json | Created by Scout | Keep as-is |

**Tech Stack Scout stays because:**
- It runs at Step 0.5, BEFORE PM spawn
- It outputs `bazinga/project_context.json` with stack detection
- It suggests specializations per component
- The skill will READ from project_context.json, not duplicate detection

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 0.5: Tech Stack Scout (EXISTING - NO CHANGES)                      │
├─────────────────────────────────────────────────────────────────────────┤
│ Scout → Glob/Grep → Detects stack → Writes bazinga/project_context.json │
│                                                                          │
│ Output: { primary_language: "java", components: [...], ... }             │
└──────────────────────────────────────────┬──────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 1: PM Planning (EXISTING - NO CHANGES)                             │
├─────────────────────────────────────────────────────────────────────────┤
│ PM reads project_context.json → Assigns specializations per task group   │
│ PM stores: bazinga-db create-task-group --specializations '[...]'        │
└──────────────────────────────────────────┬──────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Orchestrator Spawn (MODIFIED)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ BEFORE spawning developer:                                               │
│                                                                          │
│ 1. Check skills_config.json: specializations.enabled?                    │
│    └── If false: skip specialization loading                             │
│                                                                          │
│ 2. Query task_group.specializations from DB                              │
│                                                                          │
│ 3. Read project_context.json for versions & style signals                │
│                                                                          │
│ 4. Invoke: Skill(command: "specialization-loader")                       │
│    └── Skill returns COMPOSED BLOCK (not file paths)                     │
│                                                                          │
│ 5. Prepend specialization block to developer prompt                      │
└──────────────────────────────────────────┬──────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ NEW: specialization-loader Skill                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Input: specialization paths + project_context.json                       │
│                                                                          │
│ Process:                                                                 │
│ 1. Read each template file                                               │
│ 2. Apply version guards (skip sections for wrong version)                │
│ 3. Detect style signals (Lombok, JUnit version, injection style)         │
│ 4. Compose identity string from detected stack                           │
│ 5. Condense content within token budget (1200 soft / 1800 hard)          │
│ 6. Wrap with advisory disclaimer                                         │
│ 7. Return composed block                                                 │
│                                                                          │
│ Output: Markdown block ready for prompt injection                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component 1: specialization-loader Skill

### Directory Structure

```
.claude/skills/specialization-loader/
├── SKILL.md                    # Skill definition (~150 lines)
└── references/
    └── usage.md                # Detailed documentation
```

### SKILL.md Design

```markdown
---
version: 1.0.0
name: specialization-loader
description: Compose technology-specific agent identity and patterns. Invoke before spawning developers to enhance expertise based on project stack.
author: BAZINGA Team
tags: [orchestration, specialization, context]
allowed-tools: [Read, Grep]
---

# Specialization Loader Skill

You are the specialization-loader skill. You compose technology-specific
identity and pattern guidance for agents based on detected project stack.

## When to Invoke This Skill

- Before spawning Developer/SSE agents (orchestrator invokes you)
- When task_group has assigned specializations
- Never invoke multiple times for same agent spawn

## Your Task

### Step 1: Read Input Context

Read the orchestrator's provided context:
- `specialization_paths`: JSON array of template paths
- `project_context_path`: Path to project_context.json

### Step 2: Load Project Context

Read project_context.json and extract:
- `primary_language` and version (if detected)
- `framework` and version
- `components[].type` (frontend/backend/etc.)

### Step 3: Read Templates with Token Tracking

For each path in specialization_paths:
1. Read the template file
2. Parse frontmatter (priority, token_estimate, compatible_with)
3. Apply version guards (skip `<!-- version: X -->` sections not matching)
4. Track token count (estimate: chars / 4)

**Token Budget Rules:**
- Soft limit: 1200 tokens
- Hard limit: 1800 tokens
- If over soft limit: trim "Code Patterns (Reference)" sections
- If still over: trim verification checklists
- If still over hard limit: stop adding templates

**Priority Order:**
1. Language templates (priority 1)
2. Framework templates (priority 2)
3. Domain templates (priority 3)
4. Quality templates (priority 4)

### Step 4: Apply Version Guards

For each template section marked with version guards:
```markdown
<!-- version: java >= 14 -->
[Include this if project Java version >= 14]

<!-- version: java < 14 -->
[Include this if project Java version < 14]
```

Match against `project_context.json` version data.

### Step 5: Compose Identity String

Build identity from detected stack:
```
You are a {Language} {Version} {Domain} Developer specialized in {Framework} {FrameworkVersion}.
```

Examples:
- "You are a Java 8 Backend API Developer specialized in Spring Boot 2.7."
- "You are a TypeScript Frontend Developer specialized in Next.js 14."
- "You are a Python Backend Developer specialized in FastAPI."

### Step 6: Build Specialization Block

Compose the final block:

```markdown
## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates (tests must pass)
> - Routing and status requirements (READY_FOR_QA, etc.)
> - Pre-commit quality checks (lint, build)
> - Core agent workflow rules

For this session, your identity is enhanced:

**{Composed Identity String}**

Your expertise includes:
- {Key point 1 from templates}
- {Key point 2 from templates}
- {Key point 3 from templates}

### Patterns to Apply
{Condensed patterns from templates - max 600 tokens}

### Patterns to Avoid
{Combined anti-patterns - max 200 tokens}

### Verification Checklist
{Combined checklist if token budget allows}
```

### Step 7: Return Result

Return the composed specialization block. The orchestrator will prepend
this to the developer spawn prompt.

## Token Counting

Estimate tokens as: `character_count / 4`

Track cumulative tokens as you build the block:
- Identity section: ~50 tokens
- Expertise bullets: ~30 tokens
- Patterns to Apply: ~600 tokens max
- Patterns to Avoid: ~200 tokens max
- Verification Checklist: ~150 tokens (if budget allows)
- Advisory wrapper: ~100 tokens

## Example Output

For project: Java 8, Spring Boot 2.7, backend-api domain

```markdown
## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates (tests must pass)
> - Routing and status requirements (READY_FOR_QA, etc.)
> - Pre-commit quality checks (lint, build)
> - Core agent workflow rules

For this session, your identity is enhanced:

**You are a Java 8 Backend API Developer specialized in Spring Boot 2.7.**

Your expertise includes:
- Java 8 features: lambdas, streams, Optional, CompletableFuture
- Spring Boot 2.7: constructor injection, Data JPA, @Transactional
- RESTful API design: proper status codes, structured errors, pagination

### Patterns to Apply

**Constructor Injection (Java 8 + Spring Boot 2.7):**
```java
@Service
public class UserService {
    private final UserRepository userRepository;

    @Autowired  // Explicit in Spring Boot 2.x
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}
```

**Optional for Nullable Returns:**
```java
public Optional<User> findById(Long id) {
    return repository.findById(id);
}
```

### Patterns to Avoid
- `var` keyword (Java 10+ only)
- Records (Java 14+ only)
- Text blocks `"""` (Java 15+ only)
- Field injection (@Autowired on fields)
- Returning null from methods

### Verification Checklist
- [ ] Constructor injection used (no @Autowired on fields)
- [ ] Optional for nullable returns
- [ ] @Transactional on service methods
- [ ] Proper HTTP status codes
```
```

### Token Budget Enforcement Algorithm

```python
def compose_block(templates, project_context, config):
    budget_soft = config.get("soft_limit", 1200)
    budget_hard = config.get("hard_limit", 1800)

    # Sort by priority
    templates = sorted(templates, key=lambda t: t.priority)

    composed_sections = {
        "identity": compose_identity(project_context),  # ~50 tokens
        "expertise": [],      # ~30 tokens
        "patterns": [],       # target 600 tokens
        "anti_patterns": [],  # target 200 tokens
        "checklist": []       # target 150 tokens
    }

    current_tokens = 150  # Base wrapper overhead

    for template in templates:
        # Apply version guards
        content = apply_version_guards(template, project_context)

        # Extract sections
        patterns = extract_patterns(content)
        anti_patterns = extract_anti_patterns(content)
        checklist = extract_checklist(content)

        # Add patterns if within budget
        for pattern in patterns:
            pattern_tokens = estimate_tokens(pattern)
            if current_tokens + pattern_tokens <= budget_soft:
                composed_sections["patterns"].append(pattern)
                current_tokens += pattern_tokens
            elif current_tokens + pattern_tokens <= budget_hard:
                # Over soft, under hard - add condensed version
                condensed = condense_pattern(pattern)
                composed_sections["patterns"].append(condensed)
                current_tokens += estimate_tokens(condensed)

        # Add anti-patterns (always concise)
        for ap in anti_patterns[:5]:  # Max 5 per template
            composed_sections["anti_patterns"].append(ap)

        # Add checklist items if budget allows
        if current_tokens < budget_soft:
            for item in checklist[:3]:  # Max 3 per template
                composed_sections["checklist"].append(item)

    return build_final_block(composed_sections)
```

---

## Component 2: Template Version Guards

### Current Template Format

Templates currently have inline version comments:
```markdown
<!-- version: java >= 14 -->
```java
public record User(...) {}
```
```

### Enhanced Format

Add version guards to templates that need them. The skill will parse these.

**Example: java.md with version guards**

```markdown
---
name: java
type: language
priority: 1
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
---

# Java Engineering Expertise

## Patterns to Follow

### Immutability

<!-- version: java >= 16 -->
**Records** (Java 16+):
```java
public record User(String id, String email) {}
```

<!-- version: java >= 8, java < 16 -->
**Final Classes** (Java 8-15):
```java
public final class User {
    private final String id;
    private final String email;
    // Constructor, getters, equals, hashCode, toString...
}
```

### Modern Features

<!-- version: java >= 21 -->
**Virtual Threads** (Java 21+):
```java
Thread.startVirtualThread(() -> processOrder(order));
```

<!-- version: java >= 8, java < 21 -->
**Thread Pools** (Java 8-20):
```java
ExecutorService executor = Executors.newFixedThreadPool(10);
executor.submit(() -> processOrder(order));
```
```

### Templates Requiring Version Guards

| Template | Needs Guards | Reason |
|----------|--------------|--------|
| java.md | Yes | Records (14+), var (10+), virtual threads (21+) |
| python.md | Yes | match/case (3.10+), walrus operator (3.8+) |
| typescript.md | Minor | satisfies operator (4.9+) |
| spring-boot.md | Yes | Virtual threads (3.2+), records for config |
| react.md | Yes | Server Components (18+), hooks (16.8+) |

---

## Component 3: Advisory Wrapper

### Current (Wrong) Language

Templates say:
```markdown
> **MANDATORY**: Apply these patterns to ALL code you write.
```

And orchestrator says:
```markdown
MANDATORY: Apply ALL patterns from these files. These are required practices.
```

### Correct Language

Templates should say:
```markdown
> This guidance is supplementary. It does NOT override mandatory workflow rules.
```

And composed block should say:
```markdown
## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates (tests must pass)
> - Routing and status requirements
> - Pre-commit quality checks
> - Core agent workflow rules
```

### Template Updates Required

All 72 templates need this header replaced:

**Find:**
```markdown
> **MANDATORY**: Apply these patterns to ALL code you write. This is NOT optional guidance—these are required practices. Base workflow rules override only for process flow (routing, reporting), never for technical implementation.
```

**Replace with:**
```markdown
> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.
```

---

## Component 4: Configuration Flags

### skills_config.json Changes

```json
{
  "specializations": {
    "enabled": true,
    "mode": "advisory",
    "soft_token_limit": 1200,
    "hard_token_limit": 1800,
    "include_code_examples": true,
    "include_checklist": true
  },
  ...existing config...
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | true | Enable/disable specialization loading |
| `mode` | string | "advisory" | "advisory" (supplementary) or "strict" (must follow) |
| `soft_token_limit` | int | 1200 | Target token limit |
| `hard_token_limit` | int | 1800 | Maximum token limit |
| `include_code_examples` | boolean | true | Include code snippets in patterns |
| `include_checklist` | boolean | true | Include verification checklist |

---

## Component 5: Orchestrator Changes

### Current Implementation (lines 1204-1274)

Currently tells agents to READ files:
```markdown
## Specialization References

Read and apply these patterns BEFORE implementation:
- `path1`
- `path2`

MANDATORY: Apply ALL patterns from these files.
```

### New Implementation

Replace with skill invocation that returns COMPOSED content:

```markdown
## §Specialization Loading (REVISED)

**Purpose:** Inject technology-specific patterns into agent prompts.

### Process (at agent spawn)

**Step 1: Check if specializations enabled**
```
Read bazinga/skills_config.json
IF specializations.enabled == false:
    Skip specialization loading
    Continue to spawn
```

**Step 2: Query task group specializations**
```
bazinga-db, get task groups for session [session_id]
specializations = task_group["specializations"]  # JSON array
```

**Step 3: Skip if no specializations**
```
IF specializations is null OR empty:
    Skip specialization loading
    Continue to spawn
```

**Step 4: Invoke specialization-loader skill**
```
Skill(command: "specialization-loader")

Context to provide in preceding message:
- specialization_paths: [list from step 2]
- project_context_path: "bazinga/project_context.json"
- config: skills_config.json specializations section
```

**Step 5: Receive composed block**

The skill returns a composed markdown block (~1000-1800 tokens) with:
- Advisory wrapper
- Composed identity
- Condensed patterns
- Anti-patterns
- Checklist (if budget allows)

**Step 6: Prepend to agent prompt**
```markdown
{composed_specialization_block}

---

## Your Task
{task_description from PM}
```

### Fallback Scenarios

| Scenario | Action |
|----------|--------|
| specializations.enabled = false | Skip entirely |
| No specializations assigned | Skip entirely |
| Skill invocation fails | Log warning, spawn without specialization |
| Token budget exceeded | Skill handles trimming |
```

---

## Implementation Checklist

### Phase 1: Create Skill

- [ ] Create `.claude/skills/specialization-loader/SKILL.md`
- [ ] Create `.claude/skills/specialization-loader/references/usage.md`
- [ ] Test skill invocation independently

### Phase 2: Add Version Guards to Templates

- [ ] Update `01-languages/java.md` with version guards
- [ ] Update `01-languages/python.md` with version guards
- [ ] Update `03-frameworks-backend/spring-boot.md` with version guards
- [ ] Update remaining templates as needed (lower priority)

### Phase 3: Fix Advisory Wrapper

- [ ] Update all 72 templates to replace MANDATORY header
- [ ] Single regex replacement across all files

### Phase 4: Add Config Flags

- [ ] Add `specializations` section to `bazinga/skills_config.json`
- [ ] Document configuration options

### Phase 5: Update Orchestrator

- [ ] Replace §Specialization Loading section (lines 1204-1274)
- [ ] Add skill invocation before developer spawn
- [ ] Test end-to-end flow

### Phase 6: Update prompt_building.md

- [ ] Update `templates/prompt_building.md` with new specialization block format
- [ ] Remove old "agent reads files" approach

### Phase 7: Documentation

- [ ] Create `docs/dynamic-specialization.md` (user-facing)
- [ ] Update README with feature description

---

## Token Budget Validation

### Sample Calculation

For a Java 8 + Spring Boot 2.7 + Backend API project:

| Section | Estimated Tokens |
|---------|------------------|
| Advisory wrapper | 100 |
| Identity + expertise | 80 |
| Patterns (2 code examples) | 500 |
| Anti-patterns (8 items) | 160 |
| Checklist (6 items) | 120 |
| **Total** | **960** |

This is under the 1200 soft limit.

### Over-budget Scenario

If 4 templates assigned (language + framework + domain + security):

| Section | Estimated Tokens |
|---------|------------------|
| Advisory wrapper | 100 |
| Identity + expertise | 100 |
| Patterns (4 templates × 400) | 1600 |
| Anti-patterns (20 items) | 300 |
| Checklist (12 items) | 200 |
| **Raw Total** | **2300** |

Trimming strategy:
1. Reduce patterns to 2 examples per template: 800 tokens
2. Reduce anti-patterns to 3 per template: 120 tokens
3. Reduce checklist to 2 per template: 80 tokens

**Trimmed Total:** 100 + 100 + 800 + 120 + 80 = **1200 tokens** (at soft limit)

---

## Risk Analysis

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Skill invocation fails | Low | Medium | Graceful fallback to no specialization |
| Token budget exceeded | Medium | Low | Enforced trimming algorithm |
| Version detection wrong | Low | Medium | Conservative version guards |
| Agent ignores advisory | Medium | Low | Still better than nothing |

### Compatibility Notes

- Skill requires orchestrator to be updated
- Skill reads project_context.json (created by Scout)
- Skill reads templates from `templates/specializations/`
- No changes to PM, QA, Tech Lead, or Developer agents
- No database schema changes needed

---

## Questions for User Validation

1. **Token limits:** Are 1200 soft / 1800 hard limits correct?
2. **Version guards:** Should we add guards to all 72 templates or prioritize top 10?
3. **Advisory vs Strict mode:** Should we support a "strict" mode that makes patterns mandatory?
4. **Skill location:** Should skill be in `.claude/skills/` (installed to clients) or dev-only?

---

## References

- `research/dynamic-agent-specializations.md` - Original strategy doc
- `research/dynamic-specialization-skill-design.md` - Skill architecture (LLM reviewed)
- `research/specialization-implementation-audit-2025-12-04.md` - Gap analysis
- `research/skill-implementation-guide.md` - How to create skills
- `agents/tech_stack_scout.md` - Existing Scout agent
- `agents/orchestrator.md` lines 1204-1274 - Current specialization loading

---

## Multi-LLM Review Integration

### Codex Review (2025-12-04)

**Reviewer:** Codex (automated code review)

#### Summary

Codex found the implementation generally matches or exceeds the plan, with token budgets scaling by model instead of fixed values, and orchestrator/prompt-building docs consistently reflecting the new skill-driven flow.

#### Issues Raised

| Issue | Severity | Status | Resolution |
|-------|----------|--------|------------|
| Missing `compatible_with` filtering | Medium | **VALID** | Skill needs to filter templates by agent type |
| project_context.json handling contradiction | Medium | **VALID** | Remove conflicting "do not invoke" guidance |
| Missing references/usage.md | Low | **REJECTED** | SKILL.md is comprehensive (356 lines) |

#### Issue 1: Missing Compatibility Filtering (VALID)

**Codex said:**
> Templates still declare compatibility only for developer/SSE (e.g., Java's frontmatter). The skill does not describe filtering by `compatible_with`, so QA/TL agents could receive developer-focused guidance.

**Analysis:** This is **VALID**. Templates have `compatible_with` frontmatter:
- `java.md`: `compatible_with: [developer, senior_software_engineer]`
- `qa-strategies.md`: `compatible_with: [qa_expert, tech_lead]`
- `code-review.md`: `compatible_with: [tech_lead, senior_software_engineer]`

But the skill doesn't filter templates by this field when loading.

**Fix required:** Add Step 3.5 to SKILL.md:
```markdown
### Step 3.5: Filter by Agent Compatibility

For each template, check frontmatter `compatible_with` array:
- If agent_type is in compatible_with: include template
- If agent_type NOT in compatible_with: skip template
- If compatible_with is empty/missing: include by default

This ensures QA agents get testing patterns, not implementation patterns.
```

#### Issue 2: project_context.json Contradiction (VALID)

**Codex said:**
> The skill's guard list says not to invoke it when project_context.json is missing, whereas the orchestrator fallback table assumes the skill will handle missing context conservatively.

**Analysis:** This is **VALID**. Two conflicting statements:
1. Line 23: "Do NOT invoke when: No project_context.json exists"
2. Line 52 + error table: "If project_context.json missing, use conservative defaults"

**Resolution:** The skill should be defensive. Remove the "do not invoke" guidance and rely on graceful handling. The orchestrator might not know if project_context.json exists until the skill checks.

**Fix required:** Update SKILL.md "Do NOT invoke when" section:
```markdown
**Do NOT invoke when:**
- specializations array is empty or null
- skills_config.json has specializations.enabled = false

**Handle gracefully (with defaults):**
- No project_context.json exists → skip version guards, use generic patterns
```

#### Issue 3: Missing references/usage.md (REJECTED)

**Codex said:**
> The Option A document called for an additional references/usage.md under the skill directory; that file is absent.

**Resolution:** **REJECTED**. The SKILL.md is 356 lines with comprehensive documentation including:
- Step-by-step process
- Token budgets by model
- Agent-specific customization
- Complete example output
- Error handling table

Creating a separate usage.md would only duplicate content and increase maintenance burden.

### User Responses to LLM Suggestions

| Suggestion | User Decision | Rationale |
|------------|---------------|-----------|
| Add `compatible_with` filtering | **APPROVED** | Prevents developer patterns going to QA |
| Fix project_context.json handling | **APPROVED** | Skill should be defensive |
| Create references/usage.md | **REJECTED** | SKILL.md is already comprehensive |

---

## Implementation Status

### Completed ✅

1. specialization-loader skill (SKILL.md - 356 lines)
2. Token budgets per model (haiku/sonnet/opus)
3. Composed identity per agent type
4. Advisory wrapper on all 71 templates
5. Version guards on 70 templates (303 total guards)
6. Config flags in skills_config.json
7. Orchestrator section updated
8. prompt_building.md updated

### Pending Fixes (from LLM Review)

1. **Add `compatible_with` filtering to skill** - Step 3.5
2. **Remove project_context.json contradiction** - Update "Do NOT invoke" section

---

## Next Step

Apply the two fixes identified in LLM review, then mark implementation as complete.
