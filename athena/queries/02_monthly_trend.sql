-- Monthly income trend with month-over-month growth (24 months, 2024-2025).

WITH monthly AS (
    SELECT
        SUBSTR(CAST(order_date AS VARCHAR), 1, 7) AS sales_month,
        COUNT(*) AS transactions,
        SUM(income) AS income
    FROM sales_curated
    GROUP BY 1
)
SELECT
    sales_month,
    transactions,
    CAST(income AS DECIMAL(18, 2)) AS income,
    CAST(
        ROUND(
            100.0
            * (income - LAG(income) OVER (ORDER BY sales_month))
            / LAG(income) OVER (ORDER BY sales_month),
            1
        )
        AS DOUBLE
    ) AS mom_growth_pct
FROM monthly
ORDER BY sales_month;
