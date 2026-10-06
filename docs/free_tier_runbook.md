# Deploying this project on real AWS (Free Tier)

The repo already ships every deploy-time artifact this guide uses:
`infra/cloudformation.yaml`, `athena/ddl.sql`, `athena/queries/*.sql`,
`python/run_athena_queries.py`, `python/schedule_quicksight_refresh.py`.

Everything here runs on the Athena + S3 + Glue free tier when the
resources come down the same day. Athena bills per query (~$5/TB scanned);
this dataset is ~1 MB, so each query costs a fraction of a cent.

## 0. One-time setup (~10 min)

1. AWS account (credit card required; nothing below exceeds free tier).
2. Console: IAM → Users → the new user → **Create access key** → CLI use-case.
3. Locally: `pip install boto3` then `aws configure` (Access Key, Secret, region `us-east-1`).

## 1. Provision infrastructure with CloudFormation (~2 min)

AWS Console → CloudFormation → **Create stack → With new resources**:

- **Template source:** Upload a template file → pick `infra/cloudformation.yaml`
- **Stack name:** `sales-analytics-dev`
- **Parameters:** leave defaults (`ProjectName=sales-analytics`, `DatabaseName=sales_analytics_dev`)
- Check the IAM acknowledgement box → **Create stack**

Wait for `CREATE_COMPLETE` — the **Outputs** tab shows the bucket name
every later command uses.

## 2. Run the ETL locally and upload (~2 min)

```bash
python python/etl_pipeline.py                 # builds data/curated/sales/category=*/
aws s3 sync data/curated/sales/ s3://<BUCKET>/curated/sales/
```

The S3 console then shows the `category=...` partition folders under
`curated/sales/` — the partitioning the Glue crawler and Athena rely on.

## 3. Create the Athena table and run the queries (~2 min)

```bash
python python/run_athena_queries.py --bucket <BUCKET> --region us-east-1
```

This executes `athena/ddl.sql` (CREATE EXTERNAL TABLE + MSCK REPAIR) and
all three query files. Results land under `s3://<BUCKET>/athena-results/`,
and the Athena console shows rows returned for each analytics query.

## 4. QuickSight dashboards (~15 min, 30-day free trial)

1. Sign up at QuickSight with the same account (Enterprise edition trial).
2. **New dataset → Athena** → select the `sales_analytics_dev` database → `sales_curated`.
3. Build 2–3 visuals: monthly revenue trend, income by category, top products.
4. Optional scheduled refresh:

```bash
python python/schedule_quicksight_refresh.py --dataset-id <ID> --account <ACCOUNT_ID> --region us-east-1
```

## 5. Tear down (same day)

1. Delete the QuickSight subscription (Manage QuickSight → account settings → unsubscribe).
2. Empty + delete the S3 bucket.
3. CloudFormation → delete the stack.

**Cost when done same-day: $0.**

## What this run actually demonstrates

- "I provisioned the data lake, Glue catalog database and Athena workgroup via CloudFormation,
  ran a partitioned Parquet ETL, and queried it in Athena."
- The repo's `run_athena_queries.py` is the proof — it is deploy-time tooling
  that only runs against a real account.
