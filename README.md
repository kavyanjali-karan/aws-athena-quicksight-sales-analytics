# aws-athena-quicksight-sales-analytics

[![AWS](https://img.shields.io/badge/AWS-Athena%20%7C%20S3%20%7C%20Glue%20%7C%20QuickSight-orange?logo=amazonaws)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![SQL](https://img.shields.io/badge/SQL-Presto%2FTrino-lightgrey)](https://prestodb.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A production-quality Business Intelligence pipeline built on AWS — using Amazon S3, AWS Glue, Amazon Athena, and Amazon QuickSight — to deliver executive-level sales analytics from a synthetic public dataset.

---

## Project Overview

This repository demonstrates an end-to-end BI engineering workflow:

1. **Synthetic data generation** — realistic customers, products, and sales transactions
2. **Data lake storage** — partitioned Parquet files on Amazon S3
3. **Catalog & schema** — AWS Glue Data Catalog with external Athena tables
4. **Analytical SQL** — KPIs, segmentation, ranking, window functions, data quality
5. **Dashboards** — fully specified QuickSight dashboards (executive, regional, customer)

All data is synthetic and reproducible. No proprietary or confidential information is used.

---

## Business Context

A retail company sells products across multiple regions. Business stakeholders need:

- Visibility into monthly and quarterly revenue trends
- Regional performance comparisons
- Customer lifetime value and segmentation
- Product profitability ranking
- Data quality monitoring

This pipeline answers those questions at scale using serverless AWS infrastructure, keeping infrastructure costs near zero on small datasets and scaling cost-linearly to petabyte workloads.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Data Sources                         │
│   Python Scripts → Synthetic CSV/Parquet → Amazon S3        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     AWS Glue Data Catalog                   │
│   Crawlers → Tables → Partitions → Schema Registry          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Amazon Athena                          │
│   SQL Queries → CTAS Views → KPI Aggregations               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Amazon QuickSight                         │
│   SPICE → Executive / Regional / Customer Dashboards        │
└─────────────────────────────────────────────────────────────┘
```

See [`architecture/`](architecture/) for the draw.io XML and full diagram description.

---

## AWS Services Used

| Service | Purpose |
|---|---|
| Amazon S3 | Data lake storage (raw, processed, query results) |
| AWS Glue Data Catalog | Schema management and table definitions |
| AWS Glue Crawlers | Automatic schema inference |
| Amazon Athena | Serverless SQL query engine (Presto/Trino) |
| Amazon QuickSight | Managed BI dashboards and SPICE in-memory engine |
| AWS IAM | Fine-grained access control |
| AWS CloudTrail | Audit logging |

---

## Data Pipeline

```
[Python: generate_datasets.py]
        │
        ▼
[S3: raw/customers/, raw/products/, raw/sales_transactions/]
        │
        ▼
[Python: clean_sales_data.py]
        │
        ▼
[S3: processed/ — Parquet, partitioned by year/month]
        │
        ▼
[AWS Glue Crawler → Data Catalog]
        │
        ▼
[Athena: 01_create_database → 02_create_external_tables → 03_validation → ...]
        │
        ▼
[QuickSight SPICE Dataset → Dashboards]
```

---

## Project Structure

```
aws-athena-quicksight-sales-analytics/
├── README.md                        # This file
├── LICENSE                          # MIT
├── .gitignore
├── requirements.txt
│
├── architecture/                    # Diagrams and architecture docs
│   ├── architecture.drawio          # draw.io XML source
│   ├── architecture_description.md  # Narrative explanation
│   └── aws_resource_map.md          # AWS resource inventory
│
├── datasets/                        # Synthetic data generation
│   └── generate_datasets.py
│
├── athena/                          # SQL queries (numbered execution order)
│   ├── 01_create_database.sql
│   ├── 02_create_external_tables.sql
│   ├── 03_validation.sql
│   ├── 04_kpi_calculations.sql
│   ├── 05_monthly_sales.sql
│   ├── 06_profitability.sql
│   ├── 07_regional_performance.sql
│   ├── 08_customer_segmentation.sql
│   ├── 09_top_products.sql
│   ├── 10_window_functions.sql
│   └── 11_data_quality_checks.sql
│
├── quicksight/                      # Dashboard specifications
│   ├── executive_dashboard.md
│   ├── regional_dashboard.md
│   └── customer_dashboard.md
│
├── docs/                            # Full documentation
│   ├── business_problem.md
│   ├── architecture_workflow.md
│   ├── aws_setup.md
│   ├── dashboard_storytelling.md
│   ├── lessons_learned.md
│   ├── interview_questions.md
│   ├── data_dictionary.md
│   ├── kpi_definitions.md
│   └── metric_glossary.md
│
├── notebooks/                       # Jupyter EDA + validation notebook
│   └── sales_analytics_eda.ipynb
│
├── python/                          # Production Python scripts
│   ├── clean_sales_data.py
│   ├── validate_dataset.py
│   └── generate_summary.py
│
├── assets/                          # Logos, icons, brand assets
│   └── README.md
│
├── screenshots/                     # Dashboard screenshots
│   └── README.md
│
└── outputs/                         # Query result samples
    └── README.md
```

---

## Data Dictionary

### customers

| Column | Type | Description |
|---|---|---|
| customer_id | STRING | Unique customer identifier (UUID) |
| first_name | STRING | Customer first name |
| last_name | STRING | Customer last name |
| email | STRING | Email address |
| region | STRING | Geographic sales region |
| country | STRING | Country |
| city | STRING | City |
| signup_date | DATE | Account creation date |
| segment | STRING | Customer segment: Consumer, Corporate, Home Office |

### products

| Column | Type | Description |
|---|---|---|
| product_id | STRING | Unique product identifier |
| product_name | STRING | Product name |
| category | STRING | Product category |
| sub_category | STRING | Product sub-category |
| unit_cost | DOUBLE | Cost of goods sold per unit |
| unit_price | DOUBLE | Retail price per unit |
| brand | STRING | Brand name |

### sales_transactions

| Column | Type | Description |
|---|---|---|
| transaction_id | STRING | Unique transaction identifier |
| customer_id | STRING | Foreign key → customers |
| product_id | STRING | Foreign key → products |
| order_date | DATE | Date of order |
| ship_date | DATE | Date of shipment |
| quantity | INT | Units ordered |
| unit_price | DOUBLE | Price at time of sale |
| discount | DOUBLE | Discount percentage applied |
| region | STRING | Region where sale occurred |
| year | INT | Partition column |
| month | INT | Partition column |

---

## SQL Examples

### Monthly Revenue

```sql
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    SUM(quantity * unit_price * (1 - discount))  AS net_revenue,
    COUNT(DISTINCT transaction_id)               AS order_count
FROM sales.sales_transactions
GROUP BY 1
ORDER BY 1;
```

### Customer LTV with Window Function

```sql
SELECT
    customer_id,
    SUM(net_revenue)                                          AS lifetime_value,
    RANK() OVER (ORDER BY SUM(net_revenue) DESC)             AS ltv_rank,
    SUM(SUM(net_revenue)) OVER ()                            AS total_revenue,
    SUM(net_revenue) / SUM(SUM(net_revenue)) OVER () * 100  AS revenue_share_pct
FROM (
    SELECT
        customer_id,
        quantity * unit_price * (1 - discount) AS net_revenue
    FROM sales.sales_transactions
)
GROUP BY customer_id
ORDER BY ltv_rank;
```

---

## Dashboard Preview

> **Note:** Screenshots are not included in this repository. Run the pipeline end-to-end and connect QuickSight to view dashboards. See [`quicksight/`](quicksight/) for full visual specifications.

| Dashboard | Key Visuals |
|---|---|
| Executive | Revenue KPI card, MoM trend line, regional heat map |
| Regional | Bar chart by region, YoY growth table, top 10 cities |
| Customer | LTV histogram, segment donut, cohort retention grid |

---

## Key Business Insights

The following insights are reproducible after running the full pipeline:

- **Top 20% of customers generate ~65% of revenue** (Pareto distribution built into synthetic data)
- **Q4 (Oct–Dec) accounts for ~35% of annual revenue** — driven by seasonal promotions
- **West and Northeast regions outperform** on average order value
- **Technology category has the highest margin** (avg. 38%) vs. Furniture (avg. 12%)
- **Discount rates above 20% erode profitability** — negative margin observed in 8% of transactions

---

## Reproducibility

All data is synthetically generated with a fixed random seed (`seed=42`).

Running `python datasets/generate_datasets.py` produces identical output on every execution.

No AWS account is required to run data generation, cleaning, validation, or notebook exploration locally.

---

## Setup Guide

### 1. Local Environment

```bash
git clone https://github.com/your-username/aws-athena-quicksight-sales-analytics.git
cd aws-athena-quicksight-sales-analytics
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate Synthetic Datasets

```bash
python datasets/generate_datasets.py
# Output: data/raw/customers.csv, products.csv, sales_transactions.csv
```

### 3. Clean and Validate

```bash
python python/clean_sales_data.py
python python/validate_dataset.py
python python/generate_summary.py
```

### 4. Upload to S3

```bash
aws s3 sync data/processed/ s3://YOUR-BUCKET/sales-analytics/processed/
```

### 5. AWS Glue

- Create a Glue database named `sales`
- Run a Glue crawler on `s3://YOUR-BUCKET/sales-analytics/processed/`
- Verify tables appear in the Data Catalog

### 6. Athena

- Set query results location: `s3://YOUR-BUCKET/athena-results/`
- Execute SQL files in numbered order under `athena/`

### 7. QuickSight

- Create a new dataset using Athena as source
- Select the `sales` database
- Follow specifications in `quicksight/` to build dashboards

---

## Interview Talking Points

- **Why Athena over Redshift?** — Athena is serverless and cost-effective for ad-hoc analysis; Redshift is better for sustained high-concurrency BI workloads. This project uses Athena to demonstrate the query-on-S3 pattern common in data lake architectures.
- **Partitioning strategy** — Partitioning by `year/month` reduces data scanned per query by up to 90% for time-ranged filters.
- **CTAS for materialized views** — Used to pre-aggregate KPIs and reduce QuickSight SPICE refresh latency.
- **Data quality as a first-class concern** — Validation SQL runs before any analytical query to catch nulls, duplicates, and referential integrity failures.
- **Cost optimization** — Parquet columnar format reduces Athena scan costs by ~75% vs. raw CSV.

---

## Future Improvements

- [ ] Replace static CTAS with scheduled Glue ETL jobs
- [ ] Add dbt models for transformation layer
- [ ] Implement column-level data lineage with AWS Lake Formation
- [ ] Add row-level security in QuickSight for regional managers
- [ ] CI/CD pipeline for SQL linting and regression tests (SQLFluff + GitHub Actions)
- [ ] Add Terraform IaC for reproducible AWS infrastructure

---

## License

MIT — see [LICENSE](LICENSE)
