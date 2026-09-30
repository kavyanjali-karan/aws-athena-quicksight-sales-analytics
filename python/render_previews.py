"""Render dashboard preview PNGs from the curated Parquet.

Executes the actual athena/queries/*.sql files through DuckDB (the local
Athena stand-in used by the tests) and plots the results, so the images
in assets/ show exactly what the queries return. These are local renders
of query results -- the QuickSight version of these visuals lives in an
AWS account (spec: quicksight/dashboard_spec.md).

Usage:
    python python/render_previews.py

Requires the curated data: run the Quick Start steps first if missing.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT = Path(__file__).resolve().parents[1]
ASSETS = PROJECT / "assets"
QUERIES = PROJECT / "athena" / "queries"
CURATED = PROJECT / "data" / "curated" / "sales"

ACCENT = "#1D4E89"      # highlight (Technology / primary series)
SECONDARY = "#7B8794"   # remaining bars
INK = "#1F2933"
MUTED = "#52606D"
GRID = "#E4E7EB"


def connect():
    try:
        import duckdb
    except ImportError:
        sys.exit("duckdb is required: pip install -r requirements.txt")
    con = duckdb.connect()
    parquet_glob = (CURATED / "*" / "*.parquet").as_posix()
    con.execute(
        f"CREATE OR REPLACE VIEW sales_curated AS "
        f"SELECT * FROM read_parquet('{parquet_glob}', hive_partitioning=true)"
    )
    return con


def run_query(con, filename):
    return con.execute((QUERIES / filename).read_text(encoding="utf-8")).fetchall()


def style_axes(ax):
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="both", length=0, colors=MUTED)
    ax.set_axisbelow(True)


def header(fig, title, subtitle, left, title_y=0.97, sub_y=0.895):
    """Figure-level header: positions are explicit, so nothing can collide."""
    fig.text(left, title_y, title, fontsize=15, fontweight="bold",
             color=INK, va="top")
    fig.text(left, sub_y, subtitle, fontsize=9.5, color=MUTED, va="top")


def save(fig, name):
    ASSETS.mkdir(exist_ok=True)
    fig.savefig(ASSETS / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"OK {name}")


def plot_category_income(rows):
    """rows: (category, transactions, income, pct_of_total)"""
    rows = sorted(rows, key=lambda r: float(r[2]))
    categories = [r[0] for r in rows]
    incomes = [float(r[2]) for r in rows]
    pcts = [float(r[3]) for r in rows]
    colors = [ACCENT if c == "Technology" else SECONDARY for c in categories]

    fig, ax = plt.subplots(figsize=(10, 4.8))
    fig.subplots_adjust(left=0.14, right=0.96, top=0.78, bottom=0.12)
    bars = ax.barh(categories, incomes, color=colors, height=0.58)
    for bar, income, pct in zip(bars, incomes, pcts):
        ax.text(
            bar.get_width() + max(incomes) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"${income / 1e6:,.2f}M  ·  {pct}%",
            va="center", fontsize=11, fontweight="bold", color=INK,
        )
    ax.set_xlim(0, max(incomes) * 1.34)
    ax.xaxis.set_major_formatter(lambda v, _: f"${v / 1e6:,.0f}M")
    ax.xaxis.grid(True, color=GRID)
    style_axes(ax)
    header(
        fig,
        "Income by category",
        "52,000 transactions · $48.9M total · Athena query 01_category_income.sql",
        left=0.045,
    )
    save(fig, "category_income.png")


def plot_monthly_trend(rows):
    """rows: (sales_month, transactions, income, mom_growth_pct)"""
    months = [r[0] for r in rows]
    incomes = [float(r[2]) / 1e6 for r in rows]

    fig, ax = plt.subplots(figsize=(10, 4.8))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.78, bottom=0.14)
    ax.plot(range(len(months)), incomes, color=ACCENT, linewidth=2.2)
    ax.fill_between(range(len(months)), incomes, color=ACCENT, alpha=0.08)
    ax.yaxis.grid(True, color=GRID)
    ax.set_ylim(0, max(incomes) * 1.18)
    ax.set_xlim(-0.5, len(months) - 0.5)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.1f}M")
    ticks = [i for i, m in enumerate(months) if m.endswith(("-01", "-04", "-07", "-10"))]
    ax.set_xticks(ticks, [months[i][2:] for i in ticks], fontsize=9)
    style_axes(ax)
    header(
        fig,
        "Monthly income trend, 2024–2025",
        "24 months · month-over-month growth computed in SQL · Athena query 02_monthly_trend.sql",
        left=0.045,
    )
    save(fig, "monthly_trend.png")


def plot_top_products(rows):
    """rows: (product_name, sub_category, transactions, income)"""
    rows = list(reversed(rows))
    names = [r[0] for r in rows]
    incomes = [float(r[3]) for r in rows]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.subplots_adjust(left=0.24, right=0.96, top=0.82, bottom=0.09)
    bars = ax.barh(names, incomes, color=ACCENT, height=0.6)
    for bar, income in zip(bars, incomes):
        ax.text(
            bar.get_width() + max(incomes) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"${income / 1e6:,.2f}M",
            va="center", fontsize=10, fontweight="bold", color=INK,
        )
    ax.set_xlim(0, max(incomes) * 1.24)
    ax.xaxis.set_major_formatter(lambda v, _: f"${v / 1e6:,.1f}M")
    ax.xaxis.grid(True, color=GRID)
    style_axes(ax)
    header(
        fig,
        "Top 10 products by income",
        "Ranked from the curated Parquet · Athena query 03_top_products.sql",
        left=0.045,
        title_y=0.97, sub_y=0.915,
    )
    save(fig, "top_products.png")


def main():
    if not CURATED.is_dir():
        sys.exit(
            "Curated data not found.\n"
            "Run first:\n"
            "  python data/generate_sales_data.py\n"
            "  python python/etl_pipeline.py"
        )
    con = connect()
    plot_category_income(run_query(con, "01_category_income.sql"))
    plot_monthly_trend(run_query(con, "02_monthly_trend.sql"))
    plot_top_products(run_query(con, "03_top_products.sql"))
    print(f"Previews written to {ASSETS}")


if __name__ == "__main__":
    main()
