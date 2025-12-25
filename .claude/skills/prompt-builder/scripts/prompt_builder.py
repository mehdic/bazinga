#!/usr/bin/env python3
"""
Deterministically builds agent prompts.
This script does ALL prompt composition - no LLM interpretation.

It queries the database for:
- Specializations (from task_groups.specializations)
- Context packages
- Error patterns
- Prior agent reasoning

Then reads from filesystem:
- Agent definition files (agents/*.md)
- Specialization templates (bazinga/templates/specializations/*.md)

Usage (params-file mode - RECOMMENDED for orchestrator):
    python3 prompt_builder.py --params-file "bazinga/prompts/{session}/params.json"

    The params file contains all configuration as JSON.
    Output: JSON to stdout with {success, prompt_file, tokens_estimate, ...}
    The prompt itself is saved to the output_file path specified in params.

Usage (CLI mode - for manual testing):
    python3 prompt_builder.py --agent-type developer --session-id "bazinga_xxx" \\
        --branch "main" --mode "simple" --testing-mode "full"

    Output: Raw prompt to stdout (backward compatibility)
    Add --json-output for JSON response instead.

Exit codes:
    0 = success
    1 = validation failure or error
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path


def get_project_root():
    """Detect project root by looking for .claude directory or bazinga directory.

    Returns:
        Path to project root, or current working directory if not found.
    """
    # Start from script location and traverse up
    script_dir = Path(__file__).resolve().parent

    # Look for project markers going up from script location
    current = script_dir
    for _ in range(10):  # Max 10 levels up
        if (current / ".claude").is_dir() or (current / "bazinga").is_dir():
            return current
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    # Fallback: check CWD
    cwd = Path.cwd()
    if (cwd / ".claude").is_dir() or (cwd / "bazinga").is_dir():
        return cwd

    # Last resort: use CWD and hope for the best
    return cwd


# Detect project root once at module load
PROJECT_ROOT = get_project_root()

# Database path - relative to project root
DB_PATH = str(PROJECT_ROOT / "bazinga" / "bazinga.db")


def _ensure_cwd_at_project_root():
    """Change to project root so all relative paths work correctly.

    This is critical when the script is invoked from a different CWD.
    See: research/absolute-path-resolution-ultrathink.md

    Must be called at entry point (main), NOT at module import time,
    to avoid side effects when this module is imported by tests.
    """
    try:
        os.chdir(PROJECT_ROOT)
        # Only log if BAZINGA_VERBOSE is set to reduce noise
        if os.environ.get("BAZINGA_VERBOSE"):
            print(f"[INFO] project_root={PROJECT_ROOT}", file=sys.stderr)
    except OSError as e:
        print(f"[WARNING] Failed to chdir to project root {PROJECT_ROOT}: {e}", file=sys.stderr)

# Agent file names (without directory prefix - resolved dynamically)
AGENT_FILE_NAMES = {
    "developer": "developer.md",
    "senior_software_engineer": "senior_software_engineer.md",
    "qa_expert": "qa_expert.md",
    "tech_lead": "tech_lead.md",
    "project_manager": "project_manager.md",
    "investigator": "investigator.md",
    "requirements_engineer": "requirements_engineer.md",
}

# Legacy filename aliases for backward compatibility
# Projects installed before the tech_lead rename may have the old filename
LEGACY_AGENT_ALIASES = {
    "tech_lead": "techlead.md",  # Pre-rename: techlead.md → tech_lead.md
}

# Agent directories to search (in order of preference)
# - .claude/agents/ is used in installed mode (client projects after `bazinga install`)
# - agents/ is used in dev mode (running from bazinga repo)
AGENT_DIRECTORIES = [
    ".claude/agents",
    "agents",
]

# Specialization templates base directory
SPECIALIZATIONS_BASE = PROJECT_ROOT / "bazinga" / "templates" / "specializations"

# Minimum lines expected in each agent file (sanity check)
# Note: project_manager is a kernel file (~350 lines) that references templates
MIN_AGENT_LINES = {
    "developer": 1000,
    "senior_software_engineer": 1200,
    "qa_expert": 800,
    "tech_lead": 600,
    "project_manager": 300,  # Kernel file - details in bazinga/templates/pm_*.md
    "investigator": 400,
    "requirements_engineer": 500,
}

# Token budgets per model
TOKEN_BUDGETS = {
    "haiku": {"soft": 900, "hard": 1350},
    "sonnet": {"soft": 1800, "hard": 2700},
    "opus": {"soft": 2400, "hard": 3600},
}

# Context budget allocation by agent type
# Increased developer from 0.20 to 0.35 (haiku 900 * 0.35 = 315 tokens for context)
CONTEXT_ALLOCATION = {
    "developer": 0.35,
    "senior_software_engineer": 0.30,
    "qa_expert": 0.30,
    "tech_lead": 0.40,
    "investigator": 0.35,
    "project_manager": 0.10,
    "requirements_engineer": 0.30,
}

# =============================================================================
# FILE READ LIMIT ENFORCEMENT (Claude's 25000 token limit)
# See: research/automated-token-budget-implementation.md
# =============================================================================

# File read limit - configurable via environment variable
FILE_READ_LIMIT = int(os.environ.get('BAZINGA_PROMPT_FILE_LIMIT', 25000))

# Per-agent safety margins
# PM has reduced margin because its agent file is already close to the limit
AGENT_SAFETY_MARGINS = {
    'project_manager': 0.03,  # 3% margin for PM (agent file already ~24k tokens)
    'default': 0.08           # 8% margin for other agents
}


def get_effective_budget(agent_type: str) -> int:
    """Get effective token budget for agent type (with safety margin)."""
    margin = AGENT_SAFETY_MARGINS.get(agent_type, AGENT_SAFETY_MARGINS['default'])
    return int(FILE_READ_LIMIT * (1 - margin))


def estimate_tokens(text):
    """Estimate tokens matching Claude's actual tokenizer.

    Calibrated against actual Claude file read tokenizer:
    - Uses 3.85 chars/token (derived from actual Claude counts)
    - 2% safety margin to catch edge cases without over-counting

    This matches Claude's actual behavior within ~3% accuracy.
    """
    # Handle None/empty
    if not text:
        return 0

    # Handle non-string input (defensive)
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return 0

    # Very short strings - use simpler estimate
    if len(text) < 10:
        return max(1, len(text) // 4)

    # Standard estimation: 3.85 chars/token with 2% safety margin
    # Calibrated against actual Claude file read token count
    base_estimate = len(text) / 3.85
    return int(base_estimate * 1.02)


def balance_code_fences(text: str) -> str:
    """Balance code fences to ensure even number of ``` markers.

    Handles edge case where truncation leaves an unclosed fence.
    """
    if not text:
        return text

    # Track fence state properly (not just count)
    in_fence = False
    i = 0
    while i < len(text) - 2:
        if text[i:i+3] == '```':
            in_fence = not in_fence
            i += 3
        else:
            i += 1

    # If we ended inside a fence, close it
    if in_fence:
        text = text.rstrip() + "\n```"

    return text


def truncate_safely(text: str, target_tokens: int) -> str:
    """Truncate text at safe boundaries with code fence balancing.

    Safe boundaries (in order of preference):
    1. Paragraph break (\\n\\n)
    2. Sentence end (. or ? or !)
    3. Line break (\\n)
    4. Character limit (fallback)
    """
    if not text:
        return ""

    current_tokens = estimate_tokens(text)
    if current_tokens <= target_tokens:
        return text

    # Calculate target character count (reverse the estimation formula)
    target_chars = int(target_tokens * 3.5 / 1.10)

    if target_chars <= 0:
        return "[Content removed due to token budget]"

    if target_chars >= len(text):
        return text

    truncated = text[:target_chars]

    # Strategy 1: Find paragraph break
    para_break = truncated.rfind('\n\n')
    if para_break > target_chars * 0.70:
        truncated = truncated[:para_break]
    else:
        # Strategy 2: Find sentence end
        sentence_ends = [
            truncated.rfind('. '),
            truncated.rfind('.\n'),
            truncated.rfind('? '),
            truncated.rfind('! '),
        ]
        best_sentence = max((p for p in sentence_ends if p > target_chars * 0.80), default=-1)

        if best_sentence > 0:
            truncated = truncated[:best_sentence + 1]
        else:
            # Strategy 3: Find any line break
            line_break = truncated.rfind('\n')
            if line_break > target_chars * 0.85:
                truncated = truncated[:line_break]
            # Strategy 4: Just cut at target (fallback)

    # Always balance fences
    truncated = balance_code_fences(truncated)

    # Add marker
    if not truncated.endswith('\n'):
        truncated += '\n'
    truncated += "\n[... content trimmed due to token budget ...]"

    return truncated


