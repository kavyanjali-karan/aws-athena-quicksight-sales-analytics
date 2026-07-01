-- =============================================================================
-- 07_regional_performance.sql
-- Purpose : Regional revenue breakdown, ranking, and growth comparisons.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- Revenue, orders, and margin by region
-- ---------------------------------------------------------------------------
SELECT
    t.region,
    COUNT(DISTINCT t.transaction_id)                                AS order_count,
    COUNT(DISTINCT t.customer_id)                                   AS unique_customers,
    ROUND(SUM(t.net_revenue), 2)                                    AS total_revenue,
    ROUND(SUM(t.net_revenue) / COUNT(DISTINCT t.transaction_id), 2) AS avg_order_value,
    ROUND(SUM(t.net_revenue) / COUNT(DISTINCT t.customer_id), 2)    AS revenue_per_customer,
    ROUND(
        SUM(t.net_revenue - p.unit_cost * t.quantity)
        / NULLIF(SUM(t.net_revenue), 0) * 100,
        2
    )                                                               AS gross_margin_pct,
    ROUND(AVG(t.discount) * 100, 2)                                 AS avg_discount_pct,
    ROUND(SUM(t.net_revenue)
        / SUM(SUM(t.net_revenue)) OVER () * 100, 2)                AS revenue_share_pct
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY t.region
ORDER BY total_revenue DESC;

-- ---------------------------------------------------------------------------
-- Regional performance by year (YoY regional comparison)
-- ---------------------------------------------------------------------------
WITH regional_yearly AS (
    SELECT
        region,
        year,
        SUM(net_revenue) AS revenue
    FROM sales_transactions
    GROUP BY region, year
)
SELECT
    curr.region,
    curr.year,
    ROUND(curr.revenue, 2)                              AS revenue,
    ROUND(prior.revenue, 2)                             AS prior_year_revenue,
    ROUND(
        (curr.revenue - prior.revenue) / NULLIF(prior.revenue, 0) * 100,
        2
    )                                                   AS yoy_growth_pct
FROM regional_yearly curr
LEFT JOIN regional_yearly prior
    ON curr.region = prior.region
    AND curr.year  = prior.year + 1
ORDER BY curr.region, curr.year;

-- ---------------------------------------------------------------------------
-- Top cities by revenue within each region
-- ---------------------------------------------------------------------------
WITH city_revenue AS (
    SELECT
        c.region,
        c.city,
        ROUND(SUM(t.net_revenue), 2) AS revenue,
        COUNT(DISTINCT t.transaction_id) AS orders
    FROM sales_transactions t
    JOIN customers c ON t.customer_id = c.customer_id
    GROUP BY c.region, c.city
),
ranked AS (
    SELECT
        region,
        city,
        revenue,
        orders,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY revenue DESC) AS city_rank
    FROM city_revenue
)
SELECT region, city_rank, city, revenue, orders
FROM ranked
WHERE city_rank <= 5
ORDER BY region, city_rank;

-- ---------------------------------------------------------------------------
-- Monthly revenue trend per region (for small-multiples line chart)
-- ---------------------------------------------------------------------------
SELECT
    region,
    year,
    month,
    ROUND(SUM(net_revenue), 2) AS monthly_revenue,
    COUNT(DISTINCT transaction_id) AS orders
FROM sales_transactions
GROUP BY region, year, month
ORDER BY region, year, month;

-- ---------------------------------------------------------------------------
-- Regional market share shift (year comparison)
-- ---------------------------------------------------------------------------
WITH yr AS (
    SELECT
        region,
        year,
        SUM(net_revenue) AS revenue
    FROM sales_transactions
    GROUP BY region, year
),
totals AS (
    SELECT year, SUM(revenue) AS total FROM yr GROUP BY year
)
SELECT
    yr.region,
    yr.year,
    ROUND(yr.revenue, 2)                                    AS revenue,
    ROUND(yr.revenue / totals.total * 100, 2)               AS market_share_pct
FROM yr
JOIN totals ON yr.year = totals.year
ORDER BY yr.year, yr.revenue DESC;
