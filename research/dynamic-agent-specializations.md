# Dynamic Agent Specializations: Implementation Strategy

**Date:** 2025-12-03
**Context:** Enhancing BAZINGA agents with dynamic, project-specific specializations
**Decision:** Proceed with PM-embedded specialization approach
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

BAZINGA currently uses generic agent roles (Developer, QA Expert, Tech Lead, etc.) that don't adapt to project-specific contexts. A developer working on a React frontend project receives the same instructions as one working on a Go backend service. This limits effectiveness because:

1. **Context Loss**: Generic agents lack domain-specific expertise patterns
2. **Suboptimal Routing**: PM cannot assign tasks based on specialization match
3. **Missed Best Practices**: Language/framework-specific idioms are not enforced
4. **Efficiency Gap**: Agents spend tokens discovering project context instead of applying known patterns

**Goal**: Enable the PM to dynamically inject specializations into agents based on project analysis, while maintaining BAZINGA's orchestration workflow integrity.

---

## Current State Analysis

### BAZINGA's Existing Agent Structure

| Agent | Model | Current Role |
|-------|-------|--------------|
| developer | haiku | Generic implementation |
| senior_software_engineer | sonnet | Complex task escalation |
| qa_expert | sonnet | Test generation/validation |
| tech_lead | opus | Code review, architecture |
| project_manager | opus | Coordination, planning |
| investigator | opus | Root cause analysis |
| requirements_engineer | opus | Requirements discovery |

**Key Insight**: Agents are role-based (what they do) but not specialization-based (how they do it in specific contexts).

### How External Repositories Organize Specializations

#### Pattern 1: Language/Framework Specialists (VoltAgent, 0xfurai)

```
├── Language Specialists (24 agents)
│   ├── python-pro: Advanced Python patterns, optimization
│   ├── typescript-pro: Type systems, generics, strict mode
│   ├── golang-pro: Goroutines, channels, concurrency
│   ├── rust-pro: Ownership, memory safety patterns
│   └── java-pro: JVM optimization, streams, concurrency
│
├── Framework Specialists
│   ├── react-specialist: Server Components, hooks, testing
│   ├── vue-expert: Composition API, Pinia, Nuxt
│   ├── angular-architect: RxJS, dependency injection
│   ├── nextjs-developer: App Router, SSR, ISR patterns
│   ├── django-developer: ORM, middleware, DRF
│   └── rails-expert: ActiveRecord, concerns, turbo
```

**Value**: Each specialist encapsulates language/framework-specific idioms, patterns, and anti-patterns that a generic developer wouldn't know to apply.

#### Pattern 2: Domain Specialists (eluttner, ArchitectVS7)

```
├── Architecture Specialists
│   ├── backend-architect: API design, microservices
│   ├── frontend-architect: Component systems, state
│   ├── cloud-architect: AWS/GCP/Azure patterns
│   ├── microservices-architect: Service boundaries, sagas
│   └── graphql-architect: Schema design, federation
│
├── Infrastructure Specialists
│   ├── kubernetes-specialist: Container orchestration
│   ├── terraform-engineer: IaC patterns, modules
│   ├── devops-engineer: CI/CD, automation
│   └── sre-engineer: Reliability, observability
│
├── Data Specialists
│   ├── data-engineer: ETL, warehouses, streaming
│   ├── ml-engineer: Pipelines, model serving
│   └── ai-engineer: LLM applications, RAG
```

**Value**: Domain specialists understand the holistic concerns of their area, not just coding syntax.

#### Pattern 3: Three-Phase Execution Framework (VoltAgent)

Every agent follows a consistent execution pattern:

```
Phase 1: Context Discovery
  → Query project context from context-manager
  → Review existing patterns and infrastructure
  → Identify integration points and constraints

Phase 2: Development Execution
  → Apply specialization-specific patterns
  → Provide progress updates
  → Coordinate with related specialists

Phase 3: Handoff & Documentation
  → Deliver specialized artifacts
  → Update project documentation
  → Handoff to next workflow stage
```

**Value**: Structured phases ensure consistent quality regardless of specialization.

---

## Implementation Options

### Option A: Template Injection (Recommended)

