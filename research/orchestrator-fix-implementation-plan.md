# Orchestrator Context Fix - Detailed Implementation Plan

**Status**: Ready for Implementation
**Created**: 2025-11-18
**Estimated Time**: 11-13 hours total
**Priority**: Critical

## Implementation Overview

This plan fixes the orchestrator's role violation where it performs code analysis instead of pure coordination. The solution implements a three-layer context system with PM-generated context, task hints, and optional developer analysis.

## Pre-Implementation Checklist

- [ ] Create feature branch: `fix-orchestrator-context-violation`
- [ ] Backup current orchestrator.md
- [ ] Review all affected files
- [ ] Ensure tests are passing before changes

## Phase 1: Remove Orchestrator Violations (2 hours)

### 1.1 Remove Code Context Sections from orchestrator.md

**File**: `agents/orchestrator.md`

**Step 1: Remove Phase 2A.0 Section**
- **Location**: Lines 1525-1532
- **Action**: Delete entire "Step 2A.0: Prepare Code Context" section
- **Validation**: Ensure Step 2A.1 follows directly after Phase 2A header

**Step 2: Remove Phase 2B.0 Section**
- **Location**: Lines 2770-2778
- **Action**: Delete entire "Step 2B.0: Prepare Code Context for Each Group" section
- **Validation**: Ensure Step 2B.1 follows directly after Phase 2B header

**Step 3: Update Developer Prompt Building References**
- **Location**: Line ~1559 (Phase 2A)
- **Find**: "Code context from Step 2A.0"
- **Replace**: "Task description from PM"
- **Validation**: No references to "Step 2A.0" or "Step 2B.0" remain

**Step 4: Update Parallel Mode References**
- **Location**: Line ~2811 (Phase 2B)
- **Find**: "Code context for THIS group (from Step 2B.0)"
- **Replace**: "Task description for THIS group from PM"
- **Validation**: Check all developer prompt sections

### 1.2 Update Command File

**File**: `.claude/commands/bazinga.orchestrate.md`

**Action**: Run build script to sync changes
```bash
./scripts/build-slash-commands.sh
```

**Validation**: Verify command file matches orchestrator.md

### 1.3 Test Basic Functionality

**Test Case 1: Simple Mode**
```bash
# Test orchestration still works without code context
/orchestrate "Add a simple hello world endpoint"
```
**Expected**: Orchestration proceeds, developer receives task without code context

**Test Case 2: Parallel Mode**
```bash
# Test parallel spawning still works
/orchestrate "Implement user CRUD operations"
```
**Expected**: Multiple developers spawn correctly

## Phase 2: Enhance PM with Context Generation (3 hours)

### 2.1 Add Project Context Generation to PM

**File**: `agents/project_manager.md`

**Location**: After requirements analysis, before task group creation

**Add Section**: "Project Context Generation"
```markdown
## Project Context Generation

After analyzing requirements and before creating task groups, generate project context:

### When to Generate Context

Generate project context on:
- First planning iteration (no existing context)
- Major scope changes
- New feature areas being touched

### Context Structure

Save to `bazinga/project_context.json`:

{
  "project_type": "Detected project type (REST API, CLI tool, library, etc)",
  "primary_language": "Main language and framework",
  "architecture_patterns": [
    "Patterns found (MVC, service layer, repository, etc)"
  ],
  "conventions": {
    "error_handling": "How errors are handled",
    "authentication": "Auth approach if present",
    "validation": "Validation approach",
    "testing": "Test framework and patterns"
  },
  "key_directories": {
    "services": "Business logic location",
    "models": "Data models location",
    "utilities": "Shared utilities location",
    "tests": "Test files location"
  },
  "common_utilities": [
    {
      "name": "Utility name",
      "location": "File path",
      "purpose": "What it does"
    }
  ],
  "test_framework": "Testing framework used",
  "coverage_target": "Expected coverage percentage",
  "generated_at": "ISO timestamp",
  "session_id": "Current session ID"
}

### Context Discovery Process

1. **Detect Project Type**
   - Check for framework files (package.json, requirements.txt, go.mod)
   - Identify main entry points
   - Detect API vs CLI vs library

2. **Find Architecture Patterns**
   - Look for common directories (controllers, services, models)
   - Identify layering approach
   - Detect design patterns in use

3. **Extract Conventions**
   - Read a few files to identify style
   - Find error handling patterns
   - Identify naming conventions

4. **Discover Utilities**
   - List files in common utility directories
   - Extract exported functions/classes
   - Note their purposes

### Saving Context

Invoke bazinga-db skill to save:

bazinga-db, please save project context:
Session ID: {session_id}
Context Type: project_context
Data: {context_json}

Then write to file for developer access:
Write to: bazinga/project_context.json
```

