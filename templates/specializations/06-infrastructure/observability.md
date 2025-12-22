---
name: observability
type: infrastructure
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Observability Engineering Expertise

## Specialist Profile
Observability specialist implementing the three pillars. Expert in metrics, structured logging, and distributed tracing.

---

## Patterns to Follow

### Structured Logging
- **JSON format**: Machine-parseable
- **Consistent fields**: service, version, environment, timestamp
- **Request context**: requestId, userId, traceId
- **Log levels semantically**: debug, info, warn, error
- **Child loggers**: Add context progressively

### Metrics (RED/USE Methods)
- **RED for services**: Rate, Errors, Duration
- **USE for resources**: Utilization, Saturation, Errors
- **Histograms for latency**: Buckets for percentiles
- **Counters for totals**: Monotonically increasing
- **Labels carefully**: Low cardinality only

### Distributed Tracing
- **OpenTelemetry**: Vendor-neutral standard
- **Auto-instrumentation**: HTTP, DB, cache automatic
- **Manual spans for business**: Key operations
- **Context propagation**: Across service boundaries
- **Span attributes**: Add business context
<!-- version: opentelemetry >= 1.0 -->
- **Stable APIs**: Metrics and traces stable
- **Semantic conventions**: Standardized attribute names
<!-- version: opentelemetry >= 1.20 -->
- **Logs support**: Logs as first-class signals
- **Profiling integration**: Continuous profiling data
<!-- version: opentelemetry >= 1.30 -->
- **Improved auto-instrumentation**: Better framework coverage
- **OTLP/HTTP default**: Simpler deployment than gRPC

### Health Endpoints
- **Liveness (/health)**: Is process alive?
- **Readiness (/ready)**: Can serve traffic?
- **Startup probe**: For slow-starting apps
- **Dependency checks**: DB, cache connectivity

### Alerting
- **Alert on symptoms**: User impact, not causes
- **SLO-based alerts**: Error budget consumption
- **Runbooks**: Link in alert description
- **Reduce noise**: High signal, low fatigue
- **Escalation paths**: On-call rotations

### Dashboards
- **Service overview**: Golden signals (latency, traffic, errors, saturation)
- **Drill-down capability**: Top-level → component → instance
- **Business metrics**: Revenue, signups, conversions
- **Comparisons**: Current vs. baseline/yesterday/last week

---

## Patterns to Avoid

### Logging Anti-Patterns
- ❌ **Unstructured log messages**: Hard to query
- ❌ **Missing request correlation**: Can't trace flows
- ❌ **PII in logs**: Compliance violation
- ❌ **Excessive debug in prod**: Cost and noise
- ❌ **Log and throw exception**: Double logging

### Metrics Anti-Patterns
- ❌ **Unbounded cardinality labels**: userId, orderId as labels
- ❌ **Missing units in names**: `_seconds`, `_bytes` suffix
- ❌ **Gauges for request counts**: Use counters
- ❌ **No histograms for latency**: Can't calculate percentiles
- ❌ **Too many metrics**: Focus on actionable

### Tracing Anti-Patterns
- ❌ **Not propagating context**: Broken traces
- ❌ **Too much span detail**: High cost, noise
- ❌ **Missing business attributes**: Can't filter by user/order
- ❌ **Sampling without strategy**: Miss important traces

### Alerting Anti-Patterns
- ❌ **Alert on causes not symptoms**: Low signal
- ❌ **No runbook attached**: On-call confusion
- ❌ **Too many alerts**: Alert fatigue
- ❌ **Static thresholds only**: Missing anomalies

---

## Verification Checklist

### Logging
- [ ] JSON structured format
- [ ] Request ID propagation
- [ ] Appropriate log levels
- [ ] No PII in logs

### Metrics
- [ ] RED metrics for services
- [ ] Histogram for latency
- [ ] Low-cardinality labels
- [ ] /metrics endpoint exposed

### Tracing
- [ ] OpenTelemetry configured
- [ ] Auto-instrumentation enabled
- [ ] Manual spans for key ops
- [ ] Context propagation verified

### Health
- [ ] Liveness endpoint
- [ ] Readiness endpoint
- [ ] Dependency checks
- [ ] Graceful degradation

---

## Code Patterns (Reference)

### Logging (pino)
- **Setup**: `const logger = pino({ level: 'info', base: { service: 'api', version: '1.0' } })`
- **Child logger**: `const reqLogger = logger.child({ requestId, path })`
- **Usage**: `logger.info({ userId, action: 'login' }, 'User logged in')`

### Metrics (Prometheus)
- **Histogram**: `new Histogram({ name: 'http_request_duration_seconds', labelNames: ['method', 'route', 'status'], buckets: [0.01, 0.1, 0.5, 1] })`
- **Counter**: `new Counter({ name: 'http_requests_total', labelNames: ['method', 'status'] })`
- **Middleware**: `const end = histogram.startTimer(); res.on('finish', () => end({ method, status }))`

### Tracing (OpenTelemetry)
- **Setup**: `new NodeSDK({ serviceName: 'api', traceExporter: new OTLPTraceExporter(), instrumentations: [getNodeAutoInstrumentations()] })`
- **Manual span**: `tracer.startActiveSpan('processOrder', async (span) => { span.setAttribute('order.id', id); ... span.end(); })`

### Health Checks
- **Liveness**: `GET /health → { status: 'ok' }`
- **Readiness**: `GET /ready → { status: 'ready', checks: { db: 'ok', redis: 'ok' } }`

