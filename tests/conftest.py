"""Shared fixtures: materialise the dataset once per test session."""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]


def run_cli(*script):
    """Run a project script the same way the README documents it."""
    subprocess.run(
        [sys.executable, str(PROJECT.joinpath(*script))],
        check=True,
        cwd=PROJECT,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="session")
def project_dir():
    return PROJECT


@pytest.fixture(scope="session")
def raw_csv():
    """Raw extract, generated on demand (deterministic seed)."""
    path = PROJECT / "data" / "raw" / "sales_transactions.csv"
    if not path.exists():
        run_cli("data", "generate_sales_data.py")
    return path


@pytest.fixture(scope="session")
def curated_dir(raw_csv):
    """Partitioned Parquet output, produced by the real ETL entry point."""
    run_cli("python", "etl_pipeline.py")
    path = PROJECT / "data" / "curated" / "sales"
    assert path.is_dir(), "ETL did not produce the curated output"
    return path


@pytest.fixture(scope="session")
def duck(curated_dir):
    """DuckDB connection exposing the curated data as `sales_curated`.

    DuckDB stands in for Athena locally: it reads the same hive-partitioned
    Parquet and runs the same ANSI-flavoured SQL.
    """
    duckdb = pytest.importorskip("duckdb")
    con = duckdb.connect()
    parquet_glob = (curated_dir / "*" / "*.parquet").as_posix()
    con.execute(
        f"CREATE OR REPLACE VIEW sales_curated AS "
        f"SELECT * FROM read_parquet('{parquet_glob}', hive_partitioning=true)"
    )
    return con
