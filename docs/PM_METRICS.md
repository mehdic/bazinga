# PM Metrics & Data-Driven Project Management

## Overview

BAZINGA PM combines **Tier 1** (velocity tracking), **Tier 2** (predictive analytics), and **Tier 3** (advanced insights) for intelligent, proactive project management. This document covers the metrics system that transforms PM from a reactive firefighter into a proactive manager.

---

## 1. The Problem - Why Metrics Matter for PM

### Blind PM (Before Metrics)

Traditional project management operated in the dark:

- ❌ **No velocity measurement** → Can't predict capacity or how much work fits in a sprint
- ❌ **No cycle time tracking** → Can't detect bottlenecks or inefficiencies
- ❌ **No historical learning** → Each run starts from zero; lessons disappear
- ❌ **No stuck task detection** → Tasks labeled "almost done" live forever
- ❌ **No trend analysis** → Can't tell if team is improving or declining
- ❌ **No resource visibility** → Can't see who's overworked or underutilized

**Result:** PM was a reactive firefighter, not a proactive manager.

### Real-World Impact

Without metrics:
```
Day 1: "Feature X will take 2 days" (guess)
Day 3: Feature X still in progress (surprise!)
Day 5: "Database migration broke everything" (crisis mode)
Day 7: Feature X finally done (3.5x original estimate)
Next feature: Estimate is still 2 days (no learning)
```

With metrics:
```
Run 1: Database tasks take 2.5x initial estimate (measured)
Run 2: Account for 2.5x multiplier in planning (learned)
Run 3: Prediction is accurate (confident)
```

---

## 2. Velocity Tracker - What It Provides

### Overview

The **velocity-tracker** Skill runs in **3-5 seconds** (faster than lint-check) and is always enabled. It measures real development velocity and detects problems early.

### Velocity Tracker Output

```json
{
  "current_run": {
    "velocity": 12,
    "percent_complete": 60,
    "revision_rate": 1.2,
    "tasks_in_progress": 3,
    "estimated_remaining_hours": 2.5
  },
  "trends": {
    "velocity": "improving",
    "quality": "improving",
    "efficiency": "stable"
  },
  "stuck_tasks": [],
  "warnings": [
    "G002 (database migration) taking 3x longer than expected - escalate to Tech Lead",
    "Developer-1 revision rate high (2.1x) - may need pair programming"
  ],
  "recommendations": [
    "Current velocity (12) exceeds historical average (10.5) - team performing well",
    "Continue parallel execution - it's working"
  ]
}
```

### What Each Metric Means

| Metric | Measures | Good Range | Warning |
|--------|----------|-----------|---------|
| **Velocity** | Story points completed per run | Increasing trend | Decreasing |
| **Cycle Time** | Hours per task group | Decreasing | Increasing |
| **Revision Rate** | Iterations needed per task | <1.5 revisions | >3 revisions |
| **Percent Complete** | Progress through current run | 0-100% | Stuck at 90% |

### Real Example: PM Using Velocity Data

**Scenario:** PM checks metrics after 2 hours of development.

```
📊 Checking metrics...

Current Velocity: 12 story points
Historical Average: 10.5
Trend: Improving ✓

⚠️  ALERT: Task Group G002 (database migration)
- Assigned: 3 hours
- Elapsed: 6 hours
- Status: In progress, 1st revision

🎯 ACTION: Task is now 2x over estimate
- This violates the 99% rule threshold
- Trigger: Escalate to Tech Lead for review
- Reason: Complexity may be underestimated or blocker exists

📝 PM Decision:
"@tech_lead, please review Group G002. Database migration is taking 2x longer than expected.
Are we hitting a complexity issue that needs architectural input?"
```

This is the power of metrics: **data-driven decision making in real time**.

---

## 3. 99% Rule Detection - Catching Stuck Tasks

### What Is the 99% Rule?

An industry anti-pattern where tasks spend 99% of time in the final 1% of work:

