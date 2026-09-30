"""ETL behaviour: the exact defects removed, idempotency, output schema."""

import sys
from pathlib import Path

import pyarrow.csv as pv

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "python"))

import etl_pipeline  # noqa: E402


def load_raw(raw_csv):
    return pv.read_csv(raw_csv, convert_options=pv.ConvertOptions(
        strings_can_be_null=True, null_values=[""],
    ))


def test_removes_exactly_the_injected_defects(raw_csv):
    table = load_raw(raw_csv)
    _, stats = etl_pipeline.clean(table)
    assert stats == {
        "raw": 52_150,
        "duplicates_dropped": 60,
        "null_customer_dropped": 50,
        "invalid_measures_dropped": 40,
        "clean": 52_000,
    }


def test_clean_is_idempotent(raw_csv):
    table = load_raw(raw_csv)
    once, first = etl_pipeline.clean(table)
    twice, second = etl_pipeline.clean(once)
    assert twice.num_rows == once.num_rows == 52_000
    assert second["duplicates_dropped"] == 0
    assert second["null_customer_dropped"] == 0
    assert second["invalid_measures_dropped"] == 0


def test_output_schema_matches_published_types(curated_dir):
    import pyarrow as pa
    import pyarrow.dataset as ds
    dataset = ds.dataset(
        curated_dir,
        format="parquet",
        partitioning=ds.HivePartitioning(pa.schema([("category", pa.string())])),
    )
    schema = dataset.schema
    assert schema.field("order_date").type == "date32[day]"
    assert schema.field("quantity").type == "int32"
    assert schema.field("income").type == "double"
    assert "category" in schema.names


def test_etl_cli_is_rerunnable(curated_dir, project_dir):
    """Running the ETL again must succeed and reproduce the same output."""
    import subprocess
    subprocess.run(
        [sys.executable, str(project_dir / "python" / "etl_pipeline.py")],
        check=True, cwd=project_dir, capture_output=True,
    )
    import pyarrow.dataset as ds
    dataset = ds.dataset(curated_dir, format="parquet")
    assert dataset.count_rows() == 52_000
