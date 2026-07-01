-- =============================================================================
-- 11_data_quality_checks.sql
-- Purpose : Comprehensive data quality monitoring queries.
--           Schedule these via Amazon Athena scheduled queries or AWS Lambda
--           to run after each incremental load.
--           All "violation" queries should return 0 rows in a clean dataset.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- DQ-010  Completeness — row count baseline
-- ---------------------------------------------------------------------------
SELECT
    'customers'          AS table_name,
    COUNT(*)             AS row_count,
    COUNT(customer_id)   AS non_null_pk,
    COUNT(*) - COUNT(customer_id) AS null_pk_count
FROM customers
UNION ALL
SELECT
    'products',
    COUNT(*),
    COUNT(product_id),
    COUNT(*) - COUNT(product_id)
FROM products
UNION ALL
SELECT
    'sales_transactions',
    COUNT(*),
    COUNT(transaction_id),
    COUNT(*) - COUNT(transaction_id)
FROM sales_transactions;

-- ---------------------------------------------------------------------------
-- DQ-02  Uniqueness — duplicate primary keys
-- ---------------------------------------------------------------------------
SELECT 'customers'    AS table_name, customer_id   AS pk_value, COUNT(*) AS occurrences
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1
UNION ALL
SELECT 'products',    product_id,    COUNT(*)
FROM products
GROUP BY product_id
HAVING COUNT(*) > 1
UNION ALL
SELECT 'transactions', transaction_id, COUNT(*)
FROM sales_transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- ---------------------------------------------------------------------------
-- DQ-03  Validity — numeric range checks
-- ---------------------------------------------------------------------------
-- Products: unit_price must be positive and greater than unit_cost
SELECT 'products.unit_price <= 0'  AS check_name, COUNT(*) AS violations
FROM products WHERE unit_price <= 0
UNION ALL
SELECT 'products.unit_cost <= 0',  COUNT(*) FROM products WHERE unit_cost <= 0
UNION ALL
SELECT 'products.margin_pct < -50', COUNT(*) FROM products WHERE margin_pct < -50
UNION ALL
SELECT 'transactions.quantity < 1', COUNT(*) FROM sales_transactions WHERE quantity < 1
UNION ALL
SELECT 'transactions.discount < 0', COUNT(*) FROM sales_transactions WHERE discount < 0
UNION ALL
SELECT 'transactions.discount > 1', COUNT(*) FROM sales_transactions WHERE discount > 1
UNION ALL
SELECT 'transactions.unit_price <= 0', COUNT(*) FROM sales_transactions WHERE unit_price <= 0
UNION ALL
SELECT 'transactions.net_revenue < 0', COUNT(*) FROM sales_transactions WHERE net_revenue < 0;

-- ---------------------------------------------------------------------------
-- DQ-04  Temporal consistency
-- ---------------------------------------------------------------------------
SELECT 'ship_date < order_date'     AS check_name, COUNT(*) AS violations
FROM sales_transactions
WHERE ship_date < order_date
UNION ALL
SELECT 'order_date > today', COUNT(*)
FROM sales_transactions
WHERE order_date > CURRENT_DATE
UNION ALL
SELECT 'ship_date > today', COUNT(*)
FROM sales_transactions
WHERE ship_date > CURRENT_DATE
UNION ALL
SELECT 'signup_date in future', COUNT(*)
FROM customers
WHERE DATE(signup_date) > CURRENT_DATE;

-- ---------------------------------------------------------------------------
-- DQ-05  Domain validation
-- ---------------------------------------------------------------------------
SELECT 'invalid region (transactions)' AS check_name, COUNT(*) AS violations
FROM sales_transactions
WHERE region NOT IN ('Northeast', 'Southeast', 'Midwest', 'West', 'Southwest')
UNION ALL
SELECT 'invalid region (customers)', COUNT(*)
FROM customers
WHERE region NOT IN ('Northeast', 'Southeast', 'Midwest', 'West', 'Southwest')
UNION ALL
SELECT 'invalid segment', COUNT(*)
FROM customers
WHERE segment NOT IN ('Consumer', 'Corporate', 'Home Office');

-- ---------------------------------------------------------------------------
-- DQ-06  Referential integrity
-- ---------------------------------------------------------------------------
SELECT 'orphan customer_id in transactions' AS check_name, COUNT(*) AS violations
FROM sales_transactions t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'orphan product_id in transactions', COUNT(*)
FROM sales_transactions t
LEFT JOIN products p ON t.product_id = p.product_id
WHERE p.product_id IS NULL;

-- ---------------------------------------------------------------------------
-- DQ-07  Statistical anomalies — outlier detection
-- ---------------------------------------------------------------------------
WITH stats AS (
    SELECT
        AVG(net_revenue)    AS avg_rev,
        STDDEV(net_revenue) AS std_rev
    FROM sales_transactions
)
SELECT
    transaction_id,
    order_date,
    net_revenue,
    ROUND((net_revenue - stats.avg_rev) / stats.std_rev, 2) AS z_score
FROM sales_transactions, stats
WHERE ABS((net_revenue - stats.avg_rev) / stats.std_rev) > 4
ORDER BY z_score DESC;

-- ---------------------------------------------------------------------------
-- DQ-08  Freshness check — latest data timestamp by partition
-- ---------------------------------------------------------------------------
SELECT
    year,
    month,
    MAX(order_date) AS latest_order_date,
    COUNT(*)        AS row_count
FROM sales_transactions
GROUP BY year, month
ORDER BY year DESC, month DESC
LIMIT 6;

-- ---------------------------------------------------------------------------
-- DQ-09  Customer email format validation (basic regex check)
-- ---------------------------------------------------------------------------
SELECT customer_id, email
FROM customers
WHERE NOT REGEXP_LIKE(email, '^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$')
LIMIT 50;

-- ---------------------------------------------------------------------------
-- DQ-10  Summary scorecard (one row per check — useful for monitoring executive reportings)
-- ---------------------------------------------------------------------------
SELECT
    check_name,
    violations,
    CASE WHEN violations = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM (
    SELECT 'DQ-02: Duplicate PKs'           AS check_name,
           (SELECT COUNT(*) FROM (SELECT customer_id FROM customers GROUP BY customer_id HAVING COUNT(*) > 1)) AS violations
    UNION ALL
    SELECT 'DQ-03: Invalid quantity',
           (SELECT COUNT(*) FROM sales_transactions WHERE quantity < 1)
    UNION ALL
    SELECT 'DQ-03: Invalid discount',
           (SELECT COUNT(*) FROM sales_transactions WHERE discount < 0 OR discount > 1)
    UNION ALL
    SELECT 'DQ-04: Ship before order',
           (SELECT COUNT(*) FROM sales_transactions WHERE ship_date < order_date)
    UNION ALL
    SELECT 'DQ-06: Orphan customer FK',
           (SELECT COUNT(*) FROM sales_transactions t LEFT JOIN customers c ON t.customer_id = c.customer_id WHERE c.customer_id IS NULL)
    UNION ALL
    SELECT 'DQ-06: Orphan product FK',
           (SELECT COUNT(*) FROM sales_transactions t LEFT JOIN products p ON t.product_id = p.product_id WHERE p.product_id IS NULL)
)
ORDER BY status DESC, check_name;
