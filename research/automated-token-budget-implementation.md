# Automated Token Budget Enforcement: Implementation Plan

**Date:** 2025-12-17
**Context:** PM prompt (25306 tokens) exceeded 25000 file read limit, blocking integration test
**Decision:** Implement automated token budgeting in prompt_builder.py (no LLM calls)
**Status:** Proposed
**Reviewed by:** Pending (OpenAI GPT-5, Google Gemini 3 Pro Preview)

---

## Problem Statement

The `prompt_builder.py` script generates prompts that can exceed Claude's 25000 token file read limit:
- **Observed:** PM prompt was 25306 tokens
- **Limit:** 25000 tokens (Claude file read limit)
- **Result:** Spawned agent cannot read its own prompt file

**Current code issues:**
1. `TOKEN_BUDGETS` are tiny (900-3600 tokens) - meant for specialization blocks, not total prompt
2. `estimate_tokens()` uses `len(text) // 4` (~4 chars/token) - but actual Claude ratio is closer to 3.5-3.7
3. `enforce_global_budget()` targets wrong limit (3600 vs 25000)
4. No distinction between trimmable content (examples) and critical content (identity)

---

## Current Code Analysis

### What exists (prompt_builder.py lines 100-122):
```python
TOKEN_BUDGETS = {
    "haiku": {"soft": 900, "hard": 1350},
    "sonnet": {"soft": 1800, "hard": 2700},
    "opus": {"soft": 2400, "hard": 3600},
}
# ^ These are for SPECIALIZATION blocks, not total prompt!

def estimate_tokens(text):
    """Rough token estimate (characters / 4)."""
    return len(text) // 4
# ^ Too conservative - actual is ~3.5-3.7 chars/token
```

### What's missing:
1. `FILE_READ_LIMIT = 25000` constant
2. Accurate token estimation with safety margin
3. Priority-based trimming for total prompt
4. Code example identification and removal
5. Safe truncation (preserve code fence balance)
6. Final size validation before returning

---

## Proposed Solution: Automated Budgeting

### Core Constants

```python
# File read limit (Claude's hard limit)
FILE_READ_LIMIT = 25000

# Effective budget with safety margin (5%)
EFFECTIVE_BUDGET = 23750  # 25000 * 0.95

# Component priorities (higher = trimmed first)
TRIM_PRIORITY = {
    'code_examples': 1,      # Trim first - verbose, low value
    'project_context': 2,    # Trim second - history details
    'specialization_patterns': 3,  # Trim third - patterns/guidance
    'specialization_identity': 4,  # Last resort - "You are a Python developer"
    # NEVER TRIM:
    # - agent_definition
    # - task_requirements
}
```

### Improved Token Estimation

```python
def estimate_tokens(text: str) -> int:
    """Estimate tokens with safety margin.

    Analysis shows Claude tokenizer produces ~3.5-3.7 chars/token for mixed content.
    We use 3.5 for conservative estimate, then add 10% safety margin.

    Returns:
        Estimated token count (may be slightly higher than actual)
    """
    if not text:
        return 0

    # Base estimate: 3.5 chars/token
    base_estimate = len(text) / 3.5

    # Add 10% safety margin
    return int(base_estimate * 1.10)
```

**Why this is realistic:**
- Current code uses 4.0 chars/token → underestimates by ~15%
- 3.5 chars/token is closer to observed Claude behavior
- 10% safety margin catches edge cases
- Still deterministic - no LLM calls needed

### Component Measurement

```python
def measure_prompt_components(components: dict) -> dict:
    """Measure token count for each prompt component.

    Args:
        components: Dict with keys like 'agent_definition', 'task_requirements', etc.

    Returns:
        Dict mapping component name to token count
    """
    return {
        name: estimate_tokens(content)
        for name, content in components.items()
        if content  # Skip empty components
    }
```

### Code Example Detection