**Concept**: PM analyzes project, selects appropriate specialization templates, and injects them into agent prompts dynamically.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│     PM      │────>│ Specialization   │────>│   Orchestrator  │
│  (Analysis) │     │ Templates        │     │  (Injection)    │
└─────────────┘     │ - react-frontend │     └────────┬────────┘
                    │ - python-backend │              │
                    │ - go-microservice│              ▼
                    └──────────────────┘     ┌─────────────────┐
                                             │   Developer +   │
                                             │  Specialization │
                                             └─────────────────┘
```

**Implementation Structure**:

```
agents/
├── _templates/                     # Specialization templates
│   ├── languages/
│   │   ├── python.md              # Python-specific patterns
│   │   ├── typescript.md          # TypeScript expertise
│   │   ├── go.md                  # Go concurrency patterns
│   │   └── rust.md                # Memory safety patterns
│   │
│   ├── frameworks/
│   │   ├── react.md               # React 18+ patterns
│   │   ├── vue.md                 # Vue 3 Composition API
│   │   ├── nextjs.md              # Next.js App Router
│   │   ├── django.md              # Django REST Framework
│   │   ├── fastapi.md             # FastAPI async patterns
│   │   └── gin.md                 # Go Gin framework
│   │
│   ├── domains/
│   │   ├── backend-api.md         # RESTful API design
│   │   ├── frontend-spa.md        # SPA architecture
│   │   ├── microservices.md       # Distributed systems
│   │   ├── data-pipeline.md       # ETL patterns
│   │   └── ml-inference.md        # ML serving patterns
│   │
│   └── quality/
│       ├── security-focused.md    # Security-first development
│       ├── performance-critical.md # Performance optimization
│       └── accessibility.md       # WCAG compliance
│
├── developer.md                    # Base developer (receives injection)
└── _sources/
    └── developer.base.md          # Core developer logic
```

**PM Decision Flow**:

```python
# PM analyzes codebase and selects specializations
project_analysis = {
    "languages": ["typescript", "python"],
    "frameworks": ["nextjs", "fastapi"],
    "domains": ["frontend-spa", "backend-api"],
    "quality_focus": ["security-focused"]
}

# PM includes in task group assignment
task_group = {
    "group_id": "A",
    "name": "Implement user authentication",
    "specializations": [
        "templates/languages/typescript.md",
        "templates/frameworks/nextjs.md",
        "templates/domains/backend-api.md",
        "templates/quality/security-focused.md"
    ]
}
```

**Orchestrator Injection**:

```python
def spawn_developer(task_group):
    base_prompt = read("agents/developer.md")

    # Inject specializations
    specialization_content = ""
    for template in task_group["specializations"]:
        specialization_content += read(f"agents/{template}")

    enhanced_prompt = f"""
{base_prompt}

## Project-Specific Specialization

{specialization_content}
"""

    return spawn_agent("developer", enhanced_prompt)
```

**Pros**:
- Minimal changes to existing architecture
- Specializations are reusable across projects
- PM retains control over agent capability assignment
- Templates can be version-controlled and shared

**Cons**:
- Increases prompt size (token cost)
- Requires PM to understand available specializations
- Template maintenance overhead

---

### Option B: Agent Variants (Static Specializations)

**Concept**: Pre-create specialized agent variants that extend the base developer.

```
agents/
├── developer.md                    # Base developer
├── developer.react-frontend.md     # React frontend specialist
├── developer.python-backend.md     # Python backend specialist
├── developer.go-microservice.md    # Go microservice specialist
└── developer.security.md           # Security specialist
```

**PM Selection**:

```markdown
**Group A:** Implement Auth UI
- **Specialized Agent:** developer.react-frontend
- **Rationale:** React-specific component patterns needed
```

**Pros**:
- Clean separation of concerns
- Each variant is self-contained
- No runtime injection complexity

**Cons**:
- Explosion of agent files (N languages × M frameworks × K domains)
- Duplication of common logic
- Harder to combine specializations

---

### Option C: Capability Plugins (Modular Skills)

**Concept**: Extend the existing Skills system to include specialization capabilities.

```
.claude/skills/
├── bazinga-db/                     # Existing skill
├── lint-check/                     # Existing skill
│
├── specializations/                # NEW: Specialization skills
│   ├── react-patterns/
│   │   └── SKILL.md               # React-specific patterns
│   ├── python-backend/
│   │   └── SKILL.md               # Python backend patterns
│   └── security-audit/
│       └── SKILL.md               # Security review patterns
```

**Agent Invocation**:

```markdown
## Before Implementation

