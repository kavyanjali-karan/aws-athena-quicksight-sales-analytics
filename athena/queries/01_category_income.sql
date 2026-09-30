-- Income share by product category.
-- Headline result: Technology = 67.6% of income ($33.06M of $48.9M).

SELECT
    category,
    COUNT(*) AS transactions,
    CAST(SUM(income) AS DECIMAL(18, 2)) AS income,
    CAST(
        ROUND(100.0 * SUM(income) / SUM(SUM(income)) OVER (), 1)
        AS DOUBLE
    ) AS pct_of_total
FROM sales_curated
GROUP BY category
ORDER BY income DESC;