def find_example_sections(text: str) -> list:
    """Find sections explicitly titled as examples.

    Only matches sections with "Example" in the header to avoid
    removing important code blocks that aren't examples.

    Returns:
        List of (start_pos, end_pos, section_content) tuples
    """
    if not text or len(text) < 50:
        return []

    try:
        # Match markdown headers containing "Example" or "Usage"
        # Pattern: ## Examples, ### Usage Examples, etc.
        pattern = r'(#+\s*(?:Examples?|Usage Examples?|Reference Examples?|Code Examples?)\s*\n)([\s\S]*?)(?=\n#+\s|\Z)'

        sections = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = match.start()
            end = match.end()
            content = match.group(0)
            sections.append((start, end, content))

        return sections

    except re.error:
        return []
    except Exception:
        return []


def remove_example_sections(text: str, tokens_to_remove: int) -> tuple:
    """Remove example sections to free up tokens.

    Only removes sections explicitly titled as examples.

    Args:
        text: Text containing example sections
        tokens_to_remove: Target number of tokens to free

    Returns:
        (modified_text, tokens_actually_removed)
    """
    sections = find_example_sections(text)
    if not sections:
        return text, 0

    # Sort by position (remove from end first - least disruptive)
    sections.sort(key=lambda x: x[0], reverse=True)

    removed_tokens = 0
    result = text

    for start, end, content in sections:
        section_tokens = estimate_tokens(content)

        # Create minimal placeholder
        placeholder = "\n## Examples\n[Examples removed - see documentation]\n\n"

        # Replace section
        result = result[:start] + placeholder + result[end:]
        removed_tokens += section_tokens - estimate_tokens(placeholder)

        if removed_tokens >= tokens_to_remove:
            break

    return result, removed_tokens


def extract_specialization_identity(spec: str) -> tuple:
    """Extract identity portion from specialization.

    The "identity" is the core role description (e.g., "You are a Python Developer").
    This should be preserved even when trimming other content.

    Returns:
        (identity_text, remaining_text)
    """
    if not spec:
        return "", ""

    # Strategy 1: Look for first ## header after initial content
    first_section = spec.find('\n## ', 200)  # Skip first 200 chars
    if first_section > 0 and first_section < 2000:
        return spec[:first_section], spec[first_section:]

    # Strategy 2: Look for "Advisory" section end (common in our templates)
    advisory_end = spec.find('\n---\n', 100)
    if advisory_end > 0 and advisory_end < 1500:
        return spec[:advisory_end + 5], spec[advisory_end + 5:]

    # Strategy 3: Just take first 1800 chars
    if len(spec) > 1800:
        # Find safe break point
        break_point = spec.rfind('\n', 1600, 1900)
        if break_point > 1600:
            return spec[:break_point], spec[break_point:]
        return spec[:1800], spec[1800:]

    # Entire spec is small - keep all as identity
    return spec, ""


def enforce_file_read_budget(
    agent_definition: str,
    task_requirements: str,
    agent_type: str,
    project_context: str = "",
    specialization: str = "",
    feedback_context: str = ""
) -> tuple:
    """Enforce FILE_READ_LIMIT by trimming low-priority content.

    Priority (NEVER trim first two):
    1. agent_definition - NEVER TRIM
    2. task_requirements - NEVER TRIM
    3. feedback_context - trim first (retry info)
    4. example sections in specialization - trim second
    5. project_context - trim third
    6. specialization patterns - trim fourth (preserve identity)

    Args:
        agent_definition: Full agent definition (NEVER trimmed)
        task_requirements: Task context (NEVER trimmed)
        agent_type: Agent type for budget calculation
        project_context: Context from prior work (trimmable)
        specialization: Specialization block (trimmable, preserve identity)
        feedback_context: QA/TL feedback for retries (trimmable)

    Returns:
        (components_dict, trim_report)
    """
    # Coerce all inputs to strings
    agent_definition = str(agent_definition or "")
    task_requirements = str(task_requirements or "")
    project_context = str(project_context or "")
    specialization = str(specialization or "")
    feedback_context = str(feedback_context or "")

    components = {
        'agent_definition': agent_definition,
        'task_requirements': task_requirements,
        'project_context': project_context,
        'specialization': specialization,
        'feedback_context': feedback_context,
    }

    effective_budget = get_effective_budget(agent_type)

    trim_report = {
        'original_total': sum(estimate_tokens(c) for c in components.values()),
        'budget': effective_budget,
        'file_read_limit': FILE_READ_LIMIT,
        'actions': [],
    }

    total = trim_report['original_total']

    # Check if we fit
    if total <= effective_budget:
        trim_report['action'] = 'none_needed'
        trim_report['final_total'] = total
        return components, trim_report

    overage = total - effective_budget

    # Step 1: Remove feedback context entirely
    if components['feedback_context'] and overage > 0:
        freed = estimate_tokens(components['feedback_context'])
        components['feedback_context'] = ""
        overage -= freed
        trim_report['actions'].append(f"Removed feedback_context ({freed} tokens)")

    if overage <= 0:
        trim_report['action'] = 'trimmed'
        trim_report['final_total'] = sum(estimate_tokens(c) for c in components.values())
        return components, trim_report

    # Step 2: Remove example sections from specialization
    if components['specialization'] and overage > 0:
        new_spec, freed = remove_example_sections(components['specialization'], overage)
        if freed > 0:
            components['specialization'] = new_spec
            overage -= freed
            trim_report['actions'].append(f"Removed example sections ({freed} tokens)")

    if overage <= 0:
        trim_report['action'] = 'trimmed'
        trim_report['final_total'] = sum(estimate_tokens(c) for c in components.values())
        return components, trim_report

    # Step 3: Truncate project context (keep minimum 500 tokens)
    if components['project_context'] and overage > 0:
        current_ctx_tokens = estimate_tokens(components['project_context'])
        min_ctx = 500
        available_to_trim = max(0, current_ctx_tokens - min_ctx)

        if available_to_trim > 0:
            trim_amount = min(overage, available_to_trim)
            target_ctx_tokens = current_ctx_tokens - trim_amount

            components['project_context'] = truncate_safely(
                components['project_context'],
                target_ctx_tokens
            )
            actual_freed = current_ctx_tokens - estimate_tokens(components['project_context'])
            overage -= actual_freed
            trim_report['actions'].append(f"Truncated project_context ({actual_freed} tokens)")

    if overage <= 0:
        trim_report['action'] = 'trimmed'
        trim_report['final_total'] = sum(estimate_tokens(c) for c in components.values())
        return components, trim_report

    # Step 4: Truncate specialization (preserve identity header)
    if components['specialization'] and overage > 0:
        current_spec_tokens = estimate_tokens(components['specialization'])

        # Preserve identity (first ~500 tokens of specialization)
        identity, rest = extract_specialization_identity(components['specialization'])
        identity_tokens = estimate_tokens(identity)
        rest_tokens = estimate_tokens(rest)

        # Only truncate the non-identity part
        available_to_trim = rest_tokens
        if available_to_trim > 0:
            trim_amount = min(overage, available_to_trim)
            target_rest_tokens = rest_tokens - trim_amount

            if target_rest_tokens > 0:
                rest = truncate_safely(rest, target_rest_tokens)
            else:
                rest = ""  # Remove entirely, keep only identity

            components['specialization'] = identity + rest
            actual_freed = current_spec_tokens - estimate_tokens(components['specialization'])
            overage -= actual_freed
            trim_report['actions'].append(f"Truncated specialization (kept identity) ({actual_freed} tokens)")

    if overage <= 0:
        trim_report['action'] = 'trimmed'
        trim_report['final_total'] = sum(estimate_tokens(c) for c in components.values())
        return components, trim_report

    # Step 5: FAIL - cannot fit even after all trimming
    agent_tokens = estimate_tokens(components['agent_definition'])
    task_tokens = estimate_tokens(components['task_requirements'])

    trim_report['action'] = 'FAILED'
    trim_report['error'] = (
        f"Cannot fit prompt in budget. "
        f"Agent definition ({agent_tokens}) + Task requirements ({task_tokens}) = "
        f"{agent_tokens + task_tokens} tokens. Budget is {effective_budget}. "
        f"Remaining overage: {overage} tokens."
    )
    trim_report['final_total'] = sum(estimate_tokens(c) for c in components.values())

    return components, trim_report


