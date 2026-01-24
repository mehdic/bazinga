#!/usr/bin/env python3
"""
Check agents and prompts for Claude-specific elements that need Copilot adaptation.

Usage:
    python scripts/check-copilot-compatibility.py [--fix] [--path PATH]

Options:
    --fix       Show suggested fixes (doesn't modify files)
    --path      Check specific directory (default: checks both .claude and .github)
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# ANSI colors
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


@dataclass
class Issue:
    file: Path
    line_num: int
    line: str
    pattern: str
    suggestion: str
    severity: str  # "error" or "warning"


# Patterns to check (pattern, suggestion, severity)
CLAUDE_PATTERNS = [
    # Tool syntax
    (r'\bTask\(', '#runSubagent(', 'error', 'Claude Task() should be #runSubagent() in Copilot'),
    (r'\bTask tool\b', '#runSubagent tool', 'warning', 'Task tool reference'),

    # Directory paths
    (r'\.claude/agents/', '.github/agents/', 'error', 'Claude agent path'),
    (r'\.claude/skills/', '.github/skills/', 'error', 'Claude skills path'),
    (r'\.claude/commands/', '.github/prompts/', 'error', 'Claude commands path'),
    (r'\.claude/templates/', 'bazinga/templates/', 'warning', 'Claude templates path'),
    (r'\.claude/hooks/', 'bazinga/hooks/', 'warning', 'Claude hooks path (not supported in Copilot)'),

    # Agent file references (underscore naming)
    (r'agents/project_manager\.md', '.github/agents/project-manager.agent.md', 'error', 'Claude agent file reference'),
    (r'agents/developer\.md', '.github/agents/developer.agent.md', 'error', 'Claude agent file reference'),
    (r'agents/senior_software_engineer\.md', '.github/agents/senior-software-engineer.agent.md', 'error', 'Claude agent file reference'),
    (r'agents/qa_expert\.md', '.github/agents/qa-expert.agent.md', 'error', 'Claude agent file reference'),
    (r'agents/tech_lead\.md', '.github/agents/tech-lead.agent.md', 'error', 'Claude agent file reference'),
    (r'agents/orchestrator\.md', '.github/agents/orchestrator.agent.md', 'error', 'Claude agent file reference'),
    (r'agents/investigator\.md', '.github/agents/investigator.agent.md', 'error', 'Claude agent file reference'),
    (r'agents/requirements_engineer\.md', '.github/agents/requirements-engineer.agent.md', 'error', 'Claude agent file reference'),
    (r'agents/tech_stack_scout\.md', '.github/agents/tech-stack-scout.agent.md', 'error', 'Claude agent file reference'),

    # Generic agent pattern (but not .github/agents/)
    (r'(?<!\.github/)agents/\w+\.md\b', '.github/agents/*.agent.md', 'warning', 'Possible Claude agent reference'),

    # Terminology
    (r'\bClaude Code\b(?! (and|or|vs|versus) )', 'GitHub Copilot', 'warning', 'Claude Code terminology'),
    (r'\bClaude Code Multi-Agent Dev Team\b', 'BAZINGA Multi-Agent Dev Team', 'warning', 'Claude branding'),

    # Model references (informational only in Copilot)
    (r'model:\s*(haiku|sonnet|opus)\b', None, 'info', 'Model selection (informational only in Copilot)'),

    # Subagent syntax variations
    (r'subagent_type:\s*"', None, 'warning', 'Claude subagent_type parameter (use name: in Copilot)'),
    (r'run_in_background:\s*(true|false)', None, 'info', 'Background execution (check Copilot support)'),
]

# Patterns that are OK in Copilot (don't flag these)
COPILOT_OK_PATTERNS = [
    r'\.github/agents/',
    r'\.github/skills/',
    r'\.github/prompts/',
    r'#runSubagent',
    r'\.agent\.md',
]


def check_file(filepath: Path, show_fix: bool = False) -> list[Issue]:
    """Check a single file for Claude-specific patterns."""
    issues = []

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"{RED}Error reading {filepath}: {e}{RESET}")
        return issues

    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#') and not stripped.startswith('#run'):
            continue

        for pattern, suggestion, severity, description in CLAUDE_PATTERNS:
            if re.search(pattern, line):
                # Check if line also has Copilot-OK pattern (might be documentation showing both)
                has_copilot_ok = any(re.search(ok_pat, line) for ok_pat in COPILOT_OK_PATTERNS)

                # Skip if it's comparing Claude vs Copilot (documentation)
                if 'Claude Code' in line and ('Copilot' in line or 'vs' in line.lower()):
                    continue

                # Skip if line has both patterns (likely a replacement mapping)
                if has_copilot_ok and suggestion and suggestion in line:
                    continue

                issues.append(Issue(
                    file=filepath,
                    line_num=line_num,
                    line=line.strip()[:100] + ('...' if len(line.strip()) > 100 else ''),
                    pattern=pattern,
                    suggestion=suggestion,
                    severity=severity
                ))

    return issues


def check_directory(dirpath: Path, extensions: list[str] = None) -> list[Issue]:
    """Check all files in a directory."""
    if extensions is None:
        extensions = ['.md', '.json', '.py', '.sh']

    issues = []

    if not dirpath.exists():
        print(f"{YELLOW}Directory not found: {dirpath}{RESET}")
        return issues

    for ext in extensions:
        for filepath in dirpath.rglob(f'*{ext}'):
            # Skip node_modules, __pycache__, etc.
            if any(skip in str(filepath) for skip in ['node_modules', '__pycache__', '.git', 'venv']):
                continue
            issues.extend(check_file(filepath))

    return issues


def print_report(issues: list[Issue], show_fix: bool = False):
    """Print a formatted report of issues."""
    if not issues:
        print(f"\n{GREEN}✓ No Claude-specific patterns found!{RESET}")
        return

    # Group by file
    by_file: dict[Path, list[Issue]] = {}
    for issue in issues:
        if issue.file not in by_file:
            by_file[issue.file] = []
        by_file[issue.file].append(issue)

    # Count by severity
    errors = sum(1 for i in issues if i.severity == 'error')
    warnings = sum(1 for i in issues if i.severity == 'warning')
    infos = sum(1 for i in issues if i.severity == 'info')

    print(f"\n{BOLD}Copilot Compatibility Report{RESET}")
    print("=" * 60)
    print(f"Files checked: {len(by_file)}")
    print(f"Issues found: {RED}{errors} errors{RESET}, {YELLOW}{warnings} warnings{RESET}, {CYAN}{infos} info{RESET}")
    print("=" * 60)

    for filepath, file_issues in sorted(by_file.items()):
        print(f"\n{BOLD}{filepath}{RESET}")

        for issue in sorted(file_issues, key=lambda x: x.line_num):
            if issue.severity == 'error':
                color = RED
                icon = '✗'
            elif issue.severity == 'warning':
                color = YELLOW
                icon = '⚠'
            else:
                color = CYAN
                icon = 'ℹ'

            print(f"  {color}{icon}{RESET} Line {issue.line_num}: {issue.line}")

            if show_fix and issue.suggestion:
                print(f"    {GREEN}→ Suggestion: {issue.suggestion}{RESET}")

    print("\n" + "=" * 60)
    print(f"{BOLD}Summary:{RESET}")
    if errors > 0:
        print(f"  {RED}✗ {errors} error(s) - Must fix for Copilot compatibility{RESET}")
    if warnings > 0:
        print(f"  {YELLOW}⚠ {warnings} warning(s) - Review for Copilot compatibility{RESET}")
    if infos > 0:
        print(f"  {CYAN}ℹ {infos} info - Informational (may work differently in Copilot){RESET}")


def main():
    parser = argparse.ArgumentParser(
        description='Check agents and prompts for Claude-specific elements'
    )
    parser.add_argument('--fix', action='store_true', help='Show suggested fixes')
    parser.add_argument('--path', type=str, help='Check specific directory')
    parser.add_argument('--copilot-only', action='store_true',
                        help='Only check .github/ directory (Copilot files)')
    parser.add_argument('--claude-only', action='store_true',
                        help='Only check .claude/ directory (Claude files)')
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    all_issues = []

    if args.path:
        # Check specific path
        check_path = Path(args.path)
        if not check_path.is_absolute():
            check_path = project_root / check_path
        print(f"Checking: {check_path}")
        all_issues.extend(check_directory(check_path))
    else:
        # Check relevant directories
        dirs_to_check = []

        if not args.copilot_only:
            dirs_to_check.extend([
                project_root / '.claude' / 'commands',
                project_root / '.claude' / 'agents',
                project_root / 'agents',  # Source agents
            ])

        if not args.claude_only:
            dirs_to_check.extend([
                project_root / '.github' / 'prompts',
                project_root / '.github' / 'agents',
                project_root / 'agents' / 'copilot',  # Copilot-specific agents
            ])

        # Always check templates
        dirs_to_check.append(project_root / 'templates')

        for dir_path in dirs_to_check:
            if dir_path.exists():
                print(f"Checking: {dir_path}")
                all_issues.extend(check_directory(dir_path))

    print_report(all_issues, show_fix=args.fix)

    # Exit with error code if errors found
    errors = sum(1 for i in all_issues if i.severity == 'error')
    sys.exit(1 if errors > 0 else 0)


if __name__ == '__main__':
    main()