Invoke relevant specialization skills:
- `Skill(command: "react-patterns")` - for React-specific guidance
- `Skill(command: "python-backend")` - for Python patterns
```

**Pros**:
- Leverages existing Skills infrastructure
- Agents can dynamically invoke what they need
- Skills can provide runtime context (not just static templates)

**Cons**:
- Skills are currently used for tools, not knowledge injection
- Requires agents to know which skills to invoke
- Less control from PM perspective

---

### Option D: Context Manager Pattern (External Repository Pattern)

**Concept**: Implement a dedicated Context Manager agent that provides specialization context to other agents.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Developer  │────>│ Context Manager  │<────│   PM Decision   │
│  (queries)  │     │ (provides specs) │     │   (configures)  │
└─────────────┘     └──────────────────┘     └─────────────────┘
```

**Developer Request**:

```json
{
  "query": "Frontend development context needed",
  "include": ["component_ecosystem", "design_language", "testing_patterns"]
}
```

**Context Manager Response**:

```markdown
## Frontend Context for This Project

**Framework:** Next.js 14 with App Router
**State Management:** Zustand with immer middleware
**Styling:** Tailwind CSS with custom design tokens
**Testing:** Vitest + React Testing Library
**Patterns:**
- Container/Presenter component separation
- Custom hooks for data fetching
- Zod schemas for form validation
```

**Pros**:
- Centralizes context management
- Dynamic and always up-to-date
- Mirrors successful external patterns

**Cons**:
- Adds another agent to spawn (cost/latency)
- Requires building the Context Manager agent
- PM cannot directly control what context is provided

---

## Recommended Approach: Hybrid Template Injection

**Recommendation**: Combine Options A (Template Injection) and D (Context Manager) for maximum flexibility.

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        PM Analysis Phase                          │
├──────────────────────────────────────────────────────────────────┤
│ 1. Analyze codebase (languages, frameworks, patterns)            │
│ 2. Select applicable specialization templates                     │
│ 3. Store selections in task_group metadata                        │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Orchestrator Injection                        │
├──────────────────────────────────────────────────────────────────┤
│ 1. Read base agent definition                                     │
│ 2. Load specialization templates from task_group                  │
│ 3. Construct enhanced prompt with injected specializations        │
│ 4. Spawn specialized developer                                    │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Specialized Developer                           │
├──────────────────────────────────────────────────────────────────┤
│ Base Developer Logic                                              │
│   +                                                               │
│ Specialization: React 18+ Patterns                                │
│   +                                                               │
│ Specialization: TypeScript Strict Mode                            │
│   +                                                               │
│ Specialization: Security-First Development                        │
└──────────────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: Template Structure (Week 1)

1. Create `agents/_templates/` directory structure
2. Define template format specification:

```markdown
---
name: react-frontend
type: framework
version: 1.0.0
description: React 18+ frontend development patterns
compatible_with: [developer, senior_software_engineer]
token_estimate: 800
---

# React Frontend Specialization

## You Are
A React 18+ specialist with deep expertise in:
- Server Components vs Client Components decisions
- Hooks patterns (useState, useEffect, useCallback, useMemo)
- State management (Context, Zustand, Jotai patterns)
- Performance optimization (memo, lazy, Suspense)

## Patterns You Apply

### Component Structure
- Collocate related files: Component.tsx, Component.test.tsx, Component.stories.tsx
- Use TypeScript strict mode with explicit prop interfaces
- Prefer composition over inheritance

### State Management Rules
- Local state first (useState)
- Lift state only when needed
- Global state only for truly global concerns

### Testing Standards
- Test behavior, not implementation
- Use React Testing Library queries in priority order
- Mock at boundaries (API, not internal functions)

## Anti-Patterns You Avoid
- Prop drilling beyond 2 levels
- useEffect for derived state
- Inline function definitions in JSX (when perf matters)
- any type (use unknown + type guards)
```