```python
import re

def find_code_examples(text: str) -> list[tuple[int, int, str]]:
    """Find code blocks that are examples (vs required code).

    Returns:
        List of (start_pos, end_pos, block_content) tuples
    """
    # Match fenced code blocks
    pattern = r'```[\w]*\n([\s\S]*?)```'

    examples = []
    for match in re.finditer(pattern, text):
        block = match.group(0)
        # Heuristic: examples are usually >10 lines and contain comments like "# Example"
        lines = block.count('\n')
        is_example = (
            lines > 10 or
            '# Example' in block or
            '// Example' in block or
            '# Usage' in block or
            'example' in block.lower()[:50]
        )
        if is_example:
            examples.append((match.start(), match.end(), block))

    return examples


def remove_code_examples(text: str, tokens_to_remove: int) -> tuple[str, int]:
    """Remove code examples to free up tokens.

    Args:
        text: The text containing code examples
        tokens_to_remove: Target number of tokens to free

    Returns:
        (modified_text, tokens_actually_removed)
    """
    examples = find_code_examples(text)
    if not examples:
        return text, 0

    # Sort by size (largest first) for efficient removal
    examples.sort(key=lambda x: len(x[2]), reverse=True)

    removed_tokens = 0
    result = text

    for start, end, block in examples:
        block_tokens = estimate_tokens(block)

        # Create placeholder
        placeholder = "```\n[Code example removed - see documentation]\n```"

        # Find and replace (accounting for prior removals)
        result = result.replace(block, placeholder, 1)
        removed_tokens += block_tokens - estimate_tokens(placeholder)

        if removed_tokens >= tokens_to_remove:
            break

    return result, removed_tokens
```

### Safe Truncation

