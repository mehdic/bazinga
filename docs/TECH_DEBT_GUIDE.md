# Tech Debt Logging Guide

## Core Principle: TRY FIRST, LOG LATER

⚠️ **CRITICAL**: Tech debt is for **CONSCIOUS TRADEOFFS**, not lazy shortcuts!

You MUST attempt to solve issues properly before logging them as tech debt.

## When Tech Debt Logging is APPROPRIATE

✅ **After genuine attempts to fix:**
- Spent 30+ minutes trying different approaches
- Solution requires architectural changes beyond current scope
- Fix would delay delivery significantly for marginal benefit
- External dependency limitation (library, API, platform)
- Performance optimization that requires profiling data not yet available

✅ **Conscious engineering tradeoffs:**
- "Implemented basic auth; OAuth requires more setup time than MVP allows"
- "Using in-memory cache; Redis setup blocked by infrastructure team"
- "Single-threaded processing sufficient for current 100 users; will need workers at 10K+"

## When Tech Debt Logging is INAPPROPRIATE

❌ **Lazy shortcuts (DO NOT LOG THESE):**
- "Didn't add error handling" → ADD ERROR HANDLING
- "No input validation" → ADD VALIDATION
- "Hardcoded values" → USE ENVIRONMENT VARIABLES
- "Skipped tests" → WRITE THE TESTS
- "TODO comments in code" → FINISH THE WORK

❌ **Things you should just fix:**
- Basic error handling (try/except, if/else checks)
- Input validation (null checks, type validation)
- Simple edge cases (empty arrays, zero values)
- Missing docstrings
- Code formatting issues

## Decision Framework

Before logging tech debt, ask yourself:

### 1. Can I fix this in < 30 minutes?
- **YES** → Fix it now, don't log
- **NO** → Continue evaluation

### 2. Does this require changes outside current scope?
- **YES** → Consider tech debt
- **NO** → Fix it now

### 3. Will this actually impact users?
- **YES** → Must fix OR log with HIGH severity
- **NO** → Might be over-engineering, reconsider if needed