def get_required_markers(conn, agent_type):
    """Read required markers from database."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT required_markers FROM agent_markers WHERE agent_type = ?",
            (agent_type,)
        )
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return []
        return []
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (agent_markers): {e}", file=sys.stderr)
        return []


def validate_markers(prompt, markers, agent_type):
    """Ensure all required markers are present in prompt.

    Returns:
        True if all markers present, False if missing (caller should handle exit)
    """
    missing = [m for m in markers if m not in prompt]
    if missing:
        print(f"ERROR: Prompt for {agent_type} missing required markers: {missing}", file=sys.stderr)
        print(f"This means the agent file may be corrupted or incomplete.", file=sys.stderr)
        return False
    return True


def read_agent_file(agent_type):
    """Read the agent definition file.

    Searches for agent files in multiple directories to support both:
    - Dev mode: agents/ at repo root (bazinga repo)
    - Installed mode: .claude/agents/ (client projects after `bazinga install`)

    Also checks legacy filename aliases for backward compatibility with
    projects installed before file renames.
    """
    file_name = AGENT_FILE_NAMES.get(agent_type)
    if not file_name:
        print(f"ERROR: Unknown agent type: {agent_type}", file=sys.stderr)
        print(f"Valid types: {list(AGENT_FILE_NAMES.keys())}", file=sys.stderr)
        sys.exit(1)

    # Build list of filenames to try (primary + legacy alias if exists)
    filenames_to_try = [file_name]
    legacy_name = LEGACY_AGENT_ALIASES.get(agent_type)
    if legacy_name:
        filenames_to_try.append(legacy_name)

    # Search for agent file in all configured directories
    searched_paths = []
    for agent_dir in AGENT_DIRECTORIES:
        for fname in filenames_to_try:
            path = PROJECT_ROOT / agent_dir / fname
            searched_paths.append(str(path))
            if path.exists():
                # Warn if using legacy filename
                if fname != file_name:
                    print(f"WARNING: Using legacy filename '{fname}' for {agent_type}. "
                          f"Consider renaming to '{file_name}'.", file=sys.stderr)

                content = path.read_text(encoding="utf-8")
                lines = len(content.splitlines())

                min_lines = MIN_AGENT_LINES.get(agent_type, 400)
                if lines < min_lines:
                    print(f"WARNING: Agent file {path} has only {lines} lines (expected {min_lines}+)", file=sys.stderr)

                return content

    # Not found in any directory
    print(f"ERROR: Agent file not found for type '{agent_type}'", file=sys.stderr)
    print(f"Project root: {PROJECT_ROOT}", file=sys.stderr)
    print(f"Searched paths:", file=sys.stderr)
    for p in searched_paths:
        print(f"  - {p}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# SPECIALIZATION BUILDING (Replaces specialization-loader skill)
# =============================================================================

def get_task_group_specializations(conn, session_id, group_id):
    """Get specialization paths from task_groups table."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT specializations FROM task_groups WHERE session_id = ? AND id = ?",
            (session_id, group_id)
        )
        row = cursor.fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return []
        return []
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (task_groups): {e}", file=sys.stderr)
        return []


