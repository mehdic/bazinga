# Velocity & Metrics Tracker Skill

**Type:** Model-invoked project metrics analyzer
**Purpose:** Track development velocity, cycle times, and identify trends for PM decision-making
**Complexity:** Low (3-5 seconds runtime)

## What This Skill Does

Analyzes historical project data to provide PM with quantitative metrics for:

1. **Velocity Tracking**: Measures work completed per iteration (story points)
2. **Cycle Time Analysis**: Time taken per task group from start to completion
3. **Trend Detection**: Identifies if team is improving, declining, or stable
4. **99% Rule Detection**: Flags tasks taking abnormally long (>3x estimate)
5. **Historical Comparison**: Compares current run to past performance

## Why This Exists

**Current Problem:** PM operates blind - no metrics, no learning, no prediction
- Can't answer "Are we getting faster or slower?"
- Can't detect tasks stuck at 99% completion
- Each project starts from zero knowledge
- Estimation never improves

**Solution:** Track quantitative metrics to enable data-driven PM decisions

## Usage

```bash
# Automatically invoked by PM during progress reviews
/velocity-tracker
```

The PM should invoke this Skill:
- After completing each task group (track cycle time)
- Before spawning new developers (check velocity)
- Before sending BAZINGA (record final metrics)
- When detecting potential delays (identify patterns)

## Output

**File:** `coordination/project_metrics.json`

```json
{
  "timestamp": "2024-11-08T10:30:00Z",
  "current_run": {
    "run_id": "run-003",
    "total_groups": 5,
    "completed_groups": 3,
    "in_progress": 1,
    "pending": 1,
    "percent_complete": 60,
    "velocity": 12,
    "estimated_remaining_time": "1.5 hours",
    "cycle_times": {
      "G001": {
        "duration_minutes": 45,
        "story_points": 3,
        "iterations": 1,
        "status": "completed"
      },
      "G002": {
        "duration_minutes": 135,
        "story_points": 5,
        "iterations": 3,
        "status": "completed",
        "warning": "took 3x longer than similar tasks"
      },
      "G003": {
        "duration_minutes": 72,
        "story_points": 4,
        "iterations": 1,
        "status": "in_progress"
      }
    }
  },
  "historical_metrics": {
    "total_runs": 3,
    "average_velocity": 10.5,
    "average_cycle_time_minutes": 52,
    "completion_rate": 0.95,
    "revision_rate": 1.3
  },
  "trends": {
    "velocity": "improving",
    "cycle_time": "stable",
    "quality": "improving"
  },
  "warnings": [
    {
      "type": "99_percent_rule",
      "group_id": "G002",
      "message": "Task taking 3x longer than expected (135 min vs 45 min estimate)",
      "recommendation": "Consider Tech Lead escalation or breaking into smaller tasks"
    }
  ],
  "recommendations": [
    "Current velocity (12) exceeds historical average (10.5) - good progress",
    "G002 pattern: Database tasks taking 2.5x estimate - budget more time",
    "Quality trend improving - fewer revisions per task"
  ]
}
```

## Metrics Explained

### Velocity
**Definition:** Total story points completed in current run
**Use:** Forecast capacity, measure team throughput
**Good:** Increasing or stable velocity
**Bad:** Declining velocity (bottleneck indicator)

### Cycle Time
**Definition:** Time from task start to completion (in minutes)
**Use:** Identify slow tasks, detect 99% rule violations
**Good:** Decreasing cycle time (getting faster)
**Bad:** Increasing cycle time (getting slower)

### 99% Rule Violation
**Definition:** Tasks taking >3x estimated time
**Use:** Detect "stuck forever" tasks requiring intervention
**Action:** Escalate to Tech Lead, break into smaller tasks, or get user input

### Revision Rate
**Definition:** Average iterations per task group
**Use:** Quality indicator (lower is better)
**Good:** <1.5 revisions per task
**Bad:** >3 revisions (quality issues)

## How It Works

### Step 1: Read PM State
```bash
# Read coordination/pm_state.json
# Extract: task_groups, completed_groups, timestamps
```

### Step 2: Calculate Current Metrics
- **Velocity**: Sum story_points from completed groups
- **Cycle Time**: (end_time - start_time) per group
- **% Complete**: completed / total * 100
- **Remaining Time**: (total - completed) * avg_cycle_time

### Step 3: Load Historical Data
```bash
# Read coordination/historical_metrics.json
# Extract: past velocities, cycle times, patterns
```

### Step 4: Detect Trends
- Compare current to historical average
- Classify: improving, stable, declining
- Identify patterns (e.g., "DB tasks take 2.5x longer")

### Step 5: Generate Warnings
- **99% Rule**: Tasks >3x expected time
- **Velocity Drop**: >20% below historical average
- **Stuck Tasks**: In progress >2x average cycle time

### Step 6: Write Output
```bash
# Write coordination/project_metrics.json
# Append to coordination/historical_metrics.json
```

## PM Integration

**Before spawning developers:**
```markdown
@orchestrator

Checking project metrics...

[Invoke /velocity-tracker]

Current velocity: 12 (above average 10.5) ✓
Estimated remaining: 1.5 hours
Warning: Database tasks taking 2.5x estimate

Adjusting plan: Allocating extra time for remaining DB migration task.

Spawning Developer-1 for group G004...
```

**When detecting delay:**
```markdown
@orchestrator

Progress check: Group G002 has been in progress for 2 hours.

[Invoke /velocity-tracker]

⚠️ 99% Rule Violation detected!
- G002 expected: 45 minutes
- G002 actual: 135 minutes (3x over)
- Recommendation: Escalate to Tech Lead

Spawning Tech Lead to investigate G002 delay...
```

## When PM Should Use This

✅ **Use when:**
- After completing a task group (record metrics)
- Before spawning new developers (check capacity)
- When task appears stuck (detect 99% rule)
- Before BAZINGA (record final metrics for learning)
- Planning next iteration (use historical data)

❌ **Don't use when:**
- First run (no historical data yet)
- Emergency bug fixes (skip metrics)
- User explicitly requests fast mode

## Benefits

**Without Metrics:**
- PM guesses blindly
- No learning from past runs
- Can't detect stuck tasks
- Estimation never improves
- No visibility into progress
- **Result:** Inefficient, reactive PM

**With Metrics:**
- Data-driven decisions
- Continuous improvement
- Early problem detection
- Improving estimates over time
- User visibility
- **Result:** Efficient, proactive PM

**ROI:** 10x (transforms PM from reactive to proactive)

## Implementation

**Files:**
- `track.sh`: Bash script for metrics calculation
- `track.ps1`: PowerShell script for Windows
- `SKILL.md`: This documentation

**Dependencies:**
- `jq` (for JSON parsing in bash) - graceful fallback if missing
- Standard shell utilities (date, awk, bc)

**Runtime:**
- Small projects (<5 groups): 1-2 seconds
- Medium projects (5-15 groups): 2-4 seconds
- Large projects (15+ groups): 4-6 seconds

**Data Storage:**
```
coordination/
├── project_metrics.json      # Current run metrics
└── historical_metrics.json   # Cross-run learning
```

## Integration with Other Features

- **Tech Debt Tracking**: Metrics help PM decide if debt is acceptable
- **Model Escalation**: Velocity drop triggers earlier escalation
- **Adaptive Parallelism**: Velocity data informs spawn decisions
- **Quality Gates**: Revision rate affects approval decisions

This Skill transforms PM from "orchestrator" to "data-driven manager" - making BAZINGA smarter with every run.