### 2.2 Update Task Group Creation

**Location**: Task group creation section

**Enhancement**: Include file hints in task descriptions

**Original Task Format**:
```
Group A: User Authentication
- Implement login endpoint
- Add JWT token generation
```

**Enhanced Task Format**:
```
Group A: User Authentication
- Implement login endpoint
- Add JWT token generation

Relevant files:
- Existing auth: /auth/basic_auth.py
- User model: /models/user.py
- JWT utility: /utils/token.py
- Similar endpoint: /api/register.py

Key patterns:
- Use service layer pattern (see /services/user_service.py)
- Error handling via error_response() from /utils/responses.py
- Validation using validators from /utils/validators.py
```

### 2.3 Add Context Check at PM Start

**Location**: Beginning of PM workflow

**Add Logic**:
```markdown
## Initial Context Check

1. Check if bazinga/project_context.json exists
2. If exists and age < 1 hour:
   - Load and use existing context
3. If not exists or stale:
   - Generate new project context
   - Save to file

This ensures context is always available for developers.
```

## Phase 3: Create Codebase Analysis Skill (4-6 hours)

### 3.1 Create Skill Directory Structure

**Create directories**:
```bash
mkdir -p .claude/skills/codebase-analysis
cd .claude/skills/codebase-analysis
```

**Create files**:
- `SKILL.md` - Skill definition
- `scripts/analyze_codebase.py` - Main analysis script
- `scripts/pattern_detector.py` - Pattern detection logic
- `scripts/similarity.py` - Code similarity functions
- `scripts/cache_manager.py` - Caching logic

### 3.2 Implement SKILL.md

**File**: `.claude/skills/codebase-analysis/SKILL.md`

```markdown
---
version: 1.0.0
name: codebase-analysis
description: Analyzes codebase to find similar features, reusable utilities, and architectural patterns
author: BAZINGA Team
tags: [development, analysis, codebase]
allowed-tools: [Bash, Read]
---

# Codebase Analysis Skill

You are the codebase-analysis skill. Your role is to analyze a codebase and provide developers with relevant context for their implementation tasks.

## When to Invoke This Skill

You should be invoked when:
- A developer needs to understand existing patterns before implementation
- Complex features require architectural guidance
- Reusable utilities need to be discovered
- Similar features exist that could be referenced

## Your Task

When invoked with a task description:

### Step 1: Execute Analysis Script

Run the analysis script with the task:

```bash
python3 .claude/skills/codebase-analysis/scripts/analyze_codebase.py \
  --task "$TASK_DESCRIPTION" \
  --session "$SESSION_ID" \
  --cache-enabled
```

### Step 2: Read Analysis Results

Read the generated analysis:

```bash
cat bazinga/codebase_analysis.json
```

### Step 3: Return Summary

Return a structured summary including:
- Similar features found (with file paths)
- Reusable utilities discovered
- Architectural patterns to follow
- Suggested implementation approach

## Example Invocation

**Input**: "Implement password reset functionality"

**Your Actions**:
1. Run analysis script
2. Read results from bazinga/codebase_analysis.json
3. Return summary

**Output**:
```
CODEBASE ANALYSIS COMPLETE