```python
def truncate_safely(text: str, target_tokens: int) -> str:
    """Truncate text at safe boundaries.

    Safe boundaries (in order of preference):
    1. Paragraph break (\\n\\n)
    2. Sentence end (. or ? or !)
    3. Code fence boundary (```)

    Also ensures code fences are balanced after truncation.
    """
    if estimate_tokens(text) <= target_tokens:
        return text

    # Calculate target character count
    target_chars = int(target_tokens * 3.5 / 1.10)  # Reverse the estimation

    if target_chars >= len(text):
        return text

    truncated = text[:target_chars]

    # Find best break point
    break_points = [
        truncated.rfind('\n\n'),      # Paragraph
        truncated.rfind('. '),         # Sentence
        truncated.rfind('.\n'),        # Sentence at line end
        truncated.rfind('```\n'),      # After code fence
    ]

    # Use the latest safe break point (at least 70% of content)
    min_pos = int(target_chars * 0.70)
    best_break = max((p for p in break_points if p > min_pos), default=-1)

    if best_break > 0:
        truncated = truncated[:best_break + 1]

    # Balance code fences
    truncated = balance_code_fences(truncated)

    # Add truncation marker
    truncated += "\n\n[... content trimmed due to token budget ...]"

    return truncated


def balance_code_fences(text: str) -> str:
    """Ensure code fences are balanced (even number of ```)."""
    fence_count = text.count('```')

    if fence_count % 2 == 1:
        # Odd number - we're inside an unclosed fence
        # Close it
        text += "\n```"

    return text
```

### Priority-Based Trimming Algorithm

```python
def enforce_file_read_budget(
    agent_definition: str,
    task_requirements: str,
    project_context: str,
    specialization: str,
    feedback_context: str = ""
) -> tuple[dict, dict]:
    """Enforce FILE_READ_LIMIT by trimming low-priority content.

    Priority (NEVER trim first two):
    1. agent_definition - NEVER TRIM
    2. task_requirements - NEVER TRIM
    3. feedback_context - trim first (retry info)
    4. code_examples in specialization - trim second
    5. project_context - trim third
    6. specialization patterns - trim fourth
    7. specialization identity - last resort (keep "You are a X")

    Returns:
        (components_dict, trim_report)
    """
    components = {
        'agent_definition': agent_definition,
        'task_requirements': task_requirements,
        'project_context': project_context,
        'specialization': specialization,
        'feedback_context': feedback_context,
    }

    trim_report = {
        'original_total': sum(estimate_tokens(c) for c in components.values()),
        'budget': EFFECTIVE_BUDGET,
        'actions': [],
    }

    total = trim_report['original_total']

    # Check if we fit
    if total <= EFFECTIVE_BUDGET:
        trim_report['action'] = 'none_needed'
        trim_report['final_total'] = total
        return components, trim_report

    overage = total - EFFECTIVE_BUDGET

    # Step 1: Remove feedback context entirely
    if components['feedback_context'] and overage > 0:
        freed = estimate_tokens(components['feedback_context'])
        components['feedback_context'] = ""
        overage -= freed
        trim_report['actions'].append(f"Removed feedback_context ({freed} tokens)")

    if overage <= 0:
        trim_report['final_total'] = EFFECTIVE_BUDGET - abs(overage)
        return components, trim_report

    # Step 2: Remove code examples from specialization
    if components['specialization'] and overage > 0:
        new_spec, freed = remove_code_examples(components['specialization'], overage)
        if freed > 0:
            components['specialization'] = new_spec
            overage -= freed
            trim_report['actions'].append(f"Removed code examples ({freed} tokens)")

    if overage <= 0:
        trim_report['final_total'] = EFFECTIVE_BUDGET - abs(overage)
        return components, trim_report

    # Step 3: Truncate project context
    if components['project_context'] and overage > 0:
        current_ctx_tokens = estimate_tokens(components['project_context'])
        target_ctx_tokens = max(500, current_ctx_tokens - overage)  # Keep min 500

        components['project_context'] = truncate_safely(
            components['project_context'],
            target_ctx_tokens
        )
        freed = current_ctx_tokens - estimate_tokens(components['project_context'])
        overage -= freed
        trim_report['actions'].append(f"Truncated project_context ({freed} tokens)")

    if overage <= 0:
        trim_report['final_total'] = EFFECTIVE_BUDGET - abs(overage)
        return components, trim_report

    # Step 4: Truncate specialization (preserve identity header)
    if components['specialization'] and overage > 0:
        spec = components['specialization']
        current_spec_tokens = estimate_tokens(spec)

        # Preserve identity (first ~500 tokens, typically "You are a X developer...")
        identity_end = spec.find('\n## ', 200)  # Find first major section after intro
        if identity_end == -1:
            identity_end = min(1800, len(spec))  # Fallback: first 1800 chars

        identity = spec[:identity_end]
        rest = spec[identity_end:]

        # Only truncate the non-identity part
        rest_tokens = estimate_tokens(rest)
        target_rest = max(0, rest_tokens - overage)

        if target_rest > 0:
            rest = truncate_safely(rest, target_rest)
        else:
            rest = ""

        components['specialization'] = identity + rest
        freed = current_spec_tokens - estimate_tokens(components['specialization'])
        overage -= freed
        trim_report['actions'].append(f"Truncated specialization (kept identity) ({freed} tokens)")

    if overage <= 0:
        trim_report['final_total'] = EFFECTIVE_BUDGET - abs(overage)
        return components, trim_report

    # Step 5: FAIL - cannot fit even after all trimming
    # Agent definition + task requirements alone exceed budget
    agent_tokens = estimate_tokens(components['agent_definition'])
    task_tokens = estimate_tokens(components['task_requirements'])

    trim_report['action'] = 'FAILED'
    trim_report['error'] = (
        f"Cannot fit prompt in budget. "
        f"Agent definition ({agent_tokens}) + Task requirements ({task_tokens}) = "
        f"{agent_tokens + task_tokens} tokens. Budget is {EFFECTIVE_BUDGET}. "
        f"Remaining overage: {overage} tokens."
    )
    trim_report['final_total'] = sum(estimate_tokens(c) for c in components.values())

    return components, trim_report
```

---

## Integration with Existing Code

### Modify `build_prompt()` function

```python
def build_prompt(args):
    """Build the complete agent prompt."""
    # ... existing code to build components ...

    # BEFORE composing final prompt, enforce file read budget
    components, trim_report = enforce_file_read_budget(
        agent_definition=agent_definition,
        task_requirements=task_context,
        project_context=context_block,
        specialization=spec_block,
        feedback_context=feedback_context
    )

    # Check for failure
    if trim_report.get('action') == 'FAILED':
        print(f"ERROR: {trim_report['error']}", file=sys.stderr)
        if args.json_output:
            print(json.dumps({
                "success": False,
                "error": trim_report['error'],
                "budget_exceeded": True,
                "trim_report": trim_report
            }))
        sys.exit(1)

    # Log trimming actions
    for action in trim_report.get('actions', []):
        print(f"WARNING: {action}", file=sys.stderr)

    # Compose final prompt from trimmed components
    prompt_parts = [
        components['agent_definition'],
        components['task_requirements'],
    ]
    if components['project_context']:
        prompt_parts.insert(0, components['project_context'])
    if components['specialization']:
        prompt_parts.insert(0, components['specialization'])
    if components['feedback_context']:
        prompt_parts.append(components['feedback_context'])

    full_prompt = "\n\n".join(prompt_parts)

    # FINAL VALIDATION: Double-check we're under limit
    final_tokens = estimate_tokens(full_prompt)
    if final_tokens > FILE_READ_LIMIT:
        print(f"ERROR: Final prompt still exceeds limit ({final_tokens} > {FILE_READ_LIMIT})", file=sys.stderr)
        sys.exit(1)

    # ... rest of existing code ...
```

### Add to JSON output

```python
result = {
    "success": True,
    "prompt_file": output_path,
    "tokens_estimate": final_tokens,
    "lines": lines,
    "markers_ok": markers_valid,
    "budget": {
        "limit": FILE_READ_LIMIT,
        "effective": EFFECTIVE_BUDGET,
        "used": final_tokens,
        "remaining": FILE_READ_LIMIT - final_tokens
    },
    "trim_report": trim_report
}
```

---

## Realistic Assessment

### What WILL work:
1. **Token estimation with safety margin** - Simple math, no LLM needed
2. **Code example detection** - Regex patterns are reliable for fenced blocks
3. **Safe truncation** - String operations, deterministic
4. **Priority-based trimming** - Rule-based, no ambiguity
5. **Final validation** - Hard check before return

### What MIGHT need tuning:
1. **Token estimation accuracy** - May need calibration against real Claude counts
   - Mitigation: Conservative 10% safety margin
   - Can log actual vs estimated for tuning

2. **Code example heuristics** - May miss some examples or catch non-examples
   - Mitigation: Err on side of NOT removing (only remove clear examples)
   - Can refine patterns based on observed content

3. **Identity preservation boundary** - "First section" heuristic may vary
   - Mitigation: Use character limit (1800 chars) as fallback
   - Most specializations have clear section headers

### What WON'T be an issue:
- No LLM latency or costs
- Deterministic output (same input = same output)
- Fast execution (pure Python string ops)
- Easy to debug (can log each step)

---

## Testing Strategy

### Unit Tests

```python
def test_token_estimation_accuracy():
    """Verify estimation is within acceptable range."""
    # Test cases with known token counts (from Claude API)
    cases = [
        ("Hello world", 2),  # Known: 2 tokens
        ("def foo():\n    pass", 8),  # Known: ~8 tokens
    ]
    for text, expected in cases:
        estimated = estimate_tokens(text)
        # Allow 20% variance
        assert expected * 0.8 <= estimated <= expected * 1.3


def test_code_example_removal():
    """Verify code examples are identified and removed."""
    text = '''
## Guide
Here's how to use this:

```python
# Example usage
def example():
    return "hello"

example()
```

More text here.
'''
    result, removed = remove_code_examples(text, 100)
    assert "[Code example removed" in result
    assert removed > 0


def test_safe_truncation_balances_fences():
    """Verify code fences are balanced after truncation."""
    text = "Start\n```python\ncode here\n"  # Unclosed fence
    result = truncate_safely(text, 10)
    assert result.count('```') % 2 == 0  # Even number


def test_budget_enforcement_priority():
    """Verify trimming follows priority order."""
    # Large components that will require trimming
    components, report = enforce_file_read_budget(
        agent_definition="x" * 50000,  # ~14k tokens
        task_requirements="y" * 20000,  # ~5.7k tokens
        project_context="z" * 10000,   # ~2.8k tokens
        specialization="s" * 10000,    # ~2.8k tokens
        feedback_context="f" * 5000,   # ~1.4k tokens
    )

    # Feedback should be trimmed first
    assert "feedback_context" in report['actions'][0].lower()
```

### Integration Test

```bash
# Build PM prompt and verify it's under limit
python3 .claude/skills/prompt-builder/scripts/prompt_builder.py \
    --agent-type project_manager \
    --session-id "test_123" \
    --branch "main" \
    --mode "simple" \
    --testing-mode "full" \
    --json-output

# Check the output
# Expected: tokens_estimate < 25000
# Expected: budget.used < budget.limit
```

---

## File Changes Required

| File | Change |
|------|--------|
| `.claude/skills/prompt-builder/scripts/prompt_builder.py` | Add budget enforcement logic |
| `tests/test_prompt_builder.py` | Add unit tests (new file) |

**Estimated lines of code:** ~200 new lines in prompt_builder.py

---

## Rollback Plan

If the automated budgeting causes issues:
1. The changes are additive - existing code paths preserved
2. Can add `--disable-budget-enforcement` flag to bypass
3. Budget constants are easily adjustable

---

## Success Criteria

1. ✅ PM prompt builds successfully (was failing at 25306 tokens)
2. ✅ All prompts stay under 25000 tokens (FILE_READ_LIMIT)
3. ✅ Agent definition and task requirements are NEVER trimmed
4. ✅ Trimming is logged (visibility into what was removed)
5. ✅ Build remains fast (< 1 second, no LLM calls)
6. ✅ Integration test passes end-to-end

---

## Open Questions for Review

1. **Token estimation ratio** - Should we use 3.5 or 3.7 chars/token?
   - Current proposal: 3.5 with 10% margin = effective 3.18 chars/token
   - Conservative, may over-trim slightly

2. **Identity preservation size** - How much of specialization to protect?
   - Current proposal: First 1800 chars or until first `## ` header
   - Should this be configurable?

3. **Orchestrator retry** - Should orchestrator auto-retry with stricter mode if build fails?
   - Current proposal: Script fails, orchestrator handles retry logic
   - Alternative: Script has "strict mode" flag for auto-retry

---

## Edge Cases and Robustness

### Critical Edge Cases Handled

| Edge Case | Problem | Solution |
|-----------|---------|----------|
| Empty strings | Division by zero, empty outputs | Check `if not text` early, return 0 or "" |
| None values | AttributeError on `.count()` | Coerce to empty string with `text or ""` |
| Very long single lines | No break points for truncation | Fallback to character-based cut with fence balance |
| Nested code fences | Fence counting gets confused | Track fence state properly, not just count |
| Unicode characters | Byte length ≠ char length | Use `len(text)` (char count), not bytes |
| Binary content | Regex crashes on invalid UTF-8 | Wrap in try/except, fallback to simple truncation |
| Agent def alone exceeds budget | Can't trim anything | Fail with clear error (already handled) |
| Specialization has no sections | Identity detection returns all | Use char limit fallback (1800 chars) |
| Regex catastrophic backtracking | Hangs on pathological input | Use non-greedy patterns, add timeout |
| Zero-length code blocks | Empty ``` ``` pairs | Skip blocks with no content |

### Robust Code Patterns

```python
def estimate_tokens(text: str) -> int:
    """Estimate tokens with comprehensive edge case handling."""
    # Handle None/empty
    if not text:
        return 0

    # Handle non-string input (defensive)
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return 0

    # Very short strings
    if len(text) < 10:
        return max(1, len(text) // 4)

    # Standard estimation
    base_estimate = len(text) / 3.5
    return int(base_estimate * 1.10)


def find_code_examples_safe(text: str) -> list[tuple[int, int, str]]:
    """Find code blocks with timeout and error handling."""
    if not text or len(text) < 10:
        return []

    try:
        # Use non-greedy pattern to prevent catastrophic backtracking
        # Limit match length to prevent hangs on pathological input
        pattern = r'```[\w]{0,20}\n([\s\S]{0,10000}?)```'

        examples = []
        for match in re.finditer(pattern, text):
            block = match.group(0)

            # Skip empty or tiny blocks
            if len(block) < 20:
                continue

            lines = block.count('\n')
            content_lower = block.lower()

            # More conservative heuristic - only remove clear examples
            is_example = (
                lines > 15 and  # Must be substantial
                (
                    '# example' in content_lower[:100] or
                    '// example' in content_lower[:100] or
                    '# usage' in content_lower[:100] or
                    '"""example' in content_lower[:100]
                )
            )

            if is_example:
                examples.append((match.start(), match.end(), block))

        return examples

    except re.error:
        # Regex compilation failed - return empty (don't crash)
        return []
    except Exception:
        # Any other error - return empty (don't crash)
        return []


def balance_code_fences_robust(text: str) -> str:
    """Balance code fences handling nested and malformed cases."""
    if not text:
        return text

    # Track fence state properly (not just count)
    in_fence = False
    fence_positions = []

    i = 0
    while i < len(text) - 2:
        if text[i:i+3] == '```':
            fence_positions.append(i)
            in_fence = not in_fence
            i += 3
        else:
            i += 1

    # If we ended inside a fence, close it
    if in_fence:
        text = text.rstrip() + "\n```"

    return text


def truncate_safely_robust(text: str, target_tokens: int) -> str:
    """Truncate with multiple fallback strategies."""
    if not text:
        return ""

    current_tokens = estimate_tokens(text)
    if current_tokens <= target_tokens:
        return text

    # Calculate target character count with buffer
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
    truncated = balance_code_fences_robust(truncated)

    # Add marker
    if not truncated.endswith('\n'):
        truncated += '\n'
    truncated += "\n[... content trimmed due to token budget ...]"

    return truncated


def extract_specialization_identity(spec: str) -> tuple[str, str]:
    """Extract identity portion from specialization.

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
```

### Defensive Wrapper

```python
def enforce_file_read_budget_safe(
    agent_definition: str,
    task_requirements: str,
    project_context: str = "",
    specialization: str = "",
    feedback_context: str = ""
) -> tuple[dict, dict]:
    """Wrapper with comprehensive error handling.

    GUARANTEES:
    1. Never raises exception (returns error in trim_report)
    2. Always returns valid dict structure
    3. Components are never None
    """
    # Coerce all inputs to strings
    agent_definition = str(agent_definition or "")
    task_requirements = str(task_requirements or "")
    project_context = str(project_context or "")
    specialization = str(specialization or "")
    feedback_context = str(feedback_context or "")

    try:
        return enforce_file_read_budget(
            agent_definition=agent_definition,
            task_requirements=task_requirements,
            project_context=project_context,
            specialization=specialization,
            feedback_context=feedback_context
        )
    except Exception as e:
        # Something went very wrong - return safe fallback
        # Keep only critical components
        return {
            'agent_definition': agent_definition,
            'task_requirements': task_requirements,
            'project_context': "",  # Drop context
            'specialization': "",   # Drop specialization
            'feedback_context': "", # Drop feedback
        }, {
            'original_total': -1,
            'budget': EFFECTIVE_BUDGET,
            'action': 'FALLBACK_DUE_TO_ERROR',
            'error': str(e),
            'final_total': estimate_tokens(agent_definition + task_requirements)
        }
```

### Error Recovery in Main Flow

```python
def build_prompt(args):
    """Build prompt with graceful degradation."""

    # ... build components ...

    # Apply budget enforcement with error handling
    try:
        components, trim_report = enforce_file_read_budget_safe(
            agent_definition=agent_definition,
            task_requirements=task_context,
            project_context=context_block,
            specialization=spec_block,
            feedback_context=feedback_context
        )
    except Exception as e:
        # Last resort: just use agent definition + task
        print(f"ERROR: Budget enforcement failed: {e}", file=sys.stderr)
        print("WARNING: Falling back to minimal prompt (agent + task only)", file=sys.stderr)
        components = {
            'agent_definition': agent_definition,
            'task_requirements': task_context,
            'project_context': "",
            'specialization': "",
            'feedback_context': "",
        }
        trim_report = {'action': 'FALLBACK', 'error': str(e)}

    # ... compose and validate ...
```

---

## Invariants (Must ALWAYS Hold)

These are checked with assertions in debug mode:

```python
def validate_invariants(components: dict, trim_report: dict) -> bool:
    """Validate critical invariants. Returns True if all pass."""
    errors = []

    # Invariant 1: Agent definition is NEVER empty after trimming
    if not components.get('agent_definition'):
        errors.append("Agent definition is empty")

    # Invariant 2: Task requirements are NEVER empty after trimming
    if not components.get('task_requirements'):
        errors.append("Task requirements are empty")

    # Invariant 3: Total tokens <= FILE_READ_LIMIT (unless FAILED)
    if trim_report.get('action') != 'FAILED':
        total = sum(estimate_tokens(c) for c in components.values())
        if total > FILE_READ_LIMIT:
            errors.append(f"Total ({total}) exceeds limit ({FILE_READ_LIMIT})")

    # Invariant 4: Code fences are balanced
    for name, content in components.items():
        if content and content.count('```') % 2 != 0:
            errors.append(f"Unbalanced fences in {name}")

    if errors:
        for e in errors:
            print(f"INVARIANT VIOLATION: {e}", file=sys.stderr)
        return False

    return True
```

---

## References

- Original issue: PM prompt 25306 tokens exceeded 25000 limit
- Current code: `.claude/skills/prompt-builder/scripts/prompt_builder.py`
- Prior analysis: `research/prompt-token-budget-management.md`
