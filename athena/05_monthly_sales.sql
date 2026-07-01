-- =============================================================================
-- 05_monthly_sales.sql
-- Purpose : Monthly and quarterly sales trends with MoM/QoQ comparisons.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- Monthly revenue trend
-- ---------------------------------------------------------------------------
SELECT
    year,
    month,
    DATE_FORMAT(DATE(CONCAT(CAST(year AS VARCHAR), '-', LPAD(CAST(month AS VARCHAR), 2, '0'), '-01')), '%Y-%m') AS month_label,
    ROUND(SUM(net_revenue), 2)                AS monthly_revenue,
    COUNT(DISTINCT transaction_id)            AS order_count,
    COUNT(DISTINCT customer_id)               AS unique_customers,
    ROUND(SUM(net_revenue) / COUNT(DISTINCT transaction_id), 2) AS avg_order_value,
    ROUND(AVG(quantity), 2)                   AS avg_units_per_order,
    ROUND(AVG(discount) * 100, 2)             AS avg_discount_pct
FROM sales_transactions
GROUP BY year, month
ORDER BY year, month;

-- ---------------------------------------------------------------------------
-- Month-over-Month growth rate (using LAG window function)
-- ---------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        year,
        month,
        SUM(net_revenue) AS revenue
    FROM sales_transactions
    GROUP BY year, month
),
with_lag AS (
    SELECT
        year,
        month,
        ROUND(revenue, 2) AS revenue,
        LAG(revenue) OVER (ORDER BY year, month) AS prev_month_revenue
    FROM monthly
)
SELECT
    year,
    month,
    revenue,
    ROUND(prev_month_revenue, 2) AS prev_month_revenue,
    ROUND(
        (revenue - prev_month_revenue)
        / NULLIF(prev_month_revenue, 0) * 100,
        2
    ) AS mom_growth_pct
FROM with_lag
ORDER BY year, month;

-- ---------------------------------------------------------------------------
-- Same-month prior-year comparison (YoY by month)
-- ---------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        year,
        month,
        SUM(net_revenue) AS revenue
    FROM sales_transactions
    GROUP BY year, month
)
SELECT
    curr.year,
    curr.month,
    ROUND(curr.revenue, 2)      AS current_revenue,
    ROUND(prior.revenue, 2)     AS prior_year_revenue,
    ROUND(
        (curr.revenue - prior.revenue) / NULLIF(prior.revenue, 0) * 100,
        2
    )                           AS yoy_same_month_growth_pct
FROM monthly curr
LEFT JOIN monthly prior
    ON curr.month = prior.month
    AND curr.year  = prior.year + 1
ORDER BY curr.year, curr.month;

-- ---------------------------------------------------------------------------
-- Quarterly rollup with running total
-- ---------------------------------------------------------------------------
WITH quarterly AS (
    SELECT
        year,
        CEIL(CAST(month AS DOUBLE) / 3) AS quarter,
        SUM(net_revenue)                AS quarterly_revenue
    FROM sales_transactions
    GROUP BY year, CEIL(CAST(month AS DOUBLE) / 3)
)
SELECT
    year,
    CAST(quarter AS INT)                                AS quarter,
    ROUND(quarterly_revenue, 2)                         AS quarterly_revenue,
    ROUND(
        SUM(quarterly_revenue)
        OVER (PARTITION BY year ORDER BY quarter
              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
        2
    )                                                   AS ytd_revenue
FROM quarterly
ORDER BY year, quarter;
