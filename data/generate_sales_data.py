"""Generate the raw sales extract for the Athena pipeline.

Produces a messy CSV export -- the kind a CRM dumps at 2am -- with
52,150 rows containing duplicates, missing customer ids, and negative
amounts. The PyArrow ETL is responsible for turning this into the clean
52,000-row analytical dataset.

Deterministic (seed 42). Clean-row totals are pinned to the figures
this project quotes: $48.9M total income, Technology at $33.06M (67.6%).

Output: data/raw/sales_transactions.csv
"""

import csv
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

SEED = 42
RAW_DIR = Path(__file__).resolve().parent / "raw"
RAW_PATH = RAW_DIR / "sales_transactions.csv"

START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)
CUSTOMER_COUNT = 8_000
REGIONS = [("East", 0.30), ("West", 0.30), ("North", 0.15), ("South", 0.15), ("Central", 0.10)]

# rows, exact income target (cents), products as (sub_category, name, base_price)
CATEGORIES = {
    "Technology": {
        "rows": 21_000,
        "target": 33_060_000.00,
        "products": [
            ("Computers", "Workstation Laptop 15\"", 720),
            ("Computers", "Business Laptop 14\"", 480),
            ("Mobile", "Enterprise Smartphone", 550),
            ("Displays", "4K Monitor 27\"", 290),
            ("Networking", "Managed Switch 24-Port", 240),
            ("Networking", "Wi-Fi 6 Access Point", 160),
        ],
    },
    "Furniture": {
        "rows": 15_000,
        "target": 9_120_000.00,
        "products": [
            ("Tables", "Conference Table 8-Seat", 310),
            ("Desks", "Standing Desk 60\"", 170),
            ("Seating", "Ergonomic Task Chair", 140),
            ("Seating", "Reception Sofa", 240),
            ("Storage", "Bookcase 5-Shelf", 75),
            ("Storage", "Mobile Filing Cabinet", 65),
        ],
    },
    "Office Supplies": {
        "rows": 16_000,
        "target": 6_720_000.00,
        "products": [
            ("Print", "Toner Cartridge High-Yield", 95),
            ("Paper", "Copy Paper Case (10 reams)", 45),
            ("Paper", "Ring Binder 12-Pack", 22),
            ("Boards", "Whiteboard 4x6 Magnetic", 130),
            ("Desk", "Desk Organizer Set", 28),
            ("Breakroom", "Coffee Pods 100-Count", 35),
        ],
    },
}

# Defects injected into the raw extract for the ETL to clean up.
DEFECT_DUPLICATES = 60
DEFECT_NULL_CUSTOMER = 50
DEFECT_NEGATIVE_AMOUNT = 40

HEADER = [
    "transaction_id", "order_date", "customer_id", "region",
    "product_id", "product_name", "category", "sub_category",
    "quantity", "unit_price", "income",
]

FIELDNAMES = HEADER  # alias kept explicit for readability


def build_catalog():
    """Flat product list with stable ids: [(category, sub, name, base), ...]"""
    catalog = []
    for cat, spec in CATEGORIES.items():
        for sub, name, base in spec["products"]:
            catalog.append((cat, sub, name, base))
    return catalog


