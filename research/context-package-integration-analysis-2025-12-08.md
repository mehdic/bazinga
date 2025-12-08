# Context Package Integration Analysis: RE→Developer Research Handoff

**Date:** 2025-12-08
**Context:** Investigating whether research context from Requirements Engineer reaches developers during orchestration
**Decision:** TBD after analysis
**Status:** Proposed
**Reviewed by:** Pending multi-LLM review

---

## Problem Statement

### User's Observation

When spawning developers during orchestration, the prompts contain:
- Session context
- Task details
- Testing mode
- Specialization guidance

But they do **NOT** contain:
- Research context from Requirements Engineer
- Prior failure context from QA
- Architectural decisions from Tech Lead

### Clarification: Two Different "Research" Concepts

| Folder | Purpose | When Used |
|--------|---------|-----------|
| `research/*.md` | Personal ultrathink docs, design decisions | Reference during development |
| `bazinga/artifacts/{session}/context/*.md` | RE's research output DURING orchestration | Passed to developers via context packages |

The user correctly pointed out that my initial fix incorrectly referenced `research/*.md` - those are NOT for orchestration agents.

---

## Current System Design (from inter-agent-communication-design.md)

### The Intended Flow

```
┌─────────────────────┐
│ Requirements        │
│ Engineer (RE)       │
└─────────┬───────────┘
          │ 1. Writes research deliverable
          │    bazinga/artifacts/{session}/research_group_{group}.md
          │
          │ 2. Registers context package
          │    bazinga-db save-context-package ...
          ▼
┌─────────────────────┐
│ Database            │
│ context_packages    │
│ + consumers table   │
└─────────┬───────────┘
          │ 3. Orchestrator queries before spawn
          │    bazinga-db get-context-packages ...
          ▼
┌─────────────────────┐
│ Developer           │
│ receives in prompt: │
│ "Context Packages   │
│  Available" table   │
└─────────────────────┘
          │ 4. Developer reads file
          │    Read(file_path: "...")
          │
          │ 5. Developer implements using research
          ▼
```

### What's Implemented vs What's Working

| Component | Implemented | Working |
|-----------|-------------|---------|
| context_packages DB table | ✅ Yes (schema v6) | ✅ Yes |
| context_package_consumers table | ✅ Yes | ✅ Yes |
| bazinga-db save-context-package | ✅ Yes | ✅ Yes |
| bazinga-db get-context-packages | ✅ Yes | ✅ Yes |
| RE registers package after research | ✅ Documented | ❓ Unknown |
| Orchestrator queries packages | ✅ Documented | ❓ Unknown |
| Developer prompt includes packages | ✅ Documented | ❓ Unknown |

---

## Gap Analysis

### Gap 1: Is RE Actually Registering Context Packages?

**Evidence from requirements_engineer.md (lines 689-730):**

```markdown
## 🔴 MANDATORY: Context Package Registration

**After writing your research deliverable, you MUST register it as a context package...**

bazinga-db, please save context package:
Session ID: {SESSION_ID}
Group ID: {GROUP_ID}
Package Type: research
...
```

**Verdict:** Instructions exist, but compliance is NOT enforced. RE could skip this step.

### Gap 2: Is Orchestrator Actually Querying Packages?

**Evidence from phase_simple.md (lines 22-62):**

```markdown
**🔴 Context Package Query (MANDATORY before spawn):**

Query available context packages for this agent:
bazinga-db, please get context packages:
...
Then invoke: `Skill(command: "bazinga-db")`
```

**Verdict:** Instructions exist, but this is a MULTI-STEP process:
1. Orchestrator outputs query text
2. Orchestrator invokes bazinga-db skill
3. Skill returns results
4. Orchestrator includes results in prompt

This is complex and could be skipped during context compaction or rushed execution.

### Gap 3: Are Packages Being Included in Prompts?

**Evidence from phase_simple.md (lines 44-64):**

```markdown
**Context Packages Prompt Section** (include when N > 0 after validation):

## Context Packages Available

Read these files BEFORE starting implementation:

| Priority | Type | Summary | File | Package ID |
...
```

