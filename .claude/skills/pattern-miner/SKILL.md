---
name: pattern-miner
description: Mine historical data for patterns and predictive insights
allowed-tools: [Bash, Read, Write]
---

# Pattern Miner Skill

You are the pattern-miner skill. When invoked, you analyze historical project data to identify recurring patterns, predict future issues, and provide data-driven recommendations.

## Your Task

When invoked, you will:
1. Load historical project data
2. Identify recurring patterns in task durations, revisions, and quality
3. Calculate pattern confidence levels
4. Generate predictions for current project
5. Provide estimation adjustments
6. Generate risk indicators

---

## Step 1: Load Historical Data

Use the **Read** tool to load these files (if they exist):

1. `coordination/historical_metrics.json` - Past velocity and cycle times
2. `coordination/tech_debt.json` - Historical technical debt and issues
3. `coordination/pm_state.json` - Current project state for comparison

If files don't exist:
- Return: "Insufficient historical data. Need at least 5 completed runs for pattern detection."

---

## Step 2: Extract Task Type Patterns

From historical_metrics.json, group tasks by type:

**Task types to look for:**
- Database tasks (keywords: "database", "migration", "schema", "db")
- Authentication tasks (keywords: "auth", "login", "password", "session")
- API tasks (keywords: "api", "endpoint", "rest", "graphql")
- Payment tasks (keywords: "payment", "transaction", "checkout")
- Frontend tasks (keywords: "ui", "frontend", "component", "react")
- Backend tasks (keywords: "backend", "service", "logic")

For each task type, calculate:
```
avg_actual_time = average of actual durations
avg_estimated_time = average of estimated durations
ratio = avg_actual_time / avg_estimated_time
occurrences = count of tasks of this type
variance = standard deviation of ratios
```

---

## Step 3: Detect Patterns

For each task type:

```
if occurrences >= 5 AND (ratio > 1.2 OR ratio < 0.8):
    pattern_detected = True

    if variance < 0.3:
        confidence = 0.85 + (occurrences / 100)
    elif variance < 0.5:
        confidence = 0.70 + (occurrences / 100)
    else:
        confidence = 0.60 + (occurrences / 100)

    # Cap confidence at 0.95
    confidence = min(confidence, 0.95)
```

**Pattern types:**
- **Estimation patterns**: Tasks consistently over/under estimated
- **Process patterns**: Tasks always requiring specific steps (e.g., security review)
- **Quality patterns**: Tasks with high revision rates
- **Risk patterns**: Common failure modes

---

## Step 4: Generate Pattern Descriptions

For each detected pattern, create a description:

**If ratio > 1.2 (overruns):**
```
description = "{task_type} tasks take {ratio}x longer than estimated"
recommendation = "Multiply {task_type} task estimates by {ratio}x"
impact = "high" if ratio > 2.0 else "medium"
```

**If ratio < 0.8 (faster than expected):**
```
description = "{task_type} tasks complete faster than expected ({ratio}x estimate)"
recommendation = "Consider using {ratio}x multiplier for more accurate estimates"
impact = "low"
```

---

## Step 5: Analyze Current Project

Use the **Read** tool to read `coordination/pm_state.json`.

For each pending or in-progress task group:
1. Extract task type from description
2. Check if any patterns apply to this task type
3. Generate predictions

Example:
```
if task contains "database" AND pattern exists for "database_tasks":
    prediction = {
        "task_group": task_id,
        "prediction": "Group {id} (database task) likely needs +{percentage}% time based on pattern '{pattern_id}'",
        "confidence": pattern_confidence,
        "recommendation": "Add buffer to estimate"
    }
```

---

## Step 6: Generate Estimation Adjustments

For each task type with detected patterns:

```json
"estimation_adjustments": {
  "<task_type>": {
    "multiplier": <ratio>,
    "confidence": <confidence>,
    "note": "<explanation>"
  }
}
```