def get_task_group_component_path(conn, session_id, group_id):
    """Get component_path from task_groups table.

    The component_path identifies which monorepo component this task group
    belongs to (e.g., 'frontend/', 'backend/'). This is used to look up
    version-specific context from project_context.json.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT component_path FROM task_groups WHERE session_id = ? AND id = ?",
            (session_id, group_id)
        )
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return None
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (task_groups.component_path): {e}", file=sys.stderr)
        return None


def get_project_context():
    """Read project_context.json for version guards."""
    context_path = PROJECT_ROOT / "bazinga" / "project_context.json"
    try:
        with open(context_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def get_component_version_context(project_context, component_path):
    """Get version context for a specific component using longest-prefix matching.

    For monorepos, different components may use different language versions.
    This function finds the matching component in project_context.json and
    returns its version information.

    Args:
        project_context: Parsed project_context.json
        component_path: Path like 'frontend/' or 'backend/api/'

    Returns:
        Dict with version fields, or empty dict if no match
    """
    # Safety check for None project_context
    if not project_context:
        return {}

    if not component_path:
        # Fallback to global versions if no component specified
        return {
            'primary_language': project_context.get('primary_language'),
            'primary_language_version': project_context.get('primary_language_version'),
        }

    components = project_context.get('components', [])
    if not components:
        return {
            'primary_language': project_context.get('primary_language'),
            'primary_language_version': project_context.get('primary_language_version'),
        }

    # Normalize component_path for matching (ensure trailing slash consistency)
    normalized_path = component_path.rstrip('/') + '/' if component_path != './' else './'

    # Longest prefix match - prefer 'backend/api/' over 'backend/'
    best_match = None
    best_match_len = 0

    for comp in components:
        comp_path = comp.get('path', '')
        # Normalize stored path
        comp_normalized = comp_path.rstrip('/') + '/' if comp_path and comp_path != './' else comp_path

        # Check if component_path starts with this component's path
        if normalized_path.startswith(comp_normalized) or comp_normalized == './':
            path_len = len(comp_normalized)
            if path_len > best_match_len:
                best_match = comp
                best_match_len = path_len

    if best_match:
        # Build context with all version-related fields from the component
        # This ensures multiple specializations (python, fastapi, postgresql) all get their versions
        context = {
            'primary_language': best_match.get('language'),
            'primary_language_version': best_match.get('language_version'),
            'framework': best_match.get('framework'),
            'framework_version': best_match.get('framework_version'),
            'database': best_match.get('database'),
        }

        # Dynamically extract ALL *_version fields from the component
        # This handles: node_version, database_version, pytest_version, playwright_version, etc.
        for key, value in best_match.items():
            if key.endswith('_version') and value is not None:
                context[key] = value

        # Also extract testing list for reference
        if best_match.get('testing'):
            context['testing'] = best_match.get('testing')

        return context

    # No match - return global versions
    return {
        'primary_language': project_context.get('primary_language'),
        'primary_language_version': project_context.get('primary_language_version'),
    }


def infer_component_from_specializations(spec_paths, project_context):
    """Infer component_path from specialization paths when PM didn't set it.

    If a specialization path includes a component-specific prefix (e.g.,
    'bazinga/templates/specializations/01-languages/python.md'), we can try
    to match it to a component in project_context.json based on language or framework.

    This is a fallback when component_path is not explicitly set.

    Args:
        spec_paths: List of specialization template paths
        project_context: Parsed project_context.json

    Returns:
        Inferred component_path or None
    """
    if not spec_paths or not project_context:
        return None

    components = project_context.get('components', [])
    if not components:
        return None

    for spec_path in spec_paths:
        path_lower = spec_path.lower()
        filename = spec_path.split('/')[-1].replace('.md', '').lower()

        # 1. Check language templates (e.g., '01-languages/python.md')
        if '01-languages/' in path_lower:
            for comp in components:
                if comp.get('language', '').lower() == filename:
                    return comp.get('path')

        # 2. Check frontend framework templates (e.g., '02-frameworks-frontend/react.md')
        if '02-frameworks-frontend/' in path_lower:
            for comp in components:
                if comp.get('framework', '').lower() == filename:
                    return comp.get('path')

        # 3. Check backend framework templates (e.g., '03-frameworks-backend/fastapi.md')
        if '03-frameworks-backend/' in path_lower:
            for comp in components:
                if comp.get('framework', '').lower() == filename:
                    return comp.get('path')

    # No inference possible
    return None


def validate_template_path(template_path):
    """Validate that template path is safe (no path traversal)."""
    allowed_base = SPECIALIZATIONS_BASE.resolve()

    # Reject absolute paths
    if Path(template_path).is_absolute():
        print(f"WARNING: Rejecting absolute template path: {template_path}", file=sys.stderr)
        return None

    # Reject paths with parent traversal
    if ".." in str(template_path):
        print(f"WARNING: Rejecting path with traversal: {template_path}", file=sys.stderr)
        return None

    # Resolve relative to project root and check it's under allowed base
    resolved = (PROJECT_ROOT / template_path).resolve()
    try:
        resolved.relative_to(allowed_base)
        return resolved
    except ValueError:
        print(f"WARNING: Template path outside allowed directory: {template_path}", file=sys.stderr)
        return None


def strip_yaml_frontmatter(content):
    """Strip YAML frontmatter from template content.

    Frontmatter is metadata between --- markers at the start of a file.
    It's used by the template system but shouldn't appear in agent prompts.
    """
    lines = content.split('\n')

    # Check if content starts with frontmatter
    if not lines or lines[0].strip() != '---':
        return content

    # Find the closing ---
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            # Return content after frontmatter, stripping leading whitespace
            remaining = '\n'.join(lines[i+1:]).lstrip()
            return remaining

    # No closing --- found, return original
    return content


def parse_version(version_str):
    """Parse version string into comparable tuple.

    Handles formats: "3.10", "3.10.1", "1.8", "8" (Java 8 = 1.8)
    """
    if not version_str:
        return None

    # Normalize Java versions: "8" -> "1.8", but "11" stays "11"
    version_str = str(version_str).strip()

    try:
        parts = version_str.split('.')
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        return None


def version_matches(detected_version, operator, required_version):
    """Check if detected version matches the requirement.

    Args:
        detected_version: Tuple like (3, 10) or (3, 10, 1)
        operator: One of '>=', '>', '<=', '<', '=='
        required_version: Tuple like (3, 10)

    Returns:
        True if condition is met, False otherwise
    """
    if detected_version is None or required_version is None:
        return False

    # Pad shorter version with zeros for comparison
    max_len = max(len(detected_version), len(required_version))
    d = detected_version + (0,) * (max_len - len(detected_version))
    r = required_version + (0,) * (max_len - len(required_version))

    if operator == '>=':
        return d >= r
    elif operator == '>':
        return d > r
    elif operator == '<=':
        return d <= r
    elif operator == '<':
        return d < r
    elif operator == '==':
        return d == r
    else:
        return False


# Guard token normalization - map common aliases to canonical names
# This ensures "py >= 3.10" matches against primary_language="python"
# Covers all 93 unique version guard tokens from 72 specialization templates
GUARD_TOKEN_ALIASES = {
    # Languages
    'py': 'python',
    'python3': 'python',
    'ts': 'typescript',
    'js': 'javascript',
    'rb': 'ruby',
    'rs': 'rust',
    'golang': 'go',
    'jdk': 'java',
    'openjdk': 'java',
    'kt': 'kotlin',
    'cs': 'csharp',
    'dotnet': 'csharp',
    '.net': 'csharp',
    'c++': 'cpp',
    'cplusplus': 'cpp',
    'sh': 'bash',
    'shell': 'bash',
    'zsh': 'bash',
    # Databases
    'postgres': 'postgresql',
    'pg': 'postgresql',
    'mongo': 'mongodb',
    'mssql': 'sqlserver',
    'es': 'elasticsearch',
    # Frontend frameworks
    'next': 'nextjs',
    'next.js': 'nextjs',
    'react.js': 'react',
    'reactjs': 'react',
    'vue.js': 'vue',
    'vuejs': 'vue',
    'angular.js': 'angular',
    'angularjs': 'angular',
    'sveltejs': 'svelte',
    'tailwindcss': 'tailwind',
    'astro.js': 'astro',
    # Backend frameworks
    'spring': 'spring-boot',
    'springboot': 'spring-boot',
    'nest': 'nestjs',
    'nest.js': 'nestjs',
    'expressjs': 'express',
    'express.js': 'express',
    'rubyonrails': 'rails',
    'ror': 'rails',
    'gin-gonic': 'gin',
    'gofiber': 'fiber',
    # Mobile
    'rn': 'react-native',
    'reactnative': 'react-native',
    # Testing
    'pw': 'playwright',
    'cy': 'cypress',
    'tc': 'testcontainers',
    # Infrastructure
    'tf': 'terraform',
    'k8s': 'kubernetes',
    'otel': 'opentelemetry',
    'gha': 'github-actions',
    'gh-actions': 'github-actions',
    # Data/AI
    'spark': 'pyspark',
    'scikit-learn': 'sklearn',
    'scikit': 'sklearn',
    'lc': 'langchain',
}


def evaluate_version_guard(guard_text, project_context):
    """Evaluate a version guard against project context.

    Args:
        guard_text: e.g., "python >= 3.10" or "python >= 3.7, python < 3.10"
        project_context: Dict with version info

    Returns:
        True if all conditions are met (or no version detected = include all)
        False if any condition fails
    """
    if not project_context:
        return True  # No context = include everything

    # Parse conditions (comma-separated for AND)
    conditions = [c.strip() for c in guard_text.split(',')]

    for condition in conditions:
        # Parse: "python >= 3.10" or "jest >= 27"
        match = re.match(r'(\w+)\s*(>=|>|<=|<|==)\s*([\d.]+)', condition)
        if not match:
            continue  # Skip unparseable conditions

        lang, operator, version_str = match.groups()
        required_version = parse_version(version_str)

        # Normalize guard token (e.g., "py" -> "python", "ts" -> "typescript")
        lang_lower = GUARD_TOKEN_ALIASES.get(lang.lower(), lang.lower())

        # Get detected version from project_context
        detected_version = None

        # 1. Check primary language
        if project_context.get('primary_language', '').lower() == lang_lower:
            detected_version = parse_version(project_context.get('primary_language_version'))

        # 2. Check framework (e.g., "fastapi >= 0.100", "react >= 18")
        if detected_version is None:
            if project_context.get('framework', '').lower() == lang_lower:
                detected_version = parse_version(project_context.get('framework_version'))

        # 3. Check language/tool-specific version fields
        # These handle cases where versions are stored at top-level rather than in primary_language
        # Covers all 93 unique version guard tokens from 72 specialization templates
        if detected_version is None:
            lang_version_map = {
                # Languages
                'node': 'node_version',
                'java': 'java_version',
                'go': 'go_version',
                'php': 'php_version',
                'csharp': 'dotnet_version',
                'kotlin': 'kotlin_version',
                'scala': 'scala_version',
                'elixir': 'elixir_version',
                'swift': 'swift_version',
                'cpp': 'cpp_version',
                'bash': 'bash_version',
                'dart': 'dart_version',
                'ruby': 'ruby_version',
                'rust': 'rust_version',
                # Databases
                'postgresql': 'postgresql_version',
                'mysql': 'mysql_version',
                'mongodb': 'mongodb_version',
                'redis': 'redis_version',
                'elasticsearch': 'elasticsearch_version',
                'sqlserver': 'sqlserver_version',
                'oracle': 'oracle_version',
                # Frontend frameworks
                'react': 'react_version',
                'nextjs': 'nextjs_version',
                'vue': 'vue_version',
                'angular': 'angular_version',
                'svelte': 'svelte_version',
                'astro': 'astro_version',
                'htmx': 'htmx_version',
                'alpine': 'alpine_version',
                'tailwind': 'tailwind_version',
                # Backend frameworks
                'spring-boot': 'spring_boot_version',
                'django': 'django_version',
                'flask': 'flask_version',
                'fastapi': 'fastapi_version',
                'express': 'express_version',
                'nestjs': 'nestjs_version',
                'rails': 'rails_version',
                'laravel': 'laravel_version',
                'gin': 'gin_version',
                'fiber': 'fiber_version',
                'phoenix': 'phoenix_version',
                # Mobile
                'flutter': 'flutter_version',
                'react-native': 'react_native_version',
                'ios': 'ios_version',
                'tauri': 'tauri_version',
                'electron': 'electron_version',
                # Testing
                'playwright': 'playwright_version',
                'cypress': 'cypress_version',
                'selenium': 'selenium_version',
                'jest': 'jest_version',
                'vitest': 'vitest_version',
                'pytest': 'pytest_version',
                'testcontainers': 'testcontainers_version',
                # Infrastructure
                'terraform': 'terraform_version',
                'docker': 'docker_version',
                'kubernetes': 'kubernetes_version',
                'opentelemetry': 'opentelemetry_version',
                'prometheus': 'prometheus_version',
                'github-actions': 'github_actions_version',
                # Data/AI
                'pyspark': 'pyspark_version',
                'airflow': 'airflow_version',
                'langchain': 'langchain_version',
                'sklearn': 'sklearn_version',
                'pydantic': 'pydantic_version',
                'dbt': 'dbt_version',
                'mlflow': 'mlflow_version',
                # APIs
                'openapi': 'openapi_version',
                'grpc': 'grpc_version',
                'kafka': 'kafka_version',
                'graphql': 'graphql_version',
                'protobuf': 'protobuf_version',
                # Auth
                'oauth': 'oauth_version',
                'jwt': 'jwt_version',
                # Validation
                'zod': 'zod_version',
                'joi': 'joi_version',
                'prisma': 'prisma_version',
            }
            if lang_lower in lang_version_map:
                detected_version = parse_version(project_context.get(lang_version_map[lang_lower]))

        # 4. Check secondary languages
        if detected_version is None:
            for sec_lang in project_context.get('secondary_languages', []):
                if isinstance(sec_lang, dict) and sec_lang.get('name', '').lower() == lang_lower:
                    detected_version = parse_version(sec_lang.get('version'))
                    break
                elif isinstance(sec_lang, str) and sec_lang.lower() == lang_lower:
                    # No version info for this language
                    break

        # 5. Check infrastructure section (databases, test frameworks, CI/CD, etc.)
        if detected_version is None:
            infra = project_context.get('infrastructure', {})
            # Direct field lookup (e.g., infra.jest_version, infra.docker_version)
            version_key = f'{lang_lower}_version'.replace('-', '_')
            if version_key in infra:
                detected_version = parse_version(infra.get(version_key))
            # Also check without _version suffix (e.g., infra.docker = "24.0")
            elif lang_lower in infra:
                detected_version = parse_version(infra.get(lang_lower))

        # 6. Check testing section (for components with testing: ["jest", "playwright"])
        if detected_version is None:
            testing = project_context.get('testing', {})
            version_key = f'{lang_lower}_version'.replace('-', '_')
            if version_key in testing:
                detected_version = parse_version(testing.get(version_key))

        # 7. Check databases section
        if detected_version is None:
            databases = project_context.get('databases', {})
            version_key = f'{lang_lower}_version'.replace('-', '_')
            if version_key in databases:
                detected_version = parse_version(databases.get(version_key))
            elif lang_lower in databases:
                detected_version = parse_version(databases.get(lang_lower))

        # If we have a detected version, check the condition
        if detected_version is not None:
            if not version_matches(detected_version, operator, required_version):
                return False  # Condition failed
        # If no version detected for this language, include content (conservative)

    return True  # All conditions passed (or no version to check)


def apply_version_guards(content, project_context):
    """Apply version guards to filter content based on project versions.

    Format: <!-- version: python >= 3.10 -->
    Content after a guard is included/excluded based on version match.
    Guards apply until the next guard or section boundary (---).
    """
    # Pattern to match version guards (use .+? not [^>]+? to allow >= operators)
    guard_pattern = re.compile(r'<!--\s*version:\s*(.+?)\s*-->')

    lines = content.split('\n')
    result = []
    include_current = True  # Start by including content

    for line in lines:
        # Check for version guard
        match = guard_pattern.search(line)
        if match:
            guard_text = match.group(1)
            include_current = evaluate_version_guard(guard_text, project_context)
            # Don't include the guard comment itself in output
            continue

        # Section boundary resets to include
        if line.strip() == '---':
            include_current = True
            result.append(line)
            continue

        # Include line if current section passes version check
        if include_current:
            result.append(line)

    return '\n'.join(result)


def read_template_with_version_guards(template_path, project_context):
    """Read template file, strip frontmatter, and apply version guards."""
    # Validate path for security
    validated_path = validate_template_path(template_path)
    if validated_path is None:
        return ""

    if not validated_path.exists():
        return ""

    try:
        content = validated_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IOError) as e:
        print(f"WARNING: Failed to read template {template_path}: {e}", file=sys.stderr)
        return ""

    # 1. Strip YAML frontmatter (metadata for template system, not for agents)
    content = strip_yaml_frontmatter(content)

    # 2. Apply version guards (filter content based on detected versions)
    content = apply_version_guards(content, project_context)

    return content


def build_specialization_block(conn, session_id, group_id, agent_type, model="sonnet"):
    """Build the specialization block from templates.

    Note: No per-model budget limits here. The global trim_to_budget() handles
    trimming if the overall prompt exceeds limits. This ensures specialization
    templates are always included and trimmed intelligently at the prompt level.

    For monorepos, uses component_path to look up version-specific context,
    enabling version guards like <!-- version: python >= 3.10 --> to filter
    content based on the component's actual language version.
    """
    spec_paths = get_task_group_specializations(conn, session_id, group_id)

    if not spec_paths:
        return ""  # No specializations for this task

    project_context = get_project_context()

    # Get component_path for version context lookup
    component_path = get_task_group_component_path(conn, session_id, group_id)

    # Fallback: infer component from specialization paths if PM didn't set it
    if not component_path:
        component_path = infer_component_from_specializations(spec_paths, project_context)

    # Get component-specific version context (uses longest-prefix matching)
    # This enables different language versions for frontend/ vs backend/ in monorepos
    version_context = get_component_version_context(project_context, component_path)

    # Merge version context into project_context for version guard evaluation
    # Component-specific versions override global versions
    effective_context = dict(project_context)
    if version_context:
        for key, value in version_context.items():
            if value is not None:
                effective_context[key] = value

    # Collect ALL template content - global budget trimming handles limits
    templates_content = []

    for path in spec_paths:
        content = read_template_with_version_guards(path, effective_context)
        if content:
            templates_content.append(content)

    if not templates_content:
        return ""

    # Compose the block
    block = """## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates (tests must pass)
