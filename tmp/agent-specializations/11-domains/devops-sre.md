---
name: devops-sre
type: domain
priority: 3
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# DevOps/SRE Engineering Expertise

## Specialist Profile
DevOps/SRE specialist building reliable systems. Expert in CI/CD, infrastructure automation, and incident response.

## Implementation Guidelines

### SLO Definition

```yaml
# slo.yaml
service: user-api
slos:
  - name: availability
    description: "Service responds to requests"
    target: 99.9%
    window: 30d
    sli:
      type: availability
      good_events: "http_requests_total{status!~'5..'}"
      total_events: "http_requests_total"

  - name: latency_p99
    description: "99th percentile latency under 200ms"
    target: 99%
    window: 30d
    sli:
      type: latency
      threshold_ms: 200
      good_events: "http_request_duration_seconds_bucket{le='0.2'}"
      total_events: "http_request_duration_seconds_count"

# Error budget calculation
# Monthly budget: 100% - 99.9% = 0.1%
# 30 days * 24 hours * 60 min = 43,200 minutes
# Error budget = 43,200 * 0.1% = 43.2 minutes of downtime
```

### Alerting Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: user-api
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{service="user-api",status=~"5.."}[5m]))
          / sum(rate(http_requests_total{service="user-api"}[5m]))
          > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: LatencyHigh
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket{service="user-api"}[5m])) by (le)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.service }}"

      - alert: ErrorBudgetBurn
        expr: |
          1 - (
            sum(rate(http_requests_total{service="user-api",status!~"5.."}[1h]))
            / sum(rate(http_requests_total{service="user-api"}[1h]))
          ) > 14.4 * (1 - 0.999)
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Error budget burning too fast"
```

### Runbooks

```markdown
# Runbook: High Error Rate

## Alert: HighErrorRate

### Symptoms
- Error rate > 1% for 5+ minutes
- Users reporting failures

### Investigation Steps
1. Check recent deployments: `kubectl rollout history deployment/user-api`
2. View error logs: `kubectl logs -l app=user-api --since=10m | grep ERROR`
3. Check downstream dependencies:
   - Database: `kubectl exec -it postgres-0 -- pg_isready`
   - Redis: `kubectl exec -it redis-0 -- redis-cli ping`

### Remediation
1. **If recent deployment**: Rollback
   ```bash
   kubectl rollout undo deployment/user-api
   ```
2. **If dependency issue**: Check dependency health
3. **If resource exhaustion**: Scale up
   ```bash
   kubectl scale deployment/user-api --replicas=5
   ```

### Escalation
- After 15 min: Page on-call engineer
- After 30 min: Page engineering manager
```

### Incident Management

```typescript
// incident/manager.ts
interface Incident {
  id: string;
  severity: 'sev1' | 'sev2' | 'sev3';
  title: string;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
  commander: string;
  timeline: TimelineEntry[];
}

class IncidentManager {
  async declare(incident: Omit<Incident, 'id' | 'status' | 'timeline'>): Promise<Incident> {
    const created = await db.incidents.create({
      ...incident,
      status: 'investigating',
      timeline: [{ time: new Date(), event: 'Incident declared' }],
    });

    // Notify appropriate channels
    await slack.postMessage(getIncidentChannel(incident.severity), {
      text: `🚨 ${incident.severity.toUpperCase()}: ${incident.title}`,
      blocks: formatIncidentBlocks(created),
    });

    // Create war room
    if (incident.severity === 'sev1') {
      await zoom.createMeeting(`Incident: ${incident.title}`);
    }

    return created;
  }

  async updateStatus(id: string, status: Incident['status'], note: string): Promise<void> {
    await db.incidents.update(id, {
      status,
      $push: { timeline: { time: new Date(), event: note } },
    });
  }
}
```

## Patterns to Avoid
- ❌ Alerting on symptoms, not causes
- ❌ Missing runbooks
- ❌ No error budgets
- ❌ Manual deployments

## Verification Checklist
- [ ] SLOs defined with error budgets
- [ ] Multi-window alerting
- [ ] Runbooks for all alerts
- [ ] Incident management process
- [ ] Automated rollbacks
