# Contributing to BAZINGA

Thank you for your interest in contributing to BAZINGA! This document provides guidelines for contributing to the project.

---

## First-Time Setup

After cloning the repository, you **must** install git hooks to enable automatic build processes:

```bash
./scripts/install-hooks.sh
```

This installs the pre-commit hook that automatically rebuilds slash commands when you modify agent source files.

**⚠️ Without this step:** Your commits won't automatically sync `agents/orchestrator.md` with `.claude/commands/bazinga.orchestrate.md`, causing inconsistencies.

---

## Development Workflow

### Modifying the Orchestrator

**IMPORTANT:** The orchestrator workflow has a special development pattern to maintain consistency.

#### Source of Truth

The **single source of truth** for orchestration logic is:
```
agents/orchestrator.md
```

**DO NOT directly edit** `.claude/commands/bazinga.orchestrate.md` - it is auto-generated!

#### How it Works

1. **Edit only** `agents/orchestrator.md` when modifying orchestration logic
2. The **pre-commit hook** automatically rebuilds `.claude/commands/bazinga.orchestrate.md`
3. The generated slash command runs the orchestrator **inline** (not as a spawned agent)
4. This ensures real-time visibility of orchestration progress

#### Build Process

The build script `scripts/build-slash-commands.sh`:
- Reads `agents/orchestrator.md`
- Extracts frontmatter (name, description)
- Generates `.claude/commands/bazinga.orchestrate.md`
- Preserves inline execution (not Task() spawning)

To manually rebuild (if needed):
```bash
./scripts/build-slash-commands.sh
```

#### Pre-Commit Hook

A git pre-commit hook at `.git/hooks/pre-commit`:
- Detects changes to `agents/orchestrator.md`
- Automatically runs the build script
- Stages the generated `.claude/commands/bazinga.orchestrate.md`

This ensures the slash command always stays in sync with the source agent file.

---

## General Guidelines

### Code Contributions

- **Areas for improvement:**
  - Additional language support (Rust, C#, etc.)
  - New Skills for analysis
  - Performance optimizations
  - Documentation improvements
  - Bug fixes

### Testing

- Test all changes locally before submitting
- Ensure orchestration workflow completes successfully
- Verify slash commands work correctly

### Pull Requests

- Create a feature branch from `main`
- Write clear, descriptive commit messages
- Reference any related issues
- Ensure all tests pass

### Code Style

- Follow existing code patterns
- Keep agent prompts focused and clear
- Use markdown formatting consistently
- Document complex logic

---

## Project Structure

```
bazinga/
├── agents/                          # Agent definitions (source of truth)
│   ├── orchestrator.md             # Orchestration logic (DO NOT EDIT slash command directly!)
│   ├── project_manager.md
│   ├── developer.md
│   ├── qa_expert.md
│   ├── tech_lead.md
│   └── investigator.md
├── .claude/
│   ├── commands/                    # Slash commands (generated)
│   │   ├── bazinga.orchestrate.md  # Auto-generated from agents/orchestrator.md
│   │   └── bazinga.orchestrate-advanced.md
│   └── skills/                      # Quality and analysis skills
├── scripts/
│   └── build-slash-commands.sh     # Generates slash commands from agents
├── templates/                       # Prompt templates
└── research/                        # Design docs and experiments
```

---

## Questions?

Open an issue or discussion on GitHub: https://github.com/mehdic/bazinga

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
