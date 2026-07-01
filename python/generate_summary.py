"""
generate_summary.py
-------------------
Generates a JSON summary report of the cleaned datasets.

Output includes:
  - Record counts
  - Date ranges
  - Top categories, regions, and segments
  - Key financial KPIs (total revenue, avg order value, top product)

This report is written to outputs/summary_report.json and printed to stdout
for easy reporting-system inspection.

Usage:
    python python/generate_summary.py [--input data/processed] [--output outputs]
"""

import json
import logging
from datetime import date
from pathlib import Path

import click
import pandas as pd
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
# Utilities
# ---------------------------------------------------------------------------

def load_parquet(path: Path) -> pd.DataFrame:
    if path.is_dir():
        return pq.read_table(str(path)).to_pandas()
    return pd.read_parquet(path)


def _date_str(val) -> str:
    """Coerce a date/datetime/string to an ISO string."""
    if isinstance(val, (date,)):
        return val.isoformat()
    if hasattr(val, "date"):
        return val.date().isoformat()
    return str(val)


# ---------------------------------------------------------------------------
# Summary builders
# ---------------------------------------------------------------------------

def customer_summary(df: pd.DataFrame) -> dict:
    log.info("Building customer summary …")
    return {
        "total_customers": int(len(df)),
        "segment_distribution": df["segment"].value_counts().to_dict(),
        "region_distribution": df["region"].value_counts().to_dict(),
        "signup_date_min": _date_str(df["signup_date"].min()),
        "signup_date_max": _date_str(df["signup_date"].max()),
    }


def product_summary(df: pd.DataFrame) -> dict:
    log.info("Building product summary …")
    cat_counts = df["category"].value_counts().to_dict()
    avg_margin_by_cat = (
        df.groupby("category")["margin_pct"].mean().round(2).to_dict()
    )
    return {
        "total_products": int(len(df)),
        "category_counts": cat_counts,
        "avg_margin_pct_by_category": avg_margin_by_cat,
        "price_stats": {
            "min": float(df["unit_price"].min()),
            "max": float(df["unit_price"].max()),
            "mean": float(df["unit_price"].mean().round(2)),
            "median": float(df["unit_price"].median().round(2)),
        },
    }


def transaction_summary(
    txn: pd.DataFrame, customers: pd.DataFrame, products: pd.DataFrame
) -> dict:
    log.info("Building transaction summary …")

    # Enrich with product category and customer segment for aggregations
    txn = txn.merge(
        products[["product_id", "category", "unit_cost"]],
        on="product_id",
        how="left",
    )
    txn = txn.merge(
        customers[["customer_id", "segment"]],
        on="customer_id",
        how="left",
    )

    txn["gross_profit"] = (
        txn["net_revenue"] - txn["unit_cost"] * txn["quantity"]
    ).round(2)

    total_revenue = float(txn["net_revenue"].sum().round(2))
    total_gross_profit = float(txn["gross_profit"].sum().round(2))
    avg_order_value = float((txn["net_revenue"]).mean().round(2))
    avg_discount = float(txn["discount"].mean().round(4))

    # Revenue by region
    rev_by_region = (
        txn.groupby("region")["net_revenue"].sum().round(2).sort_values(ascending=False).to_dict()
    )

    # Revenue by category
    rev_by_category = (
        txn.groupby("category")["net_revenue"].sum().round(2).sort_values(ascending=False).to_dict()
    )

    # Revenue by segment
    rev_by_segment = (
        txn.groupby("segment")["net_revenue"].sum().round(2).sort_values(ascending=False).to_dict()
    )

    # Top 5 products by revenue
    top_products = (
        txn.groupby("product_id")["net_revenue"]
        .sum()
        .round(2)
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )

    # Revenue by year
    rev_by_year = (
        txn.groupby("year")["net_revenue"].sum().round(2).to_dict()
    )

    # Gross margin overall
    gross_margin_pct = round(total_gross_profit / total_revenue * 100, 2) if total_revenue else 0.0

    return {
        "total_transactions": int(len(txn)),
        "order_date_min": _date_str(txn["order_date"].min()),
        "order_date_max": _date_str(txn["order_date"].max()),
        "total_revenue": total_revenue,
        "total_gross_profit": total_gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "avg_order_value": avg_order_value,
        "avg_discount_rate": avg_discount,
        "revenue_by_year": {str(k): float(v) for k, v in rev_by_year.items()},
        "revenue_by_region": {k: float(v) for k, v in rev_by_region.items()},
        "revenue_by_category": {k: float(v) for k, v in rev_by_category.items()},
        "revenue_by_segment": {k: float(v) for k, v in rev_by_segment.items()},
        "top_5_products_by_revenue": {k: float(v) for k, v in top_products.items()},
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--input", "input_dir",
    default="data/processed",
    show_default=True,
    help="Directory containing cleaned Parquet files.",
)
@click.option(
    "--output", "output_dir",
    default="outputs",
    show_default=True,
    help="Directory to write summary_report.json.",
)
def main(input_dir: str, output_dir: str) -> None:
    """Generate a JSON summary report from cleaned datasets."""
    inp = Path(input_dir)
    out = Path(output_dir)

    if not inp.exists():
        log.error("Input directory '%s' does not exist. Run clean_sales_data.py first.", inp)
        raise SystemExit(1)

    log.info("=== Loading cleaned datasets ===")
    customers = load_parquet(inp / "customers")
    products = load_parquet(inp / "products")
    transactions = load_parquet(inp / "sales_transactions")

    log.info("=== Building summary ===")
    report = {
        "generated_at": date.today().isoformat(),
        "customers": customer_summary(customers),
        "products": product_summary(products),
        "transactions": transaction_summary(transactions, customers, products),
    }

    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "summary_report.json"
    with report_path.open("w") as fh:
        json.dump(report, fh, indent=2, default=str)

    log.info("Summary report written → %s", report_path)

    # Pretty-print key metrics
    t = report["transactions"]
    log.info("=== Key Metrics ===")
    log.info("  Total revenue:      $%,.2f", t["total_revenue"])
    log.info("  Gross margin:       %.1f%%", t["gross_margin_pct"])
    log.info("  Avg order value:    $%.2f", t["avg_order_value"])
    log.info("  Avg discount rate:  %.1f%%", t["avg_discount_rate"] * 100)
    log.info("  Total transactions: %d", t["total_transactions"])


if __name__ == "__main__":
    main()
