---
name: data-engineering
type: data
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Data Engineering Expertise

## Specialist Profile
Data engineering specialist building ETL pipelines. Expert in data transformation, orchestration, and warehouse patterns.

---

## Patterns to Follow

### ETL Best Practices
- **Idempotent jobs**: Re-runnable without side effects
- **Incremental processing**: Only new/changed data
- **Partition pruning**: Read only relevant partitions
- **Data quality checks**: Validate before and after
- **Lineage tracking**: Know data origins

### PySpark Patterns
- **Adaptive Query Execution**: Auto-optimization
- **Broadcast joins**: Small table to all nodes
- **Partition by key columns**: Query performance
- **Caching strategically**: Reused DataFrames
- **Avoid collect()**: Keeps data distributed

### Orchestration (Airflow)
- **DAG as code**: Version controlled
- **Idempotent tasks**: Safe retries
- **XCom for small data**: Not large datasets
- **Sensors with timeouts**: Don't block forever
- **Task groups**: Logical organization

### dbt Best Practices
- **Incremental models**: Performance at scale
- **Ephemeral for CTEs**: No materialization
- **Tests on sources**: Catch bad data early
- **Documentation**: Every model documented
- **Seeds for lookup tables**: Version controlled

### Data Quality
- **Schema validation**: Expected columns/types
- **Row counts**: Expected ranges
- **Null checks**: Critical fields
- **Freshness SLAs**: Data timeliness
- **Great Expectations or dbt tests**: Automated validation

---

## Patterns to Avoid

### ETL Anti-Patterns
- ❌ **Non-idempotent jobs**: Duplicates on retry
- ❌ **Full table scans**: Read only what's needed
- ❌ **No partitioning**: Slow queries, high costs
- ❌ **Missing data validation**: Garbage propagates

### Spark Anti-Patterns
- ❌ **collect() on large data**: OOM errors
- ❌ **UDFs when built-ins exist**: Slower
- ❌ **Skewed joins**: One partition takes forever
- ❌ **Not caching reused DFs**: Recomputes

### Orchestration Anti-Patterns
- ❌ **Logic in DAG files**: Hard to test
- ❌ **Long-running tasks**: No checkpointing
- ❌ **No task retries**: Fragile pipelines
- ❌ **Hardcoded connections**: Use Airflow connections

### Architecture Anti-Patterns
- ❌ **No lineage tracking**: Unknown data provenance
- ❌ **Monolithic pipelines**: Hard to debug
- ❌ **No alerting**: Silent failures
- ❌ **Ignoring backpressure**: Downstream overwhelm

---

## Verification Checklist

### Jobs
- [ ] Idempotent design
- [ ] Incremental where applicable
- [ ] Partitioning strategy
- [ ] Error handling with retries

### Data Quality
- [ ] Schema validation
- [ ] Row count checks
- [ ] Null/freshness validation
- [ ] Test coverage in dbt

### Orchestration
- [ ] DAG version controlled
- [ ] Task dependencies clear
- [ ] Retry/SLA configured
- [ ] Alerting on failure

### Performance
- [ ] Partition pruning enabled
- [ ] Joins optimized (broadcast/shuffle)
- [ ] Caching where beneficial
- [ ] No full table scans

---

## Code Patterns (Reference)

### PySpark
- **Session**: `spark = SparkSession.builder.config("spark.sql.adaptive.enabled", "true").getOrCreate()`
- **Read partitioned**: `spark.read.parquet(f"s3://data/date={date}")`
- **Write partitioned**: `df.write.mode("overwrite").partitionBy("date").parquet("s3://output/")`
- **Window**: `Window.partitionBy("user_id").orderBy(F.desc("created_at"))`

### Airflow
- **DAG**: `with DAG("pipeline", schedule_interval="@daily", catchup=False) as dag:`
- **Task**: `PythonOperator(task_id="extract", python_callable=extract_fn, op_kwargs={"date": "{{ ds }}"})`
- **Dependencies**: `extract >> transform >> load`

### dbt
- **Incremental**: `{{ config(materialized='incremental', unique_key='id') }} {% if is_incremental() %} WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }}) {% endif %}`
- **Ref**: `SELECT * FROM {{ ref('stg_orders') }}`
- **Test**: `- unique: user_id`, `- not_null: email`

