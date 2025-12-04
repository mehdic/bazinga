---
name: microservices
type: domain
priority: 3
token_estimate: 450
compatible_with: [developer, senior_software_engineer, tech_lead]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Microservices Architecture Expertise

## Specialist Profile
Microservices specialist designing distributed systems. Expert in service decomposition, communication patterns, and resilience.

## Implementation Guidelines

### Service Communication

```typescript
// Circuit Breaker Pattern
import CircuitBreaker from 'opossum';

const breaker = new CircuitBreaker(
  async (userId: string) => {
    const response = await fetch(`${USER_SERVICE_URL}/users/${userId}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },
  {
    timeout: 3000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
    volumeThreshold: 10,
  }
);

breaker.on('open', () => logger.warn('Circuit opened'));
breaker.on('halfOpen', () => logger.info('Circuit half-open'));
breaker.on('close', () => logger.info('Circuit closed'));

export async function getUser(userId: string): Promise<User | null> {
  try {
    return await breaker.fire(userId);
  } catch (error) {
    if (breaker.opened) {
      // Return cached/default value during outage
      return cache.get(`user:${userId}`) ?? null;
    }
    throw error;
  }
}
```

### Event-Driven Communication

```typescript
// events/userEvents.ts
interface DomainEvent<T> {
  id: string;
  type: string;
  aggregateId: string;
  timestamp: Date;
  version: number;
  payload: T;
}

// Outbox pattern for reliable publishing
async function createUserWithEvent(data: CreateUserInput): Promise<User> {
  return db.transaction(async (tx) => {
    // Create user
    const user = await tx.users.create(data);

    // Store event in outbox (same transaction)
    await tx.outbox.create({
      aggregateId: user.id,
      eventType: 'user.created',
      payload: JSON.stringify({
        userId: user.id,
        email: user.email,
      }),
    });

    return user;
  });
}

// Outbox processor (separate process)
async function processOutbox() {
  const events = await db.outbox.findUnprocessed({ limit: 100 });

  for (const event of events) {
    try {
      await messageBroker.publish(event.eventType, event.payload);
      await db.outbox.markProcessed(event.id);
    } catch (error) {
      logger.error({ error, eventId: event.id }, 'Failed to publish event');
    }
  }
}
```

### Service Discovery

```typescript
// discovery/serviceRegistry.ts
interface ServiceInstance {
  id: string;
  name: string;
  host: string;
  port: number;
  healthCheck: string;
  metadata: Record<string, string>;
}

class ServiceRegistry {
  private instances = new Map<string, ServiceInstance[]>();

  async discover(serviceName: string): Promise<ServiceInstance[]> {
    // From Consul/etcd/K8s DNS
    const instances = await consul.health.service(serviceName);
    this.instances.set(serviceName, instances);
    return instances;
  }

  selectInstance(serviceName: string): ServiceInstance {
    const instances = this.instances.get(serviceName) ?? [];
    if (!instances.length) throw new Error(`No instances for ${serviceName}`);

    // Round-robin or weighted selection
    return instances[Math.floor(Math.random() * instances.length)];
  }
}

// Client-side load balancing
async function callService(serviceName: string, path: string) {
  const instance = registry.selectInstance(serviceName);
  return fetch(`http://${instance.host}:${instance.port}${path}`);
}
```

### Saga Pattern

```typescript
// sagas/orderSaga.ts
class OrderSaga {
  private steps: SagaStep[] = [];

  async execute(): Promise<void> {
    const executedSteps: SagaStep[] = [];

    for (const step of this.steps) {
      try {
        await step.execute();
        executedSteps.push(step);
      } catch (error) {
        // Compensate in reverse order
        for (const completed of executedSteps.reverse()) {
          await completed.compensate();
        }
        throw error;
      }
    }
  }
}

// Usage
const saga = new OrderSaga()
  .addStep({
    execute: () => orderService.create(order),
    compensate: () => orderService.cancel(order.id),
  })
  .addStep({
    execute: () => paymentService.charge(payment),
    compensate: () => paymentService.refund(payment.id),
  })
  .addStep({
    execute: () => inventoryService.reserve(items),
    compensate: () => inventoryService.release(items),
  });

await saga.execute();
```

## Patterns to Avoid
- ❌ Synchronous chains across services
- ❌ Shared databases
- ❌ Missing circuit breakers
- ❌ Tight coupling between services

## Verification Checklist
- [ ] Circuit breakers for external calls
- [ ] Outbox pattern for events
- [ ] Saga for distributed transactions
- [ ] Service discovery
- [ ] Idempotent operations