3. Create initial templates for high-value specializations:
   - Languages: TypeScript, Python, Go
   - Frameworks: React, Next.js, FastAPI, Django
   - Domains: Backend API, Frontend SPA, Microservices
   - Quality: Security-focused, Performance-critical

#### Phase 2: PM Integration (Week 2)

1. Add codebase analysis step to PM initial planning:

```markdown
### Step 0.5: Project Analysis (Before Task Creation)

**Analyze codebase to determine applicable specializations:**

1. Detect primary languages (package.json, pyproject.toml, go.mod)
2. Detect frameworks (import statements, config files)
3. Detect architectural patterns (directory structure, existing code)
4. Select matching specialization templates

**Store in PM state:**
```json
{
  "project_specializations": {
    "languages": ["typescript"],
    "frameworks": ["nextjs", "prisma"],
    "domains": ["frontend-spa", "backend-api"],
    "quality": ["security-focused"]
  }
}
```
```

2. Include specializations in task group creation:

```markdown
**Group AUTH:** Implement JWT Authentication
- **Complexity:** 8 (HIGH)
- **Initial Tier:** senior_software_engineer
- **Specializations:**
  - templates/languages/typescript.md
  - templates/frameworks/nextjs.md
  - templates/quality/security-focused.md
```

#### Phase 3: Orchestrator Enhancement (Week 2-3)

1. Modify orchestrator to inject specializations when spawning:

```python
def spawn_developer_with_specializations(task_group, pm_state):
    # Read base agent
    base_agent = read(f"agents/{task_group.initial_tier}.md")

    # Collect specializations
    specs = []
    for template_path in task_group.specializations:
        spec = read(f"agents/{template_path}")
        specs.append(spec)

    # Combine
    enhanced_prompt = f"""
{base_agent}

---
## PROJECT-SPECIFIC SPECIALIZATIONS

The following specializations apply to this project. Apply these patterns
and best practices throughout your implementation.

{"".join(specs)}
---
"""

    return spawn_agent(task_group.initial_tier, enhanced_prompt)
```

2. Add database fields for tracking:

```sql
ALTER TABLE task_groups ADD COLUMN specializations TEXT;  -- JSON array
```

#### Phase 4: Validation and Refinement (Week 3-4)

1. Test with representative projects (React app, Python API, Go service)
2. Measure token usage impact
3. Validate PM selection accuracy
4. Refine templates based on outcomes

---

## Recommended Specialization Templates for BAZINGA

Based on the research, here are the highest-value specializations to implement first:

### Tier 1: Essential (Implement Immediately)

| Template | Type | Description | Value |
|----------|------|-------------|-------|
| `typescript.md` | Language | Strict types, generics, utility types | Catches type errors early |
| `python.md` | Language | Type hints, async patterns, idioms | Pythonic code quality |
| `react.md` | Framework | Hooks, components, testing patterns | Most common frontend |
| `fastapi.md` | Framework | Async endpoints, Pydantic models | Modern Python API |
| `backend-api.md` | Domain | RESTful design, error handling, validation | Universal backend needs |
| `security-focused.md` | Quality | Auth patterns, injection prevention | Security by default |

### Tier 2: High Value (Implement Next)

| Template | Type | Description | Value |
|----------|------|-------------|-------|
| `nextjs.md` | Framework | App Router, SSR, API routes | Popular React meta-framework |
| `go.md` | Language | Goroutines, error handling, idioms | Backend/CLI language |
| `django.md` | Framework | ORM, views, DRF patterns | Python web framework |
| `frontend-spa.md` | Domain | State, routing, optimization | Frontend architecture |
| `microservices.md` | Domain | Service boundaries, communication | Distributed systems |

### Tier 3: Specialized (Implement As Needed)

| Template | Type | Description |
|----------|------|-------------|
| `vue.md` | Framework | Composition API, Pinia |
| `rust.md` | Language | Ownership, lifetimes |
| `kubernetes.md` | Infrastructure | Manifests, Helm |
| `ml-inference.md` | Domain | Model serving, optimization |
| `accessibility.md` | Quality | WCAG compliance |

---

## Critical Analysis

### Pros

