# Architecture Description

## Overview

This project implements a cloud-native, serverless Business Intelligence pipeline on AWS.
The architecture follows the **Medallion pattern** (raw → processed → curated) using
Amazon S3 as the data lake foundation.

---

## Layers

### 1. Ingestion Layer

**Tool:** Python scripts (local or AWS Lambda / AWS Glue Python Shell)

- `generate_datasets.py` creates synthetic CSV data for customers, products, and transactions.
- `clean_sales_data.py` transforms raw CSVs into Snappy-compressed Parquet, partitioned by `year/month`.
- Data lands in `s3://YOUR-BUCKET/sales-analytics/processed/`.

**Why Parquet?**
Parquet is columnar, enabling Athena to skip non-queried columns and reducing both scan cost and latency. Snappy compression reduces storage footprint by ~70% vs. raw CSV.

**Why Hive-style partitioning?**
Partition pruning allows Athena to read only the `year=YYYY/month=MM` directories matching a query's `WHERE` clause, cutting I/O by up to 90% for time-filtered queries.

---

### 2. Catalog Layer

**Tool:** AWS Glue Data Catalog

- External tables are defined in Athena and registered in the Glue Catalog.
- Schema evolution: new columns can be added to Parquet files without breaking existing queries (schema-on-read).
- Partitions are discovered via `MSCK REPAIR TABLE` or Glue Crawlers.

**Glue Crawler alternative:**
For production, schedule a Glue Crawler to run 30 minutes after each ETL job completes. This auto-registers new year/month partitions without manual `MSCK REPAIR`.

---

### 3. Query Layer

**Tool:** Amazon Athena (Presto/Trino engine)

- SQL files in `athena/` are numbered in execution order.
- CTAS (CREATE TABLE AS SELECT) patterns materialize frequently-used aggregations, reducing per-query cost and latency for QuickSight.
- Athena query results are written to `s3://YOUR-BUCKET/athena-results/` (auto-purged after 30 days via S3 Lifecycle rule).

**Cost control:**
- Workgroup budget alerts set at $5/month.
- Partition projection considered for tables with predictable `year/month` ranges (eliminates need for `MSCK REPAIR`).

---

### 4. Visualisation Layer

**Tool:** Amazon QuickSight (Enterprise Edition for row-level security)

- SPICE (Super-fast, Parallel, In-memory Calculation Engine) caches Athena results for sub-second dashboard rendering.
- Three dashboards: Executive, Regional, Customer (see `quicksight/`).
- SPICE refresh: daily at 06:00 UTC.
- Row-level security: regional managers can be restricted to their own region using QuickSight RLS datasets.

---

## Data Flow (end-to-end)

```
Local / Lambda
    │
    ├── generate_datasets.py  → data/raw/ (CSV)
    │
    ├── clean_sales_data.py   → data/processed/ (Parquet, partitioned)
    │       │
    │       └── aws s3 sync  → s3://YOUR-BUCKET/sales-analytics/processed/
    │
    └── AWS Glue (optional crawler) → Glue Data Catalog
            │
            └── Amazon Athena (SQL queries 01–11)
                    │
                    └── SPICE Dataset → Amazon QuickSight Dashboards
```

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Storage format | Parquet + Snappy | Columnar I/O, 70% size reduction vs CSV |
| Partitioning | year / month | Prunes irrelevant data for time-range queries |
| Query engine | Athena (serverless) | Zero-infrastructure, pay-per-TB scanned |
| BI tool | QuickSight + SPICE | Managed service, scales to 10K users with no server ops |
| Schema management | Glue Catalog | Single source of truth; decoupled from compute |
| Authentication | IAM + QuickSight IAM roles | Least-privilege, no long-lived credentials |
| Cost guardrail | Athena workgroup budget | Prevents runaway query costs |

---

## AWS Resource Inventory

| Resource | Type | Purpose |
|---|---|---|
| `s3://YOUR-BUCKET` | S3 Bucket | Data lake storage |
| `sales` | Glue Database | Logical schema namespace |
| `sales/customers` | Glue Table | Customer dimension table |
| `sales/products` | Glue Table | Product dimension table |
| `sales/sales_transactions` | Glue Table | Fact table (partitioned) |
| `sales-analytics-workgroup` | Athena Workgroup | Query isolation + budget control |
| `SalesAnalyticsExecutive` | QuickSight Dashboard | C-suite view |
| `SalesAnalyticsRegional` | QuickSight Dashboard | Regional manager view |
| `SalesAnalyticsCustomer` | QuickSight Dashboard | CRM / marketing view |
| `sales-analytics-role` | IAM Role | Athena + S3 read permissions for QuickSight |

---

## Security Model

- **S3 bucket:** Block all public access. Bucket policy restricts to `sales-analytics-role` ARN.
- **Athena:** IAM policies limit query execution to the `sales-analytics-workgroup` only.
- **QuickSight:** Enterprise Edition enables row-level security (RLS) and VPC connectivity.
- **Encryption:** S3 server-side encryption with AWS KMS (SSE-KMS); Athena encrypts query results in transit.
- **Audit:** AWS CloudTrail logs all S3 object access and Athena query history.