Similar Features Found:
- User registration (auth/register.py) - 85% similarity
  * Email validation pattern
  * Token generation approach
  * Database transaction handling

Reusable Utilities:
- EmailService (utils/email.py) - send_email(), validate_email()
- TokenGenerator (utils/tokens.py) - generate_token(), verify_token()
- PasswordHasher (utils/crypto.py) - hash_password(), verify_password()

Architectural Patterns:
- Service layer pattern (all business logic in services/)
- Repository pattern for data access
- Decorator-based authentication

Suggested Approach:
1. Create PasswordResetService in services/
2. Reuse EmailService for sending reset emails
3. Use TokenGenerator for reset tokens
4. Follow transaction pattern from register.py

Full details saved to: bazinga/codebase_analysis.json
```

## Cache Behavior

The skill maintains a cache to improve performance:
- Project-wide patterns: Cached for 1 hour
- Utilities: Cached for entire session
- Similar features: Always fresh (task-specific)

Cache location: bazinga/.analysis_cache/

## Error Handling

If analysis fails:
- Return partial results if available
- Indicate which parts failed
- Suggest manual exploration as fallback
```

### 3.3 Implement Core Analysis Script

**File**: `.claude/skills/codebase-analysis/scripts/analyze_codebase.py`

**Key Components**:

```python
#!/usr/bin/env python3
"""
Codebase analysis for providing context to developers.
"""

import json
import os
import sys
import argparse
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from pattern_detector import PatternDetector
from similarity import SimilarityFinder
from cache_manager import CacheManager

class CodebaseAnalyzer:
    def __init__(self, task: str, session_id: str, cache_enabled: bool = True):
        self.task = task
        self.session_id = session_id
        self.cache_enabled = cache_enabled
        self.cache = CacheManager("bazinga/.analysis_cache") if cache_enabled else None
        self.pattern_detector = PatternDetector()
        self.similarity_finder = SimilarityFinder()

    def analyze(self) -> Dict[str, Any]:
        """Main analysis entry point."""
        results = {
            "task": self.task,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "cache_hits": 0,
            "cache_misses": 0
        }

        # Get or compute project patterns (cacheable)
        patterns_cache_key = "project_patterns"
        if self.cache and self.cache.get(patterns_cache_key, max_age_hours=1):
            results["project_patterns"] = self.cache.get(patterns_cache_key)
            results["cache_hits"] += 1
        else:
            results["project_patterns"] = self.pattern_detector.detect_patterns()
            if self.cache:
                self.cache.set(patterns_cache_key, results["project_patterns"])
            results["cache_misses"] += 1

        # Get or compute utilities (cacheable)
        utilities_cache_key = f"utilities_{self.session_id}"
        if self.cache and self.cache.get(utilities_cache_key):
            results["utilities"] = self.cache.get(utilities_cache_key)
            results["cache_hits"] += 1
        else:
            results["utilities"] = self.find_utilities()
            if self.cache:
                self.cache.set(utilities_cache_key, results["utilities"])
            results["cache_misses"] += 1

        # Find similar features (NOT cacheable - task specific)
        results["similar_features"] = self.similarity_finder.find_similar(self.task)
        results["cache_misses"] += 1

        # Generate suggestions based on analysis
        results["suggested_approach"] = self.generate_suggestions(results)

        # Calculate cache efficiency
        total_operations = results["cache_hits"] + results["cache_misses"]
        results["cache_efficiency"] = f"{(results['cache_hits'] / total_operations * 100):.1f}%" if total_operations > 0 else "0%"

        return results

    def find_utilities(self) -> List[Dict[str, Any]]:
        """Find reusable utilities in common directories."""
        utilities = []
        utility_dirs = ["utils", "helpers", "lib", "common", "shared"]

        for dir_name in utility_dirs:
            for root, dirs, files in os.walk("."):
                if dir_name in root.split(os.sep):
                    for file in files:
                        if file.endswith(('.py', '.js', '.ts', '.go', '.java')):
                            file_path = os.path.join(root, file)
                            utilities.append({
                                "name": file.replace('.py', '').replace('.js', ''),
                                "path": file_path,
                                "functions": self.extract_functions(file_path)
                            })

        return utilities

    def extract_functions(self, file_path: str) -> List[str]:
        """Extract function signatures from a file."""
        functions = []
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    # Simple pattern matching for function definitions
                    if 'def ' in line or 'function ' in line or 'func ' in line:
                        # Extract function name
                        func_name = line.strip().split('(')[0].split()[-1]
                        functions.append(func_name)
        except:
            pass
        return functions[:10]  # Limit to top 10 functions

    def generate_suggestions(self, results: Dict[str, Any]) -> str:
        """Generate implementation suggestions based on analysis."""
        suggestions = []

        # Based on patterns found
        if results.get("project_patterns"):
            patterns = results["project_patterns"]
            if "service_layer" in patterns:
                suggestions.append("Create service class in services/ directory")
            if "repository_pattern" in patterns:
                suggestions.append("Use repository pattern for data access")

        # Based on similar features
        if results.get("similar_features"):
            similar = results["similar_features"][0] if results["similar_features"] else None
            if similar:
                suggestions.append(f"Follow pattern from {similar['file']}")

        # Based on utilities
        if results.get("utilities"):
            relevant_utils = [u for u in results["utilities"] if any(
                keyword in u["name"].lower()
                for keyword in self.task.lower().split()
            )]
            if relevant_utils:
                suggestions.append(f"Reuse {relevant_utils[0]['name']} from {relevant_utils[0]['path']}")

        return " | ".join(suggestions) if suggestions else "Implement following project conventions"

    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save analysis results to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Analyze codebase for implementation context')
    parser.add_argument('--task', required=True, help='Task description')
    parser.add_argument('--session', required=True, help='Session ID')
    parser.add_argument('--cache-enabled', action='store_true', help='Enable caching')
    parser.add_argument('--output', default='bazinga/codebase_analysis.json', help='Output file path')

    args = parser.parse_args()

    analyzer = CodebaseAnalyzer(
        task=args.task,
        session_id=args.session,
        cache_enabled=args.cache_enabled
    )

    results = analyzer.analyze()
    analyzer.save_results(results, args.output)

    print(f"Analysis complete. Results saved to {args.output}")
    print(f"Cache efficiency: {results['cache_efficiency']}")

if __name__ == "__main__":
    main()
```

