# BAZINGA Agent subagent_type Mapping: Ultrathink Analysis

**Date:** 2025-11-28
**Context:** Should BAZINGA agents use different subagent_types instead of general-purpose for all?
**Decision:** Keep general-purpose for most, with nuanced reasoning
**Status:** Analysis Complete - Recommendation Provided

---

## Problem Statement

Currently, BAZINGA uses `subagent_type="general-purpose"` for ALL agents. Should we differentiate based on each agent's actual needs?

---

## Available subagent_types (from Claude Code)

**Source:** Claude Code system prompt (Task tool definition). These values may change as Claude Code evolves.

| subagent_type | Tools | Description | Key Characteristic |
|---------------|-------|-------------|-------------------|
| `general-purpose` | `*` (all) | "General-purpose agent for researching complex questions, searching for code, and **executing multi-step tasks**" | **Multi-step execution** |
| `Explore` | All tools | "**Fast agent** specialized for exploring codebases. Use for finding files by patterns, searching code for keywords, answering questions about codebase" | **Fast, breadth-focused** |
| `Plan` | All tools | Same as Explore (identical description) | **Fast, breadth-focused** |
| `statusline-setup` | Read, Edit only | "Configure user's Claude Code status line setting" | **Very limited, specialized** |
| `claude-code-guide` | Glob, Grep, Read, WebFetch, WebSearch | "Questions about Claude Code or Claude Agent SDK" | **Read-only, documentation** |

**⚠️ Note:** This table was extracted from the Claude Code system prompt as of 2025-11-28. If Claude Code updates its agent types, this document should be reviewed.

### Key Observations

1. **`general-purpose` = execution-focused** ("executing multi-step tasks")
2. **`Explore`/`Plan` = exploration-focused** ("Fast agent", "finding files", "answering questions")
3. **Both have "All tools"** - tool access is NOT the differentiator
4. **Behavioral optimization IS the differentiator** - "Fast" suggests breadth over depth
5. **`Plan` and `Explore` have identical descriptions** - unclear if there's any real distinction

**Critical insight:** The choice between subagent_types is about **behavioral optimization** (execution vs exploration, depth vs speed), NOT about which tools are available.

---

## BAZINGA Agent Analysis

### Agents That EXECUTE Multi-Step Tasks (Must Use general-purpose)

| Agent | Primary Actions | Why general-purpose |
|-------|----------------|---------------------|
| **Developer** | Write code, create files, run tests, fix bugs | Needs **execution-focused** behavior for multi-step implementation |
| **Senior Software Engineer** | Complex code, security-sensitive, architectural | Needs **depth** for complex multi-step tasks |
| **QA Expert** | Run test suites, validate behavior | Needs **execution-focused** behavior to run test commands |
| **Validator** | Run verification tests, check evidence | Needs **execution-focused** behavior for verification |

**Note:** While `Explore` also has "All tools", its **behavioral optimization** is for fast exploration, not multi-step execution. The distinction is about how the agent approaches tasks, not tool availability.

**Verdict:** ✅ These MUST remain `general-purpose`

### Agents That READ/ANALYZE Code (Candidates for Explore/Plan)

| Agent | Primary Actions | Tool Needs | Could Use Explore? |
|-------|----------------|------------|-------------------|
| **Tech Lead** | Review code, provide feedback, unblock | Read, Grep, Glob (no Write) | ⚠️ Maybe |
| **Project Manager** | Analyze requirements, plan tasks, coordinate | Read, Grep, Glob (no Write) | ⚠️ Maybe |
| **Investigator** | Deep-dive analysis, hypothesis testing | Read, Grep, Glob, sometimes Bash | ⚠️ Risky |

---

## Detailed Analysis by Agent

### Tech Lead - Could Use `Explore`?

**What Tech Lead does:**
- Reviews code quality and architecture
- Provides specific feedback on implementations
- Unblocks developers with concrete solutions
- Makes strategic technical decisions

**Arguments FOR Explore:**
- Tech Lead doesn't write code - just reads/reviews
- "Fast exploration" could speed up code reviews
- Explore has "all tools" so still has full access

**Arguments AGAINST Explore:**
- Tech Lead needs **depth**, not speed
- Architectural review requires **deep analysis**, not quick exploration
- "Fast agent" might sacrifice thoroughness for speed
- Complex security reviews need exhaustive analysis

**Verdict:** ⚠️ **Keep general-purpose** - Tech Lead's value is depth, not speed

### Project Manager - Could Use `Plan`?

**What PM does:**
- Analyzes requirements
- Creates task groups
- Decides execution mode (simple vs parallel)
- Tracks completion status
- Sends BAZINGA when truly complete

**Arguments FOR Plan:**
- PM doesn't implement - just plans/coordinates
- "Plan" subagent_type seems semantically perfect
- PM needs to understand codebase structure, not modify it

**Arguments AGAINST Plan:**
- PM runs on **Opus** for strategic decisions - needs depth
- Complexity scoring requires thorough analysis
- BAZINGA decision is critical - can't be "fast" and wrong
- `Plan` has identical description to `Explore` (not actually planning-focused)

**Verdict:** ⚠️ **Keep general-purpose** - PM's accuracy is paramount, can't sacrifice for speed

### Investigator - Could Use `Explore`?