```
Example Timeline:
- Hours 1-4: "We're almost done, just need to test"
- Hours 5-8: "Found bugs, fixing them now"
- Hours 9-12: "Edge cases, should be done tomorrow"
- Hours 13-20: Task finally complete (5x original estimate)
```

### How BAZINGA Detects Stuck Tasks

PM monitors three signals:

#### Signal 1: Cycle Time Threshold
```
IF task_elapsed_time > 2x average_cycle_time
THEN escalate to Tech Lead
```

**Example:**
- Average cycle time for similar tasks: 90 minutes
- Current task elapsed: 180+ minutes
- Action: Escalate

#### Signal 2: Revision Count
```
IF revision_count > 3 AND no_resolution_in_2_hours
THEN escalate to Tech Lead
```

**Example:**
- Task revised 4 times
- Still in progress
- Tech Lead hasn't been involved
- Action: Escalate now

#### Signal 3: Developer-Group Stall
```
IF same_developer_same_group > 2_hours_without_progress
THEN suggest pair programming OR escalate
```

**Example:**
- Developer stuck on DB migration logic
- No commits in 90 minutes
- Last status: "Debugging transaction deadlock"
- Action: Offer Tech Lead support or pair programming

### Real Example: 99% Rule in Action

**Timeline:**

```
13:00 - Developer starts: "Implementing user password reset"
13:45 - Status: "Form validation done, email service integration next"
14:30 - Status: "Email service working, adding tests"
15:15 - 🔴 ALERT: Task now 1.5x over estimate (75 min elapsed vs 50 min estimate)
        Velocity Tracker shows revision_rate: 2.1 (high)

PM Action: "Good pace so far. Monitoring."

15:45 - Status: "Tests failing, debugging mocking issues"
16:15 - 🔴 ALERT: Task now 2.25x over estimate (105 min elapsed)
        Status unchanged for 45 minutes

PM Action: "@tech_lead, password reset feature stuck on test mocking.
Can you pair with developer for 15 minutes? It's exceeded 99% rule threshold."

Tech Lead: (5 min pair session) → "Issue was async mock setup, here's the pattern"
Developer: (10 min) → Tests pass, feature complete

16:30 - Task complete (90 min total, 1.8x estimate)
```

**Why this matters:** Without 99% rule detection, this task might stay "almost done" until 17:30, cascading delays into the evening.

---

## 4. Metrics Dashboard - What's Tracked

### Velocity Tracker Metrics

Every run, BAZINGA tracks these metrics in `bazinga/project_metrics.json`:

```json
{
  "run_id": "run-20250109-001",
  "timestamp": "2025-01-09T14:32:00Z",
  "project_name": "authentication-system",

  "velocity_metrics": {
    "total_story_points": 13,
    "completed_story_points": 12,
    "percent_complete": 92,
    "velocity": 12,
    "cycle_time_minutes": 240,
    "average_cycle_time_minutes": 180
  },

  "quality_metrics": {
    "revision_count": 2,
    "revision_rate": 0.15,
    "test_coverage": 86,
    "security_issues": 0,
    "lint_issues": 3
  },

  "team_metrics": {
    "developers_active": 2,
    "parallelism_mode": "parallel",
    "developer_1_efficiency": 1.1,
    "developer_2_efficiency": 0.95
  },

  "trend_analysis": {
    "velocity_trend": "improving",
    "quality_trend": "improving",
    "cycle_time_trend": "stable",
    "confidence": 0.85
  }
}
```

### How PM Uses This Data

**After Each Run:**

```
VELOCITY ANALYSIS:
- Completed: 12/13 story points (92%)
- Velocity: 12 (vs historical avg 10.5)
- Trend: Improving ✓

QUALITY CHECK:
- Revisions: 2 total (1.5 avg) ✓
- Coverage: 86% (target 70%) ✓
- Security: 0 critical issues ✓

TEAM HEALTH:
- Developer 1: 1.1x ratio (optimal) ✓
- Developer 2: 0.95x ratio (optimal) ✓

PREDICTION:
- At current pace: 1 story point = 20 min
- Next 5 story points = ~1.6 hours
- Estimated completion: 16:15 (85% confidence)
```

