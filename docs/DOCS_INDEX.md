# BAZINGA - Claude Code Multi-Agent Dev Team - Documentation Index

> **Repository:** https://github.com/mehdic/bazinga

This directory contains comprehensive documentation for BAZINGA (Claude Code Multi-Agent Dev Team), organized to help you find what you need quickly.

**💡 Key Concept:** BAZINGA has two modes:
- **Lite** (default) - 3 core skills, fast iteration, perfect for most work
- **Advanced** - All 10 skills, comprehensive analysis, for production-critical code

---

## 🚀 For New Users - Start Here

If you're new to BAZINGA, start with these four documents:

### 1. **[../README.md](../README.md)** - Project Overview
**Length**: ~200 lines | **Time to read**: 10 minutes
- What is BAZINGA?
- Quick start overview
- Key concepts at a glance

**Next step**: Run through examples to see it in action.

---

### 2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command Cheat Sheet
**Length**: ~400 lines | **Time to read**: 5-10 minutes
- Quick command reference
- Common workflows and examples
- Configuration options
- Performance tips

**Perfect for**: Quick lookups and daily use.

---

### 3. **[SKILLS.md](SKILLS.md)** - Configurable Quality Analysis Tools
**Length**: ~1,000 lines | **Time to read**: 15-20 minutes
- What are Skills and why configure them?
- 3 Core Skills (lite profile) vs 7 Advanced Skills
- Configuration presets: lite (default), advanced, custom
- Language support (Python, JavaScript, Go, Java, Ruby)
- `/bazinga.configure-skills` command tutorial

**Perfect for**: Understanding what quality checks run during your workflows.

---

### 4. **[../examples/EXAMPLES.md](../examples/EXAMPLES.md)** - See It In Action
**Length**: ~350 lines | **Time to read**: 10-15 minutes
- Real workflow examples
- How agents interact with each other
- Decision points and branching

**Perfect for**: Learning by example before reading technical docs.

---

## 🏗️ Core Concepts - Deep Technical Dives

Once familiar with basics, these documents explain how BAZINGA works:

### 5. **[ADVANCED.md](ADVANCED.md)** - Advanced Features & Production Use
**Length**: ~900 lines | **Time to read**: 25-30 minutes
**Sections**:
- Profiles Overview (lite vs advanced vs custom)
- Advanced Skills (detailed explanations of 7 advanced skills)
- Full Testing Mode (QA Expert, integration/E2E tests)
- Configuration (how to switch profiles)
- Performance Considerations (time investment per skill)
- When to Use Advanced Mode (decision framework)

**Read this for**: Understanding advanced features, full testing mode, and when to escalate from lite to advanced.

**Key insight**: Most projects need lite mode (3 core skills). Use advanced mode for production-critical code, API changes, database migrations, or complex refactoring.

---

### 6. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System Design & Technical Specifications
**Length**: ~1,100 lines | **Time to read**: 30-40 minutes
**Sections**:
- System Overview (workflow types, agent roles)
- Agent Definitions (5 agents: Developer, Tech Lead, QA Expert, PM, Orchestrator)
- Workflow Patterns (5 routing strategies)
- Role Drift Prevention (6-layer defense system)
- State Management (coordination files)
- Routing Mechanism (how requests flow)
- Tool Restrictions (what each agent can do)
- Decision Logic (conditional routing)

**Read this for**: Technical specifications, implementation details, system behavior.

**Cross-reference**:
- Link to [ROLE_DRIFT_PREVENTION.md](ROLE_DRIFT_PREVENTION.md) for detailed defense system
- Link to [MODEL_ESCALATION.md](MODEL_ESCALATION.md) for escalation strategy
- Link to historical-dev-docs for original vision

---

### 7. **[ROLE_DRIFT_PREVENTION.md](ROLE_DRIFT_PREVENTION.md)** - Preventing Agent Confusion
**Length**: ~350 lines | **Time to read**: 15-20 minutes
**Sections**:
- Problem Definition (why agents drift from their roles)
- Research Findings (real cases of drift)
- 6-Layer Defense System (tooling, constraints, prompts, monitoring)
- Implementation Guide (how each layer works)
- Effectiveness Analysis