> - Routing and status requirements (READY_FOR_QA, etc.)
> - Pre-commit quality checks (lint, build)
> - Core agent workflow rules

"""
    block += "\n\n".join(templates_content)

    return block


# =============================================================================
# CONTEXT BUILDING (Replaces context-assembler skill)
# =============================================================================

def get_context_packages(conn, session_id, group_id, agent_type, limit=5):
    """Get context packages from database."""
    try:
        cursor = conn.cursor()

        # Query with priority ordering
        query = """
            SELECT id, file_path, priority, summary, group_id, created_at
            FROM context_packages
            WHERE session_id = ?
            AND (group_id = ? OR group_id IS NULL OR group_id = '')
            ORDER BY
                CASE priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                created_at DESC
            LIMIT ?
        """
        cursor.execute(query, (session_id, group_id, limit))
        return cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (context_packages): {e}", file=sys.stderr)
        return []


def get_error_patterns(conn, limit=3):
    """Get relevant error patterns.

    Note: Currently fetches global patterns. Per-session filtering can be added
    if error_patterns table gains session_id column.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT signature_json, solution, confidence, occurrences
            FROM error_patterns
            WHERE confidence > 0.7
            ORDER BY confidence DESC, occurrences DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (error_patterns): {e}", file=sys.stderr)
        return []


def get_prior_reasoning(conn, session_id, group_id, agent_type):
    """Get prior agent reasoning for handoffs."""
    # Define which agents' reasoning is relevant for each target
    relevant_agents = {
        'qa_expert': ['developer', 'senior_software_engineer'],
        'tech_lead': ['developer', 'senior_software_engineer', 'qa_expert'],
        'senior_software_engineer': ['developer'],
        'investigator': ['developer', 'senior_software_engineer', 'qa_expert'],
        'developer': ['developer', 'qa_expert', 'tech_lead'],
    }

    agents_to_query = relevant_agents.get(agent_type, [])
    if not agents_to_query:
        return []

    try:
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(agents_to_query))
        cursor.execute(f"""
            SELECT agent_type, reasoning_phase, content, confidence_level, timestamp
            FROM orchestration_logs
            WHERE session_id = ?
            AND (group_id = ? OR group_id = 'global')
            AND agent_type IN ({placeholders})
            AND log_type = 'reasoning'
            ORDER BY timestamp DESC
            LIMIT 5
        """, (session_id, group_id, *agents_to_query))
        return cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"WARNING: DB query failed (orchestration_logs): {e}", file=sys.stderr)
        return []


def build_context_block(conn, session_id, group_id, agent_type, model="sonnet"):
    """Build the context block from database."""
    budget = TOKEN_BUDGETS.get(model, TOKEN_BUDGETS["sonnet"])
    allocation = CONTEXT_ALLOCATION.get(agent_type, 0.20)
    context_budget = int(budget["soft"] * allocation)

    sections = []
    used_tokens = 0

    # 1. Context packages
    packages = get_context_packages(conn, session_id, group_id, agent_type)
    if packages:
        pkg_section = "### Relevant Context\n\n"
        for pkg_id, file_path, priority, summary, pkg_group, created in packages:
            if summary:
                # Truncate long summaries
                truncated = summary[:200] + "..." if len(summary) > 200 else summary
                line = f"**[{priority.upper()}]** {file_path}\n> {truncated}\n\n"
                line_tokens = estimate_tokens(line)
                if used_tokens + line_tokens <= context_budget:
                    pkg_section += line
                    used_tokens += line_tokens
        if pkg_section != "### Relevant Context\n\n":
            sections.append(pkg_section)

    # 2. Prior reasoning (for handoffs)
    if agent_type in ['qa_expert', 'tech_lead', 'senior_software_engineer', 'investigator']:
        reasoning = get_prior_reasoning(conn, session_id, group_id, agent_type)
        if reasoning:
            reason_section = "### Prior Agent Reasoning\n\n"
            for r_agent, r_phase, r_content, r_conf, r_time in reasoning:
                content_truncated = r_content[:300] if r_content else ""
                line = f"**[{r_agent}] {r_phase}:** {content_truncated}\n\n"
                line_tokens = estimate_tokens(line)
                if used_tokens + line_tokens <= context_budget:
                    reason_section += line
                    used_tokens += line_tokens
            if reason_section != "### Prior Agent Reasoning\n\n":
                sections.append(reason_section)

    # 3. Error patterns (global, not per-session)
    errors = get_error_patterns(conn)
    if errors:
        err_section = "### Known Error Patterns\n\n"
        for sig_json, solution, confidence, occurrences in errors:
            sig_str = sig_json[:100] if sig_json else ""
            sol_str = solution[:200] if solution else ""
            line = f"**Known Issue**: {sig_str}\n> **Solution**: {sol_str}\n\n"
            line_tokens = estimate_tokens(line)
            if used_tokens + line_tokens <= context_budget:
                err_section += line
                used_tokens += line_tokens
        if err_section != "### Known Error Patterns\n\n":
            sections.append(err_section)

    if not sections:
        return ""

    return "## Context from Prior Work\n\n" + "\n".join(sections)


