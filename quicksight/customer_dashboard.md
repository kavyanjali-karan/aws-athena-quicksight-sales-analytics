# Customer Dashboard Specification

## Business Objective

Give sales, marketing, and CRM teams a clear view of customer lifetime value,
behavioral segmentation, cohort retention, and RFM scoring to support retention
and acquisition strategy.

---

## Data Sources (Athena)

| Dataset | Athena Query |
|---|---|
| Customer LTV | `08_customer_segmentation.sql` → LTV summary |
| Segment summary | `08_customer_segmentation.sql` → LTV by segment |
| RFM scores | `08_customer_segmentation.sql` → RFM scoring |
| Cohort retention | `08_customer_segmentation.sql` → cohort retention |
| Monthly new customers | derived from `customers.signup_date` + transactions |
| Customer-level transactions | join of `sales_transactions` + `customers` |

SPICE refresh schedule: **Daily at 06:00 UTC**

---

## KPI Cards (top row)

| Card | Metric | Calculation |
|---|---|---|
| Total Customers | `COUNT(DISTINCT customer_id)` | Customer LTV query |
| Avg LTV | `SUM(ltv) / COUNT(customers)` | Customer LTV query |
| Champions Count | Count where rfm_segment = 'Champions' | RFM query |
| At-Risk Count | Count where rfm_segment = 'At Risk' | RFM query |
| Avg Orders per Customer | `total_orders / unique_customers` | Calculated |
| Avg Days Between Orders | `AVG(lifespan / (orders - 1))` | Calculated |

---

## Visuals

### 1 — LTV Distribution (Histogram)

- **Business question:** Is customer value concentrated among a small number of high-spend accounts?
- **Type:** Histogram with 20 bins
- **X-axis:** Lifetime value (USD)
- **Y-axis:** Customer count
- **Reference lines:** Median LTV, 90th-percentile LTV
- **Color:** Segment (Consumer / Corporate / Home Office)
- **Purpose:** Show the heavy right tail — identify high-value customer concentration

### 2 — Customer Segment Revenue Contribution (Stacked Bar + Donut)

- **Business question:** Which customer segments contribute the most revenue and customer count?
- **Type:** Side-by-side view
  - Donut: Revenue share % by segment
  - Bar: Absolute revenue + customer count by segment
- **Dimensions:** Segment
- **Measures:** Revenue, customer count, avg LTV
- **Tooltip:** Segment, revenue, % of total, avg LTV, avg orders

### 3 — RFM Segment Bubble Chart

- **Business question:** Which customers are most valuable right now and which are at risk of churning?
- **X-axis:** Recency score (1–5, higher = more recent)
- **Y-axis:** Frequency score (1–5, higher = more frequent)
- **Bubble size:** Monetary score
- **Color:** RFM segment label (Champions / Loyal / At Risk / Lost / etc.)
- **Tooltip:** Segment name, customer count, avg monetary value
- **Purpose:** Classic RFM quadrant view for marketing prioritisation

### 4 — RFM Segment Summary (Table)

- **Business question:** Which customer segments need immediate retention or growth action?
- **Type:** Table with conditional formatting
- **Columns:** RFM Segment, Customer Count, % of Base, Avg LTV, Avg Orders, Avg Recency (days), Action Recommended
- **Conditional formatting:** At-Risk and Lost rows highlighted in red
- **Action Recommended** (calculated string field):
  - Champions → "Loyalty program, upsell"
  - At Risk → "Win-back campaign"
  - Lost → "Re-engagement or sunset"
  - Recent Customers → "Onboarding nurture"
  - Loyal → "Reward and retain"

### 5 — Cohort Retention Heatmap

- **Business question:** How does retention change across signup cohorts and months after first purchase?
- **Type:** Heatmap (cohort retention grid)
- **Rows:** Cohort month (signup month)
- **Columns:** Month number since signup (M+0, M+1, M+2, … M+12)
- **Values:** Retention % (% of cohort that transacted in that month)
- **Color scale:** 0% = white/light → 100% = dark brand color
- **Interpretation:** Darker diagonal = stronger retention; fading across rows = churn

### 6 — Monthly New vs. Returning Customers (Combo Chart)

- **Business question:** Are new customer acquisition rates improving and how does returning-customer behavior change over time?
- **Type:** Combo: bars = new customers, line = returning customer count
- **X-axis:** Month
- **Y-axis (left):** Customer count
- **Definition:**
  - New = first transaction in that month
  - Returning = had prior transactions
- **Tooltip:** Month, new count, returning count, ratio

### 7 — Top 20 Customers by LTV (Table)

- **Business question:** Which individual customers generate the highest lifetime revenue?
- **Type:** Table
- **Columns:** Rank, Customer Name, Segment, Region, LTV, Orders, First Order, Last Order, Days Active, Avg Order Value
- **Sorting:** LTV descending
- **Row action:** Click customer → filter transactions table to that customer

### 8 — Customer Geographic Distribution (Map Visual)

- **Business question:** Where geographically are the strongest customer clusters concentrated?
- **Type:** Point / bubble map (US states or city-level)
- **Dimension:** City / State
- **Measure:** `SUM(net_revenue)` or `COUNT(customer_id)`
- **Color:** Region
- **Bubble size:** Revenue or customer count
- **Tooltip:** City, state, customer count, total revenue

---

## Filters

| Filter | Type | Default |
|---|---|---|
| Segment | Multi-select | All segments |
| Region | Multi-select | All regions |
| RFM Segment | Multi-select | All RFM labels |
| Signup Year | Single-select | All years |
| Date Range (orders) | Date picker | Full dataset |

---

## Drill-Down Paths

```
dashboard level
  └── Click RFM segment bubble → Filter all visuals to that segment
        └── LTV distribution shows only that segment
        └── Top 20 table shows only that segment's customers
  └── Click cohort row → Highlight that cohort's retention across columns
  └── Click map region → Regional view filtered to that geography
```

---

## Business Questions Answered

1. What is the distribution of customer lifetime value — are we dependent on a few?
2. Which customer segment (Consumer / Corporate / Home Office) is most valuable?
3. Which customers are at risk of churning and should be targeted for win-back?
4. How does retention vary across signup cohorts?
5. Are new customer acquisition rates growing or declining month-over-month?
6. Which individual customers generate the highest lifetime revenue?
7. Where geographically are our best customers concentrated?

---

## Layout

```
┌────────────────────────────────────────────────────────────────────┐
│ [Logo]  Customer Intelligence Dashboard  [Filters: Segment / Region / RFM Segment / Signup Year / Date Range] │
├───────┬────────┬────────────┬───────────┬─────────┬───────────────┤
│Total  │Avg LTV │ Champions  │ At-Risk   │Avg Ord  │ Days Between  │
│Cust.  │  KPI   │   KPI      │   KPI     │  KPI    │  Orders KPI   │
├──────────────────────────┬─────────────────────────────────────────┤
│ LTV Histogram            │ Segment Revenue Donut + Bar             │
│      (large)             │         (medium)                        │
├──────────────────────────┴─────────────────────────────────────────┤
│              Cohort Retention Heatmap (full width)                  │
├──────────────────────────┬─────────────────────────────────────────┤
│ RFM Bubble Chart         │ RFM Segment Summary Table               │
│      (medium)            │         (medium-wide)                   │
├──────────────────────────┴─────────────────────────────────────────┤
│ New vs. Returning Customers │ Top 20 Customers Table               │
│         Combo Chart          │      (scrollable)                   │
├──────────────────────────────────────────────────────────────────┤
│              Geographic Distribution Map (full width)              │
└────────────────────────────────────────────────────────────────────┘
```
