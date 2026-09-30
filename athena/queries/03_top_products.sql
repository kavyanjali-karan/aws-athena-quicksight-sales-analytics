-- Top 10 products by income.

WITH ranked AS (
    SELECT
        product_name,
        sub_category,
        COUNT(*) AS transactions,
        SUM(income) AS income,
        ROW_NUMBER() OVER (ORDER BY SUM(income) DESC) AS rn
    FROM sales_curated
    GROUP BY product_name, sub_category
)
SELECT
    product_name,
    sub_category,
    transactions,
    CAST(income AS DECIMAL(18, 2)) AS income
FROM ranked
WHERE rn <= 10
ORDER BY rn;
