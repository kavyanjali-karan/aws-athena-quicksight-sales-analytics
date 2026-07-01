# AWS Setup Guide

Complete, step-by-step instructions for provisioning the AWS infrastructure
required to run this BI reporting-system end-to-end.

Prerequisites: AWS CLI installed and configured with an IAM user or role using least-privilege access for S3, Glue, Athena, and QuickSight.

---

## Step 1 — Create the S3 Bucket

```bash
# Replace YOUR-BUCKET with a globally unique name (e.g. acme-sales-business reporting-2024)
BUCKET_NAME="YOUR-BUCKET"
REGION="us-east-1"

aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION"

# Block all public access
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

# Set lifecycle rule to expire Athena results after 30 days
cat > /tmp/lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "expire-athena-results",
      "Status": "Enabled",
      "Filter": { "Prefix": "athena-results/" },
      "Expiration": { "Days": 30 }
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET_NAME" \
  --lifecycle-configuration file:///tmp/lifecycle.json
```

---

## Step 2 — Upload Processed Data to S3

After running the Python reporting-system locally:

```bash
# Run data generation and cleaning
python datasets/generate_datasets.py
python python/clean_sales_data.py
python python/validate_dataset.py

# Sync processed Parquet files to S3
aws s3 sync data/processed/ "s3://$BUCKET_NAME/sales-business reporting/processed/" \
  --storage-class STANDARD \
  --exclude "*.DS_Store"

# Verify upload
aws s3 ls "s3://$BUCKET_NAME/sales-business reporting/processed/" --recursive --human-readable
```

---

## Step 3 — Create the Glue Database

```bash
aws glue create-database \
  --database-input '{
    "Name": "sales",
    "Description": "Sales business reporting data lake — customers, products, transactions",
    "LocationUri": "s3://YOUR-BUCKET/sales-business reporting/"
  }'
```

---

## Step 4 — Register External Tables in Athena

1. Open the **Amazon Athena** console → Query Editor.
2. Set the **Query result location** to `s3://YOUR-BUCKET/athena-results/`.
3. Run the contents of `athena/02_create_external_tables.sql` (replace `YOUR-BUCKET`).
4. Run `MSCK REPAIR TABLE sales.sales_transactions;` to register all partitions.

---

## Step 5 — Create a Glue Crawler (Optional — Automates Partition Discovery)

```bash
# Create IAM role for the crawler (attach AWSGlueServiceRole managed policy)
aws iam create-role \
  --role-name AWSGlueServiceRole-Salesbusiness reporting \
  --assume-role-policy-document '{
    "Version": "20102-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "glue.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name AWSGlueServiceRole-Salesbusiness reporting \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole

# Add S3 read permission for the bucket
aws iam put-role-policy \
  --role-name AWSGlueServiceRole-Salesbusiness reporting \
  --policy-name S3ReadSalesbusiness reporting \
  --policy-document '{
    "Version": "20102-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET",
        "arn:aws:s3:::YOUR-BUCKET/sales-business reporting/processed/*"
      ]
    }]
  }'

# Create the crawler
aws glue create-crawler \
  --name sales-business reporting-crawler \
  --role AWSGlueServiceRole-Salesbusiness reporting \
  --database-name sales \
  --targets '{
    "S3Targets": [
      { "Path": "s3://YOUR-BUCKET/sales-business reporting/processed/sales_transactions/" }
    ]
  }' \
  --schedule "cron(0 5 * * ? *)" \
  --schema-change-policy '{"UpdateBehavior": "UPDATE_IN_DATABASE", "DeleteBehavior": "LOG"}'

# Run the crawler immediately
aws glue start-crawler --name sales-business reporting-crawler
```

---

## Step 6 — Create the Athena Workgroup

```bash
aws athena create-work-group \
  --name sales-business reporting-workgroup \
  --configuration '{
    "ResultConfiguration": {
      "OutputLocation": "s3://YOUR-BUCKET/athena-results/",
      "EncryptionConfiguration": { "EncryptionOption": "SSE_S3" }
    },
    "EnforceWorkGroupConfiguration": true,
    "PublishCloudWatchMetricsEnabled": true,
    "BytesScannedCutoffPerQuery": 10737418240
  }' \
  --description "Sales business reporting workgroup with 10GB per-query limit"
```

---

## Step 7 — Run Athena SQL Files

Execute the numbered SQL files in order from the Athena Query Editor,
switching to the `sales-business reporting-workgroup` workgroup:

```
010_create_database.sql       ← skip if database already created in Step 3
02_create_external_tables.sql
03_validation.sql            ← verify 0 violations before proceeding
04_kpi_calculations.sql
05_monthly_sales.sql
06_profitability.sql
07_regional_performance.sql
08_customer_segmentation.sql
09_top_products.sql
10_window_functions.sql
11_data_quality_checks.sql
```

---

## Step 8 — Connect QuickSight to Athena

1. Open **Amazon QuickSight** → Manage QuickSight → Security & permissions.
2. Grant QuickSight access to **Amazon Athena** and the `YOUR-BUCKET` S3 bucket.
3. In QuickSight → Datasets → New dataset → **Athena** data source.
4. Data source name: `SalesAthena`; Athena workgroup: `sales-business reporting-workgroup`.
5. Select database: `sales`; table: `sales_transactions`.
6. Choose **Import to SPICE for quicker business reporting**.
7. Repeat for `customers` and `products` tables.
8. Build calculated fields as described in `quicksight/executive_dashboard.md`.

---

## Step 9 — Schedule SPICE Refresh

In QuickSight → Datasets → select dataset → **Scheduled refresh**:
- Frequency: Daily
- Time: 06:00 UTC
- Start date: today

---

## Verification Checklist

- [ ] `aws s3 ls s3://YOUR-BUCKET/sales-business reporting/processed/` shows three directories
- [ ] `SHOW TABLES IN sales;` in Athena returns `customers`, `products`, `sales_transactions`
- [ ] `SELECT COUNT(*) FROM sales.sales_transactions;` returns ~50,000
- [ ] `03_validation.sql` produces 0 violations
- [ ] QuickSight SPICE dataset shows "Import complete" status
- [ ] Executive dashboard KPI cards load within 2 seconds
