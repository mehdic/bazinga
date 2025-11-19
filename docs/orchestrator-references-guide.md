# Orchestrator References Guide

This guide explains how to use and maintain references in `agents/orchestrator.md` to avoid content duplication while keeping the file maintainable.

## Reference Types

### 1. Line References

**Basic format:**
```markdown
§line 3279
```

**With keyword validation (recommended):**
```markdown
§line 3279 (task groups)
```

The keyword in parentheses is used to:
- Validate that the referenced line contains the expected content
- Auto-fix broken references when line numbers shift

**Examples:**
```markdown
Query task groups (§line 3279) → Parse PM feedback
Build revision prompt per §Step 2A.1 → Spawn agent → Log response (§line 1697)
Spawn in parallel per §line 2788 (parallel spawn) → Log responses
```

### 2. Step References

**Format:**
```markdown
§Step 2A.1
```

References a section header like `### Step 2A.1: Spawn Single Developer`

**Example:**
```markdown
Build revision prompts per §Step 2B.1 → Spawn in parallel
```

## Validation Script

### Basic Usage

```bash
# Validate all references
./scripts/validate-orchestrator-references.sh

# Show detailed validation info
./scripts/validate-orchestrator-references.sh --verbose

# Check for orphaned sections (not referenced anywhere)
./scripts/validate-orchestrator-references.sh --check-orphans

# Auto-fix broken references (updates file)
./scripts/validate-orchestrator-references.sh --fix

# Full validation with all features
./scripts/validate-orchestrator-references.sh --fix --check-orphans --verbose
```

### What Gets Validated

1. **Line number bounds** - §line 99999 fails if file has only 3839 lines
2. **Content keywords** - §line 3279 (task groups) fails if line 3279 doesn't contain "task groups"
3. **Section existence** - §Step 99Z.99 fails if section doesn't exist
4. **Orphan detection** - Finds sections that exist but aren't referenced

### Auto-Fix Mode

When you run with `--fix`, the script:

1. **Finds broken line references**
   - Searches for the keyword in the file
   - Updates the reference to the new line number
   - Example: §line 3279 (task groups) → §line 3329 (task groups)

2. **Cannot fix Step references**
   - Step structure changes require manual updates
   - Script will report which steps are broken

3. **Updates the file in-place**
   - Make sure to review changes before committing
   - Run validation again to verify fixes

### Pre-Commit Hook

The validation runs automatically on commit:

```bash
$ git commit -m "Update orchestrator"
🔨 Detected changes to agents/orchestrator.md
   Validating §line and §Step references...
  → Found 3 unique §line references
  → Found 2 unique §Step references
  ✅ All references are valid
   Rebuilding slash commands...
   ✅ Slash command rebuilt and staged
```

If references are broken, the commit is blocked:

```bash
$ git commit -m "Update orchestrator"
🔨 Detected changes to agents/orchestrator.md
   Validating §line and §Step references...
  ❌ BROKEN: §line 99999 (file only has 3839 lines)
      Hint: Run with --fix to auto-update

❌ COMMIT BLOCKED: Broken references in agents/orchestrator.md

Fix the broken references and try again.
```

## CI/CD Integration

GitHub Actions runs validation on:
- Pull requests affecting orchestrator.md
- Pushes to main or claude/** branches

See `.github/workflows/validate-orchestrator.yml`

## Best Practices

### 1. Always Add Keywords

**❌ Bad:**
```markdown
Query task groups (§line 3279) → Parse feedback
```

**✅ Good:**
```markdown
Query task groups (§line 3279 (task groups)) → Parse feedback
```

The keyword enables auto-fix when lines shift.

### 2. Use Descriptive Keywords

**❌ Bad:**
```markdown
§line 2788 (code)
```

**✅ Good:**
```markdown
§line 2788 (parallel spawn)
```

Specific keywords are more reliable for validation and auto-fix.

### 3. Prefer Step References for Sections

**❌ Bad:**
```markdown
Follow prompt building pattern at §line 1542
```

**✅ Good:**
```markdown
Follow prompt building pattern per §Step 2A.1
```

Step references are more stable than line references.

### 4. Test After Major Edits

After adding/removing large sections:

```bash
# Check if references are still valid
./scripts/validate-orchestrator-references.sh --verbose

# Auto-fix any broken references
./scripts/validate-orchestrator-references.sh --fix

# Check for newly orphaned sections
./scripts/validate-orchestrator-references.sh --check-orphans
```

## Troubleshooting

### Reference Validation Failed

```bash
❌ BROKEN: §line 3279 (file only has 3839 lines)
```

**Solution:**
```bash
# Let the script auto-fix it
./scripts/validate-orchestrator-references.sh --fix

# Or manually find where content moved
grep -n "task groups" agents/orchestrator.md
# Update reference: §line 3279 → §line 3329
```

### Content Mismatch Warning

```bash
⚠️  CONTENT MISMATCH: §line 3279
    Expected keyword: 'task groups'
    Actual content: **Step 4: Log PM response**
```

**Solution:**
```bash
# Auto-fix will search for the keyword and update
./scripts/validate-orchestrator-references.sh --fix
```

### Step Reference Not Found

```bash
❌ BROKEN: §Step 2C.5 (section not found)
```

**Solution:**
Step references can't be auto-fixed. Check if:
1. Section was renamed (e.g., 2C.5 → 2C.6)
2. Section was removed (delete reference)
3. Section was merged (update reference to new location)

### Orphaned Sections

```bash
⚠️  ORPHAN: ### Step 2A.3 (line 1719) - not referenced
```

**Not an error** - Just means nothing explicitly references this section with §Step.

**Options:**
1. Add §Step 2A.3 references where relevant
2. Leave as-is (section is still in sequential flow)
3. Remove section if truly unused

## Future Enhancements

### Anchor-Based References

For even more stability, you can use anchor comments:

```markdown
<!-- ANCHOR: task-groups-query -->
bazinga-db, please get all task groups
<!-- /ANCHOR -->
```

Then reference:
```markdown
Query task groups (§anchor task-groups-query)
```

Anchors are line-number independent - the validation script finds them by name.

### Content Hashing

For maximum validation, you can add content hashes:

```markdown
§line 3279 [hash:abc123def456]
```

The script validates that the content at line 3279 matches the hash.

These features are not yet implemented but the validation script is designed to support them.