**Read this for**: Understanding how we prevent agents from doing the wrong job.

**Cross-reference**:
- Link to [SCOPE_REDUCTION_INCIDENT.md](SCOPE_REDUCTION_INCIDENT.md) for real case study
- Link to [ARCHITECTURE.md](ARCHITECTURE.md) Tool Restrictions section

---

### 8. **[MODEL_ESCALATION.md](MODEL_ESCALATION.md)** - Intelligent Cost-Effective Model Selection
**Length**: ~423 lines | **Time to read**: 15-20 minutes
**Sections**:
- The Problem (why revisions persist)
- The Solution (automatic escalation strategy)
- How It Works (step-by-step)
- Progressive Analysis (basic vs advanced Skills)
- Real-World Examples (JWT authentication case study)
- Implementation Details (revision tracking, model parameters)
- Best Practices (for developers, PMs, tech leads)

**Read this for**: Understanding how BAZINGA automatically picks Sonnet vs Opus based on revision count.

**Key insight**: After 3 revisions, escalate to Opus for deeper analysis. This saves money and time vs staying with fast reviews.

**Cross-reference**:
- Link to [SKILLS.md](SKILLS.md) for security-scan mode escalation
- Link to [PM_METRICS.md](PM_METRICS.md) for revision tracking data

---