---

## 5. Advanced Capabilities - Tier 2 & 3 Features

### Tier 2: Predictive Analytics

#### 1. Risk Scoring & Proactive Alerts

Calculates risk for each task group:

```
Risk Score = (revision_count × 2) + (dependencies × 1.5) + (complexity × 1)
```

**Thresholds:**

| Score | Level | Action |
|-------|-------|--------|
| <5 | Low | Normal tracking |
| 5-10 | Medium | Watch closely, check status every 30 min |
| >10 | High | Alert user + suggest mitigation |

**Real Example:**

```
Group C Risk Assessment:
- Revision count: 4 → 4 × 2 = 8
- Dependencies: 1 → 1 × 1.5 = 1.5
- Complexity: 3 → 3 × 1 = 3
- Total Risk Score: 12.5 (HIGH)

⚠️  HIGH RISK ALERT
Group C has persistent issues:
- 4 revisions without resolution
- Blocking 1 dependent task group
- Estimated effort was high

Recommendations:
1. Consider splitting into smaller subtasks
2. Escalate to Tech Lead for architectural review
3. Pair with senior developer for 30 min consultation
```

#### 2. Predictive Timeline Estimation

Predicts completion with confidence scoring:

```
Effective Velocity = (historical_avg × 0.7) + (current_run × 0.3)
Hours Remaining = (remaining_story_points / effective_velocity) × avg_hours_per_point
Confidence = 100 - (velocity_variance × 10)
```

**Real Example:**

```
📈 COMPLETION PREDICTION

Remaining Work: 8 story points
Historical Average Velocity: 10.5 points
Current Run Velocity: 12 points

Effective Velocity = (10.5 × 0.7) + (12 × 0.3) = 10.95 points
Hours Per Point = 0.5 hours
Hours Remaining = (8 / 10.95) × 0.5 = 3.65 hours

Estimated Completion: 4:30 PM (current time: 12:45 PM)
Confidence: 82%

Trend: On track ✓
Risk: Low
```

This confidence score matters: 82% means "pretty reliable" while 45% would mean "very uncertain, expect delays".

#### 3. Resource Utilization Analysis

Tracks developer efficiency and prevents burnout:

```
Efficiency Ratio = actual_time / expected_time
```

**Interpretation:**

| Ratio | Status | Action |
|-------|--------|--------|
| <0.5 | Underutilized | Could take more work |
| 0.5-1.3 | Optimal ✓ | Ideal pace |
| 1.3-1.5 | Working hard | Monitor |
| >1.5 | Overworked | Risk of mistakes |

**Real Example:**

```
DEVELOPER UTILIZATION REPORT

Developer-1 (3 tasks, 9 story points):
- Expected time: 4.5 hours
- Actual time: 8.1 hours
- Ratio: 1.8x (OVERWORKED)

⚠️  OVERWORK ALERT
Developer-1 has exceeded 1.5x threshold.

Actions:
- Check if stuck (99% rule check)
- Offer Tech Lead pair session
- Prioritize remaining work
- Consider splitting tasks to Developer-3

Developer-2 (2 tasks, 6 story points):
- Expected: 3 hours
- Actual: 2 hours
- Ratio: 0.67x (OPTIMAL)

✓ Developer-2 can handle additional work
```

#### 4. Quality Gate Enforcement

Mandatory checks before BAZINGA (configurable):

```
Security Gate:   0 critical vulnerabilities
Coverage Gate:   ≥70% line coverage
Lint Gate:       ≤5 high-severity issues
Tech Debt Gate:  0 blocking items
```

**Real Example:**

```
🚦 QUALITY GATES CHECK (Before BAZINGA)

Security Gate:       ✓ PASS (0 critical issues)
Coverage Gate:       ✓ PASS (86% coverage, target 70%)
Lint Gate:           ✓ PASS (3 issues, target <5)
Tech Debt Gate:      ✗ FAIL (1 blocking item)

🚫 BAZINGA BLOCKED

Blocking Tech Debt:
TD-001: "Password reset email template hardcoded to prod"
- Severity: HIGH
- Impact: Can't deploy to staging
- Fix time: 5 minutes

Action: Developer, please fix TD-001 password reset email template.
Then we can send BAZINGA.
```

