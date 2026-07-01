"""
validate_dataset.py
-------------------
Runs a suite of data quality checks against the cleaned Parquet datasets.

Validation categories:
  - Completeness  : required columns are present, null rates below threshold
  - Uniqueness    : primary keys are unique
  - Validity      : values are within acceptable domains
  - Referential   : foreign keys resolve across tables
  - Timeliness    : date ranges are sensible
  - Statistical   : distributions are within expected bounds

Exit code 0 → all checks passed.
Exit code 1 → one or more checks failed (details in log).

Usage:
    python python/validate_dataset.py [--input data/processed]
"""

import logging
import sys
from dataclasses import dataclass, field
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
# Result tracking
# ---------------------------------------------------------------------------
@dataclass
class ValidationResult:
    name: str
    passed: bool
    details: str = ""

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}" + (f" — {self.details}" if self.details else "")


@dataclass
class ValidationSuite:
    results: list[ValidationResult] = field(default_factory=list)

    def add(self, name: str, passed: bool, details: str = "") -> None:
        r = ValidationResult(name, passed, details)
        self.results.append(r)
        logger_fn = log.info if passed else log.error
        logger_fn("  %s", r)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    def summary(self) -> str:
        total = len(self.results)
        failed = sum(1 for r in self.results if not r.passed)
        return f"{total - failed}/{total} checks passed" + (f", {failed} FAILED" if failed else "")


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_parquet(path: Path) -> pd.DataFrame:
    """Load a Parquet file or dataset directory into a DataFrame."""
    if path.is_dir():
        return pq.read_table(str(path)).to_pandas()
    return pd.read_parquet(path)


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_not_empty(suite: ValidationSuite, name: str, df: pd.DataFrame) -> None:
    suite.add(f"{name}: not empty", len(df) > 0, f"rows={len(df)}")


def check_no_nulls(
    suite: ValidationSuite, name: str, df: pd.DataFrame, cols: list[str], threshold: float = 0.0
) -> None:
    for col in cols:
        if col not in df.columns:
            suite.add(f"{name}.{col}: column exists", False, "column missing")
            continue
        null_rate = df[col].isna().mean()
        suite.add(
            f"{name}.{col}: null rate ≤ {threshold:.0%}",
            null_rate <= threshold,
            f"null_rate={null_rate:.4%}",
        )


def check_unique(suite: ValidationSuite, name: str, df: pd.DataFrame, col: str) -> None:
    n_dupes = len(df) - df[col].nunique()
    suite.add(f"{name}.{col}: unique", n_dupes == 0, f"duplicates={n_dupes}")


def check_domain(
    suite: ValidationSuite, name: str, df: pd.DataFrame, col: str, valid_values: set
) -> None:
    if col not in df.columns:
        suite.add(f"{name}.{col}: domain valid", False, "column missing")
        return
    invalid = ~df[col].isin(valid_values)
    suite.add(
        f"{name}.{col}: domain valid",
        invalid.sum() == 0,
        f"invalid_count={invalid.sum()}",
    )


def check_range(
    suite: ValidationSuite,
    name: str,
    df: pd.DataFrame,
    col: str,
    min_val: float | None = None,
    max_val: float | None = None,
) -> None:
    if col not in df.columns:
        suite.add(f"{name}.{col}: range valid", False, "column missing")
        return
    series = pd.to_numeric(df[col], errors="coerce")
    violations = pd.Series([False] * len(series))
    if min_val is not None:
        violations |= series < min_val
    if max_val is not None:
        violations |= series > max_val
    violations |= series.isna()
    suite.add(
        f"{name}.{col}: range [{min_val}, {max_val}]",
        violations.sum() == 0,
        f"violations={violations.sum()}",
    )


def check_referential(
    suite: ValidationSuite,
    child_name: str,
    child_df: pd.DataFrame,
    child_col: str,
    parent_name: str,
    parent_ids: set,
) -> None:
    orphans = ~child_df[child_col].isin(parent_ids)
    suite.add(
        f"{child_name}.{child_col} → {parent_name}: referential integrity",
        orphans.sum() == 0,
        f"orphan_rows={orphans.sum()}",
    )


def check_date_order(
    suite: ValidationSuite, name: str, df: pd.DataFrame, earlier_col: str, later_col: str
) -> None:
    e = pd.to_datetime(df[earlier_col].astype(str), errors="coerce")
    l = pd.to_datetime(df[later_col].astype(str), errors="coerce")
    violations = (l < e).sum()
    suite.add(
        f"{name}: {earlier_col} ≤ {later_col}",
        violations == 0,
        f"violations={violations}",
    )


