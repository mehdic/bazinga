#!/usr/bin/env python3
"""
Merge developer base with senior delta to produce senior agent.

Delta commands:
- ## REPLACE: <section_marker>  - Replace section matching marker
- ## REMOVE: <section_marker>   - Remove section matching marker
- ## ADD_AFTER: <section_marker> - Insert content after section
- ## ADD_BEFORE: <section_marker> - Insert content before section
- ## MODIFY: <section_marker>   - Append modification notes to section

Section markers match headers in the base file (without the ## prefix).
Special markers:
- FRONTMATTER : The YAML frontmatter block (---)

Usage:
    python merge_agent_delta.py <base_file> <delta_file> <output_file>
"""

import re
import sys
from pathlib import Path
from typing import Optional


def parse_delta_file(delta_content: str) -> dict:
    """Parse delta file into operations."""
    operations = {
        'replace': {},      # marker -> new_content
        'remove': set(),    # set of markers to remove
        'add_after': {},    # marker -> content to add
        'add_before': {},   # marker -> content to add
        'modify': {},       # marker -> modification content
    }

    current_op = None
    current_marker = None
    current_content = []

    lines = delta_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip single-line comments (starting with '# ') and empty lines outside operations
        # Note: We must NOT skip '## ' lines as they are our operation markers
        if current_op is None:
            if (line.startswith('# ') and not line.startswith('## ')) or line.strip() == '':
                i += 1
                continue

        # Check for operation markers
        replace_match = re.match(r'^## REPLACE: (.+)$', line)
        remove_match = re.match(r'^## REMOVE: (.+)$', line)
        add_after_match = re.match(r'^## ADD_AFTER: (.+)$', line)
        add_before_match = re.match(r'^## ADD_BEFORE: (.+)$', line)
        modify_match = re.match(r'^## MODIFY: (.+)$', line)
        end_match = re.match(r'^## END_(REPLACE|ADD|MODIFY)$', line)

        if replace_match:
            # Save previous operation if any
            if current_op and current_marker:
                save_operation(operations, current_op, current_marker, current_content)
            current_op = 'replace'
            current_marker = replace_match.group(1).strip()
            current_content = []
            i += 1
            continue

        elif remove_match:
            marker = remove_match.group(1).strip()
            operations['remove'].add(marker)
            i += 1
            continue

        elif add_after_match:
            if current_op and current_marker:
                save_operation(operations, current_op, current_marker, current_content)
            current_op = 'add_after'
            current_marker = add_after_match.group(1).strip()
            current_content = []
            i += 1
            continue

        elif add_before_match:
            if current_op and current_marker:
                save_operation(operations, current_op, current_marker, current_content)
            current_op = 'add_before'
            current_marker = add_before_match.group(1).strip()
            current_content = []
            i += 1
            continue

        elif modify_match:
            if current_op and current_marker:
                save_operation(operations, current_op, current_marker, current_content)
            current_op = 'modify'
            current_marker = modify_match.group(1).strip()
            current_content = []
            i += 1
            continue

        elif end_match:
            if current_op and current_marker:
                save_operation(operations, current_op, current_marker, current_content)
            current_op = None
            current_marker = None
            current_content = []
            i += 1
            continue

        # Accumulate content for current operation
        if current_op is not None:
            current_content.append(line)

        i += 1

    # Save any remaining operation
    if current_op and current_marker:
        save_operation(operations, current_op, current_marker, current_content)

    return operations


def save_operation(operations: dict, op_type: str, marker: str, content: list):
    """Save operation content, trimming leading/trailing blank lines."""
    # Remove leading blank lines
    while content and content[0].strip() == '':
        content.pop(0)
    # Remove trailing blank lines
    while content and content[-1].strip() == '':
        content.pop()

    content_str = '\n'.join(content)

    if op_type == 'replace':
        operations['replace'][marker] = content_str
    elif op_type == 'add_after':
        operations['add_after'][marker] = content_str
    elif op_type == 'add_before':
        operations['add_before'][marker] = content_str
    elif op_type == 'modify':
        operations['modify'][marker] = content_str


def find_section_bounds(lines: list, marker: str) -> tuple[Optional[int], Optional[int]]:
    """Find the start and end line indices for a section.

    Returns (start_idx, end_idx) where end_idx is the line AFTER the section.
    """
    # Special case for frontmatter
    if marker == 'FRONTMATTER':
        if lines[0].strip() == '---':
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    return 0, i + 1
        return None, None

    # Find header matching marker - match the text after #'s
    # The marker is just the text, we need to find "# <marker>" or "## <marker>" etc.
    start_idx = None
    header_level = None

    for i, line in enumerate(lines):
        # Check if this line is a header that ends with our marker
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match:
            header_text = header_match.group(2).strip()
            if header_text == marker:
                start_idx = i
                header_level = len(header_match.group(1))
                break

    if start_idx is None:
        return None, None

    # Find end of section (next header of same or higher level)
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        header_match = re.match(r'^(#{1,6})\s+', line)
        if header_match:
            level = len(header_match.group(1))
            if level <= header_level:
                end_idx = i
                break

    return start_idx, end_idx


