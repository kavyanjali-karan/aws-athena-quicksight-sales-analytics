-- Athena DDL for the curated sales dataset.
--
-- Matches the partition layout written by python/etl_pipeline.py:
--   s3://<bucket>/curated/sales/category=<Category>/part-0.parquet
--
-- Replace YOUR_BUCKET with the bucket name CloudFormation outputs,
-- or run this through: python python/run_athena_queries.py --bucket <name>

CREATE EXTERNAL TABLE IF NOT EXISTS sales_curated (
    transaction_id STRING,
    order_date DATE,
    customer_id STRING,
    region STRING,
    product_id STRING,
    product_name STRING,
    sub_category STRING,
    quantity INT,
    unit_price DOUBLE,
    income DOUBLE
)
PARTITIONED BY (category STRING)
STORED AS PARQUET
LOCATION 's3://YOUR_BUCKET/curated/sales/'
TBLPROPERTIES ('parquet.compress' = 'SNAPPY');

-- Pick up new partitions after each ETL upload.
MSCK REPAIR TABLE sales_curated;
