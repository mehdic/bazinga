---
name: microservices
type: domain
priority: 3
token_estimate: 550
compatible_with: [developer, senior_software_engineer, tech_lead]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Microservices Architecture Expertise

## Specialist Profile
Microservices specialist designing distributed systems. Expert in service decomposition, communication patterns, resilience, and eventual consistency.

---

## Patterns to Follow

### Circuit Breaker (2025)
- **Thresholds**: 50% error rate, 10 volume minimum
- **Timeouts**: 3-5 seconds for service calls
- **Fallback strategy**: Cache, default value, or graceful degradation
- **Half-open state**: Gradually test recovery
<!-- version: resilience4j >= 2.0 -->
- **Resilience4j for Java/Kotlin**: Modern, lightweight library
- **Modular design**: Separate modules for each pattern
<!-- version: opossum >= 8.0 -->
- **opossum for Node.js**: Promise-based circuit breaker
- **Metrics export**: Prometheus integration

### Saga Pattern
- **Choreography**: Services publish events, others react
- **Orchestration**: Central coordinator directs transactions
- **Compensating transactions**: Rollback actions for each step
- **Idempotent operations**: Safe retry on failure
- **Saga state tracking**: Persist saga execution state

### Event Sourcing
- **Events as source of truth**: Immutable event log
- **Event stores**: Kafka, EventStoreDB, or database
- **Snapshots for performance**: Periodic state materialization
- **Versioned events**: Schema evolution support
- **Replay capability**: Rebuild state from events

### CQRS (Command Query Responsibility Segregation)
- **Separate read/write models**: Optimize each independently
- **Eventual consistency**: Read models updated asynchronously
- **Materialized views**: Denormalized for query performance
- **Use with event sourcing**: Natural combination
- **Independent scaling**: Scale reads vs writes differently

### Outbox Pattern
- **Transactional outbox**: Store events with business data
- **Relay process**: Publish events from outbox
- **At-least-once delivery**: Handle duplicates downstream
- **Polling or CDC**: Debezium for change data capture
- **Guaranteed delivery**: No lost events

### Service Mesh (2025)
- **mTLS automatic**: Zero-trust networking
- **Observability built-in**: Traces, metrics, logs
- **Traffic management**: Canary, A/B, circuit breaking
- **Service-to-service auth**: SPIFFE/SPIRE identities
<!-- version: istio >= 1.18 -->
- **Istio**: Sidecar-based service mesh
- **Ambient mode**: Sidecarless option for reduced overhead
<!-- version: linkerd >= 2.14 -->
- **Linkerd**: Lightweight, Rust-based mesh
- **Multi-cluster**: Cross-cluster service discovery

### Bulkhead Pattern
- **Isolated thread pools**: Per downstream service
- **Connection limits**: Prevent cascade failures
- **Resource isolation**: CPU, memory per service
- **Fail fast**: Don't wait for slow services
- **Graceful degradation**: Partial functionality over full failure

---

## Patterns to Avoid

### Communication Anti-Patterns
- ❌ **Synchronous chains**: Service A → B → C → D synchronously
- ❌ **Missing circuit breakers**: Single failure cascades
- ❌ **No timeouts**: Hanging connections exhaust resources
- ❌ **Distributed transactions (2PC)**: Use Saga instead

### Data Anti-Patterns
- ❌ **Shared databases**: Tight coupling, schema conflicts
- ❌ **Join across services**: Query N services for one request
- ❌ **Synchronous data replication**: Use events
- ❌ **No data ownership**: Unclear who owns what

### Design Anti-Patterns
- ❌ **Distributed monolith**: Microservices with tight coupling
- ❌ **Too fine-grained**: Nano-services with high coordination
- ❌ **No domain boundaries**: Services split arbitrarily
- ❌ **Shared libraries for business logic**: Hidden coupling

### Event Anti-Patterns
- ❌ **Events without idempotency**: Duplicate processing
- ❌ **Ordering assumptions**: Events may arrive out of order
- ❌ **Fat events**: Include IDs, not full entities
- ❌ **No event versioning**: Schema breaks consumers

---

## Verification Checklist

### Resilience
- [ ] Circuit breakers on all external calls
- [ ] Timeouts configured (3-5 seconds)
- [ ] Fallback strategies defined
- [ ] Bulkhead isolation for critical paths

### Data Consistency
- [ ] Saga pattern for distributed transactions
- [ ] Outbox pattern for reliable events
- [ ] Idempotent event handlers
- [ ] Eventual consistency understood

### Service Design
- [ ] Clear domain boundaries
- [ ] Single database per service
- [ ] Async communication preferred
- [ ] API contracts versioned

### Observability
- [ ] Distributed tracing (correlation IDs)
- [ ] Health check endpoints
- [ ] Metrics exported (RED method)
- [ ] Centralized logging

---

## Code Patterns (Reference)

### Circuit Breaker (Resilience4j)
- **Config**: `CircuitBreakerConfig.custom().failureRateThreshold(50).waitDurationInOpenState(Duration.ofSeconds(30)).build()`
- **Use**: `circuitBreaker.executeSupplier(() -> callRemoteService())`

### Circuit Breaker (opossum)
- **Config**: `new CircuitBreaker(fn, { timeout: 3000, errorThresholdPercentage: 50, resetTimeout: 30000 })`
- **Events**: `breaker.on('open', () => ...); breaker.on('fallback', () => ...)`

### Saga Orchestration
- **Step**: `{ execute: () => service.create(), compensate: () => service.rollback() }`
- **Execute**: Loop steps, on failure compensate in reverse

### Outbox Pattern
- **Insert**: `tx.outbox.create({ aggregateId, eventType, payload })` in same transaction
- **Relay**: Poll outbox, publish to broker, mark processed

### Event Structure
- **Format**: `{ id, type, aggregateId, timestamp, version, payload }`

