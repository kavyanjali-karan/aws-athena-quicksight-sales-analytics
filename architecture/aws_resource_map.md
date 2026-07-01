# AWS Resource Map

All resources listed below should be created in a single AWS region (e.g. `us-east-1`).
Replace `YOUR-ACCOUNT-ID` and `YOUR-BUCKET` throughout.

---

## Amazon S3

| Bucket / Prefix | Purpose | Retention |
|---|---|---|
| `s3://YOUR-BUCKET/sales-analytics/processed/customers/` | Cleaned customer Parquet | Indefinite |
| `s3://YOUR-BUCKET/sales-analytics/processed/products/` | Cleaned product Parquet | Indefinite |
| `s3://YOUR-BUCKET/sales-analytics/processed/sales_transactions/year=*/month=*/` | Transaction Parquet (partitioned) | Indefinite |
| `s3://YOUR-BUCKET/athena-results/` | Athena query output CSVs | 30-day lifecycle |

**S3 Bucket settings:**
- Block all public access: ✅
- Versioning: enabled
- Default encryption: SSE-S3 (or SSE-KMS for compliance environments)
- Lifecycle rule on `athena-results/`: expire after 30 days

---

## AWS Glue

| Resource | Name | Type |
|---|---|---|
| Database | `sales` | Glue Database |
| Table | `sales.customers` | External (Parquet) |
| Table | `sales.products` | External (Parquet) |
| Table | `sales.sales_transactions` | External, partitioned (Parquet) |
| Crawler | `sales-analytics-crawler` | Glue Crawler |
| Crawler schedule | `cron(0 5 * * ? *)` | Daily at 05:00 UTC |
| Crawler role | `AWSGlueServiceRole-SalesAnalytics` | IAM Role |

---

## Amazon Athena

| Resource | Name | Notes |
|---|---|---|
| Workgroup | `sales-analytics-workgroup` | Separate from primary workgroup |
| Query result location | `s3://YOUR-BUCKET/athena-results/` | Set on workgroup |
| Encryption | SSE-S3 | Encrypts query result files |
| Data usage control | $10/month budget | CloudWatch alarm + SNS notification |

---

## Amazon QuickSight

| Resource | Name | Type |
|---|---|---|
| Dataset | `SalesTransactionsSpice` | SPICE (from Athena) |
| Dataset | `CustomerSummarySpice` | SPICE (from Athena CTAS) |
| Dataset | `RegionalPerformanceSpice` | SPICE (from Athena CTAS) |
| Dashboard | `SalesAnalyticsExecutive` | QuickSight Dashboard |
| Dashboard | `SalesAnalyticsRegional` | QuickSight Dashboard |
| Dashboard | `SalesAnalyticsCustomer` | QuickSight Dashboard |
| Analysis | `SalesAnalyticsAnalysis` | Shared analysis source |
| Refresh schedule | Daily at 06:00 UTC | Full SPICE refresh |

**QuickSight permissions:**
- Author: BI engineers, dashboard developers
- Reader: business stakeholders (per-seat pricing or session pricing)
- Row-level security: enabled for Regional Dashboard (managers see only their region)

---

## IAM Roles and Policies

### `SalesAnalyticsAthenaRole`

Used by QuickSight to query Athena.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StopQueryExecution"
      ],
      "Resource": "arn:aws:athena:us-east-1:YOUR-ACCOUNT-ID:workgroup/sales-analytics-workgroup"
    },
    {
      "Effect": "Allow",
      "Action": ["glue:GetDatabase", "glue:GetTable", "glue:GetPartitions", "glue:BatchGetPartition"],
      "Resource": [
        "arn:aws:glue:us-east-1:YOUR-ACCOUNT-ID:catalog",
        "arn:aws:glue:us-east-1:YOUR-ACCOUNT-ID:database/sales",
        "arn:aws:glue:us-east-1:YOUR-ACCOUNT-ID:table/sales/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET",
        "arn:aws:s3:::YOUR-BUCKET/sales-analytics/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET/athena-results/*"
      ]
    }
  ]
}
```

### `AWSGlueServiceRole-SalesAnalytics`

Used by Glue Crawler.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET",
        "arn:aws:s3:::YOUR-BUCKET/sales-analytics/processed/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase", "glue:CreateTable", "glue:UpdateTable",
        "glue:GetTable", "glue:BatchCreatePartition", "glue:GetPartition",
        "glue:CreatePartition", "glue:UpdatePartition"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:/aws-glue/*"
    }
  ]
}
```

---

## Cost Estimate (Monthly — small workload)

| Service | Usage | Estimated Cost |
|---|---|---|
| Amazon S3 | ~1 GB stored + requests | ~$0.025 |
| Amazon Athena | ~10 GB scanned/month | ~$0.50 |
| AWS Glue Crawler | 1 DPU × 10 min/day × 30 days | ~$0.44 |
| Amazon QuickSight | 1 author + 5 readers | ~$18–$48 |
| **Total** | | **~$20–$50/month** |

*Costs drop significantly with partition pruning and Parquet columnar reads.*
