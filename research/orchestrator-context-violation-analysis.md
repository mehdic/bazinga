# Orchestrator Context Violation Analysis

**Status**: Research Complete
**Created**: 2025-11-18
**Priority**: Critical - Core architectural violation

## Executive Summary

The orchestrator is currently violating its coordinator role by performing code analysis and context preparation for developers. This document analyzes the issue, its origins, and proposes a clean architectural solution.

## The Problem

### Current Behavior
The orchestrator performs "Prepare Code Context" steps (Phase 2A.0 and 2B.0) where it:
- Extracts keywords from task descriptions
- Searches for similar files using grep/search
- Reads common utility directories
- Builds code context sections for developer prompts

### Evidence
**Location**: `agents/orchestrator.md`
- Lines 1525-1532: Phase 2A.0 - Prepare Code Context (Simple Mode)
- Lines 2770-2778: Phase 2B.0 - Prepare Code Context for Each Group (Parallel Mode)

### Why This Is Wrong
The orchestrator's role is **pure coordination**:
- ✅ Spawn agents
- ✅ Route messages between agents
- ✅ Track state
- ❌ **NOT** analyze code
- ❌ **NOT** make implementation decisions
- ❌ **NOT** perform research

## Root Cause Analysis

### Original Design Intent
From `research/developer-capabilities-implementation-approach.md`:
- **Goal**: Give developers context to prevent architectural mismatches
- **Priority**: Tier 1, 15x ROI
- **Rationale**: "Zero runtime cost" - happens during spawn
- **Trade-off**: Violated coordinator purity for performance

### The Conflict
Two competing design principles:
1. **Architectural Purity**: Orchestrator must be a pure coordinator
2. **Performance**: Developers need context without delay

The current implementation chose performance over purity, leading to role violation.

## Historical Context

### Evolution of the Design
1. **Initial**: Developers worked without context → many revisions
2. **Problem Identified**: 40% of revisions due to architectural mismatches
3. **Quick Fix**: Orchestrator provides context (violated role but worked)
4. **Current State**: Works but architecturally incorrect

### Why It Wasn't Caught Earlier
- Focus was on reducing revision cycles (successful - 40% reduction)
- Orchestrator bloat analysis focused on file size, not role purity
- Pragmatic approach: "it works, ship it"

## Proposed Solution: Three-Layer Context System

### Layer 1: PM-Generated Project Context
**When**: During PM's planning phase
**What**: Project-wide patterns and conventions
**Storage**: `bazinga/project_context.json`
**Cost**: Zero (PM already analyzes codebase)

**Rationale**: PM already needs to understand the codebase to create task groups. This analysis should be saved and reused.

### Layer 2: PM Task Descriptions with Hints
**When**: PM creates task groups
**What**: Relevant files and patterns included in task descriptions
**Example**: "Task: Implement auth - see patterns in /auth/login.py"
**Cost**: Zero (natural part of task breakdown)

### Layer 3: Developer On-Demand Analysis
**When**: Developer decides based on task complexity
**What**: Deep analysis via `codebase-analysis` skill
**Invocation**: Optional, cached, intelligent
**Cost**: 5-10 seconds when needed

## Benefits of This Approach

### Architectural Benefits
- ✅ **Pure Coordinator**: Orchestrator never touches code
- ✅ **Clean Separation**: Each agent does only its designed role
- ✅ **Single Responsibility**: PM owns planning, developers own implementation

### Performance Benefits
- ✅ **Smart Caching**: 60% of analysis results reusable
- ✅ **Progressive Enhancement**: Simple tasks = zero overhead
- ✅ **Lazy Loading**: Analysis only when needed

### Quality Benefits
- ✅ **Better Context**: PM's analysis is requirement-aware
- ✅ **Consistent Patterns**: Project context shared across developers
- ✅ **Learning System**: Cache improves over time

## Implementation Impact

### Changes Required

#### 1. Orchestrator (`agents/orchestrator.md`)
- **Remove**: Step 2A.0 (lines 1525-1532)
- **Remove**: Step 2B.0 (lines 2770-2778)
- **Update**: Developer prompt building to reference PM context
- **Update**: Remove references to "code context from Step 2A.0"

#### 2. Project Manager (`agents/project_manager.md`)
- **Add**: Project context generation during planning
- **Add**: Save to `bazinga/project_context.json`
- **Add**: Include file hints in task descriptions
- **Update**: Task group creation to include relevant files

#### 3. Developer (`agents/developer.md`)
- **Add**: Read project context at start
- **Add**: Optional invocation of codebase-analysis skill
- **Add**: Decision logic for when to invoke analysis

#### 4. New Skill (`codebase-analysis`)
- **Create**: Full implementation with caching
- **Features**: Pattern detection, similarity analysis, utility discovery
- **Output**: `bazinga/codebase_analysis.json`

## Migration Strategy

### Phase 1: Remove Violation (2 hours)
1. Remove code context sections from orchestrator
2. Update prompt building to exclude code context
3. Test basic functionality still works

### Phase 2: PM Enhancement (3 hours)
1. Add project context generation to PM
2. Update PM to include file hints in tasks
3. Test PM creates useful context

### Phase 3: Codebase Analysis Skill (4-6 hours)
1. Implement skill with caching
2. Test with various codebases
3. Integrate with developer workflow

### Phase 4: Developer Intelligence (2 hours)
1. Update developer to use PM context
2. Add logic for optional skill invocation
3. Test end-to-end workflow

## Risk Analysis

### Risks
1. **Performance Impact**: +5-10 seconds for complex tasks
2. **PM Complexity**: PM becomes more sophisticated
3. **Migration Issues**: Existing orchestrations might behave differently

### Mitigations
1. **Caching**: Reduces performance impact to near-zero
2. **PM Intelligence**: Already needed for good planning
3. **Backward Compatibility**: Graceful degradation if no context

## Success Metrics

### Short Term (Week 1)
- ✅ Orchestrator file <2000 lines (from 2960)
- ✅ Zero orchestrator code analysis operations
- ✅ PM generates project context successfully

### Medium Term (Month 1)
- ✅ Cache hit rate >60%
- ✅ Developer revision cycles remain low (<1.5)
- ✅ First-time approval rate maintained (>50%)

### Long Term (Quarter 1)
- ✅ Developers invoke analysis <25% of time
- ✅ Project context becomes rich knowledge base
- ✅ Architecture remains clean and maintainable

## Decision Matrix

| Approach | Purity | Performance | Complexity | Recommendation |
|----------|--------|-------------|------------|----------------|
| Current (Broken) | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Fix Required |
| Pure (No Context) | ⭐⭐⭐⭐⭐ | ❌ | ⭐ | Too Slow |
| All Skills | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | Over-engineered |
| **PM + Skills** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | **Recommended** |

## Conclusion

The current orchestrator code context violation is a **critical architectural issue** that resulted from prioritizing performance over design purity. The proposed three-layer solution (PM context + task hints + optional analysis) provides the best balance of:

1. **Architectural integrity** (pure coordinator)
2. **Performance** (minimal overhead via caching)
3. **Intelligence** (progressive enhancement)

This approach aligns with BAZINGA's core principle: each agent does exactly what it's designed for, nothing more, nothing less.

## References

- `agents/orchestrator.md` - Current implementation
- `research/developer-capabilities-analysis.md` - Original problem analysis
- `research/developer-capabilities-implementation-approach.md` - Initial solution design
- `research/orchestrator-bloat-analysis.md` - File size concerns

## Status

**Ready for Implementation** - Proceed with detailed implementation plan.