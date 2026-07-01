-- =============================================================================
-- 08_customer_segmentation.sql
-- Purpose : Customer lifetime value (LTV), RFM segmentation, and cohort analysis.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- Customer-level lifetime value summary
-- ---------------------------------------------------------------------------
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name   AS customer_name,
    c.segment,
    c.region,
    c.city,
    c.signup_date,
    COUNT(DISTINCT t.transaction_id)      AS total_orders,
    ROUND(SUM(t.net_revenue), 2)          AS lifetime_value,
    ROUND(AVG(t.net_revenue), 2)          AS avg_order_value,
    MIN(t.order_date)                     AS first_order_date,
    MAX(t.order_date)                     AS last_order_date,
    DATE_DIFF('day', MIN(t.order_date), MAX(t.order_date)) AS customer_lifespan_days
FROM customers c
JOIN sales_transactions t ON c.customer_id = t.customer_id
GROUP BY
    c.customer_id, c.first_name, c.last_name,
    c.segment, c.region, c.city, c.signup_date
ORDER BY lifetime_value DESC;

-- ---------------------------------------------------------------------------
-- LTV by customer segment
-- ---------------------------------------------------------------------------
SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id)                                    AS customers,
    ROUND(SUM(t.net_revenue), 2)                                     AS segment_revenue,
    ROUND(AVG(t.net_revenue), 2)                                     AS avg_order_value,
    ROUND(SUM(t.net_revenue) / COUNT(DISTINCT c.customer_id), 2)     AS avg_ltv,
    ROUND(SUM(t.net_revenue)
        / SUM(SUM(t.net_revenue)) OVER () * 100, 2)                 AS revenue_share_pct
FROM customers c
JOIN sales_transactions t ON c.customer_id = t.customer_id
GROUP BY c.segment
ORDER BY segment_revenue DESC;

-- ---------------------------------------------------------------------------
-- RFM scoring (Recency, Frequency, Monetary)
-- Reference date: most recent transaction in the dataset
-- ---------------------------------------------------------------------------
WITH ref_date AS (
    SELECT MAX(order_date) AS max_date FROM sales_transactions
),
rfm_raw AS (
    SELECT
        t.customer_id,
        DATE_DIFF('day', MAX(t.order_date), (SELECT max_date FROM ref_date)) AS recency_days,
        COUNT(DISTINCT t.transaction_id)                                       AS frequency,
        ROUND(SUM(t.net_revenue), 2)                                           AS monetary
    FROM sales_transactions t
    GROUP BY t.customer_id
),
rfm_scores AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        -- Lower recency = better (more recent)
        NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC)     AS m_score
    FROM rfm_raw
)
SELECT
    r.customer_id,
    c.segment,
    c.region,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    r_score + f_score + m_score                    AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4
            THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3
            THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2
            THEN 'Recent Customers'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4
            THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2
            THEN 'Lost'
        ELSE 'Potential Loyalists'
    END                                            AS rfm_segment
FROM rfm_scores r
JOIN customers c ON r.customer_id = c.customer_id
ORDER BY rfm_total DESC;

-- ---------------------------------------------------------------------------
-- Signup cohort retention (monthly cohort — customers who transacted in month N+1, N+2, …)
-- ---------------------------------------------------------------------------
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_FORMAT(DATE(signup_date), '%Y-%m') AS cohort_month
    FROM customers
),
txn_months AS (
    SELECT
        customer_id,
        DATE_FORMAT(DATE(CONCAT(CAST(year AS VARCHAR), '-', LPAD(CAST(month AS VARCHAR), 2, '0'), '-010')), '%Y-%m') AS txn_month
    FROM sales_transactions
    GROUP BY customer_id, year, month
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        t.txn_month,
        COUNT(DISTINCT c.customer_id) AS active_customers
    FROM cohorts c
    JOIN txn_months t ON c.customer_id = t.customer_id
    GROUP BY c.cohort_month, t.txn_month
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    ca.txn_month,
    cs.cohort_size,
    ca.active_customers,
    ROUND(ca.active_customers * 100.0 / cs.cohort_size, 2) AS retention_pct
FROM cohort_activity ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
ORDER BY ca.cohort_month, ca.txn_month;
