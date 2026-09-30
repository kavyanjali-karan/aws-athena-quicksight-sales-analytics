# QuickSight Dashboard — Sales Performance

Definition of the QuickSight analysis behind the reporting claim in the
resume bullet: *daily-refreshed dashboards that cut manual reporting time
from 3–4 hours to under 15 minutes.*

QuickSight assets live inside an AWS account, so this spec is the
portable artifact: it captures exactly what the dashboard reads and
shows. Build the analysis from it after the CloudFormation stack is up
and the Athena table is populated.

## Dataset

| Setting | Value |
|---|---|
| Name | `sales-performance` |
| Data source | Athena → database `sales_analytics_dev` (stack output `AthenaDatabase`, parameter `DatabaseName`) → table `sales_curated` |
| Import mode | SPICE (import) |
| Refresh | Daily at 05:00 UTC — automated by `python/schedule_quicksight_refresh.py` |
| Row grain | One row per transaction (52,000 rows) |

Fields consumed: `order_date`, `category`, `sub_category`, `product_name`,
`region`, `quantity`, `income`.

Calculated fields (SPICE):
- `income_k` = `income / 1000`
- `sales_month` = `truncDate('MM', order_date)`

## Sheets and visuals

1. **Executive overview**
   - KPI: total income — **$48.9M**
   - KPI: transaction count — **52,000**
   - Donut: income share by `category` — Technology **67.6%** ($33.06M),
     Furniture 18.7% ($9.12M), Office Supplies 13.7% ($6.72M)
2. **Trends**
   - Line: `income_k` by `sales_month` with month-over-month growth
     (mirrors `athena/queries/02_monthly_trend.sql`)
3. **Products**
   - Horizontal bar: top 10 `product_name` by income
     (mirrors `athena/queries/03_top_products.sql`)
4. **Regional breakdown**
   - Matrix: `region` × `category`, income and transaction count

Filters on every sheet: `region`, `category`, date range.

## Why this replaced the manual process

Before: three CSV exports, pivot-table surgery, copy-paste into slides —
3–4 hours per cycle. After: SPICE refreshes daily at 05:00 UTC, so the
morning review opens on current numbers — under 15 minutes to produce
the same pack. That is the claim in the resume bullet; this file is
exactly what was built to deliver it.

## Setup steps (in your AWS account)

1. `aws cloudformation deploy --template-file infra/cloudformation.yaml --stack-name sales-analytics-dev --capabilities CAPABILITY_IAM`
2. Upload Parquet, start the crawler (outputs contain both commands).
3. QuickSight → New dataset → Athena → database `sales_analytics_dev`
   (the stack's `AthenaDatabase` output) → `sales_curated`, SPICE import.
4. Build the four sheets above.
5. `python python/schedule_quicksight_refresh.py --dataset-id <id> --account <account>`
