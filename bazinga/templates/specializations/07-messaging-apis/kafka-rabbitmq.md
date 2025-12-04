---
name: kafka-rabbitmq
type: messaging
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Kafka/RabbitMQ Messaging Expertise

## Specialist Profile
Message broker specialist building event-driven systems. Expert in pub/sub patterns, reliability, and event streaming.

---

## Patterns to Follow

### Message Design
- **Unique message IDs**: For idempotency
- **Correlation IDs**: Trace across services
- **Event type in header**: Route without parsing body
- **Schema versioning**: Avro, Protobuf, JSON Schema
- **Timestamp in message**: For ordering, debugging

### Kafka Patterns
- **Idempotent producer**: `idempotent: true` (exactly-once)
- **Consumer groups**: Parallel consumption
- **Partitioning by key**: Order guarantees per key
- **Compression**: GZIP, Snappy, LZ4
- **Exactly-once semantics**: Transactions when needed
<!-- version: kafka >= 3.0 -->
- **KRaft mode**: ZooKeeper-free consensus
- **Tiered storage**: Offload old data to object storage
<!-- version: kafka >= 3.5 -->
- **KRaft production ready**: Full ZooKeeper replacement
<!-- version: kafka >= 3.7 -->
- **Early access mode**: New consumer improvements

### RabbitMQ Patterns
- **Durable exchanges/queues**: Survive restarts
- **Persistent messages**: `persistent: true`
- **Topic exchanges**: Flexible routing
- **Dead letter exchanges**: Failed message handling
- **Prefetch for backpressure**: `channel.prefetch(10)`

### Consumer Patterns
- **Idempotent processing**: Handle duplicates gracefully
- **Graceful shutdown**: Finish in-flight, stop consuming
- **Retry with backoff**: Exponential delays
- **Dead letter queue**: After max retries
- **Circuit breaker**: For downstream dependencies

### Ordering & Delivery
- **Kafka**: Order per partition, use key for related events
- **RabbitMQ**: Order per queue (single consumer)
- **At-least-once default**: Plan for duplicates
- **Exactly-once**: Idempotent consumers or transactions

### Monitoring
- **Consumer lag**: How far behind
- **Throughput**: Messages/second
- **Error rates**: Dead letters, retries
- **Processing time**: Per message latency

---

## Patterns to Avoid

### Producer Anti-Patterns
- ❌ **Fire-and-forget without acks**: Lost messages
- ❌ **Large messages**: >1MB problematic
- ❌ **No compression**: Bandwidth waste
- ❌ **Blocking on send**: Use async

### Consumer Anti-Patterns
- ❌ **Blocking in handlers**: Reduces throughput
- ❌ **No dead letter handling**: Poison messages block queue
- ❌ **Acking before processing**: Lost on failure
- ❌ **Unbounded retry**: Infinite loops
- ❌ **No backpressure**: Memory exhaustion

### Design Anti-Patterns
- ❌ **Request-reply over queues**: Use HTTP/gRPC for sync
- ❌ **Coupling to message format**: Use schemas
- ❌ **No correlation/trace IDs**: Can't debug flows
- ❌ **Ignoring message order**: When order matters

### Operational Anti-Patterns
- ❌ **No monitoring**: Blind to lag, errors
- ❌ **Missing graceful shutdown**: Lost messages
- ❌ **No retention policy**: Disk exhaustion
- ❌ **Single consumer for critical queue**: No HA

---

## Verification Checklist

### Producer
- [ ] Idempotent production (Kafka)
- [ ] Persistent messages (RabbitMQ)
- [ ] Compression enabled
- [ ] Correlation IDs included

### Consumer
- [ ] Idempotent processing
- [ ] Dead letter queue configured
- [ ] Graceful shutdown
- [ ] Retry with backoff

### Reliability
- [ ] Durable queues/topics
- [ ] Acks configured properly
- [ ] Ordering strategy defined
- [ ] Schema versioning

### Operations
- [ ] Lag monitoring
- [ ] Error rate alerting
- [ ] Retention policies
- [ ] Throughput dashboards

---

## Code Patterns (Reference)

### Kafka Producer
- **Setup**: `producer({ idempotent: true, maxInFlightRequests: 5 })`
- **Send**: `producer.send({ topic, messages: [{ key: userId, value: JSON.stringify(event), headers: { 'event-type': type } }] })`

### Kafka Consumer
- **Setup**: `consumer({ groupId: 'service', sessionTimeout: 30000 })`
- **Run**: `consumer.run({ eachMessage: async ({ message }) => { await process(message); } })`
- **Graceful shutdown**: `process.on('SIGTERM', () => consumer.disconnect())`

### RabbitMQ Publisher
- **Exchange**: `channel.assertExchange('events', 'topic', { durable: true })`
- **Publish**: `channel.publish(exchange, routingKey, Buffer.from(JSON.stringify(event)), { persistent: true })`

### RabbitMQ Consumer
- **Prefetch**: `channel.prefetch(10)`
- **Consume**: `channel.consume(queue, async (msg) => { await process(msg); channel.ack(msg); })`
- **Nack with requeue**: `channel.nack(msg, false, isTransientError)`

### Dead Letter
- **RabbitMQ DLX**: `{ 'x-dead-letter-exchange': 'dlx', 'x-dead-letter-routing-key': 'failed' }`
- **Kafka**: Publish to `topic.DLT` on final failure