### 3.4 Implement Supporting Modules

**File**: `.claude/skills/codebase-analysis/scripts/pattern_detector.py`

```python
#!/usr/bin/env python3
"""Pattern detection for architectural patterns."""

import os
from typing import Dict, List, Any

class PatternDetector:
    def detect_patterns(self) -> Dict[str, Any]:
        """Detect architectural patterns in the codebase."""
        patterns = {}

        # Check for service layer
        if os.path.exists("services") or os.path.exists("src/services"):
            patterns["service_layer"] = True

        # Check for repository pattern
        if os.path.exists("repositories") or os.path.exists("src/repositories"):
            patterns["repository_pattern"] = True

        # Check for MVC
        if all(os.path.exists(d) for d in ["models", "views", "controllers"]):
            patterns["mvc"] = True

        # Check for factory pattern
        if os.path.exists("factories") or any(
            "factory" in f.lower() for f in os.listdir(".")
            if os.path.isfile(f)
        ):
            patterns["factory_pattern"] = True

        # Detect testing framework
        if os.path.exists("pytest.ini") or os.path.exists("setup.cfg"):
            patterns["test_framework"] = "pytest"
        elif os.path.exists("jest.config.js"):
            patterns["test_framework"] = "jest"
        elif os.path.exists("go.mod"):
            patterns["test_framework"] = "go test"

        return patterns
```

**File**: `.claude/skills/codebase-analysis/scripts/similarity.py`