1. **Minimal Architecture Change**: Template injection works within existing orchestration flow
2. **PM Retains Control**: PM decides which specializations apply, not the agents
3. **Reusable Assets**: Templates can be shared across projects
4. **Gradual Adoption**: Can implement one template at a time
5. **Measurable Impact**: Token usage and outcome quality can be tracked
6. **Community Alignment**: Follows patterns used by successful external repositories

### Cons

1. **Token Cost Increase**: Each specialization adds ~500-1000 tokens per agent spawn
2. **Template Maintenance**: Specializations must be updated as frameworks evolve
3. **PM Complexity**: PM needs logic to analyze codebase and select templates
4. **Template Quality**: Poorly written templates could reduce effectiveness
5. **Scope Creep Risk**: Temptation to create too many narrow specializations

### Verdict

The token cost is acceptable given the expected quality improvement. Template maintenance is a known cost but manageable through version control and periodic reviews. The PM complexity can be addressed with clear heuristics (detect package.json → suggest React templates). Template quality should be validated through testing.

**Recommendation: Proceed with implementation.**

---

## Implementation Details

### Template Format Specification

```markdown
---
# YAML frontmatter for metadata
name: template-name                    # Unique identifier
type: language|framework|domain|quality
version: 1.0.0                         # Semantic versioning
description: Brief description
compatible_with: [developer, senior_software_engineer]  # Which agents can use this
token_estimate: 800                    # Approximate token count
prerequisites: []                      # Other templates that should be loaded first
conflicts_with: []                     # Templates that shouldn't be combined
---

# Template Display Name

## You Are
[Identity statement establishing the specialization context]

## Technical Expertise
[Specific technologies, versions, and capabilities]

## Patterns You Apply
[Best practices and patterns this specialist uses]
[Include concrete code examples where helpful]

## Anti-Patterns You Avoid
[Common mistakes and why to avoid them]

## Quality Standards
[Measurable criteria for quality work]

## Integration Points
[How this specialist coordinates with others]
```

### Database Schema Changes

```sql
-- Add specializations to task_groups
ALTER TABLE task_groups ADD COLUMN specializations JSON DEFAULT '[]';

-- Add project_specializations to pm_state
-- (Already stored as JSON in state_data, no schema change needed)

-- Track specialization usage for analytics
CREATE TABLE specialization_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    template_path TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

### PM Codebase Analysis Heuristics

```markdown
## Codebase Detection Rules

### Language Detection
| File/Pattern | Language |
|--------------|----------|
| package.json with typescript | TypeScript |
| pyproject.toml or requirements.txt | Python |
| go.mod | Go |
| Cargo.toml | Rust |
| pom.xml or build.gradle | Java |

### Framework Detection
| Import/Config Pattern | Framework |
|----------------------|-----------|
| next.config.js or "next" in dependencies | Next.js |
| "react" in dependencies (not next) | React |
| "vue" in dependencies | Vue |
| "fastapi" in requirements | FastAPI |
| "django" in requirements | Django |
| "flask" in requirements | Flask |
| "gin-gonic" in go.mod | Gin |

