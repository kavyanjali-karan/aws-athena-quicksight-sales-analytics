"""
clean_sales_data.py
-------------------
Reads raw CSV datasets, applies production-style cleaning rules,
and writes cleaned Parquet files to data/processed/.

Cleaning steps applied:
  - Schema enforcement (correct dtypes)
  - Null / missing value handling
  - Duplicate detection and removal
  - Outlier capping on numeric columns
  - Derived column creation (net_revenue, gross_profit)
  - Partitioned Parquet output (year / month) for Athena efficiency

Usage:
    python python/clean_sales_data.py [--input data/raw] [--output data/processed]
"""

import logging
import shutil
from pathlib import Path

import click
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------
CUSTOMER_DTYPES: dict[str, str] = {
    "customer_id": "string",
    "first_name":  "string",
    "last_name":   "string",
    "email":       "string",
    "region":      "string",
    "country":     "string",
    "city":        "string",
    "signup_date": "string",   # parsed to date below
    "segment":     "string",
}

PRODUCT_DTYPES: dict[str, str] = {
    "product_id":   "string",
    "product_name": "string",
    "category":     "string",
    "sub_category": "string",
    "unit_cost":    "float64",
    "unit_price":   "float64",
    "brand":        "string",
}

TRANSACTION_DTYPES: dict[str, str] = {
    "transaction_id": "string",
    "customer_id":    "string",
    "product_id":     "string",
    "order_date":     "string",
    "ship_date":      "string",
    "quantity":       "int64",
    "unit_price":     "float64",
    "discount":       "float64",
    "region":         "string",
    "year":           "int64",
    "month":          "int64",
}

VALID_REGIONS = {"Northeast", "Southeast", "Midwest", "West", "Southwest"}
VALID_SEGMENTS = {"Consumer", "Corporate", "Home Office"}


# ---------------------------------------------------------------------------
# Cleaning functions
# ---------------------------------------------------------------------------

def clean_customers(raw_path: Path) -> pd.DataFrame:
    """Load and clean customers dataset."""
    log.info("Reading customers from %s", raw_path)
    df = pd.read_csv(raw_path, dtype=str)

    initial_count = len(df)
    log.info("  Rows loaded: %d", initial_count)

    # Drop exact duplicates
    df = df.drop_duplicates(subset=["customer_id"])
    log.info("  Rows after deduplication: %d (removed %d)", len(df), initial_count - len(df))

    # Drop records missing key identifiers
    df = df.dropna(subset=["customer_id", "email"])

    # Enforce date type
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce").dt.date

    # Remove rows where signup_date could not be parsed
    invalid_dates = df["signup_date"].isna().sum()
    if invalid_dates:
        log.warning("  Dropping %d rows with unparseable signup_date", invalid_dates)
    df = df.dropna(subset=["signup_date"])

    # Standardise region
    df["region"] = df["region"].str.strip().str.title()
    invalid_regions = ~df["region"].isin(VALID_REGIONS)
    if invalid_regions.any():
        log.warning("  Replacing %d invalid region values with 'Unknown'", invalid_regions.sum())
        df.loc[invalid_regions, "region"] = "Unknown"

    # Standardise segment
    df["segment"] = df["segment"].str.strip()
    invalid_segments = ~df["segment"].isin(VALID_SEGMENTS)
    if invalid_segments.any():
        log.warning("  Replacing %d invalid segment values with 'Consumer'", invalid_segments.sum())
        df.loc[invalid_segments, "segment"] = "Consumer"

    # Lowercase email
    df["email"] = df["email"].str.lower().str.strip()

    log.info("  Final customer rows: %d", len(df))
    return df


