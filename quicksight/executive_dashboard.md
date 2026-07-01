# Executive Dashboard Specification

## Purpose

Provide C-suite and senior leadership with a single-page view of business health:
total revenue, profitability, growth trends, and top-line regional and product performance.

---

## Data Sources (Athena)

| Dataset | Athena Query |
|---|---|
| Monthly revenue | `05_monthly_sales.sql` → monthly trend |
| KPI totals | `04_kpi_calculations.sql` → KPI 1 |
| YoY growth | `04_kpi_calculations.sql` → KPI 3 |
| Regional share | `07_regional_performance.sql` → market share |
| Profitability | `06_profitability.sql` → by category |
| Top products | `09_top_products.sql` → top 20 |

SPICE refresh schedule: **Daily at 06:00 UTC**

---

## KPI Cards (top row)

| Card | Metric | Calculation | Format |
|---|---|---|---|
| Total Revenue | `SUM(net_revenue)` for current year | Athena KPI 1 | `$X.XM` |
| Gross Margin | `gross_profit / revenue × 100` | Athena KPI 1 | `XX.X%` |
| Total Orders | `COUNT(DISTINCT transaction_id)` | Athena KPI 1 | `X,XXX` |
| Avg Order Value | `revenue / orders` | Athena KPI 1 | `$XXX.XX` |
| YoY Growth | `(curr − prior) / prior × 100` | Athena KPI 3 | `+XX.X%` ▲ / `−XX.X%` ▼ |
| Unique Customers | `COUNT(DISTINCT customer_id)` | Athena KPI 1 | `X,XXX` |

All KPI cards show a comparison indicator (vs. prior year, same period).

---

## Visuals

### 1 — Monthly Revenue & Gross Profit Trend (Line + Bar Combo)

- **Type:** Combo chart (bar = revenue, line = gross profit)
- **X-axis:** Month label (`YYYY-MM`)
- **Y-axis (left):** Net Revenue (USD)
- **Y-axis (right):** Gross Margin % (secondary axis)
- **Drill-down:** Click a month bar → Regional breakdown for that month
- **Color:** Revenue bars in brand primary; profit line in accent green

### 2 — Regional Revenue Breakdown (Horizontal Bar Chart)

- **Type:** Horizontal bar chart, sorted descending by revenue
- **Dimension:** `region`
- **Measure:** `SUM(net_revenue)`
- **Color coding:** One color per region (consistent across all dashboards)
- **Tooltip:** Orders, unique customers, avg order value, gross margin %
- **Drill-down:** Click region → city-level breakdown

### 3 — Revenue by Category (Donut Chart)

- **Type:** Donut / pie chart
- **Dimension:** `category`
- **Measure:** `SUM(net_revenue)` (% of total)
- **Legend:** Category names with revenue % labels
- **Interaction:** Click slice → filter entire dashboard by category

### 4 — YoY Revenue Comparison (Grouped Bar Chart)

- **Type:** Grouped bar chart
- **X-axis:** Year (2020, 2021, 2022, 2023)
- **Bars:** Grouped by quarter (Q1–Q4)
- **Measure:** `SUM(net_revenue)`
- **Tooltip:** Revenue, prior year revenue, YoY growth %

### 5 — Top 10 Products by Revenue (Table Visual)

- **Type:** Table with conditional formatting
- **Columns:** Rank, Product Name, Category, Revenue, Gross Profit, Margin %, Orders
- **Conditional formatting:** Margin % → red (< 15%) / amber (15–25%) / green (> 25%)
- **Sorting:** Revenue descending (default)

### 6 — Discount Impact on Margin (Scatter Plot)

- **X-axis:** Average discount % per transaction bucket
- **Y-axis:** Gross margin %
- **Bubble size:** Order count
- **Color:** Category
- **Purpose:** Visually communicate the margin erosion at high discount rates

---

## Filters (Global — affect all visuals on page)

| Filter | Type | Default |
|---|---|---|
| Year | Single-select dropdown | Current year |
| Region | Multi-select | All regions |
| Category | Multi-select | All categories |
| Date Range | Date picker | Jan 1 – Dec 31 current year |

---

## Drill-Down Paths

```
Dashboard level
  └── Click month bar → Regional breakdown for that month
        └── Click region → City breakdown
              └── Click city → Customer-level detail (Customer Dashboard)
  └── Click category slice → Category filtered view
        └── Click product name → Product detail sheet
```

---

## Business Questions Answered

1. Is total revenue on track vs. last year?
2. Which quarter had the highest growth?
3. Which region is under-performing?
4. Which product categories are most and least profitable?
5. Are discount promotions helping or hurting margin?
6. Which individual products drive the most revenue?

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  [Logo]   Executive Sales Dashboard          [Filters: Year/Region] │
├────────┬────────┬────────┬────────┬────────┬────────────────────┤
│Revenue │Margin  │ Orders │Avg AOV │YoY Grw │Unique Customers    │
│ KPI ▲  │ KPI ▲  │ KPI ▲  │ KPI ▲  │ KPI ▲  │ KPI ▲              │
├────────────────────────────┬───────────────────────────────────┤
│ Monthly Rev + Profit Trend │ Regional Revenue Bar Chart        │
│         (large)            │         (medium)                  │
├──────────────────┬─────────┴──────────────────────────────────┤
│ Category Donut   │ YoY Grouped Bar Chart                       │
│   (medium)       │         (medium)                            │
├──────────────────┴────────────────────────────────────────────┤
│ Top 10 Products Table           │ Discount vs. Margin Scatter  │
│         (medium-wide)           │         (medium)             │
└──────────────────────────────────────────────────────────────┘
```
