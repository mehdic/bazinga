# Prompt Token Budget Management: Preventing Oversized Agent Prompts

**Date:** 2025-12-17
**Context:** PM prompt exceeded 25000 token read limit (25306 tokens), blocking agent spawning
**Decision:** Implement priority-based token budgeting in prompt-builder skill
**Status:** Proposed
**Reviewed by:** Pending (OpenAI GPT-5, Google Gemini 3 Pro Preview)

---

## Problem Statement

The prompt-builder skill generates prompts that can exceed Claude's 25000 token file read limit. When this happens:
1. The orchestrator builds a prompt file successfully
2. The spawned agent tries to read the file
3. **Read fails** with "File content exceeds maximum allowed tokens"
4. The entire workflow is blocked

**Root cause:** No token budget enforcement during prompt assembly.

**Observed failure:**
```
✅ PM prompt built: 2539 lines, ~22631 tokens, all markers validated.
📋 ORCHESTRATOR: Spawning PM...
Read: bazinga/prompts/pm_prompt.md
❌ File content (25306 tokens) exceeds maximum allowed tokens (25000)
```

Note: The estimate said 22631 but actual was 25306 - a 12% underestimate. This suggests the token estimation is also unreliable.

---

## Current Prompt Assembly (prompt_builder.py)

The current prompt-builder assembles components in this order:
1. Agent definition file (`agents/{agent_type}.md`)
2. Specialization block (from specialization-loader skill)
3. Task context (from params)
4. Session/branch metadata
5. Database commands template

**No size limits are enforced.** Each component is included in full regardless of total size.

---

## Proposed Solution: Priority-Based Token Budgeting

### Core Concept

Implement a **token budget system** with priority tiers:

| Priority | Component | Budget Share | Can Trim? |
|----------|-----------|--------------|-----------|
| 1 (Critical) | Agent definition | 40% (~10000 tokens) | No - fail if exceeded |
| 2 (Critical) | Task requirements | 25% (~6250 tokens) | **No - never trim** |
| 3 (Flexible) | Project context | 20% (~5000 tokens) | Summarize or truncate |
| 4 (Optional) | Specializations | 15% (~3750 tokens) | Progressively trim to 0 |

**Key constraint:** Task requirements are NEVER trimmed. If budget cannot be met after trimming specializations and project context, the build FAILS with a clear error.

**Total budget:** 24000 tokens (leaving 1000 buffer for safety)

### Algorithm

```python
def build_prompt_with_budget(params, budget=24000):
    """Build prompt with token budget enforcement."""

    # Step 1: Measure all components
    components = {
        'agent_def': read_agent_definition(params['agent_type']),
        'task_req': params.get('task_requirements', ''),
        'project_ctx': read_project_context(),
        'specialization': get_specialization_block(params)
    }

    sizes = {k: estimate_tokens(v) for k, v in components.items()}
    total = sum(sizes.values())

    # Step 2: Check if we fit within budget
    if total <= budget:
        return assemble_all(components)  # Happy path

    # Step 3: Priority-based trimming
    overage = total - budget

    # Trim specialization first (lowest priority)
    if sizes['specialization'] > 0:
        trim_amount = min(overage, sizes['specialization'] - 500)  # Keep 500 min
        components['specialization'] = truncate(components['specialization'],
                                                 sizes['specialization'] - trim_amount)
        overage -= trim_amount

    if overage <= 0:
        return assemble_all(components)

    # Trim project context next
    if sizes['project_ctx'] > 0:
        trim_amount = min(overage, sizes['project_ctx'] - 500)
        components['project_ctx'] = truncate(components['project_ctx'],
                                              sizes['project_ctx'] - trim_amount)
        overage -= trim_amount

    if overage <= 0:
        return assemble_all(components)

    # Trim task requirements (but preserve core info)
    if sizes['task_req'] > 2000:  # Must keep at least 2000 tokens
        trim_amount = min(overage, sizes['task_req'] - 2000)
        components['task_req'] = truncate(components['task_req'],
                                           sizes['task_req'] - trim_amount)
        overage -= trim_amount

    if overage <= 0:
        return assemble_all(components)

    # Cannot trim agent definition - FAIL
    raise PromptBudgetExceeded(
        f"Cannot fit prompt in budget. Agent def: {sizes['agent_def']} tokens. "
        f"Remaining overage: {overage} tokens."
    )
```

### Improved Token Estimation

Current estimation is ~12% off. Improve with:

```python
def estimate_tokens(text: str) -> int:
    """More accurate token estimation."""
    # Use cl100k_base tokenizer patterns
    # Average: 4 chars per token for English text
    # Markdown/code: 3.5 chars per token (more symbols)

    code_blocks = len(re.findall(r'```[\s\S]*?```', text))
    if code_blocks > 3:
        chars_per_token = 3.5
    else:
        chars_per_token = 4.0

    base_estimate = len(text) / chars_per_token

    # Add 10% safety margin
    return int(base_estimate * 1.10)
```

---

## Alternative Approaches Considered

### Alternative 1: Split Prompt Across Multiple Files

**Concept:** Split into `prompt_part1.md`, `prompt_part2.md`, etc.

**Pros:**
- No content loss
- Simple to implement

**Cons:**
- Spawned agent must read multiple files (complexity)
- Risk of missing a part
- Breaks "single prompt file" contract

**Verdict:** ❌ Rejected - adds complexity and fragility

### Alternative 2: Use Compression/Summarization

**Concept:** LLM-summarize large components before inclusion

**Pros:**
- Preserves semantic content
- Could significantly reduce size

**Cons:**
- Requires LLM call during prompt building (slow, expensive)
- May lose important details
- Non-deterministic output

**Verdict:** ❌ Rejected - too slow and unpredictable

### Alternative 3: Lazy Loading via Skill Invocation

**Concept:** Include pointers instead of content, agent fetches via skills

**Pros:**
- Prompt stays small
- Agent gets full content on demand

**Cons:**
- Agent may not know to invoke skills
- Adds turns to agent execution
- Skill invocation can fail

**Verdict:** ⚠️ Partial - could be used for optional specializations only

### Alternative 4: Per-Agent Budget Configuration

**Concept:** Configure token budgets per agent type in model_selection.json

```json
{
  "agents": {
    "project_manager": {
      "model": "opus",
      "token_budget": {
        "total": 24000,
        "agent_def": 12000,
        "task": 8000,
        "context": 3000,
        "specialization": 1000
      }
    }
  }
}
```

**Pros:**
- Fine-grained control
- PM can have different budget than Developer
- Explicit, auditable

**Cons:**
- More configuration to manage
- May need tuning per use case

**Verdict:** ✅ Recommended enhancement

---

## Recommended Solution

### Phase 1: Immediate Fix (Priority-Based Trimming)

1. **Add budget parameter to prompt_builder.py**
   - Default: 24000 tokens
   - Configurable via params file

2. **Measure before assembly**
   - Calculate token count for each component
   - Log sizes for visibility

3. **Trim in priority order**
   - Specialization → Project context → Task requirements
   - Keep agent definition intact (fail if too large alone)

4. **Improve token estimation**
   - Use 3.7 chars/token with 10% safety margin
   - Log both estimate and actual for calibration

### Phase 2: Enhanced Configuration

1. **Per-agent budget config** in model_selection.json
2. **Component-level budgets** for fine control
3. **Trimming strategy options**: truncate, summarize-headers, remove-examples

### Implementation Location

**File:** `.claude/skills/prompt-builder/scripts/prompt_builder.py`

**Changes:**
1. Add `TokenBudget` class
2. Add `measure_components()` function
3. Add `trim_to_budget()` function
4. Update `build_prompt()` to use budget enforcement
5. Update JSON output to include budget diagnostics

---

## Detailed Implementation

### TokenBudget Class

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TokenBudget:
    """Token budget configuration with priority-based allocation."""

    total: int = 24000
    agent_def_max: int = 12000      # Priority 1 - cannot trim
    task_req_min: int = 2000         # Priority 2 - minimum to keep
    project_ctx_min: int = 500       # Priority 3 - minimum to keep
    specialization_min: int = 0      # Priority 4 - can remove entirely

    safety_margin: float = 0.05      # 5% buffer

    @property
    def effective_budget(self) -> int:
        return int(self.total * (1 - self.safety_margin))


def load_budget_config(agent_type: str) -> TokenBudget:
    """Load budget from model_selection.json if configured."""
    try:
        with open('bazinga/model_selection.json') as f:
            config = json.load(f)

        agent_config = config.get('agents', {}).get(agent_type, {})
        budget_config = agent_config.get('token_budget', {})

        if budget_config:
            return TokenBudget(**budget_config)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return TokenBudget()  # Default
