# Reporting Workflow

End-to-end description of how data moves through the reporting system from generation
to executive reporting, including the main dependencies and operational stages.

---

## Reporting Stages

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
    aws s3 sync data/processed/ s3://YOUR-BUCKET/sales-business reporting/processed/

Stage 5: Catalog Registration
    Option A: MSCK REPAIR TABLE (manual, Athena)
    Option B: Glue Crawler (automated, daily)

Stage 6: Query Layer
    Run athena/010 through athena/11 in order
    Materialise CTAS aggregation tables

Stage 7: Visualisation
    QuickSight SPICE refresh (daily, 06:00 UTC)
    executive reportings update automatically
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
       ├──► Athena 010–03 (DDL + validation)
       │
       ├──► Athena 04–11 (business reporting queries)
       │
       └──► QuickSight SPICE ──► executive reportings
```

---

## Incremental Load Procedure

For production reporting-systems receiving new daily/monthly data:

1. **New data arrives** in `data/raw/new_transactions.csv`
2. Run `clean_sales_data.py` with `--input data/raw/new/ --output data/processed/new/`
3. Run `validate_dataset.py --input data/processed/new/`
4. Upload: `aws s3 sync data/processed/new/ s3://YOUR-BUCKET/sales-business reporting/processed/`
5. The Glue Crawler (running at 05:00 UTC) will discover any new `year/month` partitions
6. No manual `MSCK REPAIR TABLE` needed when the Glue Crawler is active
7. SPICE refreshes at 06:00 UTC, picking up the new partitions

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
| Monitor | CloudWatch metrics + SNS alert on reporting-system failure |
| Refresh | QuickSight SPICE scheduled refresh (daily 06:00 UTC) |