Example:
```json
"database_tasks": {
  "multiplier": 2.5,
  "confidence": 0.85,
  "note": "Based on 12 historical database tasks"
}
```

---

## Step 7: Generate Risk Indicators

Analyze historical data for risk patterns:

```
if revision_count > 3 occurred in 80% of cases where X:
    risk_indicator = {
        "indicator": "X condition",
        "probability": 0.80,
        "outcome": "Requires tech lead escalation"
    }
```

Common risk indicators:
- High revision count → needs escalation
- High story points → should be split
- Certain modules → high defect rate

---

## Step 8: Generate Lessons Learned

Extract top lessons from historical data:

Examples:
- "Payment processing features have 80% revision rate - break into smaller tasks"
- "Parallel mode with >3 developers shows coordination overhead"
- "Integration tests catch 90% of bugs that slip past unit tests"

---

## Step 9: Write Output

Use the **Write** tool to create `coordination/pattern_insights.json`:

```json
{
  "timestamp": "<ISO 8601 timestamp>",
  "total_runs_analyzed": <count>,
  "patterns_detected": [
    {
      "pattern_id": "<unique_id>",
      "pattern": "<pattern_name>",
      "category": "estimation|process|quality|risk|team",
      "confidence": <0-1>,
      "occurrences": <count>,
      "description": "<human readable description>",
      "evidence": {
        "avg_estimate": <value>,
        "avg_actual": <value>,
        "variance": <value>
      },
      "recommendation": "<actionable recommendation>",
      "impact": "critical|high|medium|low"
    }
  ],
  "lessons_learned": [
    "<lesson 1>",
    "<lesson 2>",
    "<lesson 3>"
  ],
  "predictions_for_current_project": [
    {
      "task_group": "<group_id>",
      "prediction": "<description>",
      "confidence": <0-1>,
      "recommendation": "<action>"
    }
  ],
  "estimation_adjustments": {
    "<task_type>": {
      "multiplier": <ratio>,
      "confidence": <0-1>,
      "note": "<explanation>"
    }
  },
  "risk_indicators": [
    {
      "indicator": "<condition>",
      "probability": <0-1>,
      "outcome": "<predicted outcome>"
    }
  ]
}
```

---

## Step 10: Return Summary

Return a concise summary to the calling agent:

```
Pattern Mining Results:
- Analyzed: X historical runs
- Patterns detected: Y
- High confidence patterns (>0.80): Z

Top patterns:
1. <pattern 1>: <description> (confidence: X%)
2. <pattern 2>: <description> (confidence: Y%)
3. <pattern 3>: <description> (confidence: Z%)

Estimation adjustments recommended:
- <task_type>: Use {multiplier}x multiplier

Predictions for current project:
- <prediction 1>
- <prediction 2>

Details saved to: coordination/pattern_insights.json
```

---

## Confidence Thresholds

When presenting patterns, use these thresholds:

- **0.90-1.00**: Very High - Apply automatically
- **0.75-0.89**: High - Apply with PM review
- **0.60-0.74**: Medium - Suggest as option
- **0.00-0.59**: Low - Informational only

---

## Minimum Data Requirements

Pattern detection requires:
- **Minimum 5 historical runs** for any pattern
- **Minimum 3 occurrences** of same task type
- **Variance < 0.8** for high confidence

If insufficient data:
- Still generate report but mark patterns as "low confidence"
- Note: "Need more historical data for reliable patterns"

---

## Error Handling

**If no historical data:**
- Return: "No historical data found. Pattern mining requires at least 5 completed runs."

**If data corrupted:**
- Try to parse what's available
- Note errors in report
- Return partial results

**If current project state not found:**
- Skip prediction generation
- Still provide general patterns and adjustments

---

## Notes

- Weight recent data more heavily (last 10 runs)
- Ignore outliers (values > 3 standard deviations)
- Continuously improve confidence as more data collected
- Patterns become more accurate over time