### Domain Detection
| Directory/Pattern | Domain |
|-------------------|--------|
| /api/ or /routes/ + controllers | Backend API |
| /components/ + /pages/ | Frontend SPA |
| /services/ (multiple) | Microservices |
| /models/ + /train/ | ML |
```

---

## Comparison to Alternatives

### vs. Fine-tuned Models
- **Specializations**: Zero additional training cost, instant updates
- **Fine-tuned**: Higher quality but expensive to create/maintain

### vs. RAG-based Context
- **Specializations**: Curated, concise, always relevant
- **RAG**: Dynamic but may retrieve irrelevant content

### vs. No Specialization (Current State)
- **Specializations**: +10-20% token cost, +significant quality improvement
- **No Specialization**: Cheaper but generic output

---

## Decision Rationale

1. **Alignment with BAZINGA's Philosophy**: PM-driven decisions, orchestrator execution
2. **Proven Pattern**: External repositories validate the template approach
3. **Incremental Value**: Each template added increases system capability
4. **Maintainable**: Templates are markdown files, easy to update
5. **Measurable**: Token usage and quality outcomes can be tracked

---

## Lessons Learned (From Research)

1. **Three-Phase Execution**: External agents consistently use Context Discovery → Execution → Handoff pattern
2. **Cross-Agent Collaboration**: Specialized agents explicitly define integration points
3. **Quality Standards**: Successful agents include measurable criteria (80% coverage, sub-100ms p95)
4. **Token Efficiency**: Progressive disclosure (load only what's needed) is critical at scale
5. **Granular Plugins**: Smaller, focused components are better than monolithic agents

---

## References

- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) - 100+ production agents
- [0xfurai/claude-code-subagents](https://github.com/0xfurai/claude-code-subagents) - Language/framework specialists
- [eluttner/claude-agents](https://github.com/eluttner/claude-agents) - 82 specialized agents
- [wshobson/agents](https://github.com/wshobson/agents) - 85 agents with hybrid orchestration
- [ArchitectVS7/claude-code-subagents](https://github.com/ArchitectVS7/claude-code-subagents) - Categorized agents
- [subagents.cc](https://subagents.cc) - Community agent catalog
- [Claude Code Subagents Guide 2025](https://www.medianeth.dev/blog/claude-code-frameworks-subagents-2025)
- [10 Essential Subagents](https://dev.to/necatiozmen/10-claude-code-subagents-every-developer-needs-in-2025-2ho)

---

## Multi-LLM Review Integration

### Consensus Points (Critical Issues Identified)

**1. Orchestrator Read-Permissions Conflict**
The original plan relied on the orchestrator reading template files from `agents/_templates/`. However, BAZINGA's orchestrator is explicitly restricted from reading code/prompt files. It can only read state files under `bazinga/` and templates under `templates/`.

**Resolution**: Adopt the **PM-embedded specialization approach**. PM pastes curated specialization guidance inline in the task group description field. The orchestrator already includes PM task descriptions in developer prompts, avoiding the need for template file reads.

**2. Context Packages "Data-Only" Constraint**
BAZINGA's agents treat context packages as data, explicitly ignoring embedded instructions. Using context packages for specialization guidance would be ineffective.

**Resolution**: Specializations must be in the agent prompt directly, not passed as context packages. The PM-embedded approach satisfies this constraint.

**3. Database Schema Changes**
The original plan proposed `ALTER TABLE` statements, but the orchestrator is forbidden from inline SQL and must use the bazinga-db skill.

**Resolution**:
- Store specialization selections in PM state JSON (already supported)
- Log specialization usage via `orchestration_logs` entries
- Do NOT create new tables; use existing state mechanisms

**4. Prompt Injection Precedence**
Injected specializations could contradict mandatory workflow gates (routing, output formats, test integrity).

**Resolution**: Add explicit precedence rule to ALL specialization templates:
```markdown
> **PRECEDENCE RULE**: This guidance augments the base agent contract.
> Mandatory workflow, routing, reporting formats, Test-Passing Integrity,
> and Spec-Kit plan.md/spec.md always take precedence over this specialization.
```

**5. Token Budget/Overflow Risk**
Combining base agent + specializations can exceed context limits, especially with 3-4 parallel developers.

**Resolution**:
- Enforce per-agent specialization budget: **≤1200 tokens total**
- If multiple templates selected: choose top 2 by priority (language + framework)
- Summarize additional specializations to bullet "Do/Don't" lists (≤200 tokens each)
- Deduplicate common sections at injection time

**6. Feature Flag/Rollout Strategy**
No mechanism to enable/disable the feature per session.

**Resolution**: Add `enable_specializations: true|false` to `bazinga/skills_config.json`:
```json
{
  "pm": {
    "enable_specializations": true,
    "max_specialization_tokens": 1200
  }
}
```

### Incorporated Feedback

| Issue | Original Approach | Revised Approach |
|-------|-------------------|------------------|
| Template loading | Orchestrator reads files | PM embeds inline in task description |
| DB schema | ALTER TABLE + new tables | Use existing pm_state JSON fields |
| Precedence | Not defined | Explicit precedence rule in all templates |
| Token budget | Not defined | 1200 token cap, priority selection |
| Rollout | Not defined | Feature flag in skills_config.json |
| Compatibility | Not validated | Loader validates compatible_with before injection |

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| Create bazinga-db "specialization-loader" command | Adds unnecessary complexity; PM-embedded approach is simpler and sufficient |
| Extend to QA/Tech Lead prompts initially | Increases scope; start with Developer/SSE, expand later if proven valuable |
| Require code owners review for templates | Overhead; templates live under agents/_templates with normal PR process |

### Revised Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        PM Analysis Phase                          │
├──────────────────────────────────────────────────────────────────┤
│ 1. Check enable_specializations flag (skills_config.json)        │
│ 2. Analyze codebase (Grep/Glob for languages, frameworks)        │
│ 3. Select applicable specializations (max 2 priority)             │
│ 4. Embed specialization guidance in task_group description       │
│ 5. Store selections in pm_state.project_specializations          │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Orchestrator (No Changes)                     │
├──────────────────────────────────────────────────────────────────┤
│ 1. Read task_group from PM state (already done)                   │
│ 2. Include task description in developer prompt (already done)   │
│ 3. Spawn developer with enhanced task description                 │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Developer Receives                              │
├──────────────────────────────────────────────────────────────────┤
│ Standard task description                                         │
│   +                                                               │
│ Embedded specialization: "Apply TypeScript strict mode, React    │
│ Testing Library patterns, security-first auth..."                │
└──────────────────────────────────────────────────────────────────┘
```

