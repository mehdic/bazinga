#!/usr/bin/env python3
"""
Fix broken cross-references in orchestrator.md after refactoring.
Updates obsolete line number references to point to correct locations.
"""

import re
from pathlib import Path


def fix_parsing_references(content: str) -> str:
    """Replace obsolete parsing line references with template references."""

    # Pattern 1: "Use §Developer Response Parsing (lines XX-YY)"
    # Replace with template reference
    patterns = [
        (r'Use §Developer Response Parsing \(lines \d+-\d+\)',
         'Use the Developer Response Parsing section in `bazinga/templates/response_parsing.md`'),

        (r'Use §QA Expert Response Parsing \(lines \d+-\d+\)',
         'Use the QA Expert Response Parsing section in `bazinga/templates/response_parsing.md`'),

        (r'Use §Tech Lead Response Parsing \(lines \d+-\d+\)',
         'Use the Tech Lead Response Parsing section in `bazinga/templates/response_parsing.md`'),

        (r'Use §PM Response Parsing \(lines \d+-\d+\)',
         'Use the PM Response Parsing section in `bazinga/templates/response_parsing.md`'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # Pattern 2: "see §Developer Response Parsing line XX-YY"
    # Replace with template reference
    fallback_patterns = [
        (r'see §Developer Response Parsing line \d+-\d+',
         'see Developer fallback strategies in `bazinga/templates/response_parsing.md`'),

        (r'see §QA Expert Response Parsing line \d+-\d+',
         'see QA fallback strategies in `bazinga/templates/response_parsing.md`'),

        (r'see §Tech Lead Response Parsing line \d+-\d+',
         'see Tech Lead fallback strategies in `bazinga/templates/response_parsing.md`'),

        (r'see §PM Response Parsing line \d+-\d+',
         'see PM fallback strategies in `bazinga/templates/response_parsing.md`'),
    ]

    for pattern, replacement in fallback_patterns:
        content = re.sub(pattern, replacement, content)

    print("✓ Fixed parsing section references (replaced line ranges with template references)")
    return content


def fix_task_groups_query_references(content: str) -> str:
    """Replace §line 146 task groups references with §Step 1.4."""

    # Replace "Query task groups (§line 146 (Query task groups))" with "Query task groups (§Step 1.4)"
    content = re.sub(
        r'Query task groups \(§line \d+ \(Query task groups\)\)',
        'Query task groups (§Step 1.4)',
        content
    )

    print("✓ Fixed task groups query references (§line 146 → §Step 1.4)")
    return content


def fix_logging_references(content: str) -> str:
    """Replace obsolete logging line references with template reference."""

    # Replace "Log response (§line XXXX)" with template reference
    content = re.sub(
        r'Log response \(§line \d+\)',
        'Log to database (see `bazinga/templates/logging_pattern.md`)',
        content
    )

    print("✓ Fixed logging references (replaced §line with template reference)")
    return content


def main():
    orchestrator_path = Path("agents/orchestrator.md")

    if not orchestrator_path.exists():
        print(f"❌ File not found: {orchestrator_path}")
        return 1

    print("Reading orchestrator.md...")
    content = orchestrator_path.read_text()
    original_content = content

    print()
    print("Fixing cross-references...")
    print()

    # Fix all reference types
    content = fix_parsing_references(content)
    content = fix_task_groups_query_references(content)
    content = fix_logging_references(content)

    # Count changes
    if content != original_content:
        print()
        print("=" * 60)
        print("Changes summary:")

        # Count specific changes
        parsing_changes = len(re.findall(r'templates/response_parsing\.md', content)) - \
                         len(re.findall(r'templates/response_parsing\.md', original_content))
        step_changes = content.count('§Step 1.4') - original_content.count('§Step 1.4')
        logging_changes = content.count('templates/logging_pattern.md') - \
                         original_content.count('templates/logging_pattern.md')

        print(f"  - Response parsing: +{parsing_changes} template references")
        print(f"  - Task groups query: +{step_changes} §Step 1.4 references")
        print(f"  - Logging pattern: +{logging_changes} template references")
        print("=" * 60)

        # Write back
        print()
        print("Writing updated orchestrator.md...")
        orchestrator_path.write_text(content)
        print("✓ Done!")
        return 0
    else:
        print()
        print("No changes needed - all references already correct")
        return 0


if __name__ == "__main__":
    exit(main())
