---
name: elasticsearch
type: database
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Elasticsearch Engineering Expertise

## Specialist Profile
Elasticsearch specialist building search and analytics solutions. Expert in mappings, queries, and aggregations.

## Implementation Guidelines

### Index Mappings

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "email": { "type": "keyword" },
      "displayName": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": { "type": "keyword" },
          "autocomplete": {
            "type": "text",
            "analyzer": "autocomplete"
          }
        }
      },
      "status": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "createdAt": { "type": "date" }
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "autocomplete": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "autocomplete_filter"]
        }
      },
      "filter": {
        "autocomplete_filter": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 20
        }
      }
    }
  }
}
```

### Search Queries

```typescript
// Full-text search with filters
const searchUsers = async (query: string, filters: SearchFilters) => {
  const response = await client.search({
    index: 'users',
    body: {
      query: {
        bool: {
          must: query
            ? {
                multi_match: {
                  query,
                  fields: ['displayName^2', 'email'],
                  type: 'best_fields',
                  fuzziness: 'AUTO',
                },
              }
            : { match_all: {} },
          filter: [
            filters.status && { term: { status: filters.status } },
            filters.tags?.length && { terms: { tags: filters.tags } },
            filters.dateRange && {
              range: {
                createdAt: {
                  gte: filters.dateRange.start,
                  lte: filters.dateRange.end,
                },
              },
            },
          ].filter(Boolean),
        },
      },
      sort: [{ _score: 'desc' }, { createdAt: 'desc' }],
      from: filters.offset || 0,
      size: filters.limit || 20,
    },
  });

  return {
    hits: response.hits.hits.map((hit) => hit._source),
    total: response.hits.total,
  };
};
```

### Aggregations

```typescript
// Analytics query
const getUserStats = async () => {
  const response = await client.search({
    index: 'users',
    body: {
      size: 0,
      aggs: {
        by_status: { terms: { field: 'status' } },
        signups_over_time: {
          date_histogram: {
            field: 'createdAt',
            calendar_interval: 'day',
          },
        },
        top_tags: {
          terms: { field: 'tags', size: 10 },
        },
      },
    },
  });

  return response.aggregations;
};
```

### Bulk Operations

```typescript
// Bulk indexing
const bulkIndex = async (users: User[]) => {
  const body = users.flatMap((user) => [
    { index: { _index: 'users', _id: user.id } },
    user,
  ]);

  const response = await client.bulk({ body, refresh: true });

  if (response.errors) {
    const errors = response.items.filter((item) => item.index?.error);
    console.error('Bulk indexing errors:', errors);
  }
};
```

## Patterns to Avoid
- ❌ Dynamic mappings in production
- ❌ Deep pagination with from/size
- ❌ Querying without filters
- ❌ Missing index aliases

## Verification Checklist
- [ ] Explicit mappings defined
- [ ] Appropriate analyzers
- [ ] Scroll or search_after for deep pagination
- [ ] Index aliases for zero-downtime reindexing
- [ ] Bulk operations for batch processing