def apply_operations(base_content: str, operations: dict) -> str:
    """Apply delta operations to base content."""
    lines = base_content.split('\n')

    # Track modifications to apply
    replacements = []  # (start, end, new_content)
    removals = []      # (start, end)
    additions_after = []   # (after_line, content)
    additions_before = []  # (before_line, content)
    modifications = []     # (end_of_section, content)

    # Process REPLACE operations
    for marker, new_content in operations['replace'].items():
        start, end = find_section_bounds(lines, marker)
        if start is not None:
            replacements.append((start, end, new_content))
            print(f"  REPLACE: '{marker}' (lines {start}-{end})")
        else:
            print(f"  Warning: Could not find section for REPLACE: {marker}", file=sys.stderr)

    # Process REMOVE operations
    for marker in operations['remove']:
        start, end = find_section_bounds(lines, marker)
        if start is not None:
            removals.append((start, end))
            print(f"  REMOVE: '{marker}' (lines {start}-{end})")
        else:
            print(f"  Warning: Could not find section for REMOVE: {marker}", file=sys.stderr)

    # Process ADD_AFTER operations
    for marker, content in operations['add_after'].items():
        start, end = find_section_bounds(lines, marker)
        if end is not None:
            additions_after.append((end, content))
            print(f"  ADD_AFTER: '{marker}' (at line {end})")
        else:
            print(f"  Warning: Could not find section for ADD_AFTER: {marker}", file=sys.stderr)

    # Process ADD_BEFORE operations
    for marker, content in operations['add_before'].items():
        start, end = find_section_bounds(lines, marker)
        if start is not None:
            additions_before.append((start, content))
            print(f"  ADD_BEFORE: '{marker}' (at line {start})")
        else:
            print(f"  Warning: Could not find section for ADD_BEFORE: {marker}", file=sys.stderr)

    # Process MODIFY operations (append to end of section)
    for marker, content in operations['modify'].items():
        start, end = find_section_bounds(lines, marker)
        if end is not None:
            # Insert before the end of section
            modifications.append((end, content))
            print(f"  MODIFY: '{marker}' (at line {end})")
        else:
            print(f"  Warning: Could not find section for MODIFY: {marker}", file=sys.stderr)

    # Apply all operations (process from end to start to preserve line numbers)
    all_ops = []

    for start, end, content in replacements:
        all_ops.append(('replace', start, end, content))

    for start, end in removals:
        all_ops.append(('remove', start, end, None))

    for pos, content in additions_after:
        all_ops.append(('add_after', pos, pos, content))

    for pos, content in additions_before:
        all_ops.append(('add_before', pos, pos, content))

    for pos, content in modifications:
        all_ops.append(('modify', pos, pos, content))

    # Sort by position (descending) so we process from end to start
    all_ops.sort(key=lambda x: x[1], reverse=True)

    # Apply operations
    for op_type, start, end, content in all_ops:
        if op_type == 'replace':
            lines[start:end] = content.split('\n')
        elif op_type == 'remove':
            # Remove section and any trailing blank lines
            while end < len(lines) and lines[end].strip() == '':
                end += 1
            del lines[start:end]
        elif op_type == 'add_after':
            insert_lines = ['', ''] + content.split('\n')  # Add blank line before
            lines[start:start] = insert_lines
        elif op_type == 'add_before':
            insert_lines = content.split('\n') + ['', '']  # Add blank line after
            lines[start:start] = insert_lines
        elif op_type == 'modify':
            insert_lines = ['', ''] + content.split('\n')
            lines[start:start] = insert_lines

    return '\n'.join(lines)


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <base_file> <delta_file> <output_file>")
        sys.exit(1)

    base_path = Path(sys.argv[1])
    delta_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    if not base_path.exists():
        print(f"Error: Base file not found: {base_path}")
        sys.exit(1)

    if not delta_path.exists():
        print(f"Error: Delta file not found: {delta_path}")
        sys.exit(1)

    # Read files
    base_content = base_path.read_text()
    delta_content = delta_path.read_text()

    # Parse delta
    print("Parsing delta file...")
    operations = parse_delta_file(delta_content)

    # Show what we found
    print(f"  Found {len(operations['replace'])} REPLACE operations")
    print(f"  Found {len(operations['remove'])} REMOVE operations")
    print(f"  Found {len(operations['add_after'])} ADD_AFTER operations")
    print(f"  Found {len(operations['add_before'])} ADD_BEFORE operations")
    print(f"  Found {len(operations['modify'])} MODIFY operations")

    # Apply operations
    print("\nApplying operations...")
    result = apply_operations(base_content, operations)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result)

    print(f"\nGenerated: {output_path}")


if __name__ == '__main__':
    main()
