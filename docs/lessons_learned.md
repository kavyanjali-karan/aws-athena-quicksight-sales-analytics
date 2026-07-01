# Lessons Learned

Engineering decisions, trade-offs, and things that would be done differently
in a production engagement. Useful for interview discussions.

---

## What Worked Well

### 1. Metric Contract First

Defining the metric contract in `docs/kpi_definitions.md` before writing SQL
eliminated the "two teams, two revenue numbers" problem. Every SQL file references
the same canonical definition, which improves consistency across reporting outputs.

**Interview talking point:** "A common failure in BI projects is that each team defines the same KPI differently. The fix is to treat metric definitions as a contract, not as a convention."

---

### 2. Partitioning by year/month

Early tests against unpartitioned Parquet showed Athena scanning the full dataset for
every date-filtered query. Adding `year/month` Hive partitions reduced scan volume by ~85%
for typical executive reporting queries (e.g., current-year filters) and cut per-query cost proportionally.

**Lesson:** Always partition on the most common filter dimension. For time-series BI, that's almost always date.

---

### 3. SPICE for Dashboard Latency

Initial prototypes connected QuickSight directly to Athena in Direct Query mode.
Dashboard load times were slow enough to make the experience feel less polished for a live demo.
Switching to SPICE reduced visual load times and made the reporting experience more usable for stakeholders.

**Trade-off:** SPICE has a 500M row limit per dataset and requires a daily refresh cycle.
For near-real-time reporting (< 1 hour freshness), Direct Query or a streaming ingestion
pattern (Kinesis → S3 → Athena) would be required.

---

### 4. Data Validation as a Reporting Gate

Early versions of the reporting-system had no validation step. A bug in date parsing caused
~3% of transactions to have `ship_date < order_date`. This silently corrupted
the "Avg Days to Ship" KPI.

Adding `validate_dataset.py` as a mandatory gate caught this class of error before
data reached Athena. The reporting-system exits with a non-zero code on any validation failure,
preventing corrupted data from reaching the executive reporting.

**Lesson:** Treat data validation like unit tests — required, not optional, and run in CI.

---

## What Would Be Done Differently in Production

### 1. dbt Instead of Raw SQL Files

The numbered SQL files in `athena/` work but have no dependency management,
no incremental run logic, and no built-in testing. A production environment
would replace these with dbt models:

- `sources.yml` defines raw tables
- `staging/` models clean and type-cast
- `marts/` models define the final business reporting tables
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
(AWS Glue DataBrew or OpenMetadata) to ensure every executive reporting metric traces back
to a source column with a known owner.

---

### 5. Row-Level Security from Day 1

The Regional executive reporting was spec'd with RLS from the start, but implementing it
after the fact required restructuring the QuickSight dataset. In production,
design the RLS dataset mapping before building any executive reporting that will be shared
across roles with different data access rights.

---

## Interview Takeaways

- **Data quality is not optional.** A ship_date ordering bug would have corrupted a reporting KPI if it had reached the downstream dataset. Validation as a reporting gate prevented that outcome.
- **Serverless BI doesn't mean no engineering.** Partitioning, SPICE tuning, and
  CTAS materialization required deliberate engineering decisions to achieve performance targets.
- **Metric contracts prevent stakeholder confusion.** Defining revenue in one place and
  citing it everywhere eliminates the "two numbers" problem seen in organizations without a
  semantic layer.