# =============================================================================
# TASK CONTEXT BUILDING
# =============================================================================

def build_task_context(args):
    """Build the task context section."""
    context = f"""
---

## Current Task Assignment

**SESSION:** {args.session_id}
**GROUP:** {args.group_id or 'N/A'}
**MODE:** {args.mode.capitalize()}
**BRANCH:** {args.branch}

**TASK:** {args.task_title or 'See requirements below'}

**REQUIREMENTS:**
{args.task_requirements or 'See original request'}

**TESTING MODE:** {args.testing_mode}
**COMMIT TO:** {args.branch}
"""

    # Add status guidance based on agent type
    if args.agent_type in ["developer", "senior_software_engineer"]:
        context += "\n**REPORT STATUS:** READY_FOR_QA (if integration tests) or READY_FOR_REVIEW (if unit tests only) or BLOCKED\n"
    elif args.agent_type == "qa_expert":
        context += "\n**REPORT STATUS:** PASS, FAIL, or BLOCKED\n"
    elif args.agent_type == "tech_lead":
        context += "\n**REPORT STATUS:** APPROVED or CHANGES_REQUESTED\n"
    elif args.agent_type == "project_manager":
        context += "\n**REPORT STATUS:** PLANNING_COMPLETE, CONTINUE, BAZINGA, or NEEDS_CLARIFICATION\n"

    return context


def build_feedback_context(args):
    """Build feedback context for retries."""
    feedback = ""

    if args.qa_feedback:
        feedback += f"""
## Previous QA Feedback (FIX THESE ISSUES)

{args.qa_feedback}
"""

    if args.tl_feedback:
        feedback += f"""
## Tech Lead Feedback (ADDRESS THESE CONCERNS)

{args.tl_feedback}
"""

    if args.investigation_findings:
        feedback += f"""
## Investigation Findings

{args.investigation_findings}
"""

    return feedback


def build_handoff_context(args):
    """Build handoff file path context for CRP (Compact Return Protocol).

    Injects the path where the prior agent wrote their detailed handoff file,
    allowing the next agent to read full context from the file instead of
    receiving it inline (which would bloat orchestrator context).

    Returns empty string if file doesn't exist or path is invalid.
    """
    if not args.prior_handoff_file:
        return ""

    # Security: Normalize path and validate it resolves under bazinga/artifacts/
    try:
        # Normalize to remove ../ traversal attempts
        normalized = os.path.normpath(args.prior_handoff_file)

        # Must still start with bazinga/artifacts/ after normalization
        if not normalized.startswith("bazinga/artifacts/"):
            print(f"⚠️ Warning: prior_handoff_file path escapes allowed directory: {args.prior_handoff_file}", file=sys.stderr)
            return ""

        # Additional check: ensure it matches expected pattern {session}/{group}/handoff_{agent}.json
        # or {session}/handoff_{agent}.json for PM (session-scoped)
        parts = normalized.split("/")
        if len(parts) < 3:
            print(f"⚠️ Warning: prior_handoff_file path too short: {args.prior_handoff_file}", file=sys.stderr)
            return ""

        # Check filename pattern
        filename = parts[-1]
        if not (filename.startswith("handoff_") and filename.endswith(".json")):
            print(f"⚠️ Warning: prior_handoff_file doesn't match handoff_*.json pattern: {args.prior_handoff_file}", file=sys.stderr)
            return ""

    except Exception as e:
        print(f"⚠️ Warning: Error validating prior_handoff_file path: {e}", file=sys.stderr)
        return ""

    # Check if the handoff file exists - if not, just log and return empty
    if not os.path.exists(normalized):
        print(f"⚠️ Warning: prior_handoff_file does not exist: {normalized}", file=sys.stderr)
        return ""

    return f"""
## PRIOR AGENT HANDOFF (READ THIS FILE)

**Handoff File:** `{normalized}`

⚠️ **MANDATORY:** Read this file FIRST to get full context from the prior agent.
The file contains detailed information that was NOT included in the orchestrator message to save context space.

```
Read: {normalized}
```
"""


def build_pm_context(args):
    """Build special context for PM spawns."""
    if args.pm_state:
        try:
            pm_state = json.loads(args.pm_state)
            return f"""
## PM STATE (from database)

```json
{json.dumps(pm_state, indent=2)}
```
"""
        except json.JSONDecodeError:
            return f"""
## PM STATE

{args.pm_state}
"""
    return ""


def build_resume_context(args):
    """Build resume context for PM resume spawns."""
    if args.resume_context:
        return f"""
## RESUME CONTEXT

{args.resume_context}

## SCOPE PRESERVATION (MANDATORY)

You are resuming an existing session. The original scope MUST be preserved.
Do NOT reduce scope without explicit user approval.
"""
    return ""


# =============================================================================
# GLOBAL BUDGET ENFORCEMENT
# =============================================================================

def enforce_global_budget(components, model="sonnet", agent_type="developer"):
    """Enforce global token budget by trimming lowest-priority sections.

    Uses the actual FILE_READ_LIMIT (default 25000 tokens) with safety margin,
    NOT the per-model specialization budgets which are much smaller.

    Priority order (highest to lowest):
    1. Agent definition (NEVER trim)
    2. Task context (NEVER trim)
    3. PM context (NEVER trim if PM)
    4. Handoff context (NEVER trim - critical for CRP)
    5. Context block (trim if needed)
    6. Specialization block (trim if needed)
    7. Feedback context (trim first)

    Returns:
        tuple: (trimmed_components, trimmed_sections_log)
    """
    # Use actual global budget, not per-model specialization limits
    hard_limit = get_effective_budget(agent_type)

    # Calculate total tokens
    total_tokens = sum(estimate_tokens(c) for c in components)

    if total_tokens <= hard_limit:
        return components, []

    # Need to trim - identify sections by content markers
    trimmed_log = []
    result = []

    # Categorize components by priority
    for i, comp in enumerate(components):
        # High priority - never trim
        if "Current Task Assignment" in comp:
            result.append(comp)
        elif "## RESUME CONTEXT" in comp or "## PM STATE" in comp:
            result.append(comp)
        # Handoff section - never trim (critical for CRP)
        elif "PRIOR AGENT HANDOFF" in comp:
            result.append(comp)
        # Agent definition - never trim (identified by size)
        elif estimate_tokens(comp) > 500 and "SPECIALIZATION GUIDANCE" not in comp and "Context from Prior Work" not in comp:
            result.append(comp)
        # Medium priority - trim if needed
        elif "Context from Prior Work" in comp:
            # Context block - can be trimmed
            if total_tokens > hard_limit:
                trimmed_log.append(f"Trimmed: Context block ({estimate_tokens(comp)} tokens)")
                total_tokens -= estimate_tokens(comp)
            else:
                result.append(comp)
        elif "SPECIALIZATION GUIDANCE" in comp:
            # Specialization block - can be trimmed
            if total_tokens > hard_limit:
                trimmed_log.append(f"Trimmed: Specialization block ({estimate_tokens(comp)} tokens)")
                total_tokens -= estimate_tokens(comp)
            else:
                result.append(comp)
        # Low priority - trim first
        elif "Previous QA Feedback" in comp or "Tech Lead Feedback" in comp or "Investigation Findings" in comp:
            # Feedback context - trim first
            if total_tokens > hard_limit:
                trimmed_log.append(f"Trimmed: Feedback context ({estimate_tokens(comp)} tokens)")
                total_tokens -= estimate_tokens(comp)
            else:
                result.append(comp)
        else:
            # Unknown section - keep by default
            result.append(comp)

    return result, trimmed_log


# =============================================================================
# MAIN PROMPT COMPOSITION
# =============================================================================

