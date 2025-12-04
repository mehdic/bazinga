---
name: data-engineering
type: data
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Data Engineering Expertise

## Specialist Profile
Data engineering specialist building ETL pipelines. Expert in data transformation, orchestration, and warehouse patterns.

## Implementation Guidelines

### ETL with PySpark

```python
# jobs/user_aggregation.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def create_spark_session() -> SparkSession:
    return SparkSession.builder \
        .appName("user_aggregation") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

def run_aggregation(spark: SparkSession, date: str):
    users = spark.read.parquet(f"s3://data-lake/users/date={date}")
    orders = spark.read.parquet(f"s3://data-lake/orders/date={date}")

    # Aggregate user metrics
    user_metrics = orders.groupBy("user_id").agg(
        F.count("*").alias("order_count"),
        F.sum("amount").alias("total_spent"),
        F.avg("amount").alias("avg_order_value"),
        F.max("created_at").alias("last_order_at"),
    )

    # Window for ranking
    window = Window.orderBy(F.desc("total_spent"))

    result = users.join(user_metrics, users.id == user_metrics.user_id, "left") \
        .select(
            users.id,
            users.email,
            F.coalesce(user_metrics.order_count, F.lit(0)).alias("order_count"),
            F.coalesce(user_metrics.total_spent, F.lit(0)).alias("total_spent"),
            F.rank().over(window).alias("spending_rank"),
        )

    result.write \
        .mode("overwrite") \
        .partitionBy("date") \
        .parquet(f"s3://data-warehouse/user_metrics/")

if __name__ == "__main__":
    spark = create_spark_session()
    run_aggregation(spark, "2024-01-15")
```

### Airflow DAG

```python
# dags/user_pipeline.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "user_metrics_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["users", "metrics"],
) as dag:

    extract_users = PythonOperator(
        task_id="extract_users",
        python_callable=extract_from_postgres,
        op_kwargs={"table": "users", "date": "{{ ds }}"},
    )

    transform = EmrAddStepsOperator(
        task_id="transform_users",
        job_flow_id="{{ var.value.emr_cluster_id }}",
        steps=[{
            "Name": "User Aggregation",
            "ActionOnFailure": "CONTINUE",
            "HadoopJarStep": {
                "Jar": "command-runner.jar",
                "Args": ["spark-submit", "s3://scripts/user_aggregation.py", "{{ ds }}"],
            },
        }],
    )

    load_warehouse = PythonOperator(
        task_id="load_to_warehouse",
        python_callable=load_to_redshift,
        op_kwargs={"table": "user_metrics", "date": "{{ ds }}"},
    )

    extract_users >> transform >> load_warehouse
```

### dbt Models

```sql
-- models/marts/user_metrics.sql
{{ config(
    materialized='incremental',
    unique_key='user_id',
    partition_by={'field': 'date', 'data_type': 'date'}
) }}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
    {% if is_incremental() %}
    WHERE created_at > (SELECT MAX(created_at) FROM {{ this }})
    {% endif %}
),

user_orders AS (
    SELECT
        user_id,
        COUNT(*) AS order_count,
        SUM(amount) AS total_spent,
        MAX(created_at) AS last_order_at
    FROM orders
    GROUP BY user_id
)

SELECT
    u.id AS user_id,
    u.email,
    COALESCE(uo.order_count, 0) AS order_count,
    COALESCE(uo.total_spent, 0) AS total_spent,
    uo.last_order_at,
    CURRENT_DATE AS date
FROM {{ ref('stg_users') }} u
LEFT JOIN user_orders uo ON u.id = uo.user_id
```

## Patterns to Avoid
- ❌ Processing without partitioning
- ❌ Missing idempotency
- ❌ Unbounded data scans
- ❌ No data quality checks

## Verification Checklist
- [ ] Idempotent jobs
- [ ] Partition pruning
- [ ] Data quality assertions
- [ ] Incremental processing
- [ ] Proper error handling
