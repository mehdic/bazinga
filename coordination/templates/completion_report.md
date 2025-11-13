# Completion Report Template

## Tier 2: Detailed Report (Save to file)

Generate report filename:
```
bazinga/reports/session_{YYYYMMDD_HHMMSS}.md
```

Query dashboard snapshot from database (contains all metrics):
```
bazinga-db, please provide dashboard snapshot:

Session ID: [current session_id]
```

Then invoke:
```
Skill(command: "bazinga-db")
```

The snapshot contains:
- pm_state, orch_state, task_groups
- token_usage, recent_logs
- All skill outputs

Write detailed markdown report with sections:
- Session Summary (mode, duration, groups)
- Quality Metrics (security, coverage, lint, build)
- Efficiency Metrics (approval rate, escalations)
- Task Groups Breakdown (iterations per group)
- Skills Usage (which skills ran, outputs)
- Anomalies Detected (if any)
- Token Usage & Cost Estimate

---

## Tier 1: Concise Report (Display to user)

Keep under 30 lines:

```markdown
═══════════════════════════════════════════════════════════
✅ BAZINGA - Orchestration Complete!
═══════════════════════════════════════════════════════════

## Summary

**Mode**: {mode} ({num_developers} developer(s))
**Duration**: {duration_minutes} minutes
**Groups**: {total_groups}/{total_groups} completed ✅
**Token Usage**: ~{total_tokens/1000}K tokens (~${estimated_cost})

## Quality Overview

**Security**: {status} ({summary})
**Coverage**: {status} {avg}% average (target: 80%)
**Lint**: {status} ({summary})
**Build**: {health_status}

## Skills Used

**Skills Invoked**: {count} of 11 available
- **security-scan**: ✅ Success - 0 vulnerabilities found
- **lint-check**: ✅ Success - 12 issues fixed
- **test-coverage**: ✅ Success - 87.5% average coverage

📁 **Detailed results**: See `bazinga/` folder for full JSON outputs

## Efficiency

**First-time approval**: {approval_rate}% ({first_time}/{total} groups)
**Model escalations**: {opus_count} group(s) → Opus at revision 3+
**Scan escalations**: {scan_count} group(s) → advanced at revision 2+

{IF anomalies exist}:
## Attention Required

⚠️ **{anomaly_title}**: {message}
   - {details}
   - Recommendation: {recommendation}

## Detailed Report

📊 **Full metrics and analysis**: `{report_filename}`

═══════════════════════════════════════════════════════════
```

## Status Emoji Legend

- ✅ Green checkmark: All good (0 issues remaining)
- ⚠️ Yellow warning: Some concerns (issues addressed, or minor gaps)
- ❌ Red X: Problems remain (should be rare)

## Examples

```
Security: ✅ All issues addressed (3 found → 3 fixed)
Security: ⚠️ Scan completed with warnings (2 medium issues addressed)
Security: ❌ Critical issues remain (1 critical unresolved)

Coverage: ✅ 87.5% average (target: 80%)
Coverage: ⚠️ 78.2% average (below 80% target)

Lint: ✅ All issues fixed (42 found → 42 fixed)
Lint: ⚠️ 3 warnings remain (5 errors fixed)
```
