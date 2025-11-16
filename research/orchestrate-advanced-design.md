# BAZINGA Orchestrate Advanced - Design Research

**Date**: 2025-11-16
**Author**: Claude
**Status**: Approved for Implementation

## Executive Summary

This document outlines the design for `/bazinga.orchestrate-advanced`, a new command that enhances BAZINGA's orchestration capabilities by adding an intelligent Requirements Discovery phase before execution.

**Key Innovation**: Pre-process user requests through a Requirements Engineer agent that performs active codebase discovery, risk analysis, and requirement clarification BEFORE the PM starts planning.

## Problem Statement

### Current State (bazinga.orchestrate)

Users provide simple text requests like "add user notifications". The PM receives this raw input and must:
- Figure out what type of notifications
- Search the codebase for existing infrastructure
- Estimate complexity blind
- Identify risks during execution (too late)
- Guess at parallelization opportunities

**Result**: PM works harder, makes suboptimal decisions, wastes time discovering during execution.

### Inspiration Source

The create-prompt.md methodology (https://github.com/mehdic/taches-cc-prompts/blob/main/meta-prompting/create-prompt.md) provides a framework for:
- Clarifying ambiguous requests
- Confirming understanding before proceeding
- Generating well-structured requirements

**However**, it's designed for creating prompts to save for later, not for immediate execution with codebase context.

## Solution Design

### What Makes BAZINGA Different

BAZINGA is unique because it:
1. **Executes immediately** - Not planning for later
2. **Has multi-agent context** - Requirements must work for PM, Devs, QA, Tech Lead
3. **Integrates with codebase** - We have access to the ACTUAL codebase
4. **Uses adaptive parallelism** - Need to identify what can run in parallel
5. **Has quality gates** - Security, coverage, lint will run - anticipate this
6. **Has Skills ecosystem** - Can leverage codebase-analysis, test-pattern-analysis, etc.

### Our Approach: Active Requirements Discovery

Instead of just clarifying user intent (like create-prompt.md), we **actively explore the codebase** to build comprehensive, execution-ready requirements.

## Architecture

### Information Flow

```
User: /bazinga.orchestrate-advanced "add notifications"
  ↓
.claude/commands/bazinga.orchestrate-advanced.md (slash command)
  ↓
STEP 1: Spawns Requirements Engineer agent
  ↓
Requirements Engineer (2-4 minutes):
  - Phase 1: CLARIFY (30s - interactive)
  - Phase 2: DISCOVER (90s - autonomous codebase exploration)
  - Phase 3: ASSESS (30s - analysis)
  - Phase 4: STRUCTURE (30s - synthesis)
  ↓
Returns Enhanced Requirements Document (markdown)
  ↓
STEP 2: orchestrate-advanced.md spawns orchestrator
  ↓
Orchestrator's prompt includes enhanced document as "requirements"
  ↓
Orchestrator spawns PM (normal flow)
  ↓
PM receives enhanced requirements (reads as markdown)
  ↓
Standard BAZINGA orchestration continues
```

### Key Design Decisions

#### Decision 1: Slash Command is Coordinator
**Why**: The slash command file orchestrates the two-phase process. No changes needed to orchestrator or PM.

#### Decision 2: Pass Enhanced Doc as Text Input
**Why**: Simpler than file-based handoff. Orchestrator and PM don't need to know about file locations.

#### Decision 3: PM Unchanged
**Why**: PM already handles markdown requirements. Enhanced doc is just better input - no special parsing needed.

#### Decision 4: Markdown Format (Not XML)
**Why**:
- PM naturally reads markdown
- Flexible structure (PM can adapt suggestions)
- PM retains decision authority (not pre-decided)
- Lighter weight than rigid XML schema

## Requirements Engineer Agent Design

### Four-Phase Process

#### Phase 1: CLARIFY (30s - Interactive)
**Goal**: Understand user intent and resolve ambiguity

**Process**:
1. Parse user request
2. Identify ambiguous terms
3. Ask targeted questions if needed
4. Confirm understanding

**Example**:
```
User: "add notifications"

Questions:
- What type? (email/push/in-app/SMS)
- What events trigger them?
- Urgency requirements?

User: "Email and in-app. New messages and mentions. Near real-time."

Confirmed: Email + in-app notifications for messages/mentions, ~30s delivery
```

#### Phase 2: DISCOVER (90s - Autonomous)
**Goal**: Explore codebase to find existing infrastructure, patterns, and gaps

**Tools Used**:
- **Grep**: Search for similar features (`notification`, `email`, `alert` patterns)
- **Glob**: Find related files (`**/notification*`, `**/email*`, `**/queue*`)
- **Read**: Examine reusable components, test patterns, architecture

**Output**:
- Existing infrastructure (what can be reused)
- Missing infrastructure (what must be built)
- Similar features (patterns to follow)
- Test patterns (how to test)
- Potential conflicts (breaking changes)

**Example**:
```
Found Existing:
✅ lib/email.py - EmailService class (reusable)
✅ lib/queue.py - TaskQueue for async processing
✅ User model has email field

Missing:
❌ No Notification model
❌ No notification API endpoints

Similar Features:
📋 lib/alerts.py - Uses observer pattern (good reference)
```

#### Phase 3: ASSESS (30s - Analysis)
**Goal**: Estimate complexity, identify parallelization, flag risks

**Analysis**:
1. **Complexity Estimation**:
   - Low: Reusing existing patterns
   - Medium: Some new patterns
   - High: New infrastructure

2. **Parallelization Analysis**:
   - Which features are independent?
   - What are the dependencies?
   - File overlap check

3. **Risk Identification**:
   - Security: Data exposure, injection risks
   - Performance: N+1 queries, scalability
   - Breaking Changes: Impact on existing code

**Example**:
```
Complexity:
- Email notifications: LOW (reuses EmailService)
- In-app system: MEDIUM (new model + API)

Parallelization:
- Email and in-app are independent
- Different files, can run parallel

Risks:
⚠️ HIGH: Email data exposure (sanitization needed)
⚠️ MEDIUM: N+1 query potential (batch loading)
✅ LOW: No breaking changes (new feature)
```

#### Phase 4: STRUCTURE (30s - Synthesis)
**Goal**: Generate execution-ready requirements document

**Output Format**: Enhanced Requirements Document (see below)

### Enhanced Requirements Document Format

```markdown
# Enhanced Requirements Document

## Original Request
[User's original text]

## Clarified Requirements
### Business Context
[Why this is needed, who uses it]

### Functional Requirements
[Given/When/Then format for each feature]

## Codebase Discovery
### Existing Infrastructure (REUSABLE)
[Components that already exist and can be leveraged]

### Missing Infrastructure (MUST BUILD)
[What needs to be created from scratch]

### Similar Features (LEARN FROM)
[Existing code that demonstrates patterns to follow]

## Risk Analysis
### Security Risks
[Issues, mitigations, verification methods]

### Performance Risks
[Potential bottlenecks, mitigations]

### Breaking Changes
[Impact on existing code]

## Suggested Task Breakdown
### Group A: [Name] (Complexity: X, Time: Y)
[Task details, can parallel: YES/NO]

### Group B: [Name] (Complexity: X, Time: Y)
[Task details, dependencies]

## Execution Recommendation
- **Mode**: SIMPLE/PARALLEL
- **Developers**: N
- **Reasoning**: [Why this approach]
- **Estimated Total**: X hours

## Testing Strategy
### Unit Tests (Developer)
[Specific test cases]

### Integration Tests (QA)
[End-to-end scenarios]

### Edge Cases (Must Cover)
[Boundary conditions, error cases]

## Success Criteria
[Testable, measurable outcomes]
```

## PM Integration

### How PM Uses Enhanced Requirements

**PM Step 1 (Analyze Requirements)**:
- Reads enhanced document as regular markdown
- Extracts codebase discoveries (knows what to reuse)
- Notes risk analysis (will brief Tech Lead)
- Understands complexity estimates

**PM Step 2 (Decide Mode)**:
- Sees recommendation: PARALLEL, 2 developers
- Sees reasoning: Groups independent
- Makes informed decision (can override if needed)

**PM Step 3 (Create Task Groups)**:
- Sees suggested breakdown with estimates
- Can use as-is or adjust based on PM judgment
- Has better context for group creation

**Result**: PM makes BETTER decisions with RICHER context.

### PM Autonomy Preserved

**Critical**: The enhanced doc provides **suggestions, not commands**.

The PM:
- ✅ Can accept suggestions
- ✅ Can modify task breakdown
- ✅ Can override mode recommendation
- ✅ Retains full decision authority

This is NOT an autopilot - it's enhanced intelligence.

## Comparison Table

| Aspect | create-prompt.md | Our Approach |
|--------|-----------------|--------------|
| **Purpose** | Create prompts to save | Immediate execution |
| **Codebase Awareness** | None (generic) | Active discovery with Grep/Read |
| **Execution Context** | Saved for later | Execution-ready |
| **Parallelization** | Not considered | Pre-analyzed with task groups |
| **Risk Analysis** | Not included | Security, performance, breaking changes |
| **Test Strategy** | Generic | Specific to discovered patterns |
| **PM Guidance** | None | Recommended mode + reasoning |
| **Time Investment** | Minimal (clarify only) | 3-5 min discovery worth it |
| **Format** | XML prompts | Markdown requirements |

## Benefits

### For Users
- 🎯 Clearer understanding of request before work begins
- ⚡ Faster execution (PM doesn't waste time discovering)
- 🔒 Risks identified upfront
- 📊 Better time estimates

### For PM
- 📚 Rich context about codebase
- 🧠 Informed decision-making
- ⚙️ Suggested task breakdown with complexity
- 🚀 Can focus on coordination vs discovery

### For Developers
- 🔧 Knows what components to reuse
- 📖 Has similar features to learn from
- 🧪 Clear test scenarios
- 🎨 Follows established patterns

### For Tech Lead
- 🔍 Aware of risks before review
- ✅ Knows what skills will check
- 🛡️ Planned mitigations
- 📋 Clear success criteria

## Implementation Files

### 1. `.claude/commands/bazinga.orchestrate-advanced.md`
**Purpose**: Slash command that coordinates two-phase process

**Responsibilities**:
1. Spawn Requirements Engineer with user request
2. Receive enhanced requirements document
3. Spawn orchestrator with enhanced doc as input

### 2. `agents/requirements_engineer.md`
**Purpose**: Agent definition for requirements discovery

**Responsibilities**:
1. Execute 4-phase process (Clarify → Discover → Assess → Structure)
2. Use Grep/Read/Glob for codebase exploration
3. Generate enhanced requirements document
4. Return markdown output

### 3. `agents/project_manager.md`
**Status**: NO CHANGES NEEDED

**Why**: PM already handles markdown requirements. Enhanced doc is just better input.

## User Experience

### Simple Request (use normal orchestrate)
```bash
User: /bazinga.orchestrate "add login page"

# Fast path - PM figures it out
```

### Complex/Ambiguous Request (use advanced)
```bash
User: /bazinga.orchestrate-advanced "improve our authentication system"

🔍 Requirements Engineer analyzing...

Questions:
1. What aspects to improve? (security/UX/performance)
2. Current pain points?
3. Constraints or requirements?

User: Add MFA and improve session management

✅ Clarified: Multi-factor auth + session management improvements

🔎 Discovering existing code...
✅ Found: AuthService at lib/auth.py
✅ Found: SessionManager at lib/session.py
❌ Missing: MFA infrastructure

⚙️ Complexity Analysis:
- Group A (MFA): MEDIUM - 120min (new infrastructure)
- Group B (Session): LOW - 60min (enhance existing)
- Mode: PARALLEL (independent features)

📋 Enhanced requirements ready. Starting orchestration...

[PM receives enriched context, proceeds with normal flow]
```

## Alternatives Considered

### Alternative 1: Enhanced PM Prompt
**Approach**: Make PM do the discovery work

**Rejected Because**:
- PM already has complex role (coordination)
- Mixing concerns (planning + discovery)
- Less modular/reusable

### Alternative 2: Parallel Analysis
**Approach**: Run discovery in parallel with PM

**Rejected Because**:
- More complex coordination
- PM might start before discovery completes
- Sequential is fine (requirements must be clear first)

### Alternative 3: Modify Existing Orchestrate
**Approach**: Make orchestrate always do discovery

**Rejected Because**:
- Adds overhead to simple cases
- Users can't opt out
- Breaking change for existing workflows

### Alternative 4: XML Output Format
**Approach**: Use rigid XML structure like create-prompt.md

**Rejected Because**:
- PM would need XML parser
- Less flexible (PM can't adapt suggestions)
- Heavier weight than needed
- Markdown is more natural for PM

## Future Enhancements

### Phase 2 Possibilities
1. **Integration with spec-kit**: Use .specify artifacts if available
2. **Skill pre-analysis**: Run codebase-analysis during discovery
3. **Cost estimation**: Calculate expected token usage upfront
4. **Template library**: Save common requirement patterns
5. **Learning mode**: Improve suggestions based on past orchestrations

### Metrics to Track
- Time saved in PM planning phase
- Accuracy of complexity estimates
- Adoption rate (advanced vs normal)
- User satisfaction scores
- Reduction in revision counts

## Success Criteria

### Implementation Complete When:
- ✅ Requirements Engineer agent created
- ✅ orchestrate-advanced command created
- ✅ Flow tested end-to-end
- ✅ Documentation complete

### Validation Tests:
1. **Simple request**: "add a logout button" → Should clarify and discover
2. **Complex request**: "improve notifications" → Should ask questions
3. **Ambiguous request**: "make it better" → Should seek clarification
4. **No existing code**: Should identify all must-build components
5. **Lots of existing code**: Should identify all reusable components

## Conclusion

The `/bazinga.orchestrate-advanced` command adds an intelligent requirements discovery layer that:
- Clarifies ambiguous requests
- Explores the codebase actively
- Identifies risks and opportunities
- Provides execution-ready context to PM

This approach is **inspired by** create-prompt.md's clarity-first methodology but **uniquely designed for** BAZINGA's multi-agent, codebase-integrated, execution-oriented context.

**Recommendation**: Implement as designed. Start with MVP (4 phases, markdown output), iterate based on usage.

---

**Next Steps**:
1. Create `agents/requirements_engineer.md`
2. Create `.claude/commands/bazinga.orchestrate-advanced.md`
3. Test with sample requests
4. Document usage in main README
