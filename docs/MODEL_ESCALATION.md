# Model Escalation Strategy

> How BAZINGA automatically escalates to more powerful models when code reviews get stuck

## The Problem: Why Revisions Persist

When code reviews go through multiple revisions, it's often a sign that the initial review analysis wasn't deep enough:

**Typical Scenario:**
```
First revision:  Tech Lead (Sonnet) → "Add error handling"
Second revision: Tech Lead (Sonnet) → "Fix edge case in validation"
Third revision:  Tech Lead (Sonnet) → "Still issues with the validation logic"
```

At this point, you're stuck in a loop. The faster model keeps catching surface-level issues, but there's likely a deeper problem:

- **Subtle bugs** or design flaws that require architectural understanding
- **Edge cases** not being handled systematically
- **Architectural issues** that can't be fixed with small tweaks
- **Fundamental approach problems** where the solution itself needs rethinking

The cost of staying with Sonnet 4.5 becomes higher than escalating: more revisions, more developer time, compounded delays.

## The Solution: Automatic Model Escalation

BAZINGA solves this with **intelligent model escalation**: automatically switching to a more powerful (and thorough) model when revisions persist.

**The Strategy:**

| Revision Count | Model Used | Cost | Strategy |
|----------------|-----------|------|----------|
| **1-2 revisions** | Sonnet 4.5 | $$ | Fast, cost-effective reviews for typical issues |
| **3+ revisions** | Opus | $$$ | Deep analysis for persistent, complex problems |

**Why this works:**
- Sonnet 4.5 is excellent at catching style issues, missing error handling, and straightforward logic problems
- Opus excels at deep architectural analysis, edge case comprehensiveness, and design-level reviews
- By escalating at revision 3, you catch persistent issues early before they become expensive

**Real Example:**
```
First review:  Sonnet 4.5 → "Add null checks"
Second review: Sonnet 4.5 → "Handle timeout case"
Third review:  Opus (escalated) → "Authentication flow needs redesign -
                 JWT token validation vulnerable to replay attacks"
```

Without escalation, you'd have revisions 4, 5, 6... Before realizing the architectural issue. With escalation, Opus catches it at revision 3.

## How It Works: Step-by-Step

BAZINGA's model escalation is fully automated. Here's the technical flow:

### Step 1: PM Tracks Revisions

Every time the Tech Lead requests changes, the Project Manager updates the revision count in `bazinga/group_status.json`:

```json
{
  "group_id": "G001",
  "status": "dev_in_progress",
  "revision_count": 2,
  "task_id": "Implement user authentication",
  "assigned_to": "Developer-1"
}
```

### Step 2: Orchestrator Checks Count Before Spawning Tech Lead

Before the orchestrator spawns the Tech Lead for the next review, it reads the revision count:

```
Orchestrator: [Reads group_status.json]
→ Revision count = 2
→ Tech Lead (Sonnet) for this review
→ Spawns Tech Lead with standard prompt
```

When revision count reaches 3:

```
Orchestrator: [Reads group_status.json]
→ Revision count = 3
→ Tech Lead (Opus) for this review
→ Spawns Tech Lead with enhanced prompt
```

### Step 3: Automatic Escalation Parameter

The orchestrator uses the `model` parameter when spawning the Tech Lead:

**Revision 1-2 (Sonnet 4.5):**
```
@tech_lead [standard review prompt]
```

**Revision 3+ (Opus):**
```
@tech_lead model=opus [enhanced review prompt]
```

### Step 4: Enhanced Prompt for Persistent Issues

When escalated to Opus, the Tech Lead receives special instructions to dig deeper:

**Enhanced Prompt Keywords:**
- Look for **subtle bugs or design flaws** that simple pattern matching misses
- **Verify edge cases** are handled systematically (not just obvious ones)
- Check for **architectural issues** that require redesign
- Consider if **the approach itself needs rethinking** before code improvements
- Identify **fundamental misunderstandings** in the implementation

This reframes the review from "find nitpicks" to "find root causes."

## Progressive Analysis: Basic vs Advanced

BAZINGA's Skills also escalate alongside model escalation:

| Revision Count | Security Scan Mode | Tech Lead Model | Speed | Depth |
|---|---|---|---|---|
| **0-1 revisions** | Basic (5-10s) | Sonnet 4.5 | 🟢 Fast | 🟡 Standard |
| **2 revisions** | Advanced (30-60s) | Sonnet 4.5 | 🟡 Medium | 🟠 Deep |
| **3+ revisions** | Advanced (comprehensive) | Opus | 🔴 Thorough | 🔴 Very Deep |

### What Each Mode Finds