```python
#!/usr/bin/env python3
"""Find similar code to a given task."""

import os
import re
from typing import List, Dict, Any
from difflib import SequenceMatcher

class SimilarityFinder:
    def find_similar(self, task: str) -> List[Dict[str, Any]]:
        """Find files similar to the given task."""
        # Extract keywords from task
        keywords = self.extract_keywords(task)
        similar_files = []

        # Search for files containing keywords
        for root, dirs, files in os.walk("."):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'dist', 'build']]

            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.go', '.java')):
                    file_path = os.path.join(root, file)
                    score = self.calculate_similarity(file_path, keywords)
                    if score > 0.3:  # 30% similarity threshold
                        similar_files.append({
                            "file": file_path,
                            "similarity": score,
                            "matched_keywords": self.get_matched_keywords(file_path, keywords)
                        })

        # Sort by similarity score
        similar_files.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_files[:5]  # Return top 5

    def extract_keywords(self, task: str) -> List[str]:
        """Extract meaningful keywords from task description."""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'implement',
                     'add', 'create', 'make', 'build', 'write'}

        # Extract words
        words = re.findall(r'\b\w+\b', task.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def calculate_similarity(self, file_path: str, keywords: List[str]) -> float:
        """Calculate similarity score between file and keywords."""
        try:
            with open(file_path, 'r') as f:
                content = f.read().lower()

            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in content)

            # Calculate similarity as ratio of matched keywords
            if keywords:
                return matches / len(keywords)
            return 0.0

        except:
            return 0.0

    def get_matched_keywords(self, file_path: str, keywords: List[str]) -> List[str]:
        """Get list of keywords that matched in the file."""
        matched = []
        try:
            with open(file_path, 'r') as f:
                content = f.read().lower()

            for keyword in keywords:
                if keyword in content:
                    matched.append(keyword)

        except:
            pass

        return matched
```

**File**: `.claude/skills/codebase-analysis/scripts/cache_manager.py`

```python
#!/usr/bin/env python3
"""Cache management for analysis results."""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib

class CacheManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get(self, key: str, max_age_hours: Optional[int] = None) -> Optional[Any]:
        """Get cached value if it exists and is not stale."""
        cache_file = os.path.join(self.cache_dir, f"{self._hash_key(key)}.json")

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check age if specified
            if max_age_hours:
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cached_time > timedelta(hours=max_age_hours):
                    return None

            return cache_data['value']

        except:
            return None

    def set(self, key: str, value: Any):
        """Set cached value."""
        cache_file = os.path.join(self.cache_dir, f"{self._hash_key(key)}.json")

        cache_data = {
            'key': key,
            'value': value,
            'timestamp': datetime.now().isoformat()
        }

        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def _hash_key(self, key: str) -> str:
        """Hash key for filename."""
        return hashlib.md5(key.encode()).hexdigest()[:16]
```

### 3.5 Add Skill to Configuration

**File**: `bazinga/skills_config.json`

**Add to developer skills**:
```json
{
  "developer": {
    "codebase-analysis": {
      "status": "optional",
      "when": "Before implementation for complex tasks",
      "output": "bazinga/codebase_analysis.json"
    }
  }
}
```

## Phase 4: Update Developer Agent (2 hours)

### 4.1 Add Context Awareness to Developer

**File**: `agents/developer.md`

**Add Section**: "Context Discovery"

```markdown
## Context Discovery

Before starting implementation:

### Step 1: Check for Project Context

Check if PM has provided project context:
```bash
if [ -f "bazinga/project_context.json" ]; then
    cat bazinga/project_context.json
fi
```

Use this context to understand:
- Project conventions
- Available utilities
- Architecture patterns
- Testing approach

### Step 2: Review PM Task Description

The PM's task description includes:
- Specific requirements
- Relevant files to reference
- Key patterns to follow

Extract these hints and review mentioned files.

### Step 3: Decide on Deep Analysis

For complex tasks, invoke codebase analysis:

**When to invoke**:
- Task involves new feature area
- Multiple integration points
- Uncertainty about patterns
- Need to find similar implementations

**How to invoke**:
```bash
/codebase-analysis "Your specific task description"
```

**When to skip**:
- Simple bug fixes
- Clear, isolated changes
- PM provided sufficient context
- Familiar with the area

### Step 4: Begin Implementation

With context gathered, proceed with implementation following discovered patterns.
```