def check_stat(
    suite: ValidationSuite,
    name: str,
    df: pd.DataFrame,
    col: str,
    expected_min: float,
    expected_max: float,
) -> None:
    if col not in df.columns:
        suite.add(f"{name}.{col}: stat check", False, "column missing")
        return
    series = pd.to_numeric(df[col], errors="coerce").dropna()
    avg = series.mean()
    suite.add(
        f"{name}.{col}: mean in [{expected_min:.2f}, {expected_max:.2f}]",
        expected_min <= avg <= expected_max,
        f"mean={avg:.4f}",
    )


# ---------------------------------------------------------------------------
# Validation orchestrator
# ---------------------------------------------------------------------------

def validate_customers(suite: ValidationSuite, df: pd.DataFrame) -> None:
    log.info("--- Validating customers ---")
    check_not_empty(suite, "customers", df)
    check_unique(suite, "customers", df, "customer_id")
    check_no_nulls(suite, "customers", df, ["customer_id", "email", "region", "signup_date"])
    check_domain(
        suite, "customers", df, "region",
        {"Northeast", "Southeast", "Midwest", "West", "Southwest"},
    )
    check_domain(
        suite, "customers", df, "segment",
        {"Consumer", "Corporate", "Home Office"},
    )


def validate_products(suite: ValidationSuite, df: pd.DataFrame) -> None:
    log.info("--- Validating products ---")
    check_not_empty(suite, "products", df)
    check_unique(suite, "products", df, "product_id")
    check_no_nulls(suite, "products", df, ["product_id", "product_name", "category", "unit_price", "unit_cost"])
    check_range(suite, "products", df, "unit_price", min_val=0.01)
    check_range(suite, "products", df, "unit_cost", min_val=0.01)
    check_range(suite, "products", df, "margin_pct", min_val=-10.0, max_val=99.0)


def validate_transactions(
    suite: ValidationSuite,
    df: pd.DataFrame,
    customer_ids: set,
    product_ids: set,
) -> None:
    log.info("--- Validating sales_transactions ---")
    check_not_empty(suite, "transactions", df)
    check_unique(suite, "transactions", df, "transaction_id")
    check_no_nulls(
        suite, "transactions", df,
        ["transaction_id", "customer_id", "product_id", "order_date", "quantity", "unit_price"],
    )
    check_range(suite, "transactions", df, "quantity", min_val=1)
    check_range(suite, "transactions", df, "unit_price", min_val=0.01)
    check_range(suite, "transactions", df, "discount", min_val=0.0, max_val=1.0)
    check_range(suite, "transactions", df, "net_revenue", min_val=0.0)
    check_domain(
        suite, "transactions", df, "region",
        {"Northeast", "Southeast", "Midwest", "West", "Southwest"},
    )
    check_referential(suite, "transactions", df, "customer_id", "customers", customer_ids)
    check_referential(suite, "transactions", df, "product_id", "products", product_ids)
    check_date_order(suite, "transactions", df, "order_date", "ship_date")
    # Statistical plausibility
    check_stat(suite, "transactions", df, "discount", expected_min=0.0, expected_max=0.25)
    check_stat(suite, "transactions", df, "quantity", expected_min=1.0, expected_max=4.0)


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
def main(input_dir: str) -> None:
    """Run data quality validation on cleaned datasets."""
    inp = Path(input_dir)

    if not inp.exists():
        log.error("Input directory '%s' does not exist. Run clean_sales_data.py first.", inp)
        sys.exit(1)

    suite = ValidationSuite()

    log.info("=== Loading datasets ===")
    try:
        customers = load_parquet(inp / "customers")
        products = load_parquet(inp / "products")
        transactions = load_parquet(inp / "sales_transactions")
    except Exception as exc:
        log.error("Failed to load data: %s", exc)
        sys.exit(1)

    log.info("=== Running validation checks ===")
    validate_customers(suite, customers)
    validate_products(suite, products)
    validate_transactions(
        suite,
        transactions,
        customer_ids=set(customers["customer_id"]),
        product_ids=set(products["product_id"]),
    )

    log.info("=== Validation Summary: %s ===", suite.summary())

    if not suite.passed:
        log.error("One or more validation checks FAILED. Review errors above.")
        sys.exit(1)

    log.info("All validation checks PASSED.")


if __name__ == "__main__":
    main()
