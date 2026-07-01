# Screenshots

This directory is reserved for dashboard and pipeline screenshots.

## How to Add Screenshots

After completing the AWS setup and building the QuickSight dashboards, capture and save screenshots here:

| File | Description |
|---|---|
| `executive_dashboard_overview.png` | Full Executive Dashboard showing all KPI cards and visuals |
| `executive_dashboard_trend.png` | Monthly Revenue + Gross Profit combo chart |
| `regional_dashboard_heatmap.png` | Region × Category profitability heatmap |
| `regional_dashboard_market_share.png` | Stacked area chart showing regional market share over time |
| `customer_dashboard_rfm.png` | RFM Bubble Chart with segment labels |
| `customer_dashboard_cohort.png` | Cohort retention heatmap |
| `athena_query_editor.png` | Athena Query Editor showing a KPI query and results |
| `glue_catalog.png` | Glue Data Catalog showing the `sales` database and tables |
| `s3_bucket_structure.png` | S3 bucket showing partitioned Parquet directory structure |

## Screenshot Tips

- Use 2560×1440 or 1920×1080 resolution for clarity
- Obscure any AWS account IDs or internal URLs before committing
- Save as PNG for lossless quality

> **Note:** Screenshots are not included in this repository because the pipeline uses synthetic data and requires an AWS account to deploy. Follow the [Setup Guide](../docs/aws_setup.md) to run the pipeline and generate your own screenshots for your portfolio.
