"""Generate a reproducible synthetic sales dataset -> data/sales_data.csv

Swap this out for a real dataset (e.g. Kaggle "Superstore") later.
Columns: Date, Category, Product, Region, Orders, Sales, Profit, Customer_ID
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
PRODUCTS = {
    "Electronics": ["Laptop", "Smartphone", "Headphones"],
    "Clothing": ["Jacket", "Sneakers", "T-Shirt"],
    "Books": ["Novel", "Textbook", "Comics"],
    "Home & Living": ["Lamp", "Backpack", "Mug"],
}
PRICE = {"Electronics": (150, 900), "Clothing": (20, 150), "Books": (8, 60), "Home & Living": (10, 120)}
REGIONS = ["North", "South", "East", "West"]

rows = []
for date in pd.date_range("2025-01-01", "2025-12-31", freq="D"):
    for _ in range(rng.integers(4, 10)):
        cat = rng.choice(list(PRODUCTS))
        orders = int(rng.integers(1, 5))
        sales = orders * float(rng.uniform(*PRICE[cat]))
        rows.append({
            "Date": date.date(),
            "Category": cat,
            "Product": rng.choice(PRODUCTS[cat]),
            "Region": rng.choice(REGIONS),
            "Orders": orders,
            "Sales": round(sales, 2),
            "Profit": round(sales * float(rng.uniform(0.08, 0.35)), 2),
            "Customer_ID": f"C{rng.integers(1, 600):04d}",
        })

pd.DataFrame(rows).to_csv("data/sales_data.csv", index=False)
print(f"Wrote {len(rows)} rows to data/sales_data.csv")