### 4. Is this a fundamental limitation?
- **YES** (external dependency, platform limit) → Valid tech debt
- **NO** (I'm being lazy) → Fix it

## Tech Debt Categories & Examples

### ✅ VALID Tech Debt Examples

**Performance:**
```
"Using sequential processing for image uploads. Parallel processing
requires worker infrastructure not in current scope. Current load
(~10 images/day) doesn't justify complexity yet."

Attempts: Tried ThreadPoolExecutor but introduced race conditions
with shared state. Proper fix needs message queue architecture.
```

**Scalability:**
```
"User search uses full table scan. Elasticsearch integration would
require ops setup + data migration. Current 500 users perform fine
with simple LIKE query + pagination."

Attempts: Added database indexes, optimized query. Works for current
scale, but won't work past ~10K users.
```

**External Dependencies:**
```
"Email verification uses polling instead of webhooks. Email provider
(SendGrid free tier) doesn't support webhook callbacks. Would need
paid tier + webhook infrastructure."

Attempts: Tried polling optimization with exponential backoff. Best
we can do without provider upgrade.
```

### ❌ INVALID Tech Debt Examples

**Just lazy:**
```
❌ "Password reset doesn't validate email format"
✅ FIX IT: Add email regex validation (5 minutes)

❌ "No error handling on API calls"
✅ FIX IT: Wrap in try/except, return proper errors (10 minutes)

❌ "Missing unit tests"
✅ FIX IT: Write the tests (part of your job)
```

## How to Log Tech Debt (Python)

```python
# Import at top of coordination script
import sys
sys.path.insert(0, 'scripts')
from tech_debt import TechDebtManager

# When you've genuinely tried and have a valid reason
manager = TechDebtManager()

debt_id = manager.add_debt(
    added_by="Developer-1",
    severity="high",  # critical, high, medium, low
    category="performance",  # See CATEGORIES
    description="User search uses full table scan, won't scale past 10K users",
    location="src/users/search.py:45",
    impact="Slow queries (>5s) when user count exceeds 10,000",
    suggested_fix="Implement Elasticsearch for full-text search with proper indexing",
    blocks_deployment=False,  # True only if prod-breaking
    attempts_to_fix=(
        "1. Added database indexes on name, email fields (helped but not enough)\n"
        "2. Tried query optimization with select_related (marginal improvement)\n"
        "3. Implemented pagination (helps UX but doesn't fix core issue)\n"
        "Conclusion: Need proper search infrastructure, outside current scope"
    )
)

print(f"✓ Tech debt logged: {debt_id}")
```

## Severity Guidelines

### CRITICAL (blocks_deployment=True)
**Production-breaking issues that WILL cause failures**

Examples:
- Data loss risk
- Security vulnerability
- Breaking changes without migration path
- Missing critical error handling that causes crashes

**Before logging CRITICAL:** Are you SURE you can't fix this? Critical items block deployment!

### HIGH (blocks_deployment=False usually)
**User-facing issues or significant quality concerns**

Examples:
- Poor performance that affects UX
- Error messages not user-friendly
- Missing validation on user input
- Edge cases that could confuse users

**Before logging HIGH:** Spend 30+ minutes trying to fix. Document attempts!

### MEDIUM
**Internal quality, non-critical performance**

Examples:
- Code duplication that should be refactored
- Missing logging/monitoring
- Suboptimal algorithms that work for current scale
- Configuration hardcoded but not urgent

### LOW
**Nice-to-have improvements**

Examples:
- Code cleanup opportunities
- Documentation improvements
- Minor optimizations

## Integration with Workflow

### Developer Workflow

1. **Implement feature**
2. **Encounter issue** (performance, complexity, external blocker)
3. **ATTEMPT TO FIX** (minimum 20-30 minutes)
4. **Document attempts** (what you tried, why it didn't work)
5. **Evaluate if truly out of scope**
6. **IF justified:** Log tech debt with detailed `attempts_to_fix`
7. **Continue with current approach**

### Tech Lead Review

Tech Lead will review tech debt items and may:
- Ask you to fix items that should have been addressed
- Approve valid tradeoffs
- Adjust severity levels
- Suggest alternative approaches

### PM Gate (Before BAZINGA)

PM will check tech debt before completion:
- **Blocking items:** Must fix or get explicit user approval
- **HIGH severity (>2 items):** Ask user for approval
- **MEDIUM/LOW:** Include in completion summary

## Python Helper Usage

```python
from tech_debt import TechDebtManager

manager = TechDebtManager()

# Add debt (after genuine attempts to fix)
debt_id = manager.add_debt(
    added_by="Developer-2",
    severity="medium",
    category="configuration",
    description="API keys hardcoded in settings.py",
    location="src/config/settings.py:12",
    impact="Requires code deploy to change keys, can't rotate easily",
    suggested_fix="Move to environment variables or secrets manager",
    blocks_deployment=False,
    attempts_to_fix="Tried using python-dotenv but broke Docker builds. Need proper env var strategy."
)

# Check for blocking debt before reporting complete
if manager.has_blocking_debt():
    blocking = manager.get_blocking_items()
    print(f"⚠️  Cannot complete: {len(blocking)} blocking items")
    for item in blocking:
        print(f"  - {item['id']}: {item['description']}")
else:
    print("✓ No blocking tech debt")

# Get summary for reporting
summary = manager.get_summary()
print(f"Total tech debt: {summary['total']}")
print(f"By severity: {summary['by_severity']}")
```

## Remember

🎯 **Tech debt is a TOOL for managing tradeoffs, not an EXCUSE for poor work**

- ✅ Use when genuine constraints prevent proper solution
- ✅ Document what you tried before giving up
- ✅ Be honest about impact and severity
- ❌ Don't use to avoid doing your job properly
- ❌ Don't log things you could fix in <30 minutes
- ❌ Don't use as excuse for missing basics (tests, error handling, validation)

**Your reputation is built on the quality of your work, not the size of your tech debt log!**