def clean_products(raw_path: Path) -> pd.DataFrame:
    """Load and clean products dataset."""
    log.info("Reading products from %s", raw_path)
    df = pd.read_csv(raw_path)

    initial_count = len(df)
    df = df.drop_duplicates(subset=["product_id"])
    df = df.dropna(subset=["product_id", "product_name"])

    # Cast numeric columns
    for col in ["unit_cost", "unit_price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop products with missing or non-positive pricing
    bad_price = (df["unit_price"].isna()) | (df["unit_price"] <= 0)
    bad_cost = (df["unit_cost"].isna()) | (df["unit_cost"] <= 0)
    df = df[~(bad_price | bad_cost)]

    # Cap extreme outliers at 99.9th percentile
    for col in ["unit_cost", "unit_price"]:
        cap = df[col].quantile(0.999)
        clipped = (df[col] > cap).sum()
        if clipped:
            log.info("  Capping %d outlier rows in %s at %.2f", clipped, col, cap)
        df[col] = df[col].clip(upper=cap)

    # Derived: margin percentage
    df["margin_pct"] = ((df["unit_price"] - df["unit_cost"]) / df["unit_price"] * 100).round(2)

    log.info("  Final product rows: %d (removed %d)", len(df), initial_count - len(df))
    return df


def clean_transactions(
    raw_path: Path,
    valid_customer_ids: set[str],
    valid_product_ids: set[str],
) -> pd.DataFrame:
    """Load and clean sales_transactions dataset."""
    log.info("Reading transactions from %s", raw_path)
    df = pd.read_csv(raw_path)

    initial_count = len(df)
    log.info("  Rows loaded: %d", initial_count)

    df = df.drop_duplicates(subset=["transaction_id"])

    # Cast types
    for col in ["unit_price", "discount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")

    # Drop rows with missing critical fields
    df = df.dropna(subset=["transaction_id", "customer_id", "product_id",
                            "order_date", "unit_price", "quantity"])

    # Date parsing
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce").dt.date
    df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce").dt.date
    df = df.dropna(subset=["order_date"])

    # Referential integrity
    orphan_customers = ~df["customer_id"].isin(valid_customer_ids)
    orphan_products = ~df["product_id"].isin(valid_product_ids)
    if orphan_customers.any():
        log.warning("  Dropping %d rows with unknown customer_id", orphan_customers.sum())
    if orphan_products.any():
        log.warning("  Dropping %d rows with unknown product_id", orphan_products.sum())
    df = df[~orphan_customers & ~orphan_products]

    # Business rule: quantity must be positive
    df = df[df["quantity"] > 0]

    # Business rule: discount must be in [0, 1]
    df["discount"] = df["discount"].clip(lower=0.0, upper=1.0).fillna(0.0)

    # Ship date must not precede order date
    bad_ship = df["ship_date"] < df["order_date"]
    if bad_ship.any():
        log.warning("  Fixing %d rows where ship_date < order_date", bad_ship.sum())
        df.loc[bad_ship, "ship_date"] = df.loc[bad_ship, "order_date"]

    # Derived columns
    df["net_revenue"] = (df["unit_price"] * df["quantity"] * (1 - df["discount"])).round(2)
    df["year"] = pd.to_datetime(df["order_date"].astype(str)).dt.year
    df["month"] = pd.to_datetime(df["order_date"].astype(str)).dt.month

    log.info("  Final transaction rows: %d (removed %d)", len(df), initial_count - len(df))
    return df


# ---------------------------------------------------------------------------
# Parquet writers
# ---------------------------------------------------------------------------

def write_parquet(df: pd.DataFrame, output_dir: Path, table_name: str) -> None:
    """Write a DataFrame to Parquet in output_dir/table_name/."""
    out = output_dir / table_name
    out.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, out / f"{table_name}.parquet", compression="snappy")
    log.info("  Wrote %s → %s (%d rows)", table_name, out, len(df))


def write_partitioned_parquet(
    df: pd.DataFrame,
    output_dir: Path,
    table_name: str,
    partition_cols: list[str],
) -> None:
    """Write a DataFrame to Parquet partitioned by partition_cols (Hive layout)."""
    out = output_dir / table_name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_to_dataset(
        table,
        root_path=str(out),
        partition_cols=partition_cols,
        compression="snappy",
    )
    log.info(
        "  Wrote %s → %s (%d rows, partitioned by %s)",
        table_name,
        out,
        len(df),
        partition_cols,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--input",  "input_dir",
    default="data/raw",
    show_default=True,
    help="Directory containing raw CSV files.",
)
@click.option(
    "--output", "output_dir",
    default="data/processed",
    show_default=True,
    help="Directory for cleaned Parquet output.",
)
def main(input_dir: str, output_dir: str) -> None:
    """Clean raw sales CSV files and write production-ready Parquet."""
    inp = Path(input_dir)
    out = Path(output_dir)

    if not inp.exists():
        log.error("Input directory '%s' does not exist. Run generate_datasets.py first.", inp)
        raise SystemExit(1)

    log.info("=== Starting data cleaning reporting-system ===")

    customers = clean_customers(inp / "customers.csv")
    products = clean_products(inp / "products.csv")
    transactions = clean_transactions(
        inp / "sales_transactions.csv",
        valid_customer_ids=set(customers["customer_id"]),
        valid_product_ids=set(products["product_id"]),
    )

    write_parquet(customers, out, "customers")
    write_parquet(products, out, "products")
    write_partitioned_parquet(
        transactions, out, "sales_transactions", partition_cols=["year", "month"]
    )

    log.info("=== Cleaning reporting-system complete ===")


if __name__ == "__main__":
    main()