**Key Benefit**: Zero orchestrator changes required. PM is the injection point.

### Revised Template Format

Templates now include mandatory precedence header and size constraints:

```markdown
---
name: react-frontend
type: framework
version: 1.0.0
description: React 18+ frontend development patterns
compatible_with: [developer, senior_software_engineer]
token_estimate: 600
max_tokens: 800  # Hard limit
priority: 2      # 1=language, 2=framework, 3=domain, 4=quality
---

> **PRECEDENCE**: Base agent workflow, routing, and reporting rules
> take precedence. This guidance is supplementary.

# React Frontend Patterns

**Apply these patterns:**
- TypeScript strict mode with explicit prop interfaces
- Server/Client Component decisions based on interactivity needs
- React Testing Library with user-event for interactions
- Custom hooks for data fetching (useQuery patterns)

**Avoid:**
- Prop drilling beyond 2 levels (use Context or Zustand)
- useEffect for derived state (compute inline or useMemo)
- any type (use unknown + type guards)
```

### Revised PM State Schema

```json
{
  "session_id": "...",
  "project_specializations": {
    "detected": {
      "languages": ["typescript"],
      "frameworks": ["nextjs"],
      "domains": ["frontend-spa"]
    },
    "selected": [
      "typescript",
      "nextjs"
    ],
    "token_budget_remaining": 600
  },
  "task_groups": [
    {
      "group_id": "A",
      "name": "Implement auth UI",
      "specialization_guidance": "Apply TypeScript strict mode. Use Next.js App Router patterns. Follow React Testing Library best practices."
    }
  ]
}
```

### Updated Implementation Plan

**Phase 1: Foundation (Days 1-3)**
1. Add `enable_specializations` flag to `bazinga/skills_config.json`
2. Create `agents/_templates/` directory with Tier 1 templates
3. Add precedence header to all templates

**Phase 2: PM Enhancement (Days 4-6)**
1. Update PM agent to detect languages/frameworks via Grep/Glob
2. Add specialization selection logic with token budget
3. Embed guidance in task_group description field

**Phase 3: Validation (Days 7-10)**
1. Test with representative projects (React app, Python API)
2. Measure token usage impact vs quality improvement
3. Refine templates based on outcomes
4. Document patterns for template creation

---

## Next Steps

1. **Create Tier 1 Templates**: TypeScript, Python, React, FastAPI, backend-api, security-focused (with precedence headers)
2. **Add Feature Flag**: `enable_specializations` in skills_config.json
3. **Update PM Agent**: Add codebase detection heuristics and specialization embedding
4. **Pilot Test**: Run on 2-3 sample projects with measurements
5. **Iterate**: Refine templates based on developer/QA/TL feedback

---

## Cleanup

After integrating this review, the temporary review files can be deleted:
```bash
rm -rf tmp/ultrathink-reviews/
```
