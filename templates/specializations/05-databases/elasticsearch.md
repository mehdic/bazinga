---
name: elasticsearch
type: database
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Elasticsearch Engineering Expertise

## Specialist Profile
Elasticsearch specialist building search and analytics solutions. Expert in mappings, queries, aggregations, and cluster management.

---

## Patterns to Follow

### Mapping Design
- **Explicit mappings**: Define before indexing, never dynamic in production
- **Keyword for exact match**: IDs, status, tags (not analyzed)
- **Text for full-text**: With appropriate analyzer
- **Multi-fields**: `displayName` as text + keyword + autocomplete
- **doc_values: false**: On text fields not used for sorting/aggregation

### Search Optimization
- **bool query structure**: must/filter/should/must_not
- **filter for non-scoring**: Cached, faster than must
- **$match early in aggregations**: Reduce document set
- **Scroll or search_after**: For deep pagination
- **Index aliases**: Zero-downtime reindexing

### Analyzers
- **standard**: Good default for most text
- **keyword**: No analysis, exact match
- **edge_ngram**: Autocomplete/typeahead
- **Custom analyzers**: Language-specific, synonyms
- **Normalizers**: For keyword case-insensitivity

### Aggregations
- **Terms for facets**: Category counts
- **Date histogram**: Time-series bucketing
- **Composite for pagination**: Large bucket sets
- **Cardinality for unique**: Approximate distinct counts
- **Sub-aggregations**: Nested analytics

### Cluster Best Practices
- **Sharding strategy**: 20-50GB per shard
- **Replica count**: At least 1 for HA
- **Index lifecycle management (ILM)**: Auto-rollover, delete
- **Hot-warm-cold**: Tiered storage for time-series
- **Shard allocation**: Aware of zones
<!-- version: elasticsearch >= 7.0 -->
- **Default single shard**: 1 primary shard default (was 5)
- **Security built-in**: Basic auth and TLS in open source
<!-- version: elasticsearch >= 8.0 -->
- **Native vector search (kNN)**: Dense vector similarity
- **Security by default**: TLS and auth required
- **Lucene 9**: Improved performance and compression
<!-- version: elasticsearch >= 8.8 -->
- **ESQL**: New query language for analytics
<!-- version: elasticsearch >= 8.11 -->
- **Semantic reranking**: AI-powered result ranking

---

## Patterns to Avoid

### Mapping Anti-Patterns
- ❌ **Dynamic mappings in production**: Mapping explosion
- ❌ **Too many fields**: Mapping explosion, memory issues
- ❌ **Missing index aliases**: Risky reindexing
- ❌ **Changing existing field types**: Requires reindex

### Query Anti-Patterns
- ❌ **from/size deep pagination**: Memory explosion, slow
- ❌ **Script scoring without cache**: CPU intensive
- ❌ **Wildcard at start**: `*pattern` scans all terms
- ❌ **must instead of filter**: Unnecessary scoring overhead
- ❌ **Querying without index**: Full index scan

### Index Anti-Patterns
- ❌ **Too many shards**: Cluster overhead
- ❌ **Too few shards**: Can't scale horizontally
- ❌ **No replicas**: Single point of failure
- ❌ **Missing ILM**: Manual cleanup, disk exhaustion

### Operational Anti-Patterns
- ❌ **Indexing without bulk**: One doc at a time
- ❌ **refresh: true on every write**: Performance killer
- ❌ **No monitoring**: Blind to issues
- ❌ **Ignoring slow logs**: Hidden performance problems

---

## Verification Checklist

### Mappings
- [ ] Explicit mappings defined
- [ ] Appropriate field types (keyword vs text)
- [ ] Custom analyzers for search requirements
- [ ] Multi-fields where needed

### Queries
- [ ] filter for non-scoring clauses
- [ ] search_after for deep pagination
- [ ] Explain API for debugging relevance
- [ ] Profile API for performance

### Indexing
- [ ] Bulk API for batch indexing
- [ ] Index aliases in use
- [ ] ILM policies configured
- [ ] Appropriate refresh interval

### Cluster
- [ ] Shard size 20-50GB
- [ ] Replicas for HA
- [ ] Monitoring configured
- [ ] Slow logs enabled

---

## Code Patterns (Reference)

### Mappings
- **Text + keyword**: `"title": { "type": "text", "fields": { "keyword": { "type": "keyword" } } }`
- **Autocomplete**: `"analyzer": "autocomplete"` with edge_ngram filter
- **Date**: `"createdAt": { "type": "date" }`

### Search
- **Bool query**: `{ "bool": { "must": [...], "filter": [...], "should": [...] } }`
- **Multi-match**: `{ "multi_match": { "query": q, "fields": ["title^2", "body"], "fuzziness": "AUTO" } }`
- **Filter (cached)**: `{ "filter": [{ "term": { "status": "active" } }, { "range": { "date": { "gte": "now-7d" } } }] }`

### Aggregations
- **Terms**: `{ "aggs": { "by_status": { "terms": { "field": "status" } } } }`
- **Date histogram**: `{ "date_histogram": { "field": "createdAt", "calendar_interval": "day" } }`
- **Composite (paginated)**: `{ "composite": { "size": 100, "sources": [...], "after": {...} } }`

### Bulk
- **Indexing**: `client.bulk({ body: docs.flatMap(d => [{ index: { _index: 'idx', _id: d.id } }, d]) })`

