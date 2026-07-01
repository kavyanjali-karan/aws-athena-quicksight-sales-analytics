# Architecture & Workflow

End-to-end description of how data moves through the pipeline from generation
to dashboard, including dependencies and failure recovery procedures.

---

## Pipeline Stages

```
Stage 1: Generate
    python datasets/generate_datasets.py
    Output: data/raw/*.csv

Stage 2: Clean & Enrich
    python python/clean_sales_data.py
    Input:  data/raw/*.csv
    Output: data/processed/**/*.parquet

Stage 3: Validate
    python python/validate_dataset.py
    Input:  data/processed/
    Output: PASS (continue) or FAIL (halt + fix)

Stage 4: Upload to S3
    aws s3 sync data/processed/ s3://YOUR-BUCKET/sales-analytics/processed/

Stage 5: Catalog Registration
    Option A: MSCK REPAIR TABLE (manual, Athena)
    Option B: Glue Crawler (automated, daily)

Stage 6: Query Layer
    Run athena/01 through athena/11 in order
    Materialise CTAS aggregation tables

Stage 7: Visualisation
    QuickSight SPICE refresh (daily, 06:00 UTC)
    Dashboards update automatically
```

---

## Dependency Graph

```
generate_datasets.py
       │
       ▼
 data/raw/*.csv
       │
       ▼
clean_sales_data.py ──────────► validate_dataset.py
       │                                │
       ▼                            PASS / FAIL
 data/processed/                        │
       │                            FAIL → halt
       ▼
 aws s3 sync
       │
       ▼
 Glue Catalog
       │
       ├──► Athena 01–03 (DDL + validation)
       │
       ├──► Athena 04–11 (analytics queries)
       │
       └──► QuickSight SPICE ──► Dashboards
```

---

## Incremental Load Procedure

For production pipelines receiving new daily/monthly data:

1. **New data arrives** in `data/raw/new_transactions.csv`
2. Run `clean_sales_data.py` with `--input data/raw/new/ --output data/processed/new/`
3. Run `validate_dataset.py --input data/processed/new/`
4. Upload: `aws s3 sync data/processed/new/ s3://YOUR-BUCKET/sales-analytics/processed/`
5. The Glue Crawler (running at 05:00 UTC) will discover any new `year/month` partitions
6. No manual `MSCK REPAIR TABLE` needed when the Glue Crawler is active
7. SPICE refreshes at 06:00 UTC, picking up the new partitions

---

## Failure Recovery

| Failure Point | Symptom | Recovery |
|---|---|---|
| `generate_datasets.py` error | Missing CSV files | Fix seed/config, re-run; output is deterministic |
| `clean_sales_data.py` error | Partial Parquet output | Delete `data/processed/`, re-run from raw |
| `validate_dataset.py` FAIL | Validation errors in log | Inspect error details; fix upstream data or cleaning rules |
| S3 sync failure (network) | Partial upload | Re-run `aws s3 sync` — sync is idempotent |
| Glue Crawler failure | Missing partitions | Run `MSCK REPAIR TABLE sales.sales_transactions` manually |
| Athena DDL error | Table already exists | `DROP TABLE IF EXISTS` then re-run SQL file |
| QuickSight SPICE failure | "Import failed" in dataset | Check Athena permissions; verify table schema hasn't changed |

---

## Scheduling in Production

For a production deployment, each stage maps to an AWS managed service:

| Stage | Production Implementation |
|---|---|
| Extract (if live data) | AWS Glue ETL Job or AWS Lambda triggered by S3 event |
| Transform | AWS Glue Python Shell job (same logic as `clean_sales_data.py`) |
| Validate | Great Expectations checkpoint in Lambda or Glue job |
| Load | Glue job writes directly to S3 processed prefix |
| Catalog | Glue Crawler triggered by S3 event via EventBridge |
| Orchestrate | AWS Step Functions (state machine across all stages) |
| Monitor | CloudWatch metrics + SNS alert on pipeline failure |
| Refresh | QuickSight SPICE scheduled refresh (daily 06:00 UTC) |
