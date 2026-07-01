-- =============================================================================
-- 02_create_external_tables.sql
-- Purpose : Register external Athena tables pointing to S3 Parquet files.
-- Engine  : Athena (Presto / Trino dialect)
-- Note    : Replace YOUR-BUCKET with your actual S3 bucket name.
--           Run MSCK REPAIR TABLE sales_transactions after first upload to
--           register all Hive-style year/month partitions.
-- =============================================================================

USE sales;

-- ---------------------------------------------------------------------------
-- customers
-- ---------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS customers (
    customer_id  STRING    COMMENT 'Unique customer identifier (UUID)',
    first_name   STRING    COMMENT 'Customer first name',
    last_name    STRING    COMMENT 'Customer last name',
    email        STRING    COMMENT 'Customer email address',
    region       STRING    COMMENT 'Geographic region: Northeast | Southeast | Midwest | West | Southwest',
    country      STRING    COMMENT 'Country of residence',
    city         STRING    COMMENT 'City',
    signup_date  DATE      COMMENT 'Date the customer account was created',
    segment      STRING    COMMENT 'Customer segment: Consumer | Corporate | Home Office'
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/sales-business reporting/processed/customers/'
TBLPROPERTIES ('parquet.compress' = 'SNAPPY');

-- ---------------------------------------------------------------------------
-- products
-- ---------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS products (
    product_id   STRING    COMMENT 'Unique product identifier',
    product_name STRING    COMMENT 'Full product name',
    category     STRING    COMMENT 'Product category',
    sub_category STRING    COMMENT 'Product sub-category',
    unit_cost    DOUBLE    COMMENT 'Cost of goods sold per unit (USD)',
    unit_price   DOUBLE    COMMENT 'Retail price per unit (USD)',
    brand        STRING    COMMENT 'Brand name',
    margin_pct   DOUBLE    COMMENT 'Gross margin percentage [(price-cost)/price * 100]'
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/sales-business reporting/processed/products/'
TBLPROPERTIES ('parquet.compress' = 'SNAPPY');

-- ---------------------------------------------------------------------------
-- sales_transactions  (partitioned by year / month for cost efficiency)
-- ---------------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS sales_transactions (
    transaction_id STRING    COMMENT 'Unique transaction identifier (UUID)',
    customer_id    STRING    COMMENT 'FK → customers.customer_id',
    product_id     STRING    COMMENT 'FK → products.product_id',
    order_date     DATE      COMMENT 'Date the order was placed',
    ship_date      DATE      COMMENT 'Date the order was shipped',
    quantity       INT       COMMENT 'Number of units ordered',
    unit_price     DOUBLE    COMMENT 'Agreed price per unit at time of sale (USD)',
    discount       DOUBLE    COMMENT 'Discount fraction applied [0.0 – 1.0]',
    net_revenue    DOUBLE    COMMENT 'unit_price * quantity * (1 - discount)',
    region         STRING    COMMENT 'Sales region'
)
PARTITIONED BY (
    year  INT  COMMENT 'Order year  — Hive partition key',
    month INT  COMMENT 'Order month — Hive partition key'
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/sales-business reporting/processed/sales_transactions/'
TBLPROPERTIES ('parquet.compress' = 'SNAPPY');

-- Register all existing partitions (run once after initial S3 upload, and after
-- each incremental load that adds new year/month directories).
MSCK REPAIR TABLE sales_transactions;

-- Alternative:
-- Configure partition projection for very large partitioned datasets
-- to avoid repeated MSCK REPAIR TABLE operations.