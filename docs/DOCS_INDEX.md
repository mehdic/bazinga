# BAZINGA - Claude Code Multi-Agent Dev Team - Documentation Index

> **Repository:** https://github.com/mehdic/bazinga

This directory contains comprehensive documentation for BAZINGA (Claude Code Multi-Agent Dev Team).

## 📚 Documentation Organization

### Main Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical deep-dive into system design | Developers, Architects |
| **[ROLE_DRIFT_PREVENTION.md](ROLE_DRIFT_PREVENTION.md)** | Detailed explanation of 6-layer defense system | System designers |
| **[SCOPE_REDUCTION_INCIDENT.md](SCOPE_REDUCTION_INCIDENT.md)** | Case study of orchestrator role drift issue | Troubleshooters |

### Original Development Documentation (Historical)

Located in `historical-dev-docs/` - Historical documentation from the development:

| Document | Purpose | Content |
|----------|---------|---------|
| **[V4_ARCHITECTURE.md](historical-dev-docs/V4_ARCHITECTURE.md)** | Original architecture specification | System design, agent roles |
| **[V4_IMPLEMENTATION_SUMMARY.md](historical-dev-docs/V4_IMPLEMENTATION_SUMMARY.md)** | Implementation history and decisions | Development notes |
| **[V4_STATE_SCHEMAS.md](historical-dev-docs/V4_STATE_SCHEMAS.md)** | State file schemas and structures | JSON schemas, examples |
| **[V4_WORKFLOW_DIAGRAMS.md](historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md)** | Visual workflow representations | Diagrams, flow charts |

## 🎯 Reading Guide

### For Quick Start
1. Start with **[../README.md](../README.md)** (project overview)
2. Read **[../examples/EXAMPLES.md](../examples/EXAMPLES.md)** (usage examples)
3. Refer to **ARCHITECTURE.md** for technical details as needed

### For Understanding System Design
1. **ARCHITECTURE.md** - Complete technical specification
2. **historical-dev-docs/V4_ARCHITECTURE.md** - Original design document
3. **historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md** - Visual representations

### For Preventing Issues
1. **ROLE_DRIFT_PREVENTION.md** - Understanding the 6-layer defense
2. **SCOPE_REDUCTION_INCIDENT.md** - Learn from past issues
3. **ARCHITECTURE.md** (Role Drift Prevention section)

### For State Management
1. **historical-dev-docs/V4_STATE_SCHEMAS.md** - Complete schema definitions
2. **ARCHITECTURE.md** (State Management section)
3. **[../scripts/README.md](../scripts/README.md)** - Initialization guide

### For Development History
1. **historical-dev-docs/V4_IMPLEMENTATION_SUMMARY.md** - Development journey
2. **SCOPE_REDUCTION_INCIDENT.md** - Key turning point
3. **ROLE_DRIFT_PREVENTION.md** - Solution evolution

## 📖 Document Summaries

### ARCHITECTURE.md
**Length**: ~1,100 lines
**Sections**:
- System Overview
- Agent Definitions (5 agents)
- Workflow Patterns (5 types)
- Role Drift Prevention (6 layers)
- State Management
- Routing Mechanism
- Tool Restrictions
- Decision Logic

**Use when**: You need technical specifications, implementation details, or system behavior understanding.

### ROLE_DRIFT_PREVENTION.md
**Length**: ~350 lines
**Sections**:
- Problem Definition
- Research Findings
- 6-Layer Defense System
- Layer Details
- Implementation Guide
- Effectiveness Analysis

**Use when**: You're experiencing role drift issues or want to understand how the prevention system works.

### SCOPE_REDUCTION_INCIDENT.md
**Length**: ~150 lines
**Sections**:
- The Incident
- Root Cause Analysis
- Solution Implemented
- Lessons Learned

**Use when**: Troubleshooting orchestrator behavior or understanding why certain constraints exist.

### historical-dev-docs/V4_ARCHITECTURE.md
**Length**: ~580 lines
**Focus**: Original system design specifications

**Use when**: You want to see the original vision or compare with current implementation.

### historical-dev-docs/V4_IMPLEMENTATION_SUMMARY.md
**Length**: ~350 lines
**Focus**: Development history, decisions, iterations

**Use when**: Understanding why certain design choices were made.

### historical-dev-docs/V4_STATE_SCHEMAS.md
**Length**: ~710 lines
**Focus**: JSON schema definitions, examples, validation

