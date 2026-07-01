# Data Dictionary

Complete field-level documentation for all three tables in the `sales` Glue database.

---

## Table: `customers`

**Location:** `s3://YOUR-BUCKET/sales-business reporting/processed/customers/`  
**Format:** Parquet (Snappy)  
**Grain:** One row per customer  
**Primary key:** `customer_id`  

| Column | Data Type | Nullable | Description | Example |
|---|---|---|---|---|
| `customer_id` | STRING | No | UUID v4 — unique customer identifier | `3fa85f64-5717-4562-b3fc-2c963f66afa6` |
| `first_name` | STRING | No | Customer first name | `James` |
| `last_name` | STRING | No | Customer last name | `Smith` |
| `email` | STRING | No | Lowercase email address | `james.smith@example.com` |
| `region` | STRING | No | Geographic sales region. One of: `Northeast`, `Southeast`, `Midwest`, `West`, `Southwest` | `Northeast` |
| `country` | STRING | No | Country of residence | `United States` |
| `city` | STRING | No | City of residence | `New York` |
| `signup_date` | DATE | No | Date the customer account was created | `2021-03-15` |
| `segment` | STRING | No | Customer segment. One of: `Consumer`, `Corporate`, `Home Office` | `Consumer` |

---

## Table: `products`

**Location:** `s3://YOUR-BUCKET/sales-business reporting/processed/products/`  
**Format:** Parquet (Snappy)  
**Grain:** One row per product SKU  
**Primary key:** `product_id`  

| Column | Data Type | Nullable | Description | Example |
|---|---|---|---|---|
| `product_id` | STRING | No | Sequential product identifier (`PROD-NNNNN`) | `PROD-00042` |
| `product_name` | STRING | No | Full product name including brand and model variant | `NovaTech Phones 247` |
| `category` | STRING | No | High-level product category. One of: `Technology`, `Furniture`, `Office Supplies`, `Clothing`, `Sports & Outdoors` | `Technology` |
| `sub_category` | STRING | No | Sub-category within the parent category | `Phones` |
| `unit_cost` | DOUBLE | No | Cost of goods sold (COGS) per unit in USD | `349.99` |
| `unit_price` | DOUBLE | No | Standard retail price per unit in USD | `499.99` |
| `brand` | STRING | No | Brand name | `NovaTech` |
| `margin_pct` | DOUBLE | No | Gross margin percentage: `(unit_price - unit_cost) / unit_price * 100` | `30.0` |

---

## Table: `sales_transactions`

**Location:** `s3://YOUR-BUCKET/sales-business reporting/processed/sales_transactions/year=*/month=*/`  
**Format:** Parquet (Snappy), Hive-partitioned  
**Grain:** One row per line item / transaction  
**Primary key:** `transaction_id`  
**Foreign keys:** `customer_id → customers.customer_id`, `product_id → products.product_id`  
**Partition keys:** `year`, `month`  

| Column | Data Type | Nullable | Description | Example |
|---|---|---|---|---|
| `transaction_id` | STRING | No | UUID v4 — unique transaction identifier | `7e4a9b2c-1234-4abc-8ef0-abcdef012345` |
| `customer_id` | STRING | No | FK → `customers.customer_id` | `3fa85f64-5717-4562-b3fc-2c963f66afa6` |
| `product_id` | STRING | No | FK → `products.product_id` | `PROD-00042` |
| `order_date` | DATE | No | Date the order was placed | `2022-11-15` |
| `ship_date` | DATE | Yes | Date the order was shipped. Always ≥ `order_date` | `2022-11-18` |
| `quantity` | INT | No | Number of units ordered. Always ≥ 1 | `2` |
| `unit_price` | DOUBLE | No | Agreed price per unit at time of sale (may differ from `products.unit_price` due to promotions) | `489.99` |
| `discount` | DOUBLE | No | Discount fraction applied to this line item. Range: `[0.0, 1.0]`. `0.20` = 20% off | `0.10` |
| `net_revenue` | DOUBLE | No | Derived: `unit_price × quantity × (1 - discount)` | `881.98` |
| `region` | STRING | No | Region where the sale occurred. Inherited from customer region at transaction time | `Northeast` |
| `year` | INT | No | Order year — Hive partition key | `2022` |
| `month` | INT | No | Order month — Hive partition key | `11` |

---

## Derived / Calculated Fields (Athena SQL)

These are not stored columns — they are computed in SQL queries:

| Field | Formula | Description |
|---|---|---|
| `gross_profit` | `net_revenue - (unit_cost × quantity)` | Revenue minus COGS |
| `gross_margin_pct` | `gross_profit / net_revenue × 100` | Gross margin as a percentage |
| `days_to_ship` | `DATE_DIFF('day', order_date, ship_date)` | Fulfilment lag |
| `ltv` | `SUM(net_revenue) per customer_id` | Customer lifetime value |
| `recency_days` | `DATE_DIFF('day', last_order_date, reference_date)` | Days since last purchase (RFM R) |

---

## Known Limitations

- `unit_price` in `sales_transactions` may differ slightly from `products.unit_price` — this represents negotiated or promotional pricing captured at time of sale.
- `ship_date` can be `NULL` for orders that have not yet shipped (not present in synthetic dataset but handled defensively in SQL).
- The `discount` column represents the **fractional** discount applied (e.g., `0.20` = 20%), not a currency amount.
