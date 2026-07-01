"""
generate_datasets.py
--------------------
Generates synthetic but realistic customers, products, and sales_transactions
datasets suitable for a Business Intelligence portfolio project.

All output is deterministic — seed=42 produces identical files on every run.

Usage:
    python datasets/generate_datasets.py

Output:
    data/raw/customers.csv
    data/raw/products.csv
    data/raw/sales_transactions.csv
"""

import logging
import os
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 42
N_CUSTOMERS = 2_000
N_PRODUCTS = 200
N_TRANSACTIONS = 50_000
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"

random.seed(SEED)
np.random.seed(SEED)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
REGIONS = ["Northeast", "Southeast", "Midwest", "West", "Southwest"]

REGION_CITIES: dict[str, list[str]] = {
    "Northeast": ["New York", "Boston", "Philadelphia", "Providence", "Hartford"],
    "Southeast": ["Atlanta", "Miami", "Charlotte", "Nashville", "Orlando"],
    "Midwest":   ["Chicago", "Detroit", "Cleveland", "Indianapolis", "Minneapolis"],
    "West":      ["Los Angeles", "Seattle", "San Francisco", "Portland", "Denver"],
    "Southwest": ["Dallas", "Houston", "Phoenix", "Austin", "Las Vegas"],
}

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SEGMENT_WEIGHTS = [0.52, 0.32, 0.16]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph",
    "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa",
    "Daniel", "Nancy", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
]

CATEGORIES: dict[str, dict] = {
    "Technology": {
        "sub_categories": ["Phones", "Computers", "Accessories", "Copiers"],
        "cost_range": (50, 1800),
        "margin_range": (0.28, 0.45),
    },
    "Furniture": {
        "sub_categories": ["Chairs", "Tables", "Bookcases", "Furnishings"],
        "cost_range": (30, 900),
        "margin_range": (0.08, 0.20),
    },
    "Office Supplies": {
        "sub_categories": ["Paper", "Binders", "Art", "Labels", "Fasteners", "Envelopes"],
        "cost_range": (2, 80),
        "margin_range": (0.18, 0.38),
    },
    "Clothing": {
        "sub_categories": ["Tops", "Bottoms", "Outerwear", "Footwear", "Accessories"],
        "cost_range": (10, 150),
        "margin_range": (0.40, 0.65),
    },
    "Sports & Outdoors": {
        "sub_categories": ["Exercise", "Camping", "Team Sports", "Water Sports"],
        "cost_range": (15, 400),
        "margin_range": (0.22, 0.42),
    },
}

BRANDS = [
    "Acme Corp", "NovaTech", "PrimeLine", "ClearVision", "ApexGear",
    "StellarBrands", "EchoPoint", "VertexPro", "LunarEdge", "ZenithCo",
]


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_customers(n: int) -> pd.DataFrame:
    """Return a DataFrame with n synthetic customer records."""
    log.info("Generating %d customer records …", n)

    records = []
    used_emails: set[str] = set()

    for _ in range(n):
        region = random.choice(REGIONS)
        city = random.choice(REGION_CITIES[region])
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)

        base_email = f"{first.lower()}.{last.lower()}"
        email = f"{base_email}@example.com"
        suffix = 1
        while email in used_emails:
            email = f"{base_email}{suffix}@example.com"
            suffix += 1
        used_emails.add(email)

        signup_date = date(2019, 1, 1) + timedelta(
            days=random.randint(0, (date(2023, 12, 31) - date(2019, 1, 1)).days)
        )
        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]

        records.append(
            {
                "customer_id": str(uuid.UUID(int=random.getrandbits(128), version=4)),
                "first_name": first,
                "last_name": last,
                "email": email,
                "region": region,
                "country": "United States",
                "city": city,
                "signup_date": signup_date.isoformat(),
                "segment": segment,
            }
        )

    return pd.DataFrame(records)