**Basic Security Scan (Revisions 0-1):**
- SQL injection vulnerabilities
- Hardcoded secrets/credentials
- Critical (CRITICAL/HIGH severity) issues only
- 5-10 second scan time
- Fast enough for rapid iteration

**Advanced Security Scan (Revisions 2+):**
- All security issues (CRITICAL through LOW severity)
- Complex vulnerability patterns
- Cross-file security implications
- 30-60 second scan time
- Comprehensive before escalating to Opus

**Opus Deep Review (Revision 3+):**
- Architectural vulnerabilities
- Complex threat modeling
- Security design flaws
- Combined with advanced scan results
- Full understanding of security implications

### Example Flow for Failing JWT Implementation

```
Developer implements JWT authentication

Tech Lead Review #1 (Sonnet 4.5, basic scan):
→ Security Scan: Basic mode finds hardcoded secret
→ Review: "Move JWT secret to environment variable"
→ Developer fixes

Tech Lead Review #2 (Sonnet 4.5, advanced scan):
→ Security Scan: Advanced mode finds weak HMAC algorithm
→ Review: "Use HS256 or RS256, not HS128"
→ Developer fixes

Tech Lead Review #3 (Opus, comprehensive):
→ Security Scan: Comprehensive + Opus review
→ Finds: "Token validation missing expiration check + replay attack vulnerability"
→ Review: "Validate token expiration and add nonce tracking"
→ Also identifies: "Refresh token rotation not implemented - security risk"
```

Without escalation, developers would keep making small fixes. With escalation, Opus catches the architectural issues.

## Cost Optimization: When to Use Which Model

This strategy balances cost and quality across three scenarios:

### Scenario 1: Routine Issues (Most Common)

**When:**
- First or second revision
- Issues are about error handling, edge cases, code style
- Developer understands the problem and can fix it

**Model:** Sonnet 4.5
**Cost:** Lowest (2-3 revisions × Sonnet cost)
**Time:** Fast (5-10 minutes per review)

**Example:**
```
Review 1: "Add validation for email format"
Review 2: "Handle case where user has no email"
→ Developer fixes both → Approved
```

### Scenario 2: Complex Issues (Uncommon)

**When:**
- Third revision with same component
- Issue still not fully resolved
- Likely architectural or design problem

**Model:** Opus (automatic escalation)
**Cost:** Medium (3 revisions × Sonnet + 1 revision × Opus)
**Time:** Slower but problem solved (15-20 minutes)

**Example:**
```
Review 1: "Missing authentication"
Review 2: "Token validation incomplete"
Review 3: "Architectural issue: auth flow vulnerable to bypass"
→ Developer redesigns → Approved
```

**Cost Analysis:**
- Without escalation: 5-6 revisions × Sonnet = X cost + many developer hours
- With escalation: 3 revisions × Sonnet + 1 Opus = ~1.5X cost + fewer developer hours
- **Savings:** 2-3 fewer revisions, lower total cost, faster completion

### Scenario 3: Critical Features (Intentional)

**When:**
- You know a feature is critical or risky
- You want maximum quality before deployment
- Examples: Authentication, payment processing, security

**Model:** Opus from the start (or enable advanced Skills)

**Cost:** Higher per revision
**Time:** Longer but highest quality
**Benefit:** Catch problems early, prevent production incidents

**Configuration:**
```
# Use advanced Skills from the start
/configure-skills
> advanced

# Or let escalation handle it naturally if revisions occur
```

## Real-World Impact

### Before Automatic Escalation

```
Feature: User profile update with image upload

Dev creates feature
Review 1: Tech Lead → "Add error handling for large files"
Review 2: Tech Lead → "What about image format validation?"
Review 3: Tech Lead → "Missing virus scan for uploads"
Review 4: Tech Lead → "Security issue: arbitrary file access"
Review 5: Tech Lead → "Need proper file permissions/isolation"

Total: 5 revisions, 3+ hours dev time, frustrated developer
Result: Finally approved after multiple back-and-forths
```

### With Automatic Escalation

```
Feature: User profile update with image upload

Dev creates feature
Review 1: Sonnet 4.5 → "Add error handling for large files"
Review 2: Sonnet 4.5 → "Add image format validation"
Review 3: Opus (escalated) → "Security architecture issue:
         Need proper file isolation, virus scanning,
         and permission model before implementation"

Total: 3 revisions, dev can implement correctly once
Result: Approved with confidence in security design
```

**Improvement:**
- 2 fewer revisions (40% reduction)
- Clear architectural guidance from day one at revision 3
- Developer spends time fixing the right thing, not iterating

## Implementation Details

### Revision Tracking

The PM tracks revisions in `bazinga/group_status.json`:

```json
{
  "groups": [
    {
      "group_id": "G001",
      "user_story_id": "US001",
      "description": "JWT authentication",
      "task_group": ["T001", "T002"],
      "assigned_to": "Developer-1",
      "status": "dev_in_progress",
      "revision_count": 2,
      "last_revision_timestamp": "2025-01-15T14:30:00Z",
      "tech_lead_decisions": [
        {
          "revision": 1,
          "decision": "CHANGES_REQUESTED",
          "reason": "Add refresh token implementation"
        },
        {
          "revision": 2,
          "decision": "CHANGES_REQUESTED",
          "reason": "Token expiration validation missing"
        }
      ]
    }
  ]
}
```

### Model Parameter in Orchestrator

The orchestrator uses `model: "opus"` parameter:

```markdown
# Orchestrator routing to Tech Lead (Revision 3+)

Reading group_status.json...
Current revision_count: 3
Escalating to Opus for deep analysis.

@tech_lead model=opus
## Enhanced Review for Persistent Issues

This code has gone through 3 revisions. Look for:
- Subtle architectural flaws
- Incomplete edge case handling
- Design-level issues, not just code issues
- Whether the approach itself needs rethinking
```

### Skill Escalation Triggers

Skills automatically escalate based on revision count:

```python
# Pseudocode - how orchestrator decides skill mode

if revision_count <= 1:
    mode = "basic"  # Fast scan, high/critical severity only
elif revision_count == 2:
    mode = "advanced"  # Full scan, all severities
elif revision_count >= 3:
    mode = "advanced"  # Full scan + Opus review
    model = "opus"  # Use Opus for Tech Lead
```

## Best Practices

### For Developers

1. **First revision**: Pay close attention, fix all issues even if they seem small
2. **Second revision**: Think architectural - what might Tech Lead be hinting at?
3. **Third revision**: If you reach this, expect deep feedback - be ready to refactor

### For Project Managers

1. **Monitor revision counts**: Watch for patterns (same developer, same file type)
2. **Alert on escalations**: When Opus is used, something important was missed
3. **Learn from escalations**: Update estimates and training based on what Opus found

### For Tech Leads

1. **Sonnet reviews (1-2)**: Focus on practical issues, clear feedback
2. **Opus reviews (3+)**: Deep analysis, architectural thinking
3. **Provide context**: Explain WHY something is wrong, not just WHAT is wrong

## Metrics and Monitoring

Track these metrics to optimize your escalation strategy:

| Metric | Good | Bad | Action |
|--------|------|-----|--------|
| **Avg revisions to approval** | <2.5 | >4 | Improve initial implementation quality |
| **Escalation rate** | <20% | >40% | Increase developer training |
| **Opus findings** | Architectural issues | Nitpicks | Sonnet skill selection needs review |
| **Cycle time** | 30min avg | >2 hours | Earlier escalation might help |

## FAQ

**Q: Won't escalating to Opus every 3 revisions get expensive?**

A: No. Most features complete in 1-2 revisions (basic strategy works). Only persistently problematic features escalate, which would have taken many more revisions without escalation. Opus review is usually cheaper than 3 extra Sonnet reviews.

**Q: Can I force Sonnet for cost reasons?**

A: Yes, but not recommended. Persistent issues cost more in developer time than Opus fees. Better to escalate and solve faster.

**Q: What if Opus also requests changes?**

A: That's rare but possible. By revision 3, Opus usually identifies the root cause (architectural issue). Fix the architecture, not the symptoms.

**Q: Can I disable automatic escalation?**

A: Not recommended, but you could. Configure BAZINGA to keep revision_count unchanged in group_status.json. However, this defeats the purpose of the system.

**Q: How does this affect cost per feature?**

A:
- Typical feature: ~2 revisions × Sonnet = $X
- Complex feature: ~3 revisions × Sonnet + 1 revision × Opus = ~$1.3X (30% more)
- But completes in 1/3 the time with higher quality

**Q: What if I want Opus from the start for critical features?**

A: Use `/configure-skills advanced` for maximum analysis on critical work. Or set revision_count to 2 when you spawn the first Tech Lead review.

## Summary

BAZINGA's automatic model escalation:

✅ **Saves money** - Fewer revisions, faster completion
✅ **Ensures quality** - Architectural issues caught early
✅ **Reduces frustration** - Developers fix root causes, not symptoms
✅ **Fully automatic** - No manual intervention needed
✅ **Data-driven** - Based on revision count, not arbitrary thresholds

**Simple rule:** Let Sonnet handle typical issues (1-2 revisions), escalate to Opus when persistence suggests deeper problems (revision 3+).
