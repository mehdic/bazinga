---
name: devops-sre
type: domain
priority: 3
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# DevOps/SRE Engineering Expertise

## Specialist Profile
DevOps/SRE specialist building reliable systems. Expert in SLOs, error budgets, incident management, and continuous delivery.

---

## Patterns to Follow

### SLO Definition (2025)
- **Availability SLO**: `99.9%` = 43 minutes/month downtime budget
- **Latency SLO**: P99 under target (e.g., 200ms)
- **30-day rolling window**: Standard measurement period
- **SLI = measurement**: What you actually measure
- **SLO = target**: What you promise
- **SLA = contract**: Business commitment with consequences

### Error Budget Management
- **Budget = 100% - SLO**: 99.9% SLO = 0.1% error budget
- **Green zone (0-50%)**: Normal development velocity
- **Yellow zone (50-80%)**: Increased reliability focus
- **Red zone (>80%)**: Feature freeze, reliability only
- **Budget exhausted**: Code freeze, mandatory postmortems
- **Budget gates in CI/CD**: Block deploys when budget low

### Multi-Window Alerting
- **Fast burn**: 5% budget in 1 hour → page immediately
- **Slow burn**: 10% budget in 6 hours → page
- **Long window**: Error budget trending → ticket
- **Avoid symptom-based**: Alert on SLO violations, not symptoms
- **Reduce noise**: Fewer, actionable alerts

### Incident Management
- **Severity levels**: SEV1 (critical) to SEV4 (minor)
- **Incident commander**: Single owner during incident
- **War room**: Immediate communication channel
- **Status page**: Customer communication
- **Timeline tracking**: Log all actions with timestamps
- **Blameless postmortems**: Focus on systems, not people

### Runbooks
- **Symptom description**: What the alert looks like
- **Investigation steps**: Ordered troubleshooting
- **Remediation actions**: Copy-paste commands
- **Escalation path**: Who to contact
- **Rollback procedures**: Quick recovery steps
- **Keep updated**: Review after each incident

### Deployment Safety
- **Canary deployments**: 1-5% traffic first
- **Progressive rollout**: Increase traffic gradually
- **Automated rollback**: On SLO violation
- **Feature flags**: Decouple deploy from release
- **Blue-green**: Instant rollback capability

### Chaos Engineering (2025)
- **Game days**: Scheduled failure injection
- **Steady state hypothesis**: Define normal behavior
- **Minimize blast radius**: Start small, expand
- **Auto-remediation tests**: Verify recovery works
<!-- version: litmuschaos >= 3.0 -->
- **LitmusChaos**: Kubernetes-native chaos engineering
- **ChaosHub**: Community experiment library
<!-- version: gremlin >= 2.0 -->
- **Gremlin**: Managed chaos as a service
- **Scenarios**: Pre-built failure scenarios

---

## Patterns to Avoid

### SLO Anti-Patterns
- ❌ **100% availability target**: Impossible, blocks development
- ❌ **Too many SLOs**: 3-5 per service maximum
- ❌ **SLO without budget policy**: No action on violations
- ❌ **Ignoring error budget**: Velocity over reliability

### Alerting Anti-Patterns
- ❌ **Alert on everything**: Alert fatigue
- ❌ **No actionable alerts**: "Something is wrong"
- ❌ **Missing runbooks**: Alerts without remediation
- ❌ **Single threshold**: No multi-window burning

### Incident Anti-Patterns
- ❌ **Blame culture**: People hide problems
- ❌ **No postmortems**: Same incidents repeat
- ❌ **Missing timeline**: Can't reconstruct events
- ❌ **Hero culture**: Single person always fixes

### Deployment Anti-Patterns
- ❌ **Big bang deployments**: All-or-nothing risk
- ❌ **Friday deploys**: No support during issues
- ❌ **No rollback plan**: Stuck with bad code
- ❌ **Manual deployments**: Inconsistent, error-prone

---

## Verification Checklist

### SLO & Budgets
- [ ] SLOs defined (availability, latency)
- [ ] Error budget calculated and tracked
- [ ] Budget policy documented (green/yellow/red zones)
- [ ] CI/CD gates on budget status

### Alerting
- [ ] Multi-window burn rate alerts
- [ ] Runbooks for all alerts
- [ ] On-call rotation defined
- [ ] Escalation paths documented

### Incident Response
- [ ] Incident severity levels defined
- [ ] Commander role assigned
- [ ] Communication channels ready
- [ ] Postmortem template available

### Deployment
- [ ] Canary/progressive rollouts enabled
- [ ] Automated rollback on SLO breach
- [ ] Feature flags infrastructure
- [ ] Deployment frequency tracked

### Observability
- [ ] SLIs measured and dashboarded
- [ ] Error budget burn visible
- [ ] Distributed tracing enabled
- [ ] Log aggregation working

---

## Code Patterns (Reference)

### SLO Definition (YAML)
- **Availability**: `sli: { good: 'status!~"5.."', total: 'requests_total' }, target: 99.9%, window: 30d`
- **Latency**: `sli: { good: 'duration_bucket{le="0.2"}', total: 'duration_count' }, target: 99%`

### Prometheus Alert (Burn Rate)
<!-- version: prometheus >= 2.40 -->
- **Fast burn**: `expr: error_rate > 14.4 * (1 - 0.999)`, `for: 5m`
- **Labels**: `severity: critical`
- **Annotations**: `summary`, `runbook_url`
<!-- version: prometheus >= 2.47 -->
- **Native histograms**: Improved memory efficiency
<!-- version: opentelemetry >= 1.0 -->
- **OTLP export**: OpenTelemetry protocol support

### Error Budget Calculation
- **Monthly budget**: `43200 minutes × (1 - SLO)` = minutes of allowed downtime
- **Remaining**: `budget - consumed_error_minutes`

### Incident Declaration
- **Create**: Incident ID, severity, title, commander, status
- **Timeline**: Append `{ time, event }` for each action
- **Notify**: Appropriate channels based on severity

