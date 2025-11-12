---
name: velocity-tracker
description: Track development velocity, cycle times, and identify trends for PM decision-making
allowed-tools: [Bash, Read, Write]
---

# Velocity Tracker Skill

You are the velocity-tracker skill. When invoked, you analyze historical project data to provide quantitative metrics for PM decision-making.

## Your Task

When invoked, you will:
1. Calculate current project velocity and cycle times
2. Compare against historical metrics
3. Detect trends (improving/stable/declining)
4. Identify 99% rule violations (tasks taking >3x estimate)
5. Generate predictions and recommendations

---

## Step 1: Read PM State

Use the **Read** tool to read `coordination/pm_state.json`.

Extract:
- `task_groups`: List of all task groups
- `completed_groups`: Groups with status "completed"
- `in_progress_groups`: Groups currently being worked on
- Timestamps: `start_time`, `end_time` for each group

---

## Step 2: Calculate Current Metrics

Based on the PM state data, calculate:

**Velocity:**
```
velocity = sum(story_points for completed groups)
```

**Cycle Time per Group:**
```
cycle_time_minutes = (end_time - start_time) in minutes
```

**Percent Complete:**
```
percent_complete = (completed_groups / total_groups) * 100
```

**Estimated Remaining Time:**
```
avg_cycle_time = average of all completed cycle times
remaining_time = (total_groups - completed_groups) * avg_cycle_time
```

**Revision Rate:**
```
revision_rate = average iterations per completed group
```

---

## Step 3: Load Historical Data

Use the **Read** tool to read `coordination/historical_metrics.json` (if it exists).

If the file doesn't exist, set:
```
historical_metrics = {
    "total_runs": 0,
    "average_velocity": 0,
    "average_cycle_time_minutes": 0,
    "completion_rate": 0,
    "revision_rate": 0
}
```

If it exists, extract:
- `average_velocity`
- `average_cycle_time_minutes`
- `completion_rate`
- `revision_rate`

---

## Step 4: Detect Trends

Compare current metrics to historical averages:

**Velocity Trend:**
- If `current_velocity > historical_avg * 1.05`: trend = "improving"
- If `current_velocity < historical_avg * 0.95`: trend = "declining"
- Otherwise: trend = "stable"

**Cycle Time Trend:**
- If `current_avg_cycle_time < historical_avg * 0.95`: trend = "improving"
- If `current_avg_cycle_time > historical_avg * 1.05`: trend = "declining"
- Otherwise: trend = "stable"

**Quality Trend:**
- If `current_revision_rate < historical_revision_rate * 0.9`: trend = "improving"
- If `current_revision_rate > historical_revision_rate * 1.1`: trend = "declining"
- Otherwise: trend = "stable"

---

## Step 5: Detect 99% Rule Violations

For each completed group, check:

```
if cycle_time > (estimated_time * 3):
    # 99% rule violation detected
    add warning: {
        "type": "99_percent_rule",
        "group_id": group_id,
        "message": "Task taking 3x longer than expected",
        "recommendation": "Consider Tech Lead escalation or breaking into smaller tasks"
    }
```

---

## Step 6: Generate Recommendations

Based on analysis, generate recommendations:

**If velocity > historical:**
- "Current velocity (X) exceeds historical average (Y) - good progress"

**If velocity < historical:**
- "Velocity below average - may need additional resources or task breakdown"

**If 99% rule violations:**
- "Task GROUP_ID taking 3x longer - recommend escalation"

**Pattern detection:**
- Look for task types that consistently take longer (database, auth, etc.)
- Example: "Database tasks taking 2.5x estimate - budget more time"

---

## Step 7: Write Output

Use the **Write** tool to create `coordination/project_metrics.json`:

```json
{
  "timestamp": "<ISO 8601 timestamp>",
  "current_run": {
    "run_id": "<from pm_state.json>",
    "total_groups": <number>,
    "completed_groups": <number>,
    "in_progress": <number>,
    "pending": <number>,
    "percent_complete": <percentage>,
    "velocity": <story points completed>,
    "estimated_remaining_time": "<hours or minutes>",
    "cycle_times": {
      "<group_id>": {
        "duration_minutes": <minutes>,
        "story_points": <points>,
        "iterations": <count>,
        "status": "completed|in_progress"
      }
    }
  },
  "historical_metrics": {
    "total_runs": <count>,
    "average_velocity": <average>,
    "average_cycle_time_minutes": <average>,
    "completion_rate": <percentage>,
    "revision_rate": <average>
  },
  "trends": {
    "velocity": "improving|stable|declining",
    "cycle_time": "improving|stable|declining",
    "quality": "improving|stable|declining"
  },
  "warnings": [
    {
      "type": "99_percent_rule",
      "group_id": "<id>",
      "message": "<description>",
      "recommendation": "<action>"
    }
  ],
  "recommendations": [
    "<recommendation 1>",
    "<recommendation 2>"
  ]
}
```

---

## Step 8: Update Historical Metrics

If this run is complete, append current metrics to `coordination/historical_metrics.json` using the **Write** tool.

Update running averages:
```
new_avg_velocity = (old_avg * total_runs + current_velocity) / (total_runs + 1)
new_avg_cycle_time = (old_avg * total_runs + current_cycle_time) / (total_runs + 1)
```

---

## Step 9: Return Summary

Return a concise summary to the calling agent:

```
Velocity Metrics:
- Current velocity: X story points (historical avg: Y)
- Trend: improving/stable/declining
- Cycle time: X minutes average
- Completion: X%

Warnings:
- [List any 99% rule violations]

Recommendations:
- [List top 3 recommendations]

Details saved to: coordination/project_metrics.json
```

---

## Error Handling

If `coordination/pm_state.json` doesn't exist:
- Return: "Error: PM state file not found. Cannot calculate metrics."

If no completed groups yet:
- Return: "No completed groups yet. Run velocity tracker after completing at least one task group."

If any step fails:
- Log the error and return a partial report with available data