```

### Component Measurement

```python
def measure_components(
    agent_def: str,
    task_req: str,
    project_ctx: str,
    specialization: str
) -> dict:
    """Measure token count for each component."""

    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        # More accurate estimation with safety margin
        chars_per_token = 3.7
        return int(len(text) / chars_per_token * 1.10)

    return {
        'agent_def': estimate_tokens(agent_def),
        'task_req': estimate_tokens(task_req),
        'project_ctx': estimate_tokens(project_ctx),
        'specialization': estimate_tokens(specialization),
        'total': estimate_tokens(agent_def + task_req + project_ctx + specialization)
    }
```

### Trimming Logic

```python
def trim_to_budget(
    components: dict,
    sizes: dict,
    budget: TokenBudget
) -> tuple[dict, dict]:
    """Trim components to fit within budget. Returns (trimmed_components, trim_report)."""

    effective_budget = budget.effective_budget
    total = sizes['total']

    trim_report = {
        'original_total': total,
        'budget': effective_budget,
        'trimmed': {}
    }

    if total <= effective_budget:
        trim_report['action'] = 'none_needed'
        return components, trim_report

    overage = total - effective_budget
    trimmed = dict(components)

    # Priority 4: Trim specialization first
    if sizes['specialization'] > budget.specialization_min and overage > 0:
        available_trim = sizes['specialization'] - budget.specialization_min
        trim_amount = min(overage, available_trim)
        new_size = sizes['specialization'] - trim_amount
        trimmed['specialization'] = truncate_text(
            components['specialization'],
            target_tokens=new_size
        )
        trim_report['trimmed']['specialization'] = {
            'from': sizes['specialization'],
            'to': new_size,
            'removed': trim_amount
        }
        overage -= trim_amount

    # Priority 3: Trim project context
    if sizes['project_ctx'] > budget.project_ctx_min and overage > 0:
        available_trim = sizes['project_ctx'] - budget.project_ctx_min
        trim_amount = min(overage, available_trim)
        new_size = sizes['project_ctx'] - trim_amount
        trimmed['project_ctx'] = truncate_text(
            components['project_ctx'],
            target_tokens=new_size
        )
        trim_report['trimmed']['project_ctx'] = {
            'from': sizes['project_ctx'],
            'to': new_size,
            'removed': trim_amount
        }
        overage -= trim_amount

    # Priority 2: Trim task requirements (preserve minimum)
    if sizes['task_req'] > budget.task_req_min and overage > 0:
        available_trim = sizes['task_req'] - budget.task_req_min
        trim_amount = min(overage, available_trim)
        new_size = sizes['task_req'] - trim_amount
        trimmed['task_req'] = truncate_text(
            components['task_req'],
            target_tokens=new_size
        )
        trim_report['trimmed']['task_req'] = {
            'from': sizes['task_req'],
            'to': new_size,
            'removed': trim_amount
        }
        overage -= trim_amount

    # Priority 1: Agent definition cannot be trimmed
    if overage > 0:
        trim_report['action'] = 'failed'
        trim_report['remaining_overage'] = overage
        raise PromptBudgetExceeded(
            f"Cannot fit prompt in budget after trimming. "
            f"Agent definition: {sizes['agent_def']} tokens. "
            f"Remaining overage: {overage} tokens. "
            f"Consider reducing agent definition size."
        )

    trim_report['action'] = 'trimmed'
    trim_report['final_total'] = effective_budget - overage
    return trimmed, trim_report


def truncate_text(text: str, target_tokens: int) -> str:
    """Truncate text to target token count with clean break."""
    if not text:
        return text

    # Estimate current tokens
    current = int(len(text) / 3.7 * 1.10)
    if current <= target_tokens:
        return text

    # Calculate target character count
    target_chars = int(target_tokens * 3.7 / 1.10)

    # Find clean break point (paragraph or sentence)
    truncated = text[:target_chars]

    # Try to break at paragraph
    last_para = truncated.rfind('\n\n')
    if last_para > target_chars * 0.7:  # Keep at least 70%
        truncated = truncated[:last_para]
    else:
        # Break at sentence
        last_sentence = max(
            truncated.rfind('. '),
            truncated.rfind('.\n'),
            truncated.rfind('? '),
            truncated.rfind('! ')
        )
        if last_sentence > target_chars * 0.8:
            truncated = truncated[:last_sentence + 1]

    return truncated + "\n\n[... content trimmed due to token budget ...]"
