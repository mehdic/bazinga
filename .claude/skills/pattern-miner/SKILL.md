---
name: pattern-miner
description: Mine historical data for patterns and predictive insights
category: analytics
execution_time: 15-20s
---

# Pattern Miner Skill

## Overview

The **pattern-miner** Skill analyzes historical project data to identify recurring patterns, predict future issues, and provide data-driven recommendations for estimation and planning.

**Purpose:** Learn from past runs to make better predictions and avoid repeating mistakes.

## When to Use

- **After creating task groups** - Adjust estimates based on historical patterns
- **Before major features** - Predict effort based on similar past features
- **Weekly retrospectives** - Identify systemic issues
- **Quarterly planning** - Understand team's actual velocity patterns

## What It Analyzes

| Source | Patterns Extracted |
|--------|-------------------|
| **historical_metrics.json** | Velocity patterns, cycle time trends, revision rates by task type |
| **tech_debt.json** | Recurring issues, problem modules, common failure modes |
| **pm_state.json** (past runs) | Task type durations, parallelization effectiveness |
| **coordination logs** | Developer efficiency patterns, common bottlenecks |

## Pattern Types Detected

### 1. Task Duration Patterns
- "Database tasks always take 2.5x initial estimate" (85% confidence)
- "Authentication features require 3 revisions on average"
- "API integrations complete faster than expected (0.7x estimate)"

### 2. Module Risk Patterns
- "Payment module has 80% revision rate (high risk)"
- "Auth module always requires security review"
- "Frontend changes rarely need QA iterations"

### 3. Team Velocity Patterns
- "Team velocity increases 20% after first week of project"
- "Parallel mode with 3+ developers shows diminishing returns"
- "Friday deployments have 2x higher rollback rate"

### 4. Quality Patterns
- "Coverage drops correlate with rushed features (r=0.85)"
- "Security issues cluster in user input handling"
- "Lint violations spike during feature freeze"

## Output Format

```json
{
  "timestamp": "2024-11-08T12:00:00Z",
  "total_runs_analyzed": 25,
  "patterns_detected": [
    {
      "pattern_id": "db_task_overrun",
      "pattern": "database_tasks_overrun",
      "category": "estimation",
      "confidence": 0.85,
      "occurrences": 12,
      "description": "Database-related tasks take 2.5x longer than estimated",
      "evidence": {
        "avg_estimate": 5.0,
        "avg_actual": 12.5,
        "variance": 2.3
      },
      "recommendation": "Multiply database task estimates by 2.5x",
      "impact": "high"
    },
    {
      "pattern_id": "auth_security_review",
      "pattern": "auth_requires_security_review",
      "category": "process",
      "confidence": 1.0,
      "occurrences": 8,
      "description": "Authentication tasks always require security review (100%)",
      "recommendation": "Plan for security review in auth task timeline",
      "impact": "medium"
    }
  ],
  "lessons_learned": [
    "Payment processing features have 80% revision rate - break into smaller tasks",
    "Parallel mode with >3 developers shows coordination overhead (diminishing returns)",
    "Integration tests catch 90% of bugs that slip past unit tests"
  ],
  "predictions_for_current_project": [
    {
      "task_group": "C",
      "prediction": "Group C (payment processing) likely needs +30% time based on pattern 'payment_module_revisions'",
      "confidence": 0.78,
      "recommendation": "Add buffer to Group C estimate"
    }
  ],
  "estimation_adjustments": {
    "database_tasks": {
      "multiplier": 2.5,
      "confidence": 0.85
    },
    "authentication": {
      "multiplier": 1.5,
      "confidence": 0.90,
      "note": "Include security review time"
    },
    "api_integration": {
      "multiplier": 0.7,
      "confidence": 0.75,
      "note": "Usually faster than expected"
    }
  },
  "risk_indicators": [
    {
      "indicator": "revision_count > 3",
      "probability": 0.85,
      "outcome": "Requires tech lead escalation"
    },
    {
      "indicator": "story_points > 8",
      "probability": 0.70,
      "outcome": "Should be split into smaller tasks"
    }
  ]
}
```

## Pattern Confidence Levels

| Confidence | Meaning | Action |
|------------|---------|--------|
| 0.90-1.00 | Very High | Apply automatically |
| 0.75-0.89 | High | Apply with PM review |
| 0.60-0.74 | Medium | Suggest as option |
| 0.00-0.59 | Low | Informational only |

## Pattern Categories

1. **Estimation** - Task duration patterns
2. **Process** - Workflow patterns (e.g., always needs review)
3. **Quality** - Defect and revision patterns
4. **Risk** - Failure mode patterns
5. **Team** - Velocity and efficiency patterns

## Usage Example

**In PM agent:**
```bash
# After creating task groups, refine estimates with patterns
/pattern-miner

# Read predictions
cat coordination/pattern_insights.json

# Apply adjustments
PATTERN_MULTIPLIER=$(jq -r '.estimation_adjustments.database_tasks.multiplier' coordination/pattern_insights.json)

if [ "$PATTERN_MULTIPLIER" != "null" ]; then
    # Adjust database task estimate
    NEW_ESTIMATE=$(echo "$ORIGINAL_ESTIMATE * $PATTERN_MULTIPLIER" | bc)
    echo "Adjusted database task estimate: $ORIGINAL_ESTIMATE → $NEW_ESTIMATE (${PATTERN_MULTIPLIER}x multiplier)"
fi

# Check predictions for current groups
jq -r '.predictions_for_current_project[] | "⚠️  \(.prediction)"' coordination/pattern_insights.json
```

## Pattern Detection Algorithm

```
For each task type:
1. Group historical tasks by type (database, auth, API, etc.)
2. Calculate avg_actual_time / avg_estimated_time ratio
3. If ratio consistently >1.2 or <0.8 across ≥5 occurrences:
   → Pattern detected
4. Calculate confidence based on:
   - Number of occurrences (more = higher confidence)
   - Variance (lower = higher confidence)
   - Recency (recent data weighted more)
```

## Benefits

✅ **Data-driven estimates** - Stop guessing, use historical data  
✅ **Avoid recurring mistakes** - Learn from past patterns  
✅ **Proactive risk management** - Predict issues before they happen  
✅ **Continuous improvement** - Estimation accuracy improves over time  
✅ **Team-specific insights** - Patterns unique to your team's velocity

## Performance

- **Execution time:** 15-20 seconds
- **Dependencies:** jq (graceful fallback if not available)
- **Minimum data:** 5 historical runs for meaningful patterns
- **Output:** `coordination/pattern_insights.json`

## Platform Support

- ✅ Linux/macOS (bash)
- ✅ Windows (PowerShell)

## Related Skills

- **velocity-tracker** - Provides historical metrics input
- **quality-dashboard** - Uses pattern insights for predictions

## Example Patterns

**Real-world patterns detected:**
```
Pattern: database_migrations_underestimated
Confidence: 0.88
Occurrences: 15/17 database tasks
Recommendation: Use 2.5x multiplier for DB tasks

Pattern: friday_deployments_risky
Confidence: 0.92
Occurrences: 11/12 Friday deploys had issues
Recommendation: Avoid Friday deployments

Pattern: parallel_mode_diminishing_returns
Confidence: 0.81
Occurrences: 8/10 runs with >3 developers
Recommendation: Cap parallelism at 3 developers
```
