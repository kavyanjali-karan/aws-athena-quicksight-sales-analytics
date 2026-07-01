-- =============================================================================
-- 06_profitability.sql
-- Purpose : Gross profit, margin analysis, and discount impact by category.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- Profitability by product category
-- ---------------------------------------------------------------------------
SELECT
    p.category,
    COUNT(DISTINCT t.transaction_id)                                AS order_count,
    ROUND(SUM(t.net_revenue), 2)                                    AS total_revenue,
    ROUND(SUM(t.net_revenue - p.unit_cost * t.quantity), 2)         AS gross_profit,
    ROUND(
        SUM(t.net_revenue - p.unit_cost * t.quantity)
        / NULLIF(SUM(t.net_revenue), 0) * 100,
        2
    )                                                               AS gross_margin_pct,
    ROUND(AVG(t.discount) * 100, 2)                                 AS avg_discount_pct,
    ROUND(AVG(t.net_revenue), 2)                                    AS avg_order_value
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.category
ORDER BY gross_margin_pct DESC;

-- ---------------------------------------------------------------------------
-- Profitability by sub-category
-- ---------------------------------------------------------------------------
SELECT
    p.category,
    p.sub_category,
    ROUND(SUM(t.net_revenue), 2)                                    AS revenue,
    ROUND(SUM(t.net_revenue - p.unit_cost * t.quantity), 2)         AS gross_profit,
    ROUND(
        SUM(t.net_revenue - p.unit_cost * t.quantity)
        / NULLIF(SUM(t.net_revenue), 0) * 100,
        2
    )                                                               AS gross_margin_pct,
    RANK() OVER (ORDER BY SUM(t.net_revenue) DESC)                  AS revenue_rank
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.category, p.sub_category
ORDER BY revenue_rank;

-- ---------------------------------------------------------------------------
-- Monthly gross margin trend (useful for detecting margin erosion)
-- ---------------------------------------------------------------------------
SELECT
    t.year,
    t.month,
    p.category,
    ROUND(SUM(t.net_revenue), 2)                                    AS revenue,
    ROUND(SUM(t.net_revenue - p.unit_cost * t.quantity), 2)         AS gross_profit,
    ROUND(
        SUM(t.net_revenue - p.unit_cost * t.quantity)
        / NULLIF(SUM(t.net_revenue), 0) * 100,
        2
    )                                                               AS gross_margin_pct
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY t.year, t.month, p.category
ORDER BY t.year, t.month, p.category;

-- ---------------------------------------------------------------------------
-- High-discount, low-margin transactions (risk identification)
-- ---------------------------------------------------------------------------
SELECT
    t.transaction_id,
    t.order_date,
    p.product_name,
    p.category,
    t.quantity,
    ROUND(t.unit_price, 2)                                          AS unit_price,
    ROUND(t.discount * 100, 1)                                      AS discount_pct,
    ROUND(t.net_revenue, 2)                                         AS net_revenue,
    ROUND(t.net_revenue - p.unit_cost * t.quantity, 2)              AS gross_profit,
    ROUND(
        (t.net_revenue - p.unit_cost * t.quantity)
        / NULLIF(t.net_revenue, 0) * 100,
        2
    )                                                               AS margin_pct
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id
WHERE t.discount >= 0.20
  AND (t.net_revenue - p.unit_cost * t.quantity) < 0
ORDER BY gross_profit ASC
LIMIT 100;