### 4.2 Update Developer Workflow

**Location**: Main workflow section

**Update to include**:
1. Context discovery before implementation
2. Optional skill invocation
3. Pattern following from context

### 4.3 Add Intelligence Logic

**Add Decision Tree**:

```markdown
## Implementation Intelligence

Decision tree for context usage:

```
Task Complexity Assessment:
├─ Simple (bug fix, typo, small change)
│  └─ Use PM context only → Begin implementation
├─ Medium (new endpoint, standard feature)
│  ├─ Read project_context.json
│  └─ Review PM's file hints → Begin implementation
└─ Complex (new system, integration, architecture)
   ├─ Read project_context.json
   ├─ Review PM's file hints
   └─ Invoke codebase-analysis → Begin implementation
```

This ensures appropriate context gathering without unnecessary overhead.
```

## Phase 5: Testing and Validation (2 hours)

### 5.1 Unit Testing

**Test 1: Orchestrator Role Purity**
```bash
# Verify orchestrator doesn't read code files
grep -n "Read\|Grep\|Search" agents/orchestrator.md | grep -v "bazinga/"
# Should only show bazinga-related file operations
```

**Test 2: PM Context Generation**
```bash
# Test PM creates context
/orchestrate "Simple test task"
# Check: ls -la bazinga/project_context.json
# Should exist after PM planning
```

**Test 3: Developer Context Usage**
```bash
# Spawn developer with context available
# Monitor if developer reads context file
```

### 5.2 Integration Testing

**Scenario 1: Simple Task Flow**
1. Orchestrate simple bug fix
2. Verify PM generates minimal context
3. Verify developer proceeds without analysis
4. Verify quick completion

**Scenario 2: Complex Task Flow**
1. Orchestrate complex feature
2. Verify PM generates rich context
3. Verify developer invokes analysis (optional)
4. Verify proper pattern following

**Scenario 3: Cache Efficiency**
1. Run analysis for task A
2. Run analysis for similar task B
3. Verify cache hits for project patterns
4. Verify fresh results for task-specific items

### 5.3 Performance Testing

**Metrics to Track**:
- Time from orchestration start to developer spawn
- Cache hit rate for repeated analyses
- Developer decision time for invoking analysis
- Overall orchestration completion time

**Target Performance**:
- Simple tasks: No overhead vs current
- Complex tasks: +5-10 seconds acceptable
- Cache efficiency: >60% hit rate

### 5.4 Regression Testing

**Ensure No Breaking Changes**:
1. Existing orchestrations still work
2. Slash command still builds correctly
3. All agents spawn properly
4. State management works

## Phase 6: Documentation and Rollout (1 hour)

### 6.1 Update Documentation

**Files to Update**:
1. `README.md` - Note architectural improvement
2. `CONTRIBUTING.md` - Explain new context system
3. `docs/architecture.md` - Document three-layer context

### 6.2 Create Migration Guide

**Document**: `docs/migration-guides/orchestrator-context-fix.md`

Include:
- What changed
- Why it changed
- Impact on existing workflows
- Benefits of new approach

### 6.3 Commit Strategy

**Commit 1: Remove Violations**
```bash
git add agents/orchestrator.md
git commit -m "fix: Remove code context preparation from orchestrator

- Orchestrator no longer performs code analysis
- Maintains pure coordinator role
- Preparation for PM-based context system"
```

**Commit 2: Enhance PM**
```bash
git add agents/project_manager.md
git commit -m "feat: Add project context generation to PM

- PM generates project_context.json during planning
- Includes file hints in task descriptions
- Provides context for developers"
```