**Why quality gates matter:** They enforce standards and prevent shipping preventable bugs.

---

## 6. Historical Learning - How Metrics Improve Over Time

### The Power of Historical Data

After 5 runs, BAZINGA knows:

```
Run 1 Data:
- Database tasks: took 4 hours (estimated 1.5)
- API endpoints: took 1.5 hours (estimated 1.5)
- Testing: took 2 hours (estimated 1 hour)

Run 2: Still using 1x multipliers (no learning yet)

Run 3-5: Historical pattern analysis discovers:
- Database tasks consistently take 2.5x-2.8x
- API endpoints right on (1.0x)
- Testing takes 1.8x-2.1x

Run 6 Plan:
- Database task (estimate 2 hours) → Plan 5 hours (2.5x)
- API work (estimate 1.5 hours) → Plan 1.5 hours (1.0x)
- Testing (estimate 1 hour) → Plan 2 hours (2.0x)
Result: Prediction accurate
```

### Pattern Miner Skill (Tier 3)

The **pattern-miner** Skill analyzes historical data for predictive insights:

```json
{
  "historical_patterns": [
    {
      "pattern": "Database migrations always complex",
      "frequency": 5,
      "confidence": 0.92,
      "multiplier": 2.7,
      "evidence": [
        "Run 1: DB task 4h vs 1.5h estimate (2.67x)",
        "Run 2: DB task 5h vs 2h estimate (2.5x)",
        "Run 3: DB task 3h vs 1.5h estimate (2x)"
      ]
    },
    {
      "pattern": "Auth features require extra testing",
      "frequency": 3,
      "confidence": 0.85,
      "multiplier": 1.8,
      "evidence": [...]
    }
  ],

  "recommendations": [
    "For next auth feature: estimate 1.8x standard",
    "DB tasks need Tech Lead review (catches complexity early)",
    "Team improving on API work (1.0x now vs 1.2x in early runs)"
  ]
}
```

### Real Example: Historical Learning in Action

**Project: Building User Management System**

```
=== EARLY RUNS (No Historical Knowledge) ===

Run 1 - User Registration
Estimate: 4 hours (guess)
Actual: 7 hours (database + security added complexity)

Run 2 - Password Reset
Estimate: 3 hours (still guessing)
Actual: 6 hours (email service integration complex)

Run 3 - User Permissions
Estimate: 5 hours (pattern starting to emerge)
Actual: 8 hours (permissions logic harder than expected)

=== LATER RUNS (With Historical Data) ===

Run 4 - Team Roles
Estimate: 4 hours
With Pattern Miner: Database work typically takes 2.5x
Adjusted estimate: 10 hours
Actual: 9 hours (accurate! 85% confidence)

Run 5 - OAuth Integration
Estimate: 3 hours
With Pattern Miner: Auth features take 1.8x, plus external service integration
Adjusted estimate: 5.4 hours
Actual: 5.2 hours (highly accurate! 92% confidence)
```

**Impact:**
- Run 1: 75% error (4h estimate, 7h actual)
- Run 5: 4% error (5.4h estimate, 5.2h actual)
- Improvement: **71 percentage points more accurate**

---

## 7. Putting It All Together: PM Decision-Making Flow

### Real Scenario: Managing a Complex Feature

**Initial State:**
```
Feature: "Implement JWT Authentication with refresh tokens"
Estimated: 6 hours
Assigned: 2 developers (parallel mode)
```

**Timeline with Metrics:**

