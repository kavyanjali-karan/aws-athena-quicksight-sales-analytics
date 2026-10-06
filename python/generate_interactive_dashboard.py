"""Build assets/interactive_dashboard.html from the Athena SQL queries.

Runs the actual athena/queries/*.sql files through DuckDB (the local
Athena stand-in used by the tests) and embeds the results as the page's
DATA payload, so the live dashboard always shows exactly what the
queries return — the same SQL behind the PNG previews and the test suite.

Usage:
    python python/generate_interactive_dashboard.py

Requires the curated Parquet: run the Quick Start steps first if missing.
"""

import json
from pathlib import Path

import duckdb

PROJECT = Path(__file__).resolve().parents[1]
QUERIES = PROJECT / "athena" / "queries"
CURATED = PROJECT / "data" / "curated" / "sales"
OUTPUT = PROJECT / "assets" / "interactive_dashboard.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cloud Sales Analytics — Sales Performance</title>
<style>
:root{--accent:#1D4E89;--muted:#52606D;--ink:#1F2933;--line:#E4E7EB;--bg:#F7F8FA}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink)}
.wrap{max-width:1040px;margin:0 auto;padding:32px 20px 48px}
header h1{font-size:26px;margin:0 0 6px}
header p{color:var(--muted);margin:0 0 24px;font-size:14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-bottom:26px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.kpi .v{font-size:28px;font-weight:700;color:var(--accent)}
.kpi .l{font-size:13px;color:var(--muted);margin-top:4px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:22px}
.card h2{font-size:16px;margin:0 0 4px}
.card .src{font-size:12px;color:var(--muted);margin:0 0 14px}
.barrow{display:grid;grid-template-columns:190px 1fr 130px;gap:10px;align-items:center;margin:8px 0;font-size:13px}
.barrow.prod{grid-template-columns:230px 1fr 100px}
.track{background:var(--bg);border-radius:6px;height:22px;overflow:hidden}
.fill{height:100%;background:#7B8794;border-radius:6px}
.fill.hi{background:var(--accent)}
.val{text-align:right;font-weight:600;font-variant-numeric:tabular-nums}
footer{color:var(--muted);font-size:12px;line-height:1.7}
svg text{fill:var(--muted);font-size:11px;font-family:inherit}
@media(max-width:640px){.barrow{grid-template-columns:120px 1fr 110px}.barrow.prod{grid-template-columns:150px 1fr 90px}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <p style="margin:0 0 10px;font-size:13px"><a href="https://kavyanjali-karan.github.io/executive-kpi-governance-platform/interactive_dashboard.html" style="color:#1D4E89;text-decoration:none">&larr; KPI Governance dashboard</a></p>
  <h1>Cloud Sales Analytics</h1>
  <p id="sub"></p>
</header>
<div class="kpis" id="kpis"></div>
<div class="card"><h2>Income by category</h2><p class="src">athena/queries/01_category_income.sql</p><div id="cat"></div></div>
<div class="card"><h2>Monthly income trend, 2024&ndash;2025</h2><p class="src">athena/queries/02_monthly_trend.sql</p><div id="trend"></div></div>
<div class="card"><h2>Top 10 products by income</h2><p class="src">athena/queries/03_top_products.sql</p><div id="top"></div></div>
<footer id="foot"></footer>
</div>
<script>
const DATA = __DATA_JSON__;
const fmtM = (v, d) => "$" + (v / 1e6).toFixed(d === undefined ? 2 : d) + "M";
const fmtN = v => v.toLocaleString("en-US");

const totalIncome = DATA.category.reduce((s, r) => s + r[2], 0);
const totalTxn = DATA.category.reduce((s, r) => s + r[1], 0);
const tech = DATA.category.find(r => r[0] === "Technology");

document.getElementById("sub").textContent =
  fmtN(totalTxn) + " transactions · 24 months (2024–2025) · rendered from the Athena queries";

document.getElementById("kpis").innerHTML =
  '<div class="kpi"><div class="v">' + fmtM(totalIncome, 1) +
  '</div><div class="l">Total income</div></div>' +
  '<div class="kpi"><div class="v">' + fmtN(totalTxn) +
  '</div><div class="l">Transactions cleaned &amp; partitioned</div></div>' +
  '<div class="kpi"><div class="v">' + tech[3] + '%</div><div class="l">Technology share &mdash; ' +
  fmtM(tech[2]) + ' of ' + fmtM(totalIncome, 1) + '</div></div>';

const maxCat = Math.max.apply(null, DATA.category.map(r => r[2]));
document.getElementById("cat").innerHTML = DATA.category.map(r =>
  '<div class="barrow"><div>' + r[0] +
  '</div><div class="track"><div class="fill' + (r[0] === "Technology" ? " hi" : "") +
  '" style="width:' + (100 * r[2] / maxCat).toFixed(1) + '%"></div></div>' +
  '<div class="val">' + fmtM(r[2]) + ' · ' + r[3] + '%</div></div>'
).join("");

function trendSVG() {
  const rows = DATA.monthly, w = 960, h = 260, L = 58, R = 14, T = 16, B = 30;
  const iw = w - L - R, ih = h - T - B;
  const vals = rows.map(r => r[2] / 1e6);
  const maxV = Math.max.apply(null, vals) * 1.12;
  const x = i => L + i * iw / (rows.length - 1);
  const y = v => T + ih - (v / maxV) * ih;
  let g = "";
  for (let k = 0; k <= 4; k++) {
    const v = maxV * k / 4, yy = y(v);
    g += '<line x1="' + L + '" y1="' + yy + '" x2="' + (w - R) + '" y2="' + yy +
         '" stroke="#E4E7EB"/><text x="' + (L - 8) + '" y="' + (yy + 4) +
         '" text-anchor="end">$' + v.toFixed(1) + 'M</text>';
  }
  const pts = rows.map((r, i) => x(i).toFixed(1) + "," + y(r[2] / 1e6).toFixed(1)).join(" ");
  const area = "M" + L + "," + (T + ih) + " L" + pts.split(" ").join(" L") +
               " L" + (w - R) + "," + (T + ih) + " Z";
  let xt = "";
  rows.forEach((r, i) => {
    if (i % 3 === 0) {
      xt += '<text x="' + x(i) + '" y="' + (h - 8) + '" text-anchor="middle">' +
            r[0].slice(2) + "</text>";
    }
  });
  return '<svg viewBox="0 0 ' + w + ' ' + h + '" width="100%" height="' + h +
         '" role="img" aria-label="Monthly income trend">' + g +
         '<path d="' + area + '" fill="#1D4E89" opacity="0.08"/>' +
         '<polyline points="' + pts + '" fill="none" stroke="#1D4E89" stroke-width="2.5"/>' +
         xt + "</svg>";
}
document.getElementById("trend").innerHTML = trendSVG();

const maxTop = Math.max.apply(null, DATA.top.map(r => r[3]));
document.getElementById("top").innerHTML = DATA.top.map(r =>
  '<div class="barrow prod"><div>' + r[0] +
  '</div><div class="track"><div class="fill hi" style="width:' +
  (100 * r[3] / maxTop).toFixed(1) + '%"></div></div>' +
  '<div class="val">' + fmtM(r[3]) + '</div></div>'
).join("");

document.getElementById("foot").innerHTML =
  "Rendered by <b>python/generate_interactive_dashboard.py</b> from <b>athena/queries/*.sql</b> against the " +
  "curated Parquet &mdash; the same SQL the PNG previews and the test suite run. " +
  "No external libraries; the page works offline.";
</script>
</body>
</html>
"""


def run_query(con: duckdb.DuckDBPyConnection, name: str):
    sql = (QUERIES / name).read_text(encoding="utf-8")
    return con.execute(sql).fetchall()


def main() -> None:
    con = duckdb.connect()
    parquet_glob = (CURATED / "*" / "*.parquet").as_posix()
    con.execute(
        f"CREATE VIEW sales_curated AS SELECT * FROM read_parquet('{parquet_glob}')"
    )

    category = [
        [r[0], int(r[1]), float(r[2]), float(r[3])]
        for r in run_query(con, "01_category_income.sql")
    ]
    monthly = [
        [r[0], int(r[1]), float(r[2]), None if r[3] is None else float(r[3])]
        for r in run_query(con, "02_monthly_trend.sql")
    ]
    top = [
        [r[0], r[1], int(r[2]), float(r[3])]
        for r in run_query(con, "03_top_products.sql")
    ]

    payload = json.dumps(
        {"category": category, "monthly": monthly, "top": top}
    )
    html = TEMPLATE.replace("__DATA_JSON__", payload)
    OUTPUT.write_text(html, encoding="utf-8", newline="\n")

    total = sum(r[2] for r in category)
    txn = sum(r[1] for r in category)
    tech = next(r for r in category if r[0] == "Technology")
    print(f"Interactive dashboard generated: {OUTPUT}")
    print(f"  Transactions: {txn:,} | Total income: ${total / 1e6:.1f}M")
    print(f"  Technology share: {tech[3]}% (${tech[2] / 1e6:.2f}M)")


if __name__ == "__main__":
    main()
