"""Pytest configuration and fixtures for agent migration tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project():
    """Provide a temporary project directory with agent structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Create common directories
        (tmppath / "agents").mkdir()
        (tmppath / "agents" / "copilot").mkdir()
        (tmppath / ".github" / "agents").mkdir(parents=True)
        (tmppath / ".claude" / "agents").mkdir(parents=True)
        yield tmppath


@pytest.fixture
def sample_agent_content():
    """Provide sample Claude agent content for testing."""
    return '''---
name: test_agent
description: A test agent for validation
model: sonnet
---

# Test Agent

You are a **TEST AGENT** for validation.

## Your Role

- Test functionality
- Validate transformations

## Tools

Use Task() to spawn agents.
Use Read() to read files.
Use Bash() for commands.

## Example

```python
# Some code example
def test():
    pass
```
'''


@pytest.fixture
def sample_agent_without_frontmatter():
    """Provide agent content without frontmatter."""
    return '''# Test Agent Without Frontmatter

This agent has no YAML frontmatter.

## Instructions

Just follow the rules.
'''


@pytest.fixture
def sample_agent_with_tools():
    """Provide agent content with various tool references."""
    return '''---
name: tool_test_agent
description: Agent with various tool references
model: opus
---

# Tool Test Agent

## Using Tools

1. Use Task(subagent_type="developer") to spawn a developer.
2. Use Read(file_path="test.py") to read files.
3. Use Bash(command="ls") for shell commands.
4. Use Grep() and Glob() for searching.
5. The Task tool is essential.
6. The Read tool helps.

## Notes

Prefer Skill(command: "lint-check") for linting.
'''


@pytest.fixture
def agents_dir(tmp_project, sample_agent_content):
    """Create a directory with sample agent files."""
    agents_path = tmp_project / "agents"

    # Create sample agents
    agent_names = [
        "orchestrator",
        "project_manager",
        "developer",
        "qa_expert",
    ]

    for name in agent_names:
        content = sample_agent_content.replace("test_agent", name)
        content = content.replace("A test agent", f"The {name}")
        (agents_path / f"{name}.md").write_text(content)

    return agents_path
