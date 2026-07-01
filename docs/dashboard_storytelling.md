# Dashboard Storytelling Guide

How to present the three dashboards to business stakeholders — the narrative
arc, key insights to highlight, and how to navigate the drill-down paths.

---

## Dashboard 1: Executive Dashboard

### Narrative

> "This dashboard gives leadership a single place to answer: Are we growing?  
> Where is the money coming from? And are we making money on it?"

### Recommended Walkthrough (5-minute demo)

1. **Open with the KPI row.** Point to Total Revenue and YoY Growth.
   - If growth is positive: "We're growing X% year-over-year. Let's see where that growth is coming from."
   - If growth is negative: "Revenue is down X% — let's diagnose why."

2. **Monthly Trend chart.** Walk left to right.
   - Highlight Q4 (Oct–Dec) as the strongest quarter driven by seasonal promotions.
   - Identify any dips and ask: "Does this match what we expected in that month?"

3. **Category Donut.** "Technology drives the largest share of revenue — but look at margin…"

4. **Discount vs. Margin Scatter.** "This is our risk view. Anything in the upper-left (high discount, low margin) is a campaign we need to revisit."

5. **Top 10 Products Table.** "These 10 products account for ~30% of revenue. If any goes out of stock, we feel it immediately."

---

## Dashboard 2: Regional Dashboard

### Narrative

> "Each region operates like a mini-business. This dashboard helps us compare them  
> apples-to-apples and ask: which regions deserve more investment?"

### Recommended Walkthrough

1. **KPI row.** Filter to a single region. Show "Market Share %" and "YoY Growth."

2. **Market Share Stacked Area.** "Over the last 4 years, West has been taking share from Midwest. Let's understand why."

3. **Small Multiples trend grid.** "All 5 regions at once. Notice how Q4 spikes more in Northeast than Southwest — different customer mix."

4. **Profitability Heatmap.** "This is the most important chart for operations. Red = we're selling in this region × category at a loss. Click any red cell to see which products."

5. **YoY Growth Table.** "Sort by CAGR. West grew 18% compounded over 4 years — it deserves more headcount and marketing budget."

---

## Dashboard 3: Customer Dashboard

### Narrative

> "Our customers are not all equal. This dashboard helps us find our best customers,  
> protect them, and identify who we're about to lose."

### Recommended Walkthrough

1. **LTV Distribution Histogram.** "Most customers cluster below $500 LTV — but there's a long right tail. Those outliers are our VIPs."

2. **RFM Bubble Chart.** "Champions — top-right, biggest bubbles — are our healthiest customers. At-Risk in the lower-left are people who used to be Champions but haven't come back."

3. **RFM Segment Table.** "The 'Action Recommended' column is your CRM playbook. Champions go into the loyalty program. At-Risk get a win-back email within 7 days."

4. **Cohort Retention Heatmap.** "Read across any row — that's how a single signup cohort behaved month by month. The 2021 cohorts show strong 3-month retention, then drop off. Why? Explore with the segment filter."

5. **Geographic Map.** "Our best customers are concentrated in New York, Los Angeles, and Chicago. Any regional marketing spend should start here."

---

## Common Stakeholder Questions and Answers

| Question | Where to look |
|---|---|
| "Why did revenue drop in March?" | Executive → Monthly Trend → hover March → drill to Regional |
| "Which region has the highest margin?" | Regional → Profitability Heatmap |
| "Are we too dependent on a few customers?" | Customer → LTV Distribution + Pareto from `09_top_products.sql` |
| "What is our churn risk?" | Customer → At-Risk KPI + RFM Segment Table |
| "Is the Q4 promotion hurting margin?" | Executive → Discount vs. Margin Scatter → filter by Q4 |
| "Which products should we discontinue?" | Executive → Top 10 Table → sort by Margin % ascending |

---

## Data Refresh Awareness

Always communicate the data freshness to stakeholders:

> "Data in this dashboard is refreshed daily at 6:00 AM UTC.  
> Yesterday's transactions are visible. Today's orders will appear tomorrow morning."

This sets correct expectations and prevents confusion when a deal closed today doesn't appear yet.