def build_prompt(args):
    """Build the complete agent prompt."""
    global PROJECT_ROOT, SPECIALIZATIONS_BASE

    # Allow project root override for testing
    if args.project_root:
        PROJECT_ROOT = Path(args.project_root)
        SPECIALIZATIONS_BASE = PROJECT_ROOT / "bazinga" / "templates" / "specializations"
        print(f"[INFO] Using override project root: {PROJECT_ROOT}", file=sys.stderr)

    # Check database exists - FAIL by default (deterministic orchestration requires DB)
    if not Path(args.db).exists():
        if args.allow_no_db:
            print(f"WARNING: Database not found at {args.db}, proceeding without DB data (--allow-no-db)", file=sys.stderr)
            conn = None
        else:
            print(f"ERROR: Database not found at {args.db}", file=sys.stderr)
            print(f"Deterministic orchestration requires database. Options:", file=sys.stderr)
            print(f"  1. Run config-seeder skill to initialize database", file=sys.stderr)
            print(f"  2. Use --allow-no-db to skip DB validation (NOT RECOMMENDED)", file=sys.stderr)
            sys.exit(1)
    else:
        conn = sqlite3.connect(args.db)

    # Use try/finally to ensure conn.close() is always called
    try:
        model = args.model or "sonnet"
        components = []
        markers_valid = True

        # 1. Build CONTEXT block (from DB - prior reasoning, packages, errors)
        if conn and args.agent_type != "project_manager":  # PM doesn't need prior context
            context_block = build_context_block(
                conn, args.session_id, args.group_id or "", args.agent_type, model
            )
            if context_block:
                components.append(context_block)

        # 2. Build SPECIALIZATION block (from DB task_groups + template files)
        if conn and args.group_id and args.agent_type not in ["project_manager"]:
            spec_block = build_specialization_block(
                conn, args.session_id, args.group_id, args.agent_type, model
            )
            if spec_block:
                components.append(spec_block)

        # 3. Read AGENT DEFINITION (MANDATORY - this is the core)
        agent_definition = read_agent_file(args.agent_type)
        components.append(agent_definition)

        # 4. Build TASK CONTEXT
        task_context = build_task_context(args)
        components.append(task_context)

        # 5. Build PM-specific context
        if args.agent_type == "project_manager":
            pm_context = build_pm_context(args)
            if pm_context:
                components.append(pm_context)
            resume_context = build_resume_context(args)
            if resume_context:
                components.append(resume_context)

        # 6. Build FEEDBACK context (for retries)
        feedback_context = build_feedback_context(args)
        if feedback_context:
            components.append(feedback_context)

        # 7. Build HANDOFF context (CRP - Compact Return Protocol)
        handoff_context = build_handoff_context(args)
        if handoff_context:
            components.append(handoff_context)

        # 8. Enforce global budget - trim lowest-priority sections if over hard limit
        components, trimmed_sections = enforce_global_budget(components, model, args.agent_type)
        if trimmed_sections:
            for trim_msg in trimmed_sections:
                print(f"WARNING: {trim_msg}", file=sys.stderr)

        # Compose final prompt
        full_prompt = "\n\n".join(components)

        # 9. ENFORCE FILE READ LIMIT (25000 tokens outer guard)
        # This is the final safety check before the prompt is delivered
        final_tokens = estimate_tokens(full_prompt)
        effective_budget = get_effective_budget(args.agent_type)

        if final_tokens > effective_budget:
            print(f"WARNING: Prompt exceeds effective budget ({final_tokens} > {effective_budget}), applying file read budget enforcement...", file=sys.stderr)

            # Extract components for targeted trimming
            # We need to identify which parts can be trimmed
            context_block_str = ""
            spec_block_str = ""
            feedback_str = ""

            for comp in components:
                if "Context from Prior Work" in comp:
                    context_block_str = comp
                elif "SPECIALIZATION GUIDANCE" in comp:
                    spec_block_str = comp
                elif "Previous QA Feedback" in comp or "Tech Lead Feedback" in comp or "Investigation Findings" in comp:
                    feedback_str = comp

            # Apply file read budget enforcement
            budget_components, trim_report = enforce_file_read_budget(
                agent_definition=agent_definition,
                task_requirements=task_context,
                agent_type=args.agent_type,
                project_context=context_block_str,
                specialization=spec_block_str,
                feedback_context=feedback_str
            )

            # Log trimming actions
            for action in trim_report.get('actions', []):
                print(f"WARNING: [FILE_READ_BUDGET] {action}", file=sys.stderr)

            # Check if enforcement failed
            if trim_report.get('action') == 'FAILED':
                error_msg = trim_report.get('error', 'Unknown budget enforcement failure')
                print(f"ERROR: {error_msg}", file=sys.stderr)
                if getattr(args, 'json_output', False):
                    print(json.dumps({
                        "success": False,
                        "error": error_msg,
                        "prompt_file": None,
                        "tokens_estimate": final_tokens,
                        "lines": 0,
                        "markers_ok": False,
                        "budget_exceeded": True,
                        "trim_report": trim_report
                    }, indent=2))
                sys.exit(1)

            # Rebuild prompt from trimmed components
            trimmed_components = []
            if budget_components['project_context']:
                trimmed_components.append(budget_components['project_context'])
            if budget_components['specialization']:
                trimmed_components.append(budget_components['specialization'])
            trimmed_components.append(budget_components['agent_definition'])
            trimmed_components.append(budget_components['task_requirements'])

            # Add PM-specific context back (if present and this is PM)
            if args.agent_type == "project_manager":
                pm_context = build_pm_context(args)
                if pm_context:
                    trimmed_components.append(pm_context)
                resume_context = build_resume_context(args)
                if resume_context:
                    trimmed_components.append(resume_context)

            if budget_components['feedback_context']:
                trimmed_components.append(budget_components['feedback_context'])

            full_prompt = "\n\n".join(trimmed_components)

            # Balance code fences on final prompt
            full_prompt = balance_code_fences(full_prompt)

            print(f"INFO: [FILE_READ_BUDGET] Trimmed from {final_tokens} to {trim_report.get('final_total', 'unknown')} tokens", file=sys.stderr)

        # Final validation: ensure we're under the hard limit
        final_tokens = estimate_tokens(full_prompt)
        if final_tokens > FILE_READ_LIMIT:
            print(f"ERROR: Final prompt ({final_tokens} tokens) still exceeds FILE_READ_LIMIT ({FILE_READ_LIMIT})", file=sys.stderr)
            if getattr(args, 'json_output', False):
                print(json.dumps({
                    "success": False,
                    "error": f"Prompt exceeds file read limit: {final_tokens} > {FILE_READ_LIMIT}",
                    "prompt_file": None,
                    "tokens_estimate": final_tokens,
                    "lines": 0,
                    "markers_ok": False,
                    "budget_exceeded": True
                }, indent=2))
            sys.exit(1)

        # 9. Validate required markers (only if DB available)
        if conn:
            markers = get_required_markers(conn, args.agent_type)
            if markers:
                markers_valid = validate_markers(full_prompt, markers, args.agent_type)

        # 10. Prepare metadata
        lines = len(full_prompt.splitlines())
        tokens = estimate_tokens(full_prompt)

        # 10. Output metadata to stderr FIRST
        print(f"[PROMPT_METADATA]", file=sys.stderr)
        print(f"agent_type={args.agent_type}", file=sys.stderr)
        print(f"project_root={PROJECT_ROOT}", file=sys.stderr)
        print(f"lines={lines}", file=sys.stderr)
        print(f"tokens_estimate={tokens}", file=sys.stderr)
        print(f"sections_trimmed={len(trimmed_sections)}", file=sys.stderr)
        if conn:
            print(f"markers_validated={str(markers_valid).lower()}", file=sys.stderr)

        # 11. Handle marker validation failure
        if not markers_valid:
            if getattr(args, 'json_output', False):
                error_result = {
                    "success": False,
                    "error": "Prompt validation failed - missing required markers",
                    "prompt_file": None,
                    "tokens_estimate": tokens,
                    "lines": lines,
                    "markers_ok": False,
                    "missing_markers": []  # Could be populated by validate_markers if we tracked them
                }
                print(json.dumps(error_result, indent=2))
            else:
                print("ERROR: Prompt validation failed - not emitting invalid prompt", file=sys.stderr)
            sys.exit(1)

        # 12. Save to file if --output-file specified
        output_path = None
        if args.output_file:
            output_path = os.path.join(PROJECT_ROOT, args.output_file)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(full_prompt)
            print(f"PROMPT_FILE={output_path}", file=sys.stderr)

        # 13. Output result
        if getattr(args, 'json_output', False):
            # JSON output for skill invocation
            result = {
                "success": True,
                "prompt_file": output_path,
                "tokens_estimate": tokens,
                "lines": lines,
                "markers_ok": markers_valid,
                "missing_markers": [],
                "error": None,
                "budget": {
                    "file_read_limit": FILE_READ_LIMIT,
                    "effective_budget": get_effective_budget(args.agent_type),
                    "used": tokens,
                    "remaining": FILE_READ_LIMIT - tokens
                }
            }
            print(json.dumps(result, indent=2))
        else:
            # Raw prompt output for backward compatibility
            print(full_prompt)

    finally:
        # Always close database connection
        if conn:
            conn.close()