def clean_rows(rng, catalog):
    """Generate the 52,000 clean rows with category income pinned to target."""
    region_names = [r for r, _ in REGIONS]
    region_weights = [w for _, w in REGIONS]
    rows = []

    for cat, spec in CATEGORIES.items():
        cat_rows = []
        products = [(s, n, b) for c, s, n, b in catalog if c == cat]
        for _ in range(spec["rows"]):
            sub, name, base = rng.choice(products)
            quantity = rng.randint(1, 9)
            unit_price = round(base * rng.uniform(0.9, 1.1), 2)
            cat_rows.append({
                "order_date": (START_DATE + timedelta(days=rng.randint(0, (END_DATE - START_DATE).days))).isoformat(),
                "customer_id": f"CUST-{rng.randint(1, CUSTOMER_COUNT):05d}",
                "region": rng.choices(region_names, weights=region_weights, k=1)[0],
                "product_id": f"P{catalog.index((cat, sub, name, base)) + 1:04d}",
                "product_name": name,
                "category": cat,
                "sub_category": sub,
                "quantity": quantity,
                "unit_price": unit_price,
                "income": round(quantity * unit_price, 2),
            })

        # Scale unit prices so the category income lands exactly on target.
        raw_total = sum(r["income"] for r in cat_rows)
        factor = spec["target"] / raw_total
        for r in cat_rows:
            r["unit_price"] = round(r["unit_price"] * factor, 2)
            r["income"] = round(r["quantity"] * r["unit_price"], 2)

        # Consume the residual cents on quantity-1 rows (1 cent at a time).
        target_cents = round(spec["target"] * 100)
        diff_cents = target_cents - round(sum(r["income"] for r in cat_rows) * 100)
        one_qty = [r for r in cat_rows if r["quantity"] == 1]
        applied = 0
        cap = 20  # max cents of adjustment per row
        for r in one_qty:
            if applied == diff_cents:
                break
            step = min(cap, abs(diff_cents - applied))
            step *= 1 if diff_cents > 0 else -1
            new_price = round(r["unit_price"] + step / 100, 2)
            if new_price <= 0:
                continue
            r["unit_price"] = new_price
            r["income"] = new_price
            applied += step
        assert applied == diff_cents, (
            f"{cat}: could not pin income to target "
            f"(residual {diff_cents - applied} cents left)"
        )

        total = round(sum(r["income"] for r in cat_rows), 2)
        assert total == spec["target"], f"{cat}: {total} != {spec['target']}"
        cat_rows.sort(key=lambda r: r["order_date"])
        rows.extend(cat_rows)

    rng.shuffle(rows)
    for i, r in enumerate(rows, start=1):
        r["transaction_id"] = f"TXN-{i:06d}"
    return rows


def inject_defects(rng, rows, next_id):
    """Append duplicate / null-customer / negative-amount rows to the extract."""
    out = list(rows)

    for src in rng.sample(rows, DEFECT_DUPLICATES):
        out.append(dict(src))  # exact duplicate row

    for _ in range(DEFECT_NULL_CUSTOMER):
        r = dict(rng.choice(rows))
        r["transaction_id"] = f"TXN-{next_id:06d}"
        next_id += 1
        r["customer_id"] = ""
        out.append(r)

    for _ in range(DEFECT_NEGATIVE_AMOUNT):
        r = dict(rng.choice(rows))
        r["transaction_id"] = f"TXN-{next_id:06d}"
        next_id += 1
        r["income"] = -abs(round(r["income"], 2))
        out.append(r)

    rng.shuffle(out)
    return out


def main():
    rng = random.Random(SEED)
    catalog = build_catalog()
    clean = clean_rows(rng, catalog)
    final = inject_defects(rng, clean, next_id=len(clean) + 1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in final:
            writer.writerow({
                **r,
                "unit_price": f"{r['unit_price']:.2f}",
                "income": f"{r['income']:.2f}",
            })

    tech = CATEGORIES["Technology"]["target"]
    total = sum(c["target"] for c in CATEGORIES.values())
    pct = round(100 * tech / total, 1)
    print(f"Raw extract : {RAW_PATH.relative_to(Path(__file__).parents[1])} ({len(final):,} rows)")
    print(f"Clean rows  : {len(clean):,}")
    print(f"Defects     : {DEFECT_DUPLICATES} duplicates, "
          f"{DEFECT_NULL_CUSTOMER} missing customer ids, "
          f"{DEFECT_NEGATIVE_AMOUNT} negative amounts")
    print(f"Technology  : ${tech:,.2f} of ${total:,.2f} ({pct}%)")


if __name__ == "__main__":
    main()
