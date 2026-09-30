"""The numbers this project publishes -- asserted, not hand-typed.

These are the figures quoted in the README and the resume bullets:
$48.9M total income, Technology at $33.06M (67.6%), 50,000+ transactions.
The query tests execute the actual athena/queries/*.sql files through
DuckDB, so the SQL and the data are checked together.
"""

from pathlib import Path

TOTAL_INCOME = 48_900_000.00
TECHNOLOGY_INCOME = 33_060_000.00
TECHNOLOGY_SHARE = 67.6


def test_total_income(duck):
    (total,) = duck.execute(
        "SELECT ROUND(SUM(income), 2) FROM sales_curated"
    ).fetchone()
    assert float(total) == TOTAL_INCOME


def test_technology_income(duck):
    (tech,) = duck.execute(
        "SELECT ROUND(SUM(income), 2) FROM sales_curated "
        "WHERE category = 'Technology'"
    ).fetchone()
    assert float(tech) == TECHNOLOGY_INCOME


def test_technology_share_is_67_6_percent(duck):
    (share,) = duck.execute(
        "SELECT ROUND(100.0 * SUM(income) "
        "/ (SELECT SUM(income) FROM sales_curated), 1) "
        "FROM sales_curated WHERE category = 'Technology'"
    ).fetchone()
    assert float(share) == TECHNOLOGY_SHARE


def test_at_least_50000_transactions(duck):
    (count,) = duck.execute("SELECT COUNT(*) FROM sales_curated").fetchone()
    assert count >= 50_000


def run_query_file(duck, path):
    """Execute a real Athena query file against DuckDB."""
    sql = path.read_text(encoding="utf-8")
    return duck.execute(sql).fetchall()


def test_category_income_query_returns_headline(duck, project_dir):
    rows = run_query_file(
        duck, project_dir / "athena" / "queries" / "01_category_income.sql"
    )
    header_order = {"category": 0, "transactions": 1, "income": 2, "pct_of_total": 3}
    technology = next(r for r in rows if r[header_order["category"]] == "Technology")
    assert float(technology[header_order["income"]]) == TECHNOLOGY_INCOME
    assert float(technology[header_order["pct_of_total"]]) == TECHNOLOGY_SHARE
    assert sum(float(r[header_order["income"]]) for r in rows) == TOTAL_INCOME


def test_monthly_trend_query_covers_24_months(duck, project_dir):
    rows = run_query_file(
        duck, project_dir / "athena" / "queries" / "02_monthly_trend.sql"
    )
    assert len(rows) == 24
    assert rows[0][0] == "2024-01"
    assert rows[-1][0] == "2025-12"


def test_top_products_query_returns_ten(duck, project_dir):
    rows = run_query_file(
        duck, project_dir / "athena" / "queries" / "03_top_products.sql"
    )
    assert len(rows) == 10
    incomes = [float(r[3]) for r in rows]
    assert incomes == sorted(incomes, reverse=True)