**Commit 3: Add Codebase Analysis Skill**
```bash
git add .claude/skills/codebase-analysis/
git commit -m "feat: Add codebase-analysis skill

- Intelligent code analysis with caching
- Optional invocation by developers
- 60% cache efficiency for repeated operations"
```

**Commit 4: Update Developer**
```bash
git add agents/developer.md
git commit -m "feat: Add context intelligence to developer

- Reads PM-generated context
- Optional codebase analysis for complex tasks
- Smart decision tree for context usage"
```

**Commit 5: Update Configs and Docs**
```bash
git add bazinga/skills_config.json docs/
git commit -m "docs: Update documentation for context system

- Document three-layer context architecture
- Add migration guide
- Update contribution guidelines"
```

## Post-Implementation Monitoring

### Week 1 Metrics
- [ ] Orchestrator file size reduced to <2000 lines
- [ ] Zero code analysis operations in orchestrator
- [ ] PM successfully generates context
- [ ] Cache hit rate >40%

### Week 2 Metrics
- [ ] Developer revision cycles remain <1.5
- [ ] First-time approval rate maintained >50%
- [ ] Cache hit rate >60%
- [ ] No performance degradation reported

### Week 4 Metrics
- [ ] Developers invoke analysis <30% of time
- [ ] Project context becomes knowledge-rich
- [ ] Architecture remains clean
- [ ] Team feedback positive

## Rollback Plan

If issues arise:

1. **Quick Rollback**:
```bash
git revert HEAD~5..HEAD  # Revert all 5 commits
./scripts/build-slash-commands.sh  # Rebuild command
```

2. **Partial Rollback**:
- Keep PM enhancements
- Restore orchestrator context temporarily
- Debug and fix issues
- Re-attempt removal

3. **Hotfix Option**:
- Add minimal context back to orchestrator
- Mark as "temporary - remove after skill implementation"
- Continue with skill development

## Success Criteria

### Technical Success
- ✅ Orchestrator under 2000 lines
- ✅ Clean architectural separation
- ✅ All agents pass tests
- ✅ Performance acceptable

### Business Success
- ✅ Development velocity maintained
- ✅ Code quality maintained
- ✅ No increase in revision cycles
- ✅ Positive developer feedback

## Risk Mitigation

### Risk 1: Performance Degradation
**Mitigation**: Aggressive caching, optional invocation

### Risk 2: PM Complexity
**Mitigation**: Phased rollout, clear documentation

### Risk 3: Developer Confusion
**Mitigation**: Clear decision tree, good defaults

### Risk 4: Cache Invalidation
**Mitigation**: Time-based expiry, session-scoped cache

## Final Checklist

**Before Starting**:
- [ ] All tests passing
- [ ] Backup created
- [ ] Team notified

**After Each Phase**:
- [ ] Tests pass
- [ ] No regressions
- [ ] Documentation updated

**Before Merging**:
- [ ] All phases complete
- [ ] Full integration test
- [ ] Performance validated
- [ ] Documentation complete

## Estimated Timeline

- **Phase 1**: 2 hours (Remove violations)
- **Phase 2**: 3 hours (Enhance PM)
- **Phase 3**: 4-6 hours (Create skill)
- **Phase 4**: 2 hours (Update developer)
- **Phase 5**: 2 hours (Testing)
- **Phase 6**: 1 hour (Documentation)

**Total**: 14-16 hours

**Recommended Schedule**:
- Day 1: Phases 1-2 (5 hours)
- Day 2: Phase 3 (4-6 hours)
- Day 3: Phases 4-6 (5 hours)

## Conclusion

This implementation plan provides a complete path to fixing the orchestrator's role violation while maintaining or improving system performance. The three-layer context system (PM context + task hints + optional analysis) balances architectural purity with practical performance needs.

The plan is designed to be:
- **Incremental**: Each phase can be tested independently
- **Reversible**: Rollback options at each stage
- **Measurable**: Clear success metrics
- **Safe**: Comprehensive testing at each phase

Ready to begin implementation upon approval.