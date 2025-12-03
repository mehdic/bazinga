#!/usr/bin/env python3
"""
Claude Code Skill Validator
Validates SKILL.md files for proper YAML frontmatter and structure.
"""

import yaml
import pathlib
import re
import sys


def validate_skill(skill_path):
    """Validate a Claude Code SKILL.md file"""
    p = pathlib.Path(skill_path)

    if not p.exists():
        print(f"❌ File not found: {skill_path}")
        return False

    text = p.read_text(encoding='utf-8')

    # Split frontmatter
    parts = text.split('---', 2)
    if len(parts) < 3:
        print(f"❌ {p.parent.name}: Missing YAML frontmatter delimiters (---)")
        return False

    # Parse YAML
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        print(f"❌ {p.parent.name}: Invalid YAML: {e}")
        return False

    if meta is None:
        print(f"❌ {p.parent.name}: Empty YAML frontmatter")
        return False

    # Check required fields
    allowed_props = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'version', 'dependencies'}
    required_props = {'name', 'description'}

    errors = []
    warnings = []

    # Check for required fields
    for prop in required_props:
        if prop not in meta:
            errors.append(f"Missing required field: {prop}")

    # Check for unexpected properties
    for prop in meta.keys():
        if prop not in allowed_props:
            warnings.append(f"Unexpected property: {prop}")

    # Validate description length
    if 'description' in meta:
        if len(meta['description']) > 1024:
            errors.append(f"Description exceeds 1024 characters ({len(meta['description'])} chars)")

    # Validate name format (lowercase, numbers, hyphens only)
    if 'name' in meta:
        if not re.match(r'^[a-z0-9-]+$', meta['name']):
            errors.append(f"Name '{meta['name']}' must use lowercase letters, numbers, and hyphens only")

        if len(meta['name']) > 64:
            errors.append(f"Name exceeds 64 characters ({len(meta['name'])} chars)")

    # Validate allowed-tools if present
    if 'allowed-tools' in meta:
        if not isinstance(meta['allowed-tools'], list):
            errors.append("allowed-tools must be a list")
        else:
            valid_tools = {'Bash', 'Read', 'Write', 'Grep', 'Edit', 'MultiEdit', 'NotebookEdit', 'Glob'}
            for tool in meta['allowed-tools']:
                if tool not in valid_tools:
                    warnings.append(f"Unknown tool in allowed-tools: {tool}")

    # Report results
    skill_name = p.parent.name
    if errors:
        print(f"❌ {skill_name}:")
        for error in errors:
            print(f"   • {error}")
        if warnings:
            for warning in warnings:
                print(f"   ⚠️  {warning}")
        return False
    elif warnings:
        print(f"⚠️  {skill_name}:")
        for warning in warnings:
            print(f"   • {warning}")
        return True
    else:
        print(f"✅ {skill_name}: Valid")
        return True


def main():
    """Validate all skills in .claude/skills/"""
    skills_dir = pathlib.Path('.claude/skills')

    if not skills_dir.exists():
        print(f"❌ Skills directory not found: {skills_dir}")
        sys.exit(1)

    print("=" * 60)
    print("Claude Code Skill Validator")
    print("=" * 60)
    print()

    # Skip internal directories (starting with _)
    skill_dirs = sorted([d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith('_')])

    if not skill_dirs:
        print("❌ No skills found in .claude/skills/")
        sys.exit(1)

    results = []

    for skill_dir in skill_dirs:
        skill_md = skill_dir / 'SKILL.md'
        if skill_md.exists():
            valid = validate_skill(skill_md)
            results.append((skill_dir.name, valid))
        else:
            print(f"❌ {skill_dir.name}: SKILL.md not found")
            results.append((skill_dir.name, False))

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    valid_count = sum(1 for _, valid in results if valid)
    total_count = len(results)

    print(f"Total skills: {total_count}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {total_count - valid_count}")

    if valid_count == total_count:
        print()
        print("🎉 All skills passed validation!")
        sys.exit(0)
    else:
        print()
        print("⚠️  Some skills failed validation. Please fix the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
