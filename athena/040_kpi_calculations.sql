-- =============================================================================
-- 04_kpi_calculations.sql
-- Purpose : Core business KPIs used across all executive reportings.
--           Results are materialised as CTAS tables for QuickSight SPICE.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- KPI 1 — Total Revenue, Gross Profit, and Gross Margin
-- ---------------------------------------------------------------------------
SELECT
    SUM(t.net_revenue)                                              AS total_revenue,
    SUM(t.net_revenue - p.unit_cost * t.quantity)                  AS total_gross_profit,
    ROUND(
        SUM(t.net_revenue - p.unit_cost * t.quantity)
        / NULLIF(SUM(t.net_revenue), 0) * 100,
        2
    )                                                               AS gross_margin_pct,
    COUNT(DISTINCT t.transaction_id)                               AS total_orders,
    COUNT(DISTINCT t.customer_id)                                  AS unique_customers,
    ROUND(SUM(t.net_revenue) / COUNT(DISTINCT t.transaction_id), 2) AS avg_order_value,
    ROUND(AVG(t.discount) * 100, 2)                                AS avg_discount_pct
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id;

-- ---------------------------------------------------------------------------
-- KPI 2 — Quarterly revenue (useful for trend cards)
-- ---------------------------------------------------------------------------
SELECT
    t.year,
    CEIL(CAST(t.month AS DOUBLE) / 3)                   AS quarter,
    SUM(t.net_revenue)                                  AS quarterly_revenue,
    COUNT(DISTINCT t.transaction_id)                    AS order_count,
    COUNT(DISTINCT t.customer_id)                       AS unique_customers
FROM sales_transactions t
GROUP BY t.year, CEIL(CAST(t.month AS DOUBLE) / 3)
ORDER BY t.year, quarter;

-- ---------------------------------------------------------------------------
-- KPI 3 — Year-over-Year revenue growth
-- ---------------------------------------------------------------------------
WITH yearly AS (
    SELECT
        year,
        SUM(net_revenue) AS annual_revenue
    FROM sales_transactions
    GROUP BY year
)
SELECT
    curr.year,
    ROUND(curr.annual_revenue, 2)                                          AS revenue,
    ROUND(prev.annual_revenue, 2)                                          AS prev_year_revenue,
    ROUND((curr.annual_revenue - prev.annual_revenue)
          / NULLIF(prev.annual_revenue, 0) * 100, 2)                      AS yoy_growth_pct
FROM yearly curr
LEFT JOIN yearly prev ON curr.year = prev.year + 1
ORDER BY curr.year;

-- ---------------------------------------------------------------------------
-- KPI 4 — Average days to ship
-- ---------------------------------------------------------------------------
SELECT
    region,
    ROUND(AVG(DATE_DIFF('day', order_date, ship_date)), 2) AS avg_days_to_ship,
    MIN(DATE_DIFF('day', order_date, ship_date))           AS min_days_to_ship,
    MAX(DATE_DIFF('day', order_date, ship_date))           AS max_days_to_ship
FROM sales_transactions
GROUP BY region
ORDER BY avg_days_to_ship;

-- ---------------------------------------------------------------------------
-- KPI 5 — Discount impact on revenue
-- ---------------------------------------------------------------------------
SELECT
    CASE
        WHEN discount = 0          THEN '0% — No discount'
        WHEN discount <= 0.05      THEN '1–5%'
        WHEN discount <= 0.10      THEN '6–10%'
        WHEN discount <= 0.20      THEN '11–20%'
        ELSE '> 20%'
    END                                                             AS discount_bucket,
    COUNT(*)                                                        AS order_count,
    ROUND(SUM(net_revenue), 2)                                      AS total_revenue,
    ROUND(AVG(net_revenue), 2)                                      AS avg_order_value,
    ROUND(SUM(net_revenue - p.unit_cost * t.quantity), 2)           AS total_gross_profit,
    ROUND(
        SUM(net_revenue - p.unit_cost * t.quantity)
        / NULLIF(SUM(net_revenue), 0) * 100,
        2
    )                                                               AS gross_margin_pct
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY 1
ORDER BY MIN(discount);