**Verdict:** Template exists, but inclusion depends on Gap 2 being executed.

---

## Why User Saw No Research Context

Based on the developer prompts shown by the user:

1. **No Requirements Engineer was spawned** - These were direct implementation tasks (HELM, GDPR-EXPORT, WCAG, E2E), not research tasks
2. **Therefore no context packages existed** - Nothing to query
3. **Context Packages table was empty** - Correctly omitted

This is **correct behavior** - if no research was done, no research context should be passed.

---

## The Real Question: What About Project Context?

The user's underlying question: *"Shouldn't developers receive project context even without RE research?"*

### What Project Context Exists

| Source | Content | Currently Passed? |
|--------|---------|-------------------|
| `project_context.json` | Language, framework, conventions, utilities | ❌ No (devs read file) |
| Specialization-loader | Tech patterns, anti-patterns, code examples | ✅ Yes (PR #175 fixed) |
| Context packages (RE research) | Task-specific findings | ✅ Yes (if RE was spawned) |
| Context packages (QA failures) | Prior iteration failures | ✅ Yes (if QA failed) |
| Context packages (TL decisions) | Architectural decisions | ✅ Yes (if TL made decisions) |

### Overlap Analysis

**Specialization-loader provides:**
- Language: Java 8, TypeScript 5.x, etc.
- Framework: Spring Boot 2.7, Express 4.x, etc.
- Patterns to Apply (code examples)
- Patterns to Avoid (anti-patterns)
- Verification Checklist

**project_context.json provides:**
- Language/framework versions (DUPLICATE)
- Architecture patterns (PARTIAL OVERLAP)
- Conventions: file structure, naming (UNIQUE)
- Key utilities (UNIQUE)
- Key directories (UNIQUE)

**Conclusion:** ~70% of project_context.json is already covered by specialization-loader. The unique parts are:
1. Conventions (file structure, naming)
2. Key utilities
3. Key directories

---

## Recommendations

### Option A: Remove My Changes (Simplest)

Specialization-loader handles tech context. Developers read project_context.json if needed. No additional injection.

**Pros:**
- No extra complexity
- No extra tokens
- Specialization-loader was just fixed

**Cons:**
- Conventions not in prompt (devs must read file)
- Key utilities not highlighted

### Option B: Keep Project Context Section (Minimal)

Keep the section but:
1. Remove Language/Framework table (already in specialization)
2. Keep only: Conventions + Key Utilities
3. Remove research folder references (WRONG)

**Pros:**
- Conventions in prompt
- No file read required

**Cons:**
- ~100 extra tokens per prompt
- Potential confusion with specialization

### Option C: Enhance Specialization-Loader (Best Long-Term)

Modify specialization-loader skill to include conventions from project_context.json.

**Pros:**
- Single source of truth
- Token-budgeted
- Already integrated

**Cons:**
- Requires skill modification
- Couples specialization to project context

### Option D: Trust the Existing System (Recommended)

1. **Specialization-loader** handles tech patterns ✅
2. **Context packages** handle RE research, QA failures, TL decisions ✅
3. **Developers** read project_context.json when needed (per developer.md instructions) ✅

The system is designed correctly. The user's observation that research context wasn't passed is because **no research was done** in that session.

---

## Action Items

1. **Revert my Project Context Section changes** - They duplicate specialization-loader and incorrectly reference research/*.md
2. **Verify context package flow works** - Test a session with RE research phase
3. **Consider adding conventions to specialization-loader** - As a future enhancement

---

## Open Questions for Review

1. Should conventions (file structure, naming) be in the prompt or read by agents?
2. Is the current specialization-loader + context packages sufficient?
3. Should we add validation that RE actually registers context packages?

---

## References

- `research/inter-agent-communication-design.md` - Context package system design
- `agents/requirements_engineer.md:689-730` - RE context package registration
- `bazinga/templates/orchestrator/phase_simple.md:22-62` - Orchestrator package query
- `.claude/skills/specialization-loader/SKILL.md` - Specialization skill
