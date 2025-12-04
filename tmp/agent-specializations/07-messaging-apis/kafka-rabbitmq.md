---
name: kafka-rabbitmq
type: messaging
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Kafka/RabbitMQ Messaging Expertise

## Specialist Profile
Message broker specialist building event-driven systems. Expert in pub/sub patterns, event sourcing, and reliable messaging.

## Implementation Guidelines

### Kafka Producer

```typescript
// producers/userEventProducer.ts
import { Kafka, CompressionTypes } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'user-service',
  brokers: process.env.KAFKA_BROKERS!.split(','),
});

const producer = kafka.producer({
  idempotent: true,
  maxInFlightRequests: 5,
});

export async function publishUserEvent(event: UserEvent): Promise<void> {
  await producer.send({
    topic: 'user-events',
    compression: CompressionTypes.GZIP,
    messages: [
      {
        key: event.userId,
        value: JSON.stringify(event),
        headers: {
          'event-type': event.type,
          'correlation-id': event.correlationId,
          timestamp: Date.now().toString(),
        },
      },
    ],
  });
}
```

### Kafka Consumer

```typescript
// consumers/userEventConsumer.ts
const consumer = kafka.consumer({
  groupId: 'notification-service',
  sessionTimeout: 30000,
  heartbeatInterval: 3000,
});

export async function startConsumer() {
  await consumer.connect();
  await consumer.subscribe({ topic: 'user-events', fromBeginning: false });

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const event = JSON.parse(message.value!.toString()) as UserEvent;

      try {
        await processEvent(event);
        // Offset committed automatically on success
      } catch (error) {
        logger.error({ error, event }, 'Failed to process event');
        // Dead letter or retry logic
        await publishToDeadLetter(event, error);
      }
    },
  });
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  await consumer.disconnect();
});
```

### RabbitMQ Publisher

```typescript
// publishers/orderPublisher.ts
import amqp from 'amqplib';

let channel: amqp.Channel;

export async function initRabbitMQ() {
  const connection = await amqp.connect(process.env.RABBITMQ_URL!);
  channel = await connection.createChannel();

  await channel.assertExchange('orders', 'topic', { durable: true });
  await channel.assertQueue('order-notifications', { durable: true });
  await channel.bindQueue('order-notifications', 'orders', 'order.*');
}

export async function publishOrderEvent(event: OrderEvent): Promise<void> {
  const routingKey = `order.${event.type}`;

  channel.publish('orders', routingKey, Buffer.from(JSON.stringify(event)), {
    persistent: true,
    contentType: 'application/json',
    headers: {
      'x-correlation-id': event.correlationId,
    },
  });
}
```

### RabbitMQ Consumer

```typescript
// consumers/orderConsumer.ts
export async function startOrderConsumer() {
  await channel.prefetch(10);

  channel.consume('order-notifications', async (msg) => {
    if (!msg) return;

    const event = JSON.parse(msg.content.toString()) as OrderEvent;

    try {
      await processOrderEvent(event);
      channel.ack(msg);
    } catch (error) {
      logger.error({ error, event }, 'Failed to process order event');
      // Requeue on transient errors, reject on permanent
      const requeue = isTransientError(error);
      channel.nack(msg, false, requeue);
    }
  });
}
```

## Patterns to Avoid
- ❌ Fire-and-forget without acks
- ❌ Blocking in message handlers
- ❌ Missing dead letter queues
- ❌ Unbounded consumers

## Verification Checklist
- [ ] Idempotent consumers
- [ ] Dead letter handling
- [ ] Graceful shutdown
- [ ] Message ordering strategy
- [ ] Monitoring lag/throughput
