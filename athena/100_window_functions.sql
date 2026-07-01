-- =============================================================================
-- 10_window_functions.sql
-- Purpose : Showcase production-grade analytical window functions:
--           running totals, rankings, moving averages, percentiles, NTILE.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- 1. Running revenue total (cumulative monthly)
-- ---------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        year,
        month,
        ROUND(SUM(net_revenue), 2) AS revenue
    FROM sales_transactions
    GROUP BY year, month
)
SELECT
    year,
    month,
    revenue,
    ROUND(
        SUM(revenue) OVER (ORDER BY year, month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
        2
    )                           AS running_total,
    ROUND(
        SUM(revenue) OVER (PARTITION BY year ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
        2
    )                           AS ytd_running_total
FROM monthly
ORDER BY year, month;

-- ---------------------------------------------------------------------------
-- 2. 3-month moving average (revenue smoothing)
-- ---------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        year,
        month,
        ROUND(SUM(net_revenue), 2) AS revenue
    FROM sales_transactions
    GROUP BY year, month
)
SELECT
    year,
    month,
    revenue,
    ROUND(
        AVG(revenue) OVER (ORDER BY year, month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),
        2
    )                           AS revenue_3mo_avg
FROM monthly
ORDER BY year, month;

-- ---------------------------------------------------------------------------
-- 3. Customer revenue ranking (RANK, DENSE_RANK, PERCENT_RANK)
-- ---------------------------------------------------------------------------
WITH customer_ltv AS (
    SELECT
        customer_id,
        ROUND(SUM(net_revenue), 2) AS lifetime_value
    FROM sales_transactions
    GROUP BY customer_id
)
SELECT
    customer_id,
    lifetime_value,
    RANK()         OVER (ORDER BY lifetime_value DESC)      AS rank,
    DENSE_RANK()   OVER (ORDER BY lifetime_value DESC)      AS dense_rank,
    ROW_NUMBER()   OVER (ORDER BY lifetime_value DESC)      AS row_num,
    ROUND(
        PERCENT_RANK() OVER (ORDER BY lifetime_value DESC) * 100,
        2
    )                                                       AS percentile_rank,
    NTILE(10)      OVER (ORDER BY lifetime_value DESC)      AS decile
FROM customer_ltv
ORDER BY rank;

-- ---------------------------------------------------------------------------
-- 4. Revenue contribution as percentage of period total (RATIO_TO_REPORT equivalent)
-- ---------------------------------------------------------------------------
WITH monthly_region AS (
    SELECT
        year,
        month,
        region,
        SUM(net_revenue) AS revenue
    FROM sales_transactions
    GROUP BY year, month, region
)
SELECT
    year,
    month,
    region,
    ROUND(revenue, 2)                                           AS revenue,
    ROUND(
        revenue / SUM(revenue) OVER (PARTITION BY year, month) * 100,
        2
    )                                                           AS pct_of_month,
    ROUND(
        revenue / SUM(revenue) OVER (PARTITION BY year) * 100,
        2
    )                                                           AS pct_of_year
FROM monthly_region
ORDER BY year, month, revenue DESC;

-- ---------------------------------------------------------------------------
-- 5. Lead / Lag — sequential order gap analysis (days between orders per customer)
-- ---------------------------------------------------------------------------
WITH ordered_txns AS (
    SELECT
        customer_id,
        order_date,
        net_revenue,
        LAG(order_date)   OVER (PARTITION BY customer_id ORDER BY order_date)  AS prev_order_date,
        LEAD(order_date)  OVER (PARTITION BY customer_id ORDER BY order_date)  AS next_order_date
    FROM sales_transactions
)
SELECT
    customer_id,
    order_date,
    prev_order_date,
    DATE_DIFF('day', prev_order_date, order_date)   AS days_since_last_order,
    net_revenue
FROM ordered_txns
WHERE prev_order_date IS NOT NULL
ORDER BY customer_id, order_date
LIMIT 500;

-- ---------------------------------------------------------------------------
-- 6. First and last purchase date per customer (FIRST_VALUE / LAST_VALUE)
-- ---------------------------------------------------------------------------
SELECT DISTINCT
    customer_id,
    FIRST_VALUE(order_date) OVER (
        PARTITION BY customer_id ORDER BY order_date ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                                           AS first_purchase_date,
    LAST_VALUE(order_date)  OVER (
        PARTITION BY customer_id ORDER BY order_date ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                                           AS last_purchase_date,
    FIRST_VALUE(net_revenue) OVER (
        PARTITION BY customer_id ORDER BY order_date ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                                           AS first_order_value,
    LAST_VALUE(net_revenue)  OVER (
        PARTITION BY customer_id ORDER BY order_date ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                                           AS last_order_value
FROM sales_transactions
ORDER BY customer_id
LIMIT 200;

-- ---------------------------------------------------------------------------
-- 7. Monthly revenue percentile buckets using NTILE
-- ---------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        year,
        month,
        region,
        SUM(net_revenue) AS revenue
    FROM sales_transactions
    GROUP BY year, month, region
)
SELECT
    year,
    month,
    region,
    ROUND(revenue, 2)                                       AS revenue,
    NTILE(4) OVER (ORDER BY revenue DESC)                   AS quartile,
    NTILE(10) OVER (ORDER BY revenue DESC)                  AS decile
FROM monthly
ORDER BY year, month, region;
