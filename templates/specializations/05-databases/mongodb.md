---
name: mongodb
type: database
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# MongoDB Engineering Expertise

## Specialist Profile
MongoDB specialist designing document databases. Expert in schema design patterns, aggregation pipelines, and performance tuning.

---

## Patterns to Follow

### Schema Design Principles
- **Data accessed together, stored together**: Embed related data
- **Favor embedding over referencing**: For 1:1 and 1:few
- **Reference for 1:many unbounded**: Avoid 16MB limit
- **Subset Pattern**: Frequently accessed subset embedded
- **Extended Reference**: Denormalize frequently joined fields
- **Schema versioning**: Add `schemaVersion` field

### Design Patterns
- **Computed Pattern**: Pre-compute expensive aggregations
- **Bucket Pattern**: Time-series, IoT data in buckets
- **Outlier Pattern**: Separate treatment for edge cases
- **Attribute Pattern**: Polymorphic attributes as array
- **Polymorphic Pattern**: Different schemas in same collection

### Index Strategy
- **Compound indexes**: Match query patterns
- **Covered queries**: Index contains all fields
- **Index order matters**: Match query filter/sort order
- **Sparse indexes**: For optional fields
- **TTL indexes**: Auto-expire documents
- **Text indexes**: Full-text search

### Aggregation Best Practices
- **$match early**: Filter before heavy operations
- **$project to reduce size**: Before $lookup
- **$lookup with indexes**: Ensure foreign key indexed
- **Aggregation explain**: Check execution plan
- **allowDiskUse for large**: When exceeding memory
<!-- version: mongodb >= 5.0 -->
- **Time-series collections**: Native time-series support
- **Live resharding**: Redistribute data without downtime
- **Versioned API**: Stable API across major versions
<!-- version: mongodb >= 6.0 -->
- **Queryable encryption**: Client-side field-level encryption
- **Cluster synchronization**: Improved cluster sync
<!-- version: mongodb >= 7.0 -->
- **Improved sharding**: Faster balancer, better chunk migrations
- **$percentile aggregation**: Built-in percentile calculation

### Performance
- **Cursor-based pagination**: `_id: { $gt: lastId }` + limit
- **lean() for read-only**: Skip Mongoose hydration
- **bulkWrite for batch**: More efficient than loops
- **Projection**: Select only needed fields
- **Connection pooling**: Appropriate pool size

---

## Patterns to Avoid

### Schema Anti-Patterns
- ❌ **Unbounded arrays**: Will hit 16MB limit
- ❌ **Bloated documents**: Split infrequently accessed data
- ❌ **Massive arrays of references**: Hard to query
- ❌ **Storing data separately without reason**: Loses document benefits
- ❌ **Over-normalizing like SQL**: Embrace embedding

### Query Anti-Patterns
- ❌ **Missing indexes on query fields**: COLLSCAN in explain
- ❌ **Skip-based pagination at scale**: Degrades with offset
- ❌ **Fetching entire documents**: Use projection
- ❌ **N+1 queries**: Use $lookup or embed
- ❌ **Regex without anchor**: `^pattern` uses index, `pattern$` doesn't

### Index Anti-Patterns
- ❌ **Too many indexes**: Slows writes
- ❌ **Wrong compound order**: Doesn't match queries
- ❌ **Indexing low-cardinality**: Boolean fields alone
- ❌ **Missing index on $lookup**: Slow joins

### Performance Anti-Patterns
- ❌ **Large documents over wire**: Project needed fields
- ❌ **Not using lean()**: Unnecessary hydration
- ❌ **Single-document loops**: Use bulkWrite
- ❌ **No connection pooling**: Connection overhead

---

## Verification Checklist

### Schema
- [ ] Embedding vs referencing justified
- [ ] No unbounded arrays
- [ ] Schema version field present
- [ ] Appropriate use of patterns

### Indexes
- [ ] Indexes match query patterns
- [ ] Compound index order correct
- [ ] Explain shows IXSCAN not COLLSCAN
- [ ] Covered queries where possible

### Aggregation
- [ ] $match early in pipeline
- [ ] $project before expensive stages
- [ ] allowDiskUse for large aggregations
- [ ] Explain reviewed

### Performance
- [ ] Cursor-based pagination
- [ ] lean() for read operations
- [ ] bulkWrite for batch operations
- [ ] Connection pool configured

---

## Code Patterns (Reference)

### Schema (Mongoose)
- **Model**: `const userSchema = new Schema({ email: { type: String, unique: true, lowercase: true } }, { timestamps: true });`
- **Compound index**: `userSchema.index({ status: 1, createdAt: -1 });`
- **Text index**: `userSchema.index({ email: 'text', displayName: 'text' });`

### Queries
- **Cursor pagination**: `User.find({ _id: { $gt: lastId } }).sort({ _id: 1 }).limit(20).lean()`
- **Projection**: `User.find({}).select('email displayName -_id')`
- **Bulk write**: `User.bulkWrite([{ updateOne: { filter: {...}, update: {...} } }])`

### Aggregation
- **Pipeline**: `User.aggregate([{ $match: { status: 'active' } }, { $lookup: {...} }, { $project: {...} }])`
- **Group**: `{ $group: { _id: '$status', count: { $sum: 1 } } }`
- **Date histogram**: `{ $group: { _id: { $dateToString: { format: '%Y-%m-%d', date: '$createdAt' } } } }`

### Transactions
- **Session**: `const session = await mongoose.startSession(); session.startTransaction(); ... session.commitTransaction();`

