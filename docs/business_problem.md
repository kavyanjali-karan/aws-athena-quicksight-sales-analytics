# Business Problem

## Context

A multi-region retail company sells products across five geographic regions in the United States.
The company operates in five product categories — Technology, Furniture, Office Supplies,
Clothing, and Sports & Outdoors — and serves three customer segments: Consumer, Corporate, and
Home Office.

As the company has grown, business stakeholders have struggled to answer fundamental questions
consistently and quickly:

- How is revenue trending month-over-month?
- Which regions are growing fastest, and which are at risk?
- Are discounts helping acquire customers or simply eroding margin?
- Who are the most valuable customers, and when should we expect them to churn?

---

## The Problem

Before this BI pipeline, the company relied on:

1. **Manual exports** from the transactional database into Excel spreadsheets
2. **Ad-hoc Python scripts** with no version control or reproducibility
3. **Monthly reporting cycles** — by the time a dashboard was ready, decisions had already been made on gut instinct

This created three failure modes:

| Failure | Business Impact |
|---|---|
| Inconsistent metric definitions | Two teams reporting different "revenue" numbers for the same month |
| No single source of truth | Finger-pointing about whose numbers were correct |
| Slow reporting cycle | Missed opportunities to react to sales dips in time |

---

## Business Questions This Pipeline Answers

### Executive / Finance

1. What is total revenue, gross profit, and gross margin YTD?
2. Are we on track to hit annual revenue targets?
3. Which quarter shows the strongest seasonality?
4. How does this year's revenue compare to last year by quarter?

### Sales / Regional

5. Which regions are growing and which are declining?
6. What is the revenue contribution from each region as a % of total?
7. Which cities within each region drive the most orders?
8. How does average order value differ by region?

### Marketing / CRM

9. Who are our top-LTV customers, and what is the average LTV by segment?
10. Which customers are at risk of churning (At-Risk RFM segment)?
11. What is the retention rate for each customer signup cohort?
12. How does the Consumer segment compare to Corporate in profitability?

### Operations

13. What is the average time from order to shipment?
14. Which products are being returned or discounted most aggressively?
15. Are there data quality anomalies — duplicates, nulls, or invalid values — entering the pipeline?

---

## Success Criteria

| Metric | Target |
|---|---|
| Dashboard refresh latency | < 6 hours (daily SPICE refresh) |
| Query response time (SPICE) | < 2 seconds for all dashboard visuals |
| Metric consistency | Zero discrepancy between Executive and Regional totals |
| Data quality | 0 critical DQ violations per daily check |
| Coverage | 100% of business questions answered without ad-hoc SQL |
