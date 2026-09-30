"""PyArrow ETL: clean the raw sales extract and write partitioned Parquet.

Steps
  1. Read data/raw/sales_transactions.csv
  2. Drop exact duplicate rows
  3. Drop rows with a missing customer id
  4. Drop rows with non-positive income or quantity
  5. Cast types (date32, int32, double)
  6. Write hive-partitioned Parquet to data/curated/sales/category=<Category>/

The partitioned output is what the Athena DDL in athena/ points at
(the same layout lands under s3://<bucket>/curated/sales/ once uploaded).
Idempotent: the output directory is replaced on every run.

Usage: python python/etl_pipeline.py [--raw PATH] [--out DIR]
"""

import argparse
import os
import shutil
import stat
import sys
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pv
import pyarrow.dataset as ds
import pyarrow.parquet as pq

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = PROJECT / "data" / "raw" / "sales_transactions.csv"
DEFAULT_OUT = PROJECT / "data" / "curated" / "sales"

SCHEMA = pa.schema([
    ("transaction_id", pa.string()),
    ("order_date", pa.date32()),
    ("customer_id", pa.string()),
    ("region", pa.string()),
    ("product_id", pa.string()),
    ("product_name", pa.string()),
    ("category", pa.string()),
    ("sub_category", pa.string()),
    ("quantity", pa.int32()),
    ("unit_price", pa.float64()),
    ("income", pa.float64()),
])


def drop_duplicate_ids(table):
    """Keep the first row for each transaction_id (duplicate exports share ids)."""
    seen = set()
    keep = []
    for i, txn_id in enumerate(table["transaction_id"].to_pylist()):
        if txn_id not in seen:
            seen.add(txn_id)
            keep.append(i)
    return table.take(keep)


def clean(table):
    """Apply the cleaning rules. Returns (clean_table, stats)."""
    stats = {"raw": table.num_rows}

    # 1. Exact duplicate rows.
    table = drop_duplicate_ids(table)
    stats["duplicates_dropped"] = stats["raw"] - table.num_rows

    # 2. Missing customer id (null or empty after strip).
    customer = pc.utf8_trim_whitespace(table["customer_id"])
    keep = pc.and_(pc.is_valid(customer), pc.not_equal(customer, ""))
    table = table.filter(keep)
    table = table.set_column(
        table.schema.get_field_index("customer_id"),
        table.field("customer_id"),
        pc.utf8_trim_whitespace(table["customer_id"]),
    )
    stats["null_customer_dropped"] = (
        stats["raw"] - stats["duplicates_dropped"] - table.num_rows
    )

    # 3. Non-positive income or quantity.
    valid = pc.and_(
        pc.greater(table["income"], 0.0),
        pc.greater(table["quantity"], 0),
    )
    table = table.filter(valid)
    stats["invalid_measures_dropped"] = (
        stats["raw"] - stats["duplicates_dropped"] - stats["null_customer_dropped"]
        - table.num_rows
    )
    stats["clean"] = table.num_rows

    # 4. Cast to the published schema.
    table = table.select(SCHEMA.names).cast(SCHEMA)
    return table, stats


def _force_remove_readonly(func, path, _exc):
    """shutil onerror/onexc callback: clear read-only bits and retry."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        pass


def _safe_rmtree(path):
    """rmtree that works on Python 3.11 (onerror) and 3.12+ (onexc)."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_force_remove_readonly)
    else:
        shutil.rmtree(path, onerror=_force_remove_readonly)


def _rmtree(path):
    """Delete a directory tree, retrying through transient locks.

    Windows (especially OneDrive-synced folders) can hold files read-only
    or open briefly, which makes a plain shutil.rmtree raise PermissionError.
    Clear read-only attributes, retry a few times, then fall back to a
    best-effort delete instead of crashing the pipeline.
    """
    try:
        _safe_rmtree(path)
        return
    except (PermissionError, OSError):
        pass
    for attempt in range(3):
        time.sleep(0.4 * (attempt + 1))
        try:
            _safe_rmtree(path)
            return
        except (PermissionError, OSError):
            continue
    shutil.rmtree(path, ignore_errors=True)


def write_partitioned(table, out_dir):
    """Write hive-partitioned Parquet (category=<Category>/...)."""
    if out_dir.exists():
        _rmtree(out_dir)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    ds.write_dataset(
        table,
        base_dir=out_dir,
        format="parquet",
        partitioning=["category"],
        partitioning_flavor="hive",
        existing_data_behavior="delete_matching",
    )
    return sorted(p.name for p in out_dir.iterdir() if p.is_dir())


def run(raw=DEFAULT_RAW, out=DEFAULT_OUT, quiet=False):
    table = pv.read_csv(raw, convert_options=pv.ConvertOptions(
        column_types={
            "transaction_id": pa.string(),
            "order_date": pa.string(),
            "customer_id": pa.string(),
            "region": pa.string(),
            "product_id": pa.string(),
            "product_name": pa.string(),
            "category": pa.string(),
            "sub_category": pa.string(),
            "quantity": pa.int32(),
            "unit_price": pa.float64(),
            "income": pa.float64(),
        },
        strings_can_be_null=True,
        null_values=[""],
    ))
    table, stats = clean(table)
    partitions = write_partitioned(table, out)
    if not quiet:
        print(f"Raw rows      : {stats['raw']:,}")
        print(f"  duplicates  : -{stats['duplicates_dropped']}")
        print(f"  null cust.  : -{stats['null_customer_dropped']}")
        print(f"  invalid     : -{stats['invalid_measures_dropped']}")
        print(f"Clean rows    : {stats['clean']:,}")
        print(f"Partitions    : {', '.join(partitions)}")
        print(f"Written to    : {out}")
    return stats


def main(argv=None):
    p = argparse.ArgumentParser(description="Clean and partition the sales extract.")
    p.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="raw CSV path")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    args = p.parse_args(argv)
    if not args.raw.exists():
        sys.exit(f"Raw file not found: {args.raw}\nRun: python data/generate_sales_data.py")
    run(raw=args.raw, out=args.out)


if __name__ == "__main__":
    main()
