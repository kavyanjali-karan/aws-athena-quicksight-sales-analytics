"""Run the Athena DDL and query files against a real AWS account.

This is deploy-time tooling: it needs AWS credentials and the
CloudFormation stack from infra/cloudformation.yaml. It is not run in CI.

Usage:
    python python/run_athena_queries.py --bucket <bucket> [--region us-east-1]
                                         [--database sales_analytics_dev]
                                         [--workgroup primary]
                                         [query_file ...]

With no query_file arguments it runs every file in athena/queries/.
The --database default matches the CloudFormation parameter DatabaseName
(stack output "AthenaDatabase"); pass it explicitly if you deploy with a
different value.
"""

import argparse
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DDL_PATH = PROJECT / "athena" / "ddl.sql"
QUERY_DIR = PROJECT / "athena" / "queries"
RESULTS_PREFIX = "athena-results/"

TIMEOUT_SECONDS = 120
POLL_SECONDS = 1.5


def statements(sql_text):
    """Split a SQL file into statements (files contain no ';' in literals)."""
    return [s.strip() for s in sql_text.split(";") if s.strip()]


def wait_for_completion(athena, execution_id, label):
    """Poll Athena until the query succeeds; print the reason and exit on failure."""
    deadline = time.time() + TIMEOUT_SECONDS
    while time.time() < deadline:
        status = athena.get_query_execution(QueryExecutionId=execution_id)
        state = status["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            return
        if state in ("FAILED", "CANCELLED"):
            reason = status["QueryExecution"]["Status"].get("StateChangeReason", "unknown")
            sys.exit(f"{label}: Athena query {state.lower()} -- {reason}")
        time.sleep(POLL_SECONDS)
    sys.exit(f"{label}: timed out after {TIMEOUT_SECONDS}s (execution {execution_id})")


def run_statement(athena, sql, args, label):
    """Start one statement, wait for it, return the fetched rows (or None)."""
    execution_id = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": args.database},
        WorkGroup=args.workgroup,
        ResultConfiguration={"OutputLocation": f"s3://{args.bucket}/{RESULTS_PREFIX}"},
    )["QueryExecutionId"]
    wait_for_completion(athena, execution_id, label)

    rows = []
    token = None
    while True:
        page = athena.get_query_results(QueryExecutionId=execution_id, NextToken=token)
        rows.extend(page["ResultSet"]["Rows"])
        token = page.get("NextToken")
        if not token:
            break
    return rows


def print_table(rows):
    """Print result rows as a plain aligned table (first row is the header)."""
    if not rows:
        print("  (no rows)")
        return
    values = [[c.get("VarCharValue", "") for c in row["Data"]] for row in rows]
    header, *body = values
    widths = [max(len(r[i]) for r in values) for i in range(len(header))]
    print("  " + "  ".join(h.ljust(w) for h, w in zip(header, widths)))
    print("  " + "  ".join("-" * w for w in widths))
    for row in body:
        print("  " + "  ".join(c.ljust(w) for c, w in zip(row, widths)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run Athena DDL + queries against AWS.")
    parser.add_argument("--bucket", required=True, help="S3 bucket from the CloudFormation outputs")
    parser.add_argument("--region", default=None, help="AWS region (defaults to your CLI config)")
    parser.add_argument("--database", default="sales_analytics_dev",
                        help="Glue/Athena database (default matches the CloudFormation DatabaseName parameter)")
    parser.add_argument("--workgroup", default="primary", help="Athena workgroup")
    parser.add_argument("queries", nargs="*", type=Path, help="specific .sql files (default: all in athena/queries/)")
    args = parser.parse_args(argv)

    try:
        import boto3
    except ImportError:
        sys.exit("boto3 is required for AWS runs: pip install boto3")

    athena = boto3.client("athena", region_name=args.region)
    query_files = args.queries or sorted(QUERY_DIR.glob("*.sql"))
    if not query_files:
        sys.exit(f"No query files found in {QUERY_DIR}")

    print(f"Applying DDL ({DDL_PATH.name})...")
    ddl = DDL_PATH.read_text(encoding="utf-8").replace("YOUR_BUCKET", args.bucket)
    for i, stmt in enumerate(statements(ddl), start=1):
        run_statement(athena, stmt, args, f"ddl statement {i}")
    print("  DDL applied.")

    for path in query_files:
        print(f"\n== {path.name}")
        rows = run_statement(athena, path.read_text(encoding="utf-8"), args, path.name)
        print_table(rows)

    print("\nAll statements succeeded.")


if __name__ == "__main__":
    main()
