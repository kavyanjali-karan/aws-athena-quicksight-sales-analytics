# Lessons Learned

Engineering decisions, trade-offs, and things that would be done differently
in a production engagement. Useful for interview discussions.

---

## What Worked Well

### 1. Contract-First API (OpenAPI for SQL)

Defining the metric contract in `docs/kpi_definitions.md` before writing any SQL
eliminated the "two teams, two revenue numbers" problem. Every SQL file references
the single canonical definition. This is the equivalent of API contract-first design —
applied to BI metrics.

**Interview talking point:** "On a past engagement I've seen teams waste weeks arguing about
whose revenue number was right. The fix is treating metric definitions as a contract, not a convention."

---

### 2. Partitioning by year/month

Early tests against unpartitioned Parquet showed Athena scanning the full dataset for
every date-filtered query. Adding `year/month` Hive partitions reduced scan volume by ~85%
for typical dashboard queries (e.g., current-year filters) and cut per-query cost proportionally.

**Lesson:** Always partition on the most common filter dimension. For time-series BI, that's almost always date.

---

### 3. SPICE for Dashboard Latency

Initial prototype connected QuickSight directly to Athena (Direct Query mode).
Dashboard load times were 4–8 seconds per visual — unacceptable for a live demo.
Switching to SPICE (in-memory cache) reduced load times to < 1 second.

**Trade-off:** SPICE has a 500M row limit per dataset and requires a daily refresh cycle.
For near-real-time reporting (< 1 hour freshness), Direct Query or a streaming ingestion
pattern (Kinesis → S3 → Athena) would be required.

---

### 4. Data Validation as a Pipeline Gate

Early versions of the pipeline had no validation step. A bug in date parsing caused
~3% of transactions to have `ship_date < order_date`. This silently corrupted
the "Avg Days to Ship" KPI.

Adding `validate_dataset.py` as a mandatory gate caught this class of error before
data reached Athena. The pipeline exits with a non-zero code on any validation failure,
preventing corrupted data from reaching the dashboard.

**Lesson:** Treat data validation like unit tests — required, not optional, and run in CI.

---

## What Would Be Done Differently in Production

### 1. dbt Instead of Raw SQL Files

The numbered SQL files in `athena/` work but have no dependency management,
no incremental run logic, and no built-in testing. A production environment
would replace these with dbt models:

- `sources.yml` defines raw tables
- `staging/` models clean and type-cast
- `marts/` models define the final analytics tables
- `schema.yml` tests enforce not-null, unique, and referential integrity

dbt also generates documentation and lineage graphs, which stakeholders can self-serve.

---

### 2. Delta Lake or Apache Iceberg Instead of Raw Parquet

Hive-partitioned Parquet is write-once. In production, transactions can be corrected,
cancelled, or back-filled. Parquet has no concept of UPDATE or DELETE.

Delta Lake or Iceberg would provide:
- ACID transactions on S3
- Time travel (query data as of a specific timestamp)
- Efficient MERGE / UPSERT for late-arriving data

Both are supported by Athena (Iceberg natively; Delta via CTAS patterns).

---

### 3. Terraform for Infrastructure

All AWS resources in this project were created manually via the CLI or console.
In production, every resource — S3 buckets, Glue databases, Athena workgroups,
IAM roles — would be defined in Terraform:

- Reproducible across environments (dev / staging / prod)
- Version-controlled infrastructure
- Automated teardown prevents cost leakage

---

### 4. Column-Level Data Lineage

QuickSight makes it easy to create new calculated fields without documenting
where they come from. On a real project, I would add column-level lineage tracking
(AWS Glue DataBrew or OpenMetadata) to ensure every dashboard metric traces back
to a source column with a known owner.

---

### 5. Row-Level Security from Day 1

The Regional Dashboard was spec'd with RLS from the start, but implementing it
after the fact required restructuring the QuickSight dataset. In production,
design the RLS dataset mapping before building any dashboard that will be shared
across roles with different data access rights.

---

## Interview Takeaways

- **Data quality is not optional.** Caught and fixed a ship_date ordering bug that
  would have corrupted a dashboard KPI. Validation as a pipeline gate is the fix.
- **Serverless BI doesn't mean no engineering.** Partitioning, SPICE tuning, and
  CTAS materialization required deliberate engineering decisions to achieve performance targets.
- **Metric contracts prevent stakeholder confusion.** Defining revenue in one place and
  citing it everywhere eliminates the "two numbers" problem seen in organizations without a
  semantic layer.
