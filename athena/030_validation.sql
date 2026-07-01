-- =============================================================================
-- 03_validation.sql
-- Purpose : Row-count checks, null audits, and referential integrity probes.
--           Run these queries immediately after creating external tables and
--           after each incremental load.  All result sets should return 0 rows
--           for the "violation" queries.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- 1. Row counts (sanity check)
-- ---------------------------------------------------------------------------
SELECT 'customers'         AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'products'          AS table_name, COUNT(*) AS row_count FROM products
UNION ALL
SELECT 'sales_transactions'AS table_name, COUNT(*) AS row_count FROM sales_transactions;

-- ---------------------------------------------------------------------------
-- 2. Null audit — critical columns must have 0 nulls
-- ---------------------------------------------------------------------------

-- customers
SELECT
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END)  AS null_customer_id,
    SUM(CASE WHEN email       IS NULL THEN 1 ELSE 0 END)  AS null_email,
    SUM(CASE WHEN region      IS NULL THEN 1 ELSE 0 END)  AS null_region,
    SUM(CASE WHEN signup_date IS NULL THEN 1 ELSE 0 END)  AS null_signup_date,
    SUM(CASE WHEN segment     IS NULL THEN 1 ELSE 0 END)  AS null_segment
FROM customers;

-- products
SELECT
    SUM(CASE WHEN product_id   IS NULL THEN 1 ELSE 0 END) AS null_product_id,
    SUM(CASE WHEN unit_price   IS NULL THEN 1 ELSE 0 END) AS null_unit_price,
    SUM(CASE WHEN unit_cost    IS NULL THEN 1 ELSE 0 END) AS null_unit_cost,
    SUM(CASE WHEN category     IS NULL THEN 1 ELSE 0 END) AS null_category
FROM products;

-- sales_transactions
SELECT
    SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) AS null_transaction_id,
    SUM(CASE WHEN customer_id    IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
    SUM(CASE WHEN product_id     IS NULL THEN 1 ELSE 0 END) AS null_product_id,
    SUM(CASE WHEN order_date     IS NULL THEN 1 ELSE 0 END) AS null_order_date,
    SUM(CASE WHEN net_revenue    IS NULL THEN 1 ELSE 0 END) AS null_net_revenue,
    SUM(CASE WHEN quantity       IS NULL THEN 1 ELSE 0 END) AS null_quantity
FROM sales_transactions;

-- ---------------------------------------------------------------------------
-- 3. Duplicate primary key checks (expect 0 rows each)
-- ---------------------------------------------------------------------------
SELECT customer_id, COUNT(*) AS cnt
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

SELECT product_id, COUNT(*) AS cnt
FROM products
GROUP BY product_id
HAVING COUNT(*) > 1;

SELECT transaction_id, COUNT(*) AS cnt
FROM sales_transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- ---------------------------------------------------------------------------
-- 4. Referential integrity — orphan transactions (expect 0 rows each)
-- ---------------------------------------------------------------------------
-- Transactions referencing a customer_id not in customers
SELECT COUNT(*) AS orphan_customer_count
FROM sales_transactions t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- Transactions referencing a product_id not in products
SELECT COUNT(*) AS orphan_product_count
FROM sales_transactions t
LEFT JOIN products p ON t.product_id = p.product_id
WHERE p.product_id IS NULL;

-- ---------------------------------------------------------------------------
-- 5. Domain validation
-- ---------------------------------------------------------------------------
-- Invalid region values
SELECT DISTINCT region AS invalid_region
FROM sales_transactions
WHERE region NOT IN ('Northeast', 'Southeast', 'Midwest', 'West', 'Southwest');

-- Invalid segment values
SELECT DISTINCT segment AS invalid_segment
FROM customers
WHERE segment NOT IN ('Consumer', 'Corporate', 'Home Office');

-- Invalid discount values (must be in [0, 1])
SELECT COUNT(*) AS invalid_discount_count
FROM sales_transactions
WHERE discount < 0 OR discount > 1;

-- Invalid quantity values (must be >= 1)
SELECT COUNT(*) AS invalid_quantity_count
FROM sales_transactions
WHERE quantity < 1;

-- Ship date before order date
SELECT COUNT(*) AS ship_before_order_count
FROM sales_transactions
WHERE ship_date < order_date;

-- ---------------------------------------------------------------------------
-- 6. Partition coverage (ensure all year/month buckets are registered)
-- ---------------------------------------------------------------------------
SELECT year, month, COUNT(*) AS row_count
FROM sales_transactions
GROUP BY year, month
ORDER BY year, month;
