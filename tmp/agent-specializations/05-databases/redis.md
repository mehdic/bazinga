---
name: redis
type: database
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Redis Engineering Expertise

## Specialist Profile
Redis specialist building high-performance caches and data stores. Expert in data structures, caching patterns, and pub/sub.

## Implementation Guidelines

### Caching Patterns

```typescript
// services/cache.ts
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

export async function getOrSet<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds = 3600
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const fresh = await fetcher();
  await redis.setex(key, ttlSeconds, JSON.stringify(fresh));
  return fresh;
}

// Cache-aside pattern
export async function getUser(id: string): Promise<User | null> {
  return getOrSet(`user:${id}`, () => db.users.findById(id), 300);
}

// Invalidation
export async function invalidateUser(id: string): Promise<void> {
  await redis.del(`user:${id}`);
}
```

### Data Structures

```typescript
// Rate limiting with sliding window
export async function checkRateLimit(
  userId: string,
  limit: number,
  windowSeconds: number
): Promise<boolean> {
  const key = `ratelimit:${userId}`;
  const now = Date.now();
  const windowStart = now - windowSeconds * 1000;

  const pipeline = redis.pipeline();
  pipeline.zremrangebyscore(key, 0, windowStart);
  pipeline.zadd(key, now, `${now}`);
  pipeline.zcard(key);
  pipeline.expire(key, windowSeconds);

  const results = await pipeline.exec();
  const count = results?.[2]?.[1] as number;
  return count <= limit;
}

// Leaderboard
export async function updateScore(userId: string, score: number): Promise<void> {
  await redis.zadd('leaderboard', score, userId);
}

export async function getTopUsers(count: number): Promise<string[]> {
  return redis.zrevrange('leaderboard', 0, count - 1, 'WITHSCORES');
}

// Session storage
export async function setSession(
  sessionId: string,
  data: SessionData,
  ttl = 86400
): Promise<void> {
  await redis.hset(`session:${sessionId}`, data);
  await redis.expire(`session:${sessionId}`, ttl);
}
```

### Pub/Sub

```typescript
// Publisher
export async function publishEvent(channel: string, event: unknown): Promise<void> {
  await redis.publish(channel, JSON.stringify(event));
}

// Subscriber
const subscriber = redis.duplicate();
subscriber.subscribe('user-events', (err) => {
  if (err) console.error('Subscribe error:', err);
});

subscriber.on('message', (channel, message) => {
  const event = JSON.parse(message);
  handleEvent(channel, event);
});
```

### Distributed Locking

```typescript
// Redlock pattern
export async function withLock<T>(
  key: string,
  fn: () => Promise<T>,
  ttlMs = 10000
): Promise<T> {
  const lockKey = `lock:${key}`;
  const lockValue = crypto.randomUUID();

  const acquired = await redis.set(lockKey, lockValue, 'PX', ttlMs, 'NX');
  if (!acquired) throw new Error('Could not acquire lock');

  try {
    return await fn();
  } finally {
    // Release only if we own the lock
    const script = `
      if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
      end
      return 0
    `;
    await redis.eval(script, 1, lockKey, lockValue);
  }
}
```

## Patterns to Avoid
- ❌ Storing large objects (>100KB)
- ❌ Using KEYS in production
- ❌ Missing TTL on cache entries
- ❌ Single point of failure

## Verification Checklist
- [ ] Appropriate data structures
- [ ] TTL on all cache entries
- [ ] Connection pooling
- [ ] Error handling for cache misses
- [ ] Lua scripts for atomic operations