def generate_products(n: int) -> pd.DataFrame:
    """Return a DataFrame with n synthetic product records."""
    log.info("Generating %d product records …", n)

    records = []
    category_names = list(CATEGORIES.keys())
    category_weights = [0.25, 0.20, 0.30, 0.15, 0.10]

    for i in range(n):
        category = random.choices(category_names, weights=category_weights, k=1)[0]
        cfg = CATEGORIES[category]
        sub_cat = random.choice(cfg["sub_categories"])
        brand = random.choice(BRANDS)
        unit_cost = round(random.uniform(*cfg["cost_range"]), 2)
        margin = random.uniform(*cfg["margin_range"])
        unit_price = round(unit_cost * (1 + margin), 2)

        records.append(
            {
                "product_id": f"PROD-{i+1:05d}",
                "product_name": f"{brand} {sub_cat} {random.randint(100, 999)}",
                "category": category,
                "sub_category": sub_cat,
                "unit_cost": unit_cost,
                "unit_price": unit_price,
                "brand": brand,
            }
        )

    return pd.DataFrame(records)


def generate_transactions(
    n: int,
    customers: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Return a DataFrame with n synthetic sales transaction records."""
    log.info("Generating %d transaction records …", n)

    customer_ids = customers["customer_id"].tolist()
    customer_regions = customers.set_index("customer_id")["region"].to_dict()
    customer_signups = customers.set_index("customer_id")["signup_date"].to_dict()
    product_ids = products["product_id"].tolist()
    product_prices = products.set_index("product_id")["unit_price"].to_dict()

    # Seasonal multipliers (index 0 = Jan)
    month_weights = [0.06, 0.06, 0.08, 0.08, 0.08, 0.07, 0.07, 0.08, 0.08, 0.10, 0.12, 0.12]

    start_date = date(2020, 1, 1)
    end_date = date(2023, 12, 31)
    date_range_days = (end_date - start_date).days

    records = []
    for _ in range(n):
        # Weighted random date (seasonal)
        month = random.choices(range(1, 13), weights=month_weights, k=1)[0]
        year = random.choices(
            [2020, 2021, 2022, 2023],
            weights=[0.18, 0.24, 0.28, 0.30],
            k=1,
        )[0]
        max_day = 28 if month == 2 else (30 if month in {4, 6, 9, 11} else 31)
        order_day = random.randint(1, max_day)
        order_date = date(year, month, order_day)

        # Ensure order is after customer signup
        customer_id = random.choice(customer_ids)
        signup_str = customer_signups[customer_id]
        signup = date.fromisoformat(signup_str)
        if order_date < signup:
            order_date = signup + timedelta(days=random.randint(1, 30))

        ship_date = order_date + timedelta(days=random.randint(1, 7))

        product_id = random.choice(product_ids)
        quantity = int(np.random.choice([1, 2, 3, 4, 5, 10], p=[0.45, 0.25, 0.15, 0.08, 0.05, 0.02]))

        # Apply discounts occasionally
        discount_options = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
        discount_weights = [0.55, 0.15, 0.12, 0.10, 0.05, 0.03]
        discount = random.choices(discount_options, weights=discount_weights, k=1)[0]

        unit_price = product_prices[product_id]
        region = customer_regions[customer_id]

        records.append(
            {
                "transaction_id": str(uuid.UUID(int=random.getrandbits(128), version=4)),
                "customer_id": customer_id,
                "product_id": product_id,
                "order_date": order_date.isoformat(),
                "ship_date": ship_date.isoformat(),
                "quantity": quantity,
                "unit_price": unit_price,
                "discount": discount,
                "region": region,
                "year": order_date.year,
                "month": order_date.month,
            }
        )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    customers = generate_customers(N_CUSTOMERS)
    products = generate_products(N_PRODUCTS)
    transactions = generate_transactions(N_TRANSACTIONS, customers, products)

    customers_path = OUTPUT_DIR / "customers.csv"
    products_path = OUTPUT_DIR / "products.csv"
    transactions_path = OUTPUT_DIR / "sales_transactions.csv"

    customers.to_csv(customers_path, index=False)
    products.to_csv(products_path, index=False)
    transactions.to_csv(transactions_path, index=False)

    log.info("Wrote %d rows → %s", len(customers), customers_path)
    log.info("Wrote %d rows → %s", len(products), products_path)
    log.info("Wrote %d rows → %s", len(transactions), transactions_path)

    # Quick sanity checks
    assert customers["customer_id"].nunique() == N_CUSTOMERS, "Duplicate customer_id detected"
    assert products["product_id"].nunique() == N_PRODUCTS, "Duplicate product_id detected"
    assert transactions["transaction_id"].nunique() == N_TRANSACTIONS, "Duplicate transaction_id detected"

    log.info("All assertions passed. Datasets ready.")


if __name__ == "__main__":
    main()