**What Investigator does:**
- Deep-dive analysis of complex problems
- Hypothesis testing
- Iterative experimentation
- Sometimes instruments code with logging

**Arguments FOR Explore:**
- Primary job is exploring/finding root causes
- "Exploring codebases" matches the use case
- Could speed up hypothesis validation

**Arguments AGAINST Explore:**
- Investigator sometimes needs Bash (for diagnostics)
- Deep multi-hypothesis analysis needs depth, not speed
- "Fast" might miss subtle root causes
- Investigator is spawned for **complex** problems - needs thoroughness

**Verdict:** ⚠️ **Keep general-purpose** - Investigator's value is thoroughness in complex problems

---

## The "Fast" Problem

The key issue is the word **"Fast"** in Explore/Plan descriptions:

> "**Fast agent** specialized for exploring codebases"

This suggests these agents are optimized for:
- ✅ Quick file discovery
- ✅ Pattern matching across codebase
- ✅ Answering simple questions quickly
- ❌ Deep analysis
- ❌ Complex multi-step reasoning
- ❌ Exhaustive security review
- ❌ Architectural decision-making

**BAZINGA agents need DEPTH:**
- Tech Lead reviewing architecture needs depth
- PM scoring complexity needs depth
- Investigator finding root causes needs depth

"Fast" and "depth" are often trade-offs.

---

## Risk Analysis

### Risk of Using Explore/Plan for Analysis Agents

| Risk | Impact | Likelihood |
|------|--------|------------|
| Tech Lead misses security issue | High | Medium |
| PM sends premature BAZINGA | High | Medium |
| Investigator misses root cause | High | Medium |
| Reviews feel superficial | Medium | High |

### Risk of Keeping general-purpose for All

| Risk | Impact | Likelihood |
|------|--------|------------|
| Slightly slower execution | Low | Medium |
| Higher token usage | Low | Medium |

**The downside of general-purpose is minimal. The downside of wrong subagent_type is significant.**

---

## Final Recommendation

### Definitive Assignments

| Agent | subagent_type | Rationale |
|-------|--------------|-----------|
| **Developer** | `general-purpose` | Must write code, execute tests |
| **Senior Software Engineer** | `general-purpose` | Must write complex code |
| **QA Expert** | `general-purpose` | Must run test suites (Bash) |
| **Tech Lead** | `general-purpose` | Depth needed for architecture review |
| **Project Manager** | `general-purpose` | Accuracy needed for BAZINGA decision |
| **Investigator** | `general-purpose` | Thoroughness needed for root cause analysis |
| **Validator** | `general-purpose` | Must run verification tests (Bash) |

### Why Not Differentiate?

1. **"Fast" trades depth for speed** - Wrong trade-off for strategic roles that need thoroughness
2. **Risk vs reward is unfavorable** - Small speed gains, significant quality risks
3. **Tool access is identical** - Explore/Plan have "All tools", so no capability restriction benefit
4. **Behavioral optimization details are opaque** - We don't know exactly what "fast" sacrifices internally
5. **Consistency is valuable** - Single subagent_type reduces cognitive load and debugging complexity

---

## When WOULD Explore/Plan Be Appropriate?

**Good use cases for Explore (outside BAZINGA):**
- "Find all files that use the auth module"
- "What patterns exist for error handling?"
- "Where is the database connection configured?"
- Quick reconnaissance before detailed work

**Good use cases for Plan (if it had unique behavior):**
- Planning refactoring scope
- Estimating change impact
- Mapping dependencies

**NOT good for:**
- Code review (needs depth)
- Security analysis (needs thoroughness)
- Root cause investigation (needs exhaustiveness)
- BAZINGA validation (needs accuracy)

---

## Alternative Consideration: Hybrid Approach

Could we use Explore/Plan for SPECIFIC phases within agents?

**Example for Investigator:**
```
Phase 1: Explore (find relevant files quickly)
Phase 2: general-purpose (deep analysis of found files)
```

**Problems:**
1. Agents are spawned once, not in phases
2. Would require orchestrator changes
3. Complexity vs benefit is poor
4. Current approach works fine

**Verdict:** Not worth the complexity.

---

## Conclusion

**Keep `general-purpose` for all BAZINGA agents.**

The available subagent_types don't offer meaningful differentiation for our use case:
- `Explore`/`Plan` trade depth for speed (wrong trade-off)
- Tool access is identical (no restriction benefit)
- "Fast" is risky for strategic decisions
- Consistency reduces complexity

The right customization lever for BAZINGA is:
- **Model** (haiku/sonnet/opus) → Intelligence level
- **Prompt** (agent .md file) → Behavior/expertise
- **Not subagent_type** → Too blunt an instrument

---

## Lessons Learned

1. **subagent_type is primarily about optimization**, not capability restriction (since most have "All tools")
2. **"Fast" has trade-offs** - good for exploration, bad for deep analysis
3. **BAZINGA agents need depth** - they make critical decisions
4. **Consistency has value** - one fewer thing to debug/maintain
5. **When in doubt, use general-purpose** - it's the safest default

---

## References

- System prompt definition of subagent_types
- `agents/developer.md` - Implementation specialist
- `agents/techlead.md` - Review specialist
- `agents/project_manager.md` - Coordination specialist
- `agents/investigator.md` - Deep-dive specialist
- `agents/qa_expert.md` - Testing specialist