def main():
    # Ensure we're in project root for relative path resolution
    _ensure_cwd_at_project_root()

    parser = argparse.ArgumentParser(
        description="Build deterministic agent prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 prompt_builder.py --agent-type developer --session-id "bazinga_123" \\
        --branch "main" --mode "simple" --testing-mode "full"

Debug mode:
    python3 prompt_builder.py --debug --agent-type developer ...
    (Prints received arguments to stderr for debugging)
"""
    )

    # Debug flag
    parser.add_argument("--debug", action="store_true",
                        help="Print debug info including received arguments")

    # Check if --params-file is present - if so, other args come from the file
    using_params_file = any(arg.startswith('--params-file') for arg in sys.argv)

    # Required arguments (not required if using --params-file)
    parser.add_argument("--agent-type", required=not using_params_file,
                        choices=list(AGENT_FILE_NAMES.keys()),
                        help="Type of agent to build prompt for")
    parser.add_argument("--session-id", required=not using_params_file,
                        help="Session identifier")
    parser.add_argument("--branch", required=not using_params_file,
                        help="Git branch name")
    parser.add_argument("--mode", required=not using_params_file,
                        choices=["simple", "parallel"],
                        help="Execution mode")
    parser.add_argument("--testing-mode", required=not using_params_file,
                        choices=["full", "minimal", "disabled"],
                        help="Testing mode")

    # Conditional arguments
    parser.add_argument("--group-id", default="",
                        help="Task group identifier")
    parser.add_argument("--task-title", default="",
                        help="Task title")
    parser.add_argument("--task-requirements", default="",
                        help="Task requirements")
    parser.add_argument("--model", default="sonnet",
                        choices=["haiku", "sonnet", "opus"],
                        help="Model for token budgeting")
    parser.add_argument("--db", default=DB_PATH,
                        help="Database path")
    parser.add_argument("--allow-no-db", action="store_true",
                        help="Allow building prompts without database (NOT RECOMMENDED)")
    parser.add_argument("--project-root", default=None,
                        help="Override detected project root (for testing)")

    # Feedback for retries
    parser.add_argument("--qa-feedback", default="",
                        help="QA failure details for developer retry")
    parser.add_argument("--tl-feedback", default="",
                        help="Tech Lead feedback for developer changes")
    parser.add_argument("--investigation-findings", default="",
                        help="Investigation findings")
    parser.add_argument("--prior-handoff-file", default="",
                        help="Path to prior agent's handoff JSON file (CRP)")

    # PM-specific
    parser.add_argument("--pm-state", default="",
                        help="PM state JSON from database")
    parser.add_argument("--resume-context", default="",
                        help="Resume context for PM resume spawns")

    # Output file option (for file-based prompt delivery)
    parser.add_argument("--output-file", default="",
                        help="Save prompt to file (in addition to stdout). Path relative to project root.")

    # JSON input/output for skill-based invocation
    parser.add_argument("--params-file", default="",
                        help="Read parameters from JSON file instead of CLI args")
    parser.add_argument("--json-output", action="store_true",
                        help="Output JSON result instead of raw prompt (for skill invocation)")

    # Sanitize sys.argv - remove empty or whitespace-only args that bash might pass
    # This handles issues with multiline commands using backslash continuations
    original_argv = sys.argv.copy()
    sanitized_argv = [arg for arg in sys.argv if arg.strip()]

    # Check if sanitization changed anything
    args_removed = len(original_argv) != len(sanitized_argv)

    # First, check for --debug early to help diagnose parsing issues
    if "--debug" in sanitized_argv:
        print(f"[DEBUG] Original sys.argv ({len(original_argv)} args):", file=sys.stderr)
        for i, arg in enumerate(original_argv):
            # Show repr() to reveal whitespace/invisible chars
            print(f"  [{i}] {repr(arg)}", file=sys.stderr)
        if args_removed:
            print(f"[DEBUG] Sanitized to ({len(sanitized_argv)} args):", file=sys.stderr)
            for i, arg in enumerate(sanitized_argv):
                print(f"  [{i}] {repr(arg)}", file=sys.stderr)
        print(f"[DEBUG] Project root: {PROJECT_ROOT}", file=sys.stderr)

    # Use sanitized argv for parsing
    if args_removed:
        print(f"[INFO] Removed {len(original_argv) - len(sanitized_argv)} empty/whitespace args from command line", file=sys.stderr)

    try:
        args = parser.parse_args(sanitized_argv[1:])  # Skip script name
    except SystemExit as e:
        # argparse calls sys.exit on error - intercept to add diagnostics
        if e.code != 0:
            print(f"\n[ERROR] Argument parsing failed. Raw sys.argv:", file=sys.stderr)
            for i, arg in enumerate(original_argv):
                print(f"  [{i}] {repr(arg)}", file=sys.stderr)
            if args_removed:
                print(f"\nSanitized argv:", file=sys.stderr)
                for i, arg in enumerate(sanitized_argv):
                    print(f"  [{i}] {repr(arg)}", file=sys.stderr)
        raise

    if args.debug:
        print(f"[DEBUG] Parsed args: {args}", file=sys.stderr)

    # Handle --params-file: read parameters from JSON file
    if args.params_file:
        params_path = os.path.join(PROJECT_ROOT, args.params_file)
        if not os.path.exists(params_path):
            error_result = {
                "success": False,
                "error": f"Params file not found: {params_path}",
                "prompt_file": None,
                "tokens_estimate": 0,
                "lines": 0,
                "markers_ok": False,
                "missing_markers": []
            }
            if args.json_output:
                print(json.dumps(error_result, indent=2))
            else:
                print(f"ERROR: Params file not found: {params_path}", file=sys.stderr)
            sys.exit(1)

        try:
            with open(params_path, 'r') as f:
                params = json.load(f)

            # Map JSON params to args object
            if 'agent_type' in params:
                args.agent_type = params['agent_type']
            if 'session_id' in params:
                args.session_id = params['session_id']
            if 'group_id' in params:
                args.group_id = params['group_id']
            if 'task_title' in params:
                args.task_title = params['task_title']
            if 'task_requirements' in params:
                args.task_requirements = params['task_requirements']
            if 'branch' in params:
                args.branch = params['branch']
            if 'mode' in params:
                args.mode = params['mode']
            if 'testing_mode' in params:
                args.testing_mode = params['testing_mode']
            if 'model' in params:
                args.model = params['model']
            if 'output_file' in params:
                args.output_file = params['output_file']
            if 'qa_feedback' in params:
                args.qa_feedback = params['qa_feedback']
            if 'tl_feedback' in params:
                args.tl_feedback = params['tl_feedback']
            if 'investigation_findings' in params:
                args.investigation_findings = params['investigation_findings']
            if 'pm_state' in params:
                args.pm_state = params['pm_state'] if isinstance(params['pm_state'], str) else json.dumps(params['pm_state'])
            if 'resume_context' in params:
                args.resume_context = params['resume_context']
            # Enable JSON output when using params file (skill invocation)
            args.json_output = True

            if args.debug:
                print(f"[DEBUG] Loaded params from {params_path}: {params}", file=sys.stderr)

            # Validate required fields after loading params
            required_fields = ['agent_type', 'session_id', 'branch', 'mode', 'testing_mode']
            missing = [f for f in required_fields if not getattr(args, f, None)]
            if missing:
                error_result = {
                    "success": False,
                    "error": f"Missing required fields in params file: {missing}",
                    "prompt_file": None,
                    "tokens_estimate": 0,
                    "lines": 0,
                    "markers_ok": False,
                    "missing_markers": []
                }
                print(json.dumps(error_result, indent=2))
                sys.exit(1)

        except json.JSONDecodeError as e:
            error_result = {
                "success": False,
                "error": f"Invalid JSON in params file: {e}",
                "prompt_file": None,
                "tokens_estimate": 0,
                "lines": 0,
                "markers_ok": False,
                "missing_markers": []
            }
            if args.json_output:
                print(json.dumps(error_result, indent=2))
            else:
                print(f"ERROR: Invalid JSON in params file: {e}", file=sys.stderr)
            sys.exit(1)

    build_prompt(args)


if __name__ == "__main__":
    main()
