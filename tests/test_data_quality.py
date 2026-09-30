"""Data quality checks on the raw extract and the curated Parquet output."""

from datetime import date

EXPECTED_CATEGORIES = {"Technology", "Furniture", "Office Supplies"}
REQUIRED_COLUMNS = [
    "transaction_id", "order_date", "customer_id", "region",
    "product_id", "product_name", "category", "sub_category",
    "quantity", "unit_price", "income",
]


def test_raw_has_all_52150_rows(raw_csv):
    with open(raw_csv, encoding="utf-8") as f:
        rows = sum(1 for _ in f) - 1  # minus header
    assert rows == 52_150


def test_curated_has_52000_rows(duck):
    (count,) = duck.execute("SELECT COUNT(*) FROM sales_curated").fetchone()
    assert count == 52_000


def test_no_duplicate_transaction_ids(duck):
    (dupes,) = duck.execute(
        "SELECT COUNT(*) - COUNT(DISTINCT transaction_id) FROM sales_curated"
    ).fetchone()
    assert dupes == 0


def test_no_missing_values_in_required_columns(duck):
    checks = " + ".join(
        f"CASE WHEN {col} IS NULL THEN 1 ELSE 0 END" for col in REQUIRED_COLUMNS
    )
    (missing,) = duck.execute(
        f"SELECT {checks} FROM sales_curated"
    ).fetchone()
    assert missing == 0


def test_measures_are_positive(duck):
    bad = duck.execute(
        "SELECT COUNT(*) FROM sales_curated "
        "WHERE income <= 0 OR quantity <= 0 OR unit_price <= 0"
    ).fetchone()[0]
    assert bad == 0


def test_dates_within_declared_range(duck):
    min_date, max_date = duck.execute(
        "SELECT MIN(order_date), MAX(order_date) FROM sales_curated"
    ).fetchone()
    assert min_date >= date(2024, 1, 1)
    assert max_date <= date(2025, 12, 31)


def test_exactly_three_categories(duck):
    categories = {
        r[0] for r in duck.execute(
            "SELECT DISTINCT category FROM sales_curated"
        ).fetchall()
    }
    assert categories == EXPECTED_CATEGORIES


def test_partition_directories_exist(curated_dir):
    found = {p.name.split("=", 1)[1] for p in curated_dir.iterdir() if p.is_dir()}
    # Hive-style encoding: the space in "Office Supplies" is %20 in the path.
    assert {"Technology", "Furniture", "Office%20Supplies"} == found
