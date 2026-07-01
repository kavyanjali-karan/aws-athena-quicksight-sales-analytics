# Regional Dashboard Specification

## Purpose

Enable regional managers and operations teams to compare performance across geographic
markets, identify growth opportunities, and monitor market share shifts over time.

---

## Data Sources (Athena)

| Dataset | Athena Query |
|---|---|
| Regional summary | `07_regional_performance.sql` → revenue by region |
| YoY regional | `07_regional_performance.sql` → YoY comparison |
| City-level | `07_regional_performance.sql` → top cities |
| Monthly by region | `07_regional_performance.sql` → monthly trend |
| Market share | `07_regional_performance.sql` → market share shift |
| Profitability | `06_profitability.sql` → enriched with region |

SPICE refresh schedule: **Daily at 06:00 UTC**

---

## KPI Cards (top row — dynamically filtered by selected region)

| Card | Metric | Calculation |
|---|---|---|
| Region Revenue | `SUM(net_revenue)` for selected region | Filtered regional summary |
| Region Orders | `COUNT(DISTINCT transaction_id)` | Filtered regional summary |
| Revenue per Customer | `revenue / unique_customers` | Calculated field |
| Avg Days to Ship | `AVG(DATE_DIFF(order_date, ship_date))` | KPI 4 |
| Market Share | `region_revenue / total_revenue × 100` | Regional market share query |
| YoY Growth | `(curr − prior) / prior × 100` | YoY regional query |

---

## Visuals

### 1 — Regional Revenue Comparison (Grouped Bar Chart — All Regions)

- **Type:** Grouped bar chart
- **X-axis:** Region
- **Y-axis:** Revenue
- **Groups (color):** Year (2020, 2021, 2022, 2023)
- **Tooltip:** Revenue, orders, unique customers, YoY growth %
- **Interaction:** Click a bar → filter all other visuals to that region

### 2 — Market Share by Region Over Time (Stacked Area Chart)

- **Type:** 100% stacked area chart
- **X-axis:** Month (`YYYY-MM`)
- **Y-axis:** Revenue share % (0–100%)
- **Color:** Region
- **Purpose:** Identify market share gains and losses over time

### 3 — Regional Monthly Revenue Trend (Small Multiples — Line Charts)

- **Type:** Small multiples (one line chart per region, 5 charts in grid)
- **X-axis:** Month
- **Y-axis:** Revenue
- **Color:** Consistent region color
- **Reference line:** Overall monthly average across all regions
- **Drill-down:** Click chart → enter full regional view

### 4 — Top 5 Cities per Region (Bar Chart — Parameterised)

- **Type:** Horizontal bar chart
- **Filter:** Controlled by Region selector parameter
- **Dimension:** `city`
- **Measure:** `SUM(net_revenue)`
- **Tooltip:** City, revenue, orders, unique customers
- **Sorting:** Revenue descending

### 5 — Regional Profitability Matrix (Heatmap / Pivot Table)

- **Type:** Pivot table with conditional formatting
- **Rows:** Region
- **Columns:** Category
- **Values:** Gross margin %
- **Conditional formatting:** Red (< 10%) / Amber (10–20%) / Green (> 20%)
- **Purpose:** Identify which category × region combinations are margin-negative

### 6 — Revenue vs. Discount Rate by Region (Bubble Chart)

- **X-axis:** Avg discount %
- **Y-axis:** Gross margin %
- **Bubble size:** Revenue
- **Color:** Region
- **Quadrants:** Reference lines at overall avg discount and margin
- **Purpose:** Compare how aggressively each region discounts and the impact

### 7 — YoY Growth by Region (Table with Sparklines)

- **Type:** Table
- **Columns:** Region, 2020 Revenue, 2021 Revenue, 2022 Revenue, 2023 Revenue, CAGR, YoY Growth %, Sparkline
- **Conditional formatting:** Growth % → red (negative) / green (positive)
- **Sorting:** CAGR descending

---

## Filters

| Filter | Type | Default |
|---|---|---|
| Region | Multi-select (with "All" toggle) | All regions |
| Year | Multi-select | All years |
| Month range | Slider / date picker | Full year |
| Category | Multi-select | All categories |

---

## Drill-Down Paths

```
All Regions view
  └── Click region (KPI filter or bar) → Single Region view
        └── Top Cities chart filters to selected region
        └── Monthly trend shows only selected region
              └── Click city → City-level detail (customers, orders)
```

---

## Business Questions Answered

1. Which region generates the most revenue and has grown the fastest?
2. Is any region losing market share?
3. Which cities within each region are the top revenue drivers?
4. How does profitability vary across region × category combinations?
5. Which regions use the most aggressive discounting, and what is the margin cost?
6. What is the year-over-year growth trend for each region?

---

## Layout

```
┌───────────────────────────────────────────────────────────────────┐
│ [Logo]  Regional Performance Dashboard    [Filters: Region / Year] │
├───────┬────────┬──────────┬────────────┬──────────┬──────────────┤
│Region │ Orders │Rev/Cust  │Avg Ship Days│Mkt Share │ YoY Growth  │
│ KPI   │  KPI   │   KPI    │    KPI     │   KPI    │    KPI      │
├──────────────────────────────┬────────────────────────────────────┤
│ Regional Revenue Grouped Bar │ Market Share Stacked Area          │
│         (large)              │         (large)                    │
├──────────────────────────────┴────────────────────────────────────┤
│         Regional Monthly Trend — Small Multiples (5-up)           │
├───────────────────────────┬───────────────────────────────────────┤
│ Top 5 Cities Bar Chart    │ Profitability Heatmap (region×category)│
│       (medium)            │              (medium)                 │
├───────────────────────────┴───────────────────────────────────────┤
│ Revenue vs Discount Bubble    │ YoY Growth Table with Sparklines  │
│          (medium)             │          (wide)                   │
└───────────────────────────────────────────────────────────────────┘
```
