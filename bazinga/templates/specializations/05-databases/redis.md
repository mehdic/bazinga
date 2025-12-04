---
name: redis
type: database
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Redis Engineering Expertise

## Specialist Profile
Redis specialist building high-performance caches and data stores. Expert in data structures, caching patterns, and distributed systems.

---

## Patterns to Follow

### Caching Patterns
- **Cache-aside (lazy loading)**: Check cache, fetch on miss, populate
- **Write-through**: Write to cache and DB synchronously
- **Write-behind (write-back)**: Write to cache, async to DB
- **Cache prefetching**: Pre-populate before needed
- **Multi-tier caching**: L1 (memory) → L2 (Redis) → DB

### TTL Strategies
- **Fixed TTL**: All keys expire after set time
- **Sliding TTL**: Reset on access
- **Randomized TTL**: Add jitter to prevent stampede
- **Never forget TTL**: Set on ALL cache keys
- **allkeys-lru policy**: For general caching

### Data Structures
- **Strings**: Simple key-value, counters
- **Hashes**: Object storage (20% less memory than strings)
- **Lists**: Queues, recent items, feeds
- **Sets**: Unique values, relationships
- **Sorted Sets**: Leaderboards, time-series, rate limiting
- **Streams**: Event streaming, message queues

### Performance Optimization
- **Pipelining**: Batch multiple commands
- **Connection pooling**: Reuse connections
- **Lua scripts**: Atomic complex operations
- **SCAN over KEYS**: Non-blocking iteration
- **Appropriate data structures**: Hashes for objects, not JSON strings

### Distributed Patterns
- **Redis Cluster**: Horizontal scaling, 70% throughput boost
- **Redlock**: Distributed locking across nodes
- **Pub/Sub**: Real-time event broadcast
- **Streams**: Reliable message queue with consumer groups
<!-- version: redis >= 6.0 -->
- **ACLs**: Fine-grained access control
- **Client-side caching**: RESP3 protocol support
<!-- version: redis >= 6.2 -->
- **GETDEL/GETEX**: Atomic get-and-delete/get-and-expire
- **COPY command**: Duplicate keys without GET/SET
<!-- version: redis >= 7.0 -->
- **Functions**: Server-side Lua function library
- **Sharded Pub/Sub**: Scalable pub/sub in cluster mode
- **Multiple AOF files**: Better persistence performance
<!-- version: redis >= 7.2 -->
- **Improved cluster**: Hash slot migration improvements

---

## Patterns to Avoid

### Cache Anti-Patterns
- ❌ **Missing TTL on cache entries**: Memory leak
- ❌ **Cache as primary data store**: Volatile, not durable
- ❌ **Overloading with full datasets**: Cache hot data only
- ❌ **Same TTL for everything**: Cache stampede risk
- ❌ **Ignoring cache misses in metrics**: Hidden latency

### Command Anti-Patterns
- ❌ **KEYS in production**: Blocks all operations
- ❌ **Large objects (>100KB)**: Latency spikes
- ❌ **Storing JSON when hash works**: Memory waste
- ❌ **Sync operations without timeout**: Hangs on network issues
- ❌ **DEL on large collections**: Use UNLINK (async)

### Architecture Anti-Patterns
- ❌ **Single point of failure**: Use Sentinel or Cluster
- ❌ **No connection pooling**: Connection overhead
- ❌ **Missing persistence config**: Data loss on restart
- ❌ **Blocking operations on main thread**: Use async clients

### Key Anti-Patterns
- ❌ **No key naming convention**: Chaos
- ❌ **Extremely long keys**: Memory waste
- ❌ **No namespace prefixes**: Key collisions
- ❌ **PII in keys**: Security/compliance risk

---

## Verification Checklist

### Caching
- [ ] TTL on all cache entries
- [ ] Appropriate eviction policy
- [ ] Cache invalidation strategy
- [ ] Stampede prevention (jittered TTL)

### Performance
- [ ] Pipelining for batch operations
- [ ] Connection pooling configured
- [ ] Lua scripts for atomic operations
- [ ] SCAN used, not KEYS

### Data Structures
- [ ] Hashes for object storage
- [ ] Sorted sets for leaderboards/rate limits
- [ ] Appropriate structure per use case
- [ ] Key naming convention

### Reliability
- [ ] Sentinel or Cluster for HA
- [ ] Persistence configured (RDB/AOF)
- [ ] Memory limits set
- [ ] Monitoring in place (redis-cli INFO)

---

## Code Patterns (Reference)

### Caching
- **Cache-aside**: `const cached = await redis.get(key); if (cached) return JSON.parse(cached); const fresh = await fetch(); await redis.setex(key, ttl, JSON.stringify(fresh));`
- **Invalidation**: `await redis.del(cacheKey);` or `await redis.unlink(cacheKey);`

### Data Structures
- **Hash**: `redis.hset('user:123', { name: 'John', email: '...' }); redis.hgetall('user:123');`
- **Sorted set**: `redis.zadd('leaderboard', score, odId); redis.zrevrange('leaderboard', 0, 9);`
- **Rate limit**: `redis.pipeline().zremrangebyscore(key, 0, windowStart).zadd(key, now, now).zcard(key).expire(key, windowSec).exec();`

### Locking
- **Acquire**: `redis.set(lockKey, lockValue, 'PX', ttlMs, 'NX')`
- **Release (Lua)**: `if redis.call("get", KEYS[1]) == ARGV[1] then return redis.call("del", KEYS[1]) end`

### Pub/Sub
- **Publish**: `redis.publish(channel, JSON.stringify(event))`
- **Subscribe**: `subscriber.subscribe(channel); subscriber.on('message', handler)`