### 9. **[PM_METRICS.md](PM_METRICS.md)** - Data-Driven Project Management
**Length**: ~668 lines | **Time to read**: 20-30 minutes
**Sections**:
- The Problem (why metrics matter)
- Velocity Tracker Skill (what it provides)
- 99% Rule Detection (catching stuck tasks)
- Metrics Dashboard (what's tracked)
- Advanced Capabilities (Tier 2 & 3)
- Historical Learning (pattern-miner for predictions)
- Real PM Decision-Making Scenarios
- Configuration & Enabling

**Read this for**: Understanding how PM makes data-driven decisions and detects problems early.

**Key metrics**:
- Velocity (story points per run)
- Cycle time (hours per task)
- Revision rate (iterations needed)
- Risk score (escalation triggers)
- Efficiency ratio (workload monitoring)

**Cross-reference**:
- Link to [SKILLS.md](SKILLS.md) for velocity-tracker and pattern-miner Skills
- Link to [MODEL_ESCALATION.md](MODEL_ESCALATION.md) for revision tracking

---

## 🎯 Specific Features - How-To Guides

### 10. **[TECH_DEBT_GUIDE.md](TECH_DEBT_GUIDE.md)** - Managing Technical Debt Responsibly
**Length**: ~253 lines | **Time to read**: 10 minutes
**Sections**:
- Core Principle: "Try First, Log Later"
- When Tech Debt is Appropriate (and when it's NOT)
- Decision Framework (4 questions before logging)
- Tech Debt Categories (valid vs invalid examples)
- How to Log Tech Debt (Python helper)
- Severity Guidelines (CRITICAL to LOW)
- Integration with Workflow (developer → tech lead → PM)

**Read this for**: Understanding what counts as legitimate tech debt vs lazy shortcuts.

**Key rule**: Spend 30+ minutes trying to fix it. Document your attempts. Then log if truly out of scope.

---

### 11. **[SCOPE_REDUCTION_INCIDENT.md](SCOPE_REDUCTION_INCIDENT.md)** - Case Study: Learning from Mistakes
**Length**: ~150 lines | **Time to read**: 10 minutes
**Sections**:
- The Incident (what went wrong)
- Root Cause Analysis (why it happened)
- Solution Implemented (how we fixed it)
- Lessons Learned (what we take forward)

**Read this for**: Real example of role drift, how it was caught, and what changes prevent it now.

**Related**: [ROLE_DRIFT_PREVENTION.md](ROLE_DRIFT_PREVENTION.md) explains the defense system built after this incident.

---

### 12. **[INVESTIGATION_WORKFLOW.md](INVESTIGATION_WORKFLOW.md)** - Investigation Loop Workflow
**Length**: ~350 lines | **Time to read**: 15 minutes
**Sections**:
- Where Investigation Fits (in main workflow)
- Investigation Loop Detail (multi-turn diagrams)
- Exit Routing (how investigations conclude)
- State Persistence (session resume handling)
- Workflow Router Integration (entry/exit vs internal loop)
- Agent Knowledge Requirements (what each agent needs to know)
- Known Gaps (implementation TODOs)

**Read this for**: Understanding how the Investigator agent integrates with the orchestrator, including workflow diagrams and state management.

**Cross-reference**:
- Link to [ARCHITECTURE.md](ARCHITECTURE.md) for overall system design
- Link to `agents/investigator.md` for agent definition
- Link to `research/investigation-loop-template-ultrathink.md` for detailed design analysis

---

## 📚 Original Documentation - Historical Reference

Located in **`historical-dev-docs/`** - These are historical records of BAZINGA's development. They're preserved for reference but not actively maintained.

### Original Architecture Documents

| Document | Length | Purpose |
|----------|--------|---------|
| **[V4_ARCHITECTURE.md](historical-dev-docs/V4_ARCHITECTURE.md)** | ~580 lines | Original system design as envisioned in V4 |
| **[V4_IMPLEMENTATION_SUMMARY.md](historical-dev-docs/V4_IMPLEMENTATION_SUMMARY.md)** | ~350 lines | Development journey and design decisions |
| **[V4_STATE_SCHEMAS.md](historical-dev-docs/V4_STATE_SCHEMAS.md)** | ~710 lines | JSON schemas for all coordination files |
| **[V4_WORKFLOW_DIAGRAMS.md](historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md)** | ~2,100 lines | ASCII diagrams and visual flows |

**When to use**: Comparing original vision with current implementation, or understanding design evolution.

---

## 🔍 Finding Information by Topic

### Quick Topic Lookup

**Agent Behavior**
- [ARCHITECTURE.md](ARCHITECTURE.md) → Agent Definitions section
- [../agents/](../agents/) → Per-agent capability files

**Workflow Routing**
- [ARCHITECTURE.md](ARCHITECTURE.md) → Routing Mechanism section
- [historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md](historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md) → Visual flows
- [../examples/EXAMPLES.md](../examples/EXAMPLES.md) → Practical examples

**Quality & Skills Configuration**
- [SKILLS.md](SKILLS.md) → All 11 Skills explained
- [ARCHITECTURE.md](ARCHITECTURE.md) → Tool Restrictions section
- [../agents/](../agents/) → Agent capability files

**Code Review & Model Escalation**
- [MODEL_ESCALATION.md](MODEL_ESCALATION.md) → Strategy & implementation
- [ARCHITECTURE.md](ARCHITECTURE.md) → Role Drift Prevention section
- [SKILLS.md](SKILLS.md) → Security-scan progressive modes

**Project Management & Metrics**
- [PM_METRICS.md](PM_METRICS.md) → Velocity, cycle time, risk scoring
- [SKILLS.md](SKILLS.md) → velocity-tracker and pattern-miner Skills
- [MODEL_ESCALATION.md](MODEL_ESCALATION.md) → Revision tracking

**Role Drift Prevention**
- [ROLE_DRIFT_PREVENTION.md](ROLE_DRIFT_PREVENTION.md) → Complete 6-layer system
- [SCOPE_REDUCTION_INCIDENT.md](SCOPE_REDUCTION_INCIDENT.md) → Real case study
- [ARCHITECTURE.md](ARCHITECTURE.md) → Role Drift Prevention section

**State Management & Configuration**
- [historical-dev-docs/V4_STATE_SCHEMAS.md](historical-dev-docs/V4_STATE_SCHEMAS.md) → Schema definitions
- [ARCHITECTURE.md](ARCHITECTURE.md) → State Management section
- [../scripts/README.md](../scripts/README.md) → Initialization

**Technical Debt**
- [TECH_DEBT_GUIDE.md](TECH_DEBT_GUIDE.md) → When to log, how to log, guidelines
- [ARCHITECTURE.md](ARCHITECTURE.md) → Tool Restrictions (why certain limits exist)
- [PM_METRICS.md](PM_METRICS.md) → Quality gates section

---

## 🤔 Common Questions → Documentation Map

| Question | Read This |
|----------|-----------|
| "What's the quick command reference?" | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → All commands and workflows |
| "When should I use advanced mode?" | [ADVANCED.md](ADVANCED.md) → When to Use Advanced Mode |
| "How do I configure Skills?" | [SKILLS.md](SKILLS.md) → Quick Start section + `/bazinga.configure-skills` |
| "What are the core vs advanced Skills?" | [SKILLS.md](SKILLS.md) → Available Skills section (lite vs advanced) |
| "How does model escalation work?" | [MODEL_ESCALATION.md](MODEL_ESCALATION.md) → How It Works section |
| "What does the PM track?" | [PM_METRICS.md](PM_METRICS.md) → Velocity Tracker section |
| "How do we prevent role drift?" | [ROLE_DRIFT_PREVENTION.md](ROLE_DRIFT_PREVENTION.md) → 6-Layer Defense System |
| "What happened in the scope incident?" | [SCOPE_REDUCTION_INCIDENT.md](SCOPE_REDUCTION_INCIDENT.md) |
| "When is tech debt appropriate?" | [TECH_DEBT_GUIDE.md](TECH_DEBT_GUIDE.md) → Decision Framework |
| "How does orchestrator route requests?" | [ARCHITECTURE.md](ARCHITECTURE.md) → Routing Mechanism section |
| "What are the 5 workflow patterns?" | [ARCHITECTURE.md](ARCHITECTURE.md) → Workflow Patterns section |
| "What tools can each agent use?" | [ARCHITECTURE.md](ARCHITECTURE.md) → Tool Restrictions section |
| "How do we catch stuck tasks?" | [PM_METRICS.md](PM_METRICS.md) → 99% Rule Detection section |
| "Why are security scans progressive?" | [MODEL_ESCALATION.md](MODEL_ESCALATION.md) → Progressive Analysis section |
| "How does the investigation loop work?" | [INVESTIGATION_WORKFLOW.md](INVESTIGATION_WORKFLOW.md) → Investigation Loop Detail |

---

## 📊 Documentation Statistics

**Active Documentation**: ~5,200 lines across 11 main files
- **For New Users**: 4 files (~1,500 lines)
- **Core Concepts**: 5 files (~3,300 lines)
- **Specific Features**: 2 files (~400 lines)

**Historical Documentation**: ~3,900 lines across 4 files (preserved for reference)

**Total**: ~7,800+ lines of comprehensive documentation

**Agent Definitions**: ~4,200 lines (in ../agents/)
**Examples**: ~350 lines (in ../examples/)
**Scripts**: ~500 lines (in ../scripts/)

**Grand Total**: ~12,800+ lines of documentation and reference material

---

## 🤝 Contributing to Documentation

When adding new documentation:

1. **For current system specs** → Add to /docs/ folder
2. **For historical reference** → Add to historical-dev-docs/ folder (rarely modified)
3. **Update this DOCS_INDEX.md** with new entries
4. **Include cross-references** to related documents
5. **Add section summaries** with length estimates and audience

**Format guidelines**:
- Use ATX-style headings (#)
- Include length estimates and read time
- Link related documents with cross-references
- Use tables for quick reference
- Include both theory and practical examples

---

## 🆘 Getting Help

Can't find what you need? Try:

1. **Quick lookup**: Check "Finding Information by Topic" section above
2. **Search questions**: Check "Common Questions" table
3. **Examples**: See [../examples/EXAMPLES.md](../examples/EXAMPLES.md) for practical usage
4. **Agent definitions**: Check [../agents/](../agents/) folder for per-agent documentation
5. **Scripts**: Check [../scripts/README.md](../scripts/README.md) for setup help

---

## 🗂️ Related Resources

- **[../README.md](../README.md)** - Project overview and quick start
- **[../examples/EXAMPLES.md](../examples/EXAMPLES.md)** - Usage examples and workflows
- **[../agents/](../agents/)** - Agent definition files (developer.md, tech_lead.md, etc.)
- **[../scripts/](../scripts/)** - Utility scripts and initialization
- **[../config/](../config/)** - Configuration files

---

**Last Updated**: 2025-01-10
**Version**: 2.1 (Added QUICK_REFERENCE, ADVANCED; restructured for lite/advanced profiles)
**Maintained By**: Project contributors