```
13:00 - START
PM invokes velocity-tracker
Baseline velocity: 11 points/run
Historical JWT tasks: 1.5x multiplier (from pattern-miner)
Adjusted estimate: 9 hours

14:30 - CHECK POINT 1 (90 min elapsed)
Metrics show:
- Velocity: 10 (on pace)
- Revision rate: 1.0 (good)
- Dev-1: 1.1x ratio (optimal)
- Dev-2: 0.9x ratio (optimal)
PM Decision: "Keep parallel mode. Team is performing well."

15:15 - CHECK POINT 2 (135 min elapsed)
⚠️  ALERT: Dev-1's task (token validation) is now 1.8x estimate
Metrics show:
- Revision count: 2
- Cycle time: 75 min vs avg 45 min
- Status: "Debugging edge cases in token expiration"
Risk Score: 7 (Medium)

PM Decision: "Task is medium risk but manageable.
Will check again in 20 minutes. If >2.5x estimate, escalate to Tech Lead."

15:45 - CHECK POINT 3 (165 min elapsed)
✓ Dev-1 resolves issue (edge case handling fixed)
Task now complete in 2.2x estimate (within acceptable range)

Metrics update:
- Velocity: 11.5 (exceeding baseline)
- Trend: improving
- Quality: 100% test coverage on JWT module

PM Decision: "Good work! Rate of improvement is accelerating.
Dev-2 finishing soon. Prepare for QA phase."

16:30 - QA PHASE
Both developers complete. All tests passing.
Tech Lead review in progress.

PM monitors:
- Coverage: 87% (target met)
- Security: 0 critical issues
- Lint: 2 issues (acceptable)
- Tech Debt: 0 blocking items

17:00 - COMPLETION
Tech Lead approves both task groups.

Final Metrics:
- Total time: 4 hours (estimate was 6, but 1.5x multiplier applied = 9 adjusted)
- Velocity: 12 (exceeding baseline 11)
- Quality: Excellent
- Team efficiency: 1.0x (spot on)

PM sends BAZINGA and includes summary:
"JWT authentication complete ahead of adjusted estimate.
Parallel execution worked well. Token validation edge cases
caught early by good test coverage. Add 1.5x multiplier to
similar auth tasks in future."
```

This demonstrates the full power of metrics:
- **Proactive monitoring** (velocity-tracker catching issues early)
- **Data-driven decisions** (99% rule, risk scoring)
- **Learning from history** (multiplier adjustments)
- **Quality enforcement** (gate checks)
- **Team health** (efficiency ratios)

---

## Summary Table: Metrics at a Glance

| Aspect | Metric | Real-Time? | Triggers | Action |
|--------|--------|-----------|----------|--------|
| **Pace** | Velocity | ✓ Every run | Low/high relative to baseline | Adjust parallelism |
| **Progress** | Completion % | ✓ Continuous | Stuck >90% | Check 99% rule |
| **Stuck Tasks** | Cycle time vs estimate | ✓ Every 30 min | >2x estimate | Escalate to Tech Lead |
| **Team Health** | Efficiency ratio | ✓ Per task | >1.5x (overworked) | Redistribute work |
| **Quality** | Coverage, security, lint | ✓ Per task | Fails gate threshold | Block BAZINGA |
| **Risk** | Risk score | ✓ Per task group | >10 (high) | Offer support |
| **Future Accuracy** | Historical multipliers | ✓ Per run | Pattern detected | Update estimates |

---

## Configuration & Enabling Metrics

### Default Setup

Velocity-tracker is **always enabled** by default (fastest Skill, 3-5s).

### Advanced Metrics (Optional)

Enable these via `/configure-skills`:

- **pattern-miner** (#9) - Historical pattern analysis (15-20s)
- **quality-dashboard** (#10) - Unified health dashboard (10-15s)

### Quick Enable

```bash
/configure-skills
> 9 10
```

This enables:
- Pattern-miner (historical learning)
- Quality dashboard (unified health score)

---

## Conclusion

Metrics transform PM from reactive firefighting to proactive management:

| Before Metrics | With Metrics |
|---|---|
| Reactive firefighting | Proactive management |
| Tasks stuck forever | Caught early (99% rule) |
| No learning | Continuous improvement |
| Blind estimates | Data-driven predictions |
| No team visibility | Health and efficiency tracking |
| Shipping surprises | Quality gates enforce standards |

The result: **Better predictions, healthier teams, higher quality, faster delivery.**
