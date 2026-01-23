# BAZINGA Multi-Agent Orchestration System

*Auto-generated for GitHub Copilot*

*Generated: 2026-01-23T16:26:56.287497*

---

## Available Agents

This project uses BAZINGA multi-agent orchestration. The following agents are available:

### @developer

**Description:** Implementation specialist that writes code, runs tests, and delivers working features

**Tools:** read, edit, execute, search

### @investigator

**Description:** Deep-dive investigation agent for complex, multi-hypothesis technical problems requiring iterative experimentation

**Tools:** read, search, execute

### @orchestrator

**Description:** BAZINGA orchestrator agent

**Tools:** read, edit, execute, search, #runSubagent

### @project-manager

**Description:** Coordinates projects, decides execution mode (simple/parallel), tracks progress, sends BAZINGA

**Tools:** read, search, #runSubagent

### @qa-expert

**Description:** Testing specialist for integration, contract, and e2e tests

**Tools:** read, edit, execute, search

### @requirements-engineer

**Description:** Analyzes user requests, discovers codebase context, and generates enhanced execution-ready requirements

**Tools:** read, search

### @senior-software-engineer

**Description:** Senior implementation specialist handling escalated complexity from developer failures

**Tools:** read, edit, execute, search

### @tech-lead

**Description:** Review specialist that evaluates code quality, provides guidance, and unblocks developers

**Tools:** read, search

### @tech-stack-scout

**Description:** Analyze project structure and detect technology stack

**Tools:** read, search

---

## Project Context

*Imported from CLAUDE.md*

### Key Rules

1. **Orchestrator coordinates** - spawns agents, does not implement
2. **PM decides execution** - simple vs parallel mode
3. **Quality gates mandatory** - QA and Tech Lead review all work
4. **BAZINGA signals completion** - only PM can send

---

## Usage

To start an orchestration:

```
@orchestrator <your requirements here>
```

The orchestrator will spawn the appropriate agents to complete your task.