**Use when**: Working with state files, debugging state issues, or extending the system.

### historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md
**Length**: ~2,100 lines
**Focus**: Visual workflow representations, ASCII diagrams

**Use when**: You need visual understanding of workflows or want to create documentation.

## 🔍 Finding Information

### By Topic

**Agent Behavior**:
- ARCHITECTURE.md → Agent Definitions section
- historical-dev-docs/V4_ARCHITECTURE.md → Agent specifications

**Workflow Routing**:
- ARCHITECTURE.md → Routing Mechanism section
- historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md → Visual flows
- ../examples/EXAMPLES.md → Practical examples

**Role Drift Prevention**:
- ROLE_DRIFT_PREVENTION.md → Complete analysis
- ARCHITECTURE.md → Role Drift Prevention section
- SCOPE_REDUCTION_INCIDENT.md → Case study

**State Management**:
- historical-dev-docs/V4_STATE_SCHEMAS.md → Schema definitions
- ARCHITECTURE.md → State Management section
- ../scripts/README.md → Initialization

**Decision Logic**:
- ARCHITECTURE.md → Decision Logic section
- historical-dev-docs/V4_IMPLEMENTATION_SUMMARY.md → Evolution

**Tool Restrictions**:
- ARCHITECTURE.md → Tool Restrictions section
- Agent definition files (../agents/*.md) → Per-agent tools

### By Question

**"How does the orchestrator decide where to route?"**
→ ARCHITECTURE.md (Routing Mechanism) + historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md

**"Why does PM never use Edit tool?"**
→ ARCHITECTURE.md (Tool Restrictions) + ROLE_DRIFT_PREVENTION.md

**"How does conditional routing work (tests vs no tests)?"**
→ ARCHITECTURE.md (Workflow Patterns) + ../examples/EXAMPLES.md

**"What's the JSON structure of state files?"**
→ historical-dev-docs/V4_STATE_SCHEMAS.md

**"How do I prevent role drift in my own agents?"**
→ ROLE_DRIFT_PREVENTION.md + SCOPE_REDUCTION_INCIDENT.md

**"What happened during development that led to current design?"**
→ historical-dev-docs/V4_IMPLEMENTATION_SUMMARY.md + SCOPE_REDUCTION_INCIDENT.md

**"How do parallel workflows work?"**
→ ARCHITECTURE.md (Workflow Patterns) + historical-dev-docs/V4_WORKFLOW_DIAGRAMS.md

## 📊 Documentation Statistics

**Total Documentation**: ~5,900 lines across 7 files
**Main Docs**: ~1,600 lines (3 files)
**Original Historical Docs**: ~3,900 lines (4 files)
**Agent Definitions**: ~4,200 lines (5 files in ../agents/)
**Examples**: ~350 lines (1 file in ../examples/)

**Grand Total**: ~10,500+ lines of comprehensive documentation

## 🤝 Contributing to Documentation

When adding new documentation:

1. **Main docs/** - For current system specifications
2. **historical-dev-docs/** - Do not modify (historical record)
3. Update this **DOCS_INDEX.md** with new entries
4. Follow existing formatting conventions
5. Include practical examples where applicable

## 📝 Documentation Conventions

- **Headings**: Use ATX-style (#) headings
- **Code blocks**: Use fenced code blocks with language tags
- **Diagrams**: ASCII art for portability
- **Examples**: Include both correct and incorrect usage
- **Status**: Label with WRONG/CORRECT, ✅/❌
- **Cross-references**: Link to related documents

## 🆘 Help & Support

If documentation doesn't answer your question:

1. Check **../examples/EXAMPLES.md** for practical usage
2. Review **SCOPE_REDUCTION_INCIDENT.md** for common issues
3. Examine agent definition files (../agents/*.md)
4. Review initialization script (../scripts/init-orchestration.sh)

## 🗂️ Related Resources

- **[../README.md](../README.md)** - Project overview and quick start
- **[../examples/EXAMPLES.md](../examples/EXAMPLES.md)** - Usage examples
- **[../agents/](../agents/)** - Agent definition files
- **[../scripts/](../scripts/)** - Utility scripts
- **[../config/](../config/)** - Configuration files

---

**Last Updated**: 2025-01-07
**Version**: 1.0 (Conditional Workflow + 6-Layer Role Drift Prevention)
**Maintained By**: Project contributors
