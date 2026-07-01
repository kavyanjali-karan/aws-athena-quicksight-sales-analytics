-- =============================================================================
-- 09_top_products.sql
-- Purpose : Product performance ranking, revenue concentration, and velocity.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- Top 20 products by revenue with margin detail
-- ---------------------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    p.brand,
    COUNT(DISTINCT t.transaction_id)                                AS orders,
    SUM(t.quantity)                                                 AS units_sold,
    ROUND(SUM(t.net_revenue), 2)                                    AS total_revenue,
    ROUND(SUM(t.net_revenue - p.unit_cost * t.quantity), 2)         AS gross_profit,
    ROUND(
        SUM(t.net_revenue - p.unit_cost * t.quantity)
        / NULLIF(SUM(t.net_revenue), 0) * 100,
        2
    )                                                               AS margin_pct,
    ROUND(AVG(t.discount) * 100, 2)                                 AS avg_discount_pct,
    RANK() OVER (ORDER BY SUM(t.net_revenue) DESC)                  AS revenue_rank
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.sub_category, p.brand
ORDER BY revenue_rank
LIMIT 20;

-- ---------------------------------------------------------------------------
-- Top products within each category (top 5 per category)
-- ---------------------------------------------------------------------------
WITH product_rev AS (
    SELECT
        p.category,
        p.product_id,
        p.product_name,
        p.brand,
        ROUND(SUM(t.net_revenue), 2)                                AS revenue,
        ROUND(SUM(t.net_revenue - p.unit_cost * t.quantity), 2)     AS gross_profit,
        ROW_NUMBER() OVER (
            PARTITION BY p.category ORDER BY SUM(t.net_revenue) DESC
        )                                                           AS cat_rank
    FROM sales_transactions t
    JOIN products p ON t.product_id = p.product_id
    GROUP BY p.category, p.product_id, p.product_name, p.brand
)
SELECT category, cat_rank, product_id, product_name, brand, revenue, gross_profit
FROM product_rev
WHERE cat_rank <= 5
ORDER BY category, cat_rank;

-- ---------------------------------------------------------------------------
-- Revenue concentration — cumulative product Pareto
-- ---------------------------------------------------------------------------
WITH product_rev AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        SUM(t.net_revenue) AS revenue
    FROM sales_transactions t
    JOIN products p ON t.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.category
),
ranked AS (
    SELECT
        product_id,
        product_name,
        category,
        ROUND(revenue, 2)                                                   AS revenue,
        RANK() OVER (ORDER BY revenue DESC)                                 AS rank,
        SUM(revenue) OVER (ORDER BY revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)               AS running_total,
        SUM(revenue) OVER ()                                                AS grand_total
    FROM product_rev
)
SELECT
    rank,
    product_id,
    product_name,
    category,
    revenue,
    ROUND(running_total, 2)                         AS cumulative_revenue,
    ROUND(running_total / grand_total * 100, 2)     AS cumulative_pct
FROM ranked
ORDER BY rank;

-- ---------------------------------------------------------------------------
-- Product sales velocity (units sold per month, last 12 months)
-- ---------------------------------------------------------------------------
WITH recent AS (
    SELECT
        product_id,
        year,
        month,
        SUM(quantity) AS units_sold
    FROM sales_transactions
    WHERE year * 12 + month >= (
        SELECT MAX(year) * 12 + MAX(month) - 12
        FROM sales_transactions
    )
    GROUP BY product_id, year, month
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(r.units_sold)                               AS units_last_12_months,
    ROUND(AVG(r.units_sold), 2)                     AS avg_monthly_units,
    MAX(r.units_sold)                               AS peak_monthly_units,
    COUNT(DISTINCT r.year * 100 + r.month)          AS months_with_sales
FROM recent r
JOIN products p ON r.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY units_last_12_months DESC
LIMIT 30;
