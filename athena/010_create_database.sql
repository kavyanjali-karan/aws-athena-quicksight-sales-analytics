-- =============================================================================
-- 01_create_database.sql
-- Purpose : Create the Athena database (Glue Data Catalog database).
-- Run     : Amazon Athena Query Editor
-- Note    : Replace YOUR-BUCKET with your actual S3 bucket name.
-- =============================================================================

-- Create the database if it does not already exist.
-- All subsequent tables will be registered under this database.
CREATE DATABASE IF NOT EXISTS sales
COMMENT 'Sales business reporting data lake — customers, products, and transactions'
LOCATION 's3://YOUR-BUCKET/sales-business reporting/';