```

### Updated JSON Output

```python
def build_prompt(params: dict) -> dict:
    """Build prompt with budget enforcement."""

    # ... existing loading code ...

    # Measure components
    sizes = measure_components(agent_def, task_req, project_ctx, specialization)

    # Load budget config
    budget = load_budget_config(params['agent_type'])

    # Trim if needed
    try:
        components, trim_report = trim_to_budget(
            {'agent_def': agent_def, 'task_req': task_req,
             'project_ctx': project_ctx, 'specialization': specialization},
            sizes,
            budget
        )
    except PromptBudgetExceeded as e:
        return {
            'success': False,
            'error': str(e),
            'budget_exceeded': True,
            'component_sizes': sizes,
            'budget': budget.total
        }

    # Assemble final prompt
    final_prompt = assemble_prompt(components)
    final_tokens = estimate_tokens(final_prompt)

    # Write and return
    write_prompt(params['output_file'], final_prompt)

    return {
        'success': True,
        'prompt_file': params['output_file'],
        'tokens_estimate': final_tokens,
        'lines': final_prompt.count('\n') + 1,
        'markers_ok': validate_markers(final_prompt),
        'budget': {
            'limit': budget.total,
            'used': final_tokens,
            'remaining': budget.total - final_tokens
        },
        'component_sizes': sizes,
        'trim_report': trim_report
    }
```

---

## Testing Strategy

### Unit Tests

```python
def test_budget_enforcement():
    """Test that prompts are trimmed to fit budget."""
    # Create components that exceed budget
    large_specialization = "x" * 50000  # ~13500 tokens

    result = build_prompt({
        'agent_type': 'developer',
        'task_requirements': 'Simple task',
        'specialization': large_specialization
    })

    assert result['success'] == True
    assert result['tokens_estimate'] <= 24000
    assert result['trim_report']['action'] == 'trimmed'
    assert 'specialization' in result['trim_report']['trimmed']


def test_agent_def_too_large_fails():
    """Test that oversized agent definition fails gracefully."""
    # Mock an agent definition that's too large
    with patch('read_agent_definition', return_value="x" * 100000):
        result = build_prompt({'agent_type': 'project_manager'})

        assert result['success'] == False
        assert result['budget_exceeded'] == True
        assert 'Agent definition' in result['error']
```

### Integration Test

Add to integration test verification:
```bash
# Verify prompt sizes are within budget
for prompt_file in bazinga/prompts/bazinga_*/*.md; do
    tokens=$(wc -c < "$prompt_file" | awk '{print int($1/3.7*1.1)}')
    if [ "$tokens" -gt 24000 ]; then
        echo "❌ FAIL: $prompt_file exceeds budget ($tokens tokens)"
        exit 1
    fi
done
echo "✅ All prompts within token budget"
```

---

## Rollout Plan

### Phase 1: Immediate (This Session)
1. Implement basic budget enforcement in prompt_builder.py
2. Add component size logging
3. Test with PM prompt that was failing

### Phase 2: Configuration (Next Session)
1. Add per-agent budget config to model_selection.json
2. Add trimming strategy options
3. Update documentation

### Phase 3: Optimization (Future)
1. Calibrate token estimation against actual tokenizer
2. Add smart truncation (preserve headers, trim examples)
3. Consider lazy-loading for specializations

---

## Success Criteria

1. **No prompt exceeds 24000 tokens** - enforced at build time
2. **Priority order respected** - specialization trimmed before task requirements
3. **Graceful degradation** - prompts still functional after trimming
4. **Visibility** - JSON output shows budget usage and any trimming
5. **Configurable** - per-agent budgets can be set

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Trimmed content causes agent failure | Medium | High | Keep minimum thresholds per component |
| Token estimation still inaccurate | Medium | Medium | Add safety margin, log actuals |
| Configuration complexity | Low | Low | Good defaults, clear docs |
| Performance overhead | Low | Low | Estimation is O(n) string ops |

---

## Open Questions

1. **Should we support "smart" truncation?** (e.g., keep headers, trim examples)
   - Pro: Better content preservation
   - Con: More complex, may break structured content

2. **Should trimming be opt-in or default?**
   - Recommendation: Default ON with explicit disable option

3. **How to handle agent definitions that are inherently too large?**
   - Recommendation: Fail fast with clear error, prompt author must reduce

---

## References

- Token limits: Claude file read limit is 25000 tokens
- Current prompt builder: `.claude/skills/prompt-builder/scripts/prompt_builder.py`
- Integration test that exposed issue: `tests/integration/simple-calculator-spec.md`
- Related: `research/skill-implementation-guide.md` for skill patterns
