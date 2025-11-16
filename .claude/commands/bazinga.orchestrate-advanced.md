---
description: Enhanced orchestration with intelligent requirements discovery and codebase analysis. Use when requests are complex, ambiguous, or would benefit from deeper analysis before execution.
---

# BAZINGA Orchestrate Advanced - Requirements Discovery + Execution

**User Request**: $ARGUMENTS

## Overview

This command adds an intelligent **Requirements Discovery** phase before standard BAZINGA orchestration.

**When to Use This Command**:
- ✅ Complex requests with multiple features
- ✅ Ambiguous requests needing clarification
- ✅ Large-scale changes requiring codebase analysis
- ✅ New features where existing patterns should be discovered
- ✅ Requests where risk assessment would add value

**When to Use `/bazinga.orchestrate` Instead**:
- Simple, well-defined requests
- Small bug fixes or typos
- Documentation-only changes
- Quick iterations on known work

---

## Two-Phase Workflow

```
Phase 1: Requirements Discovery (2-4 min)
  └─ Spawn Requirements Engineer
  └─ Clarify + Discover + Assess + Structure
  └─ Generate Enhanced Requirements Document
      ↓
Phase 2: Standard Orchestration (normal BAZINGA flow)
  └─ Spawn Orchestrator with Enhanced Requirements
  └─ PM receives rich context (discoveries, estimates, risks)
  └─ Execution proceeds with better decisions
```

---

## Phase 1: Requirements Discovery

### What Will Happen

I will spawn a **Requirements Engineer** agent that will:

1. **Clarify** your request (ask questions if ambiguous)
2. **Discover** existing codebase infrastructure
3. **Assess** complexity, parallelization opportunities, and risks
4. **Structure** enhanced requirements for the PM

### Expected Output

The Requirements Engineer will generate an **Enhanced Requirements Document** containing:
- ✅ Clarified requirements (Given/When/Then format)
- ✅ Codebase discoveries (reusable components, similar features)
- ✅ Risk analysis (security, performance, breaking changes)
- ✅ Suggested task breakdown with complexity estimates
- ✅ Testing strategy and success criteria

### Starting Discovery Phase...

I'm now spawning the Requirements Engineer to analyze your request.

**Instructions for Requirements Engineer**:

Read the full agent definition from `agents/requirements_engineer.md` and execute the four-phase workflow:

**Phase 1: CLARIFY** - Understand user intent, ask questions if needed
**Phase 2: DISCOVER** - Use Grep/Glob/Read to explore codebase
**Phase 3: ASSESS** - Estimate complexity, identify parallelization, flag risks
**Phase 4: STRUCTURE** - Generate Enhanced Requirements Document

**User Request to Analyze**: $ARGUMENTS

**Your Output**: Complete Enhanced Requirements Document in markdown format following the template in your agent definition.

---

## Phase 2: Standard BAZINGA Orchestration

### What Will Happen Next

Once the Requirements Engineer completes analysis, I will:

1. Take the Enhanced Requirements Document
2. Spawn the standard BAZINGA Orchestrator
3. Pass the enhanced document as the "User Requirements"
4. Let PM and team proceed with full context

### Benefits for the Team

**For PM**:
- Knows what components are reusable (no blind searching)
- Has complexity estimates (better mode decisions)
- Aware of risks upfront (can brief Tech Lead)
- Sees suggested task breakdown (informed group creation)

**For Developers**:
- Knows what to reuse (EmailService, TaskQueue, etc.)
- Has similar features to reference (established patterns)
- Clear test scenarios (knows what to cover)
- Risk awareness (security/performance considerations)

**For QA**:
- Has test scenarios defined upfront
- Knows edge cases to cover
- Understands success criteria

**For Tech Lead**:
- Aware of risks before review (security, performance)
- Knows what skills will validate (security-scan, etc.)
- Has planned mitigations

---

## Execution Instructions for This Session

**Step 1**: Spawn Requirements Engineer with user request

Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Requirements discovery and codebase analysis",
  prompt: [Read agents/requirements_engineer.md and provide user request: $ARGUMENTS]
)

**Step 2**: Wait for Requirements Engineer to return Enhanced Requirements Document

**Step 3**: Spawn standard orchestrator with enhanced requirements

SlashCommand(command: "/bazinga.orchestrate [Enhanced Requirements Document from Step 2]")

This passes the enhanced requirements to the normal orchestration flow, where the orchestrator will spawn PM, who will receive the rich context.

---

## Progress Display

I will show you:
- 🔍 Phase 1 progress (clarification questions, discoveries)
- 📋 Enhanced Requirements Document (full output)
- 🚀 Phase 2 start (orchestration begins)
- [Then standard BAZINGA progress messages]

---

## Time Expectations

- **Requirements Discovery**: 2-4 minutes
- **Standard Orchestration**: Depends on complexity (normal timing)
- **Total Overhead**: 2-4 minutes upfront, but saves 15-30 minutes during execution

The upfront investment in discovery prevents:
- PM wasting time searching codebase
- Developers discovering reusable components late
- Risks found during execution (too late)
- Suboptimal parallelization decisions
- Unnecessary revisions from unclear requirements

---

**Let's begin Phase 1: Requirements Discovery...**
