"""
00_generate_excel_data.py
=========================
Generates 12 monthly Excel files (Jan-Dec 2025) simulating
Greenleaf Supply Company data across 4 sheets per file:
  - Sheet 1: Sales Transactions
  - Sheet 2: Inventory
  - Sheet 3: Customer Orders
  - Sheet 4: Suppliers

Usage:
    python 00_generate_excel_data.py
    # Creates: data/raw/2025_01_january.xlsx ... data/raw/2025_12_december.xlsx

Replace these generated files with your REAL Excel files
by dropping them into data/raw/ with the same naming format.
"""

import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── Business configuration ────────────────────────────────────────────────────
PRODUCTS = [
    {"product_id": "P001", "name": "Urea Fertilizer 50kg",     "category": "Fertilizers",   "unit_cost": 3200, "unit_price": 4100},
    {"product_id": "P002", "name": "DAP Fertilizer 50kg",      "category": "Fertilizers",   "unit_cost": 4800, "unit_price": 6200},
    {"product_id": "P003", "name": "CAN Fertilizer 50kg",      "category": "Fertilizers",   "unit_cost": 2900, "unit_price": 3750},
    {"product_id": "P004", "name": "Maize Seeds 5kg",          "category": "Seeds",         "unit_cost": 850,  "unit_price": 1200},
    {"product_id": "P005", "name": "Bean Seeds 2kg",           "category": "Seeds",         "unit_cost": 620,  "unit_price": 950},
    {"product_id": "P006", "name": "Sunflower Seeds 1kg",      "category": "Seeds",         "unit_cost": 480,  "unit_price": 720},
    {"product_id": "P007", "name": "Pesticide Dursban 1L",     "category": "Pesticides",    "unit_cost": 1200, "unit_price": 1800},
    {"product_id": "P008", "name": "Herbicide Round-Up 1L",    "category": "Pesticides",    "unit_cost": 950,  "unit_price": 1450},
    {"product_id": "P009", "name": "Fungicide Ridomil 500g",   "category": "Pesticides",    "unit_cost": 780,  "unit_price": 1150},
    {"product_id": "P010", "name": "Garden Hoe",               "category": "Tools",         "unit_cost": 450,  "unit_price": 700},
    {"product_id": "P011", "name": "Watering Can 10L",         "category": "Tools",         "unit_cost": 380,  "unit_price": 600},
    {"product_id": "P012", "name": "Irrigation Pipe 50m",      "category": "Irrigation",    "unit_cost": 2200, "unit_price": 3100},
    {"product_id": "P013", "name": "Drip Kit 1 Acre",          "category": "Irrigation",    "unit_cost": 8500, "unit_price": 12000},
    {"product_id": "P014", "name": "Animal Feed Dairy 50kg",   "category": "Animal Feed",   "unit_cost": 2100, "unit_price": 2800},
    {"product_id": "P015", "name": "Animal Feed Poultry 50kg", "category": "Animal Feed",   "unit_cost": 1900, "unit_price": 2600},
]

CUSTOMERS = [
    {"customer_id": "C001", "name": "Kamau Agro Dealers",    "county": "Nyeri",    "type": "Retailer"},
    {"customer_id": "C002", "name": "Mwangi Farm Supplies",  "county": "Kiambu",   "type": "Wholesaler"},
    {"customer_id": "C003", "name": "Otieno Agricultural",   "county": "Kisumu",   "type": "Retailer"},
    {"customer_id": "C004", "name": "Koech Farmers Hub",     "county": "Bomet",    "type": "Retailer"},
    {"customer_id": "C005", "name": "Nakuru Agri Centre",    "county": "Nakuru",   "type": "Wholesaler"},
    {"customer_id": "C006", "name": "Mutua Seeds & More",    "county": "Machakos", "type": "Retailer"},
    {"customer_id": "C007", "name": "Wanjiku Supplies",      "county": "Nyeri",    "type": "Retailer"},
    {"customer_id": "C008", "name": "Coast Agro Distributors","county": "Mombasa", "type": "Wholesaler"},
    {"customer_id": "C009", "name": "Chebet Farm Store",     "county": "Uasin Gishu","type": "Retailer"},
    {"customer_id": "C010", "name": "Embu Green Supplies",   "county": "Embu",     "type": "Retailer"},
]

SUPPLIERS = [
    {"supplier_id": "S001", "name": "Kenya Seed Company",       "category": "Seeds",       "lead_days": 7},
    {"supplier_id": "S002", "name": "Yara East Africa",         "category": "Fertilizers", "lead_days": 14},
    {"supplier_id": "S003", "name": "Bayer Crop Science",       "category": "Pesticides",  "lead_days": 10},
    {"supplier_id": "S004", "name": "Syngenta Kenya",           "category": "Pesticides",  "lead_days": 10},
    {"supplier_id": "S005", "name": "Unga Feeds Limited",       "category": "Animal Feed", "lead_days": 5},
    {"supplier_id": "S006", "name": "Aquatech Irrigation",      "category": "Irrigation",  "lead_days": 21},
]

MONTHS = [
    (1, "January"), (2, "February"), (3, "March"),    (4, "April"),
    (5, "May"),     (6, "June"),     (7, "July"),     (8, "August"),
    (9, "September"),(10,"October"), (11,"November"), (12,"December"),
]

# Seasonal demand multipliers (planting seasons boost sales)
SEASONAL = {
    1: 1.4, 2: 1.6, 3: 1.8, 4: 1.3,   # Long rains prep
    5: 0.9, 6: 0.7, 7: 0.8, 8: 1.0,   # Off season
    9: 1.5, 10: 1.7, 11: 1.4, 12: 1.1  # Short rains prep
}


def random_date(month: int, year: int = 2025) -> str:
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = random.randint(1, max_day)
    return datetime(year, month, day).strftime("%Y-%m-%d")


def generate_sales(month: int, n_transactions: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n_transactions + 1):
        product = random.choice(PRODUCTS)
        customer = random.choice(CUSTOMERS)
        qty = random.randint(1, 50)
        discount = random.choice([0, 0, 0, 5, 10, 15])
        unit_price = product["unit_price"]
        revenue = round(qty * unit_price * (1 - discount / 100), 2)
        cost = round(qty * product["unit_cost"], 2)
        rows.append({
            "transaction_id": f"TXN-2025{month:02d}-{i:04d}",
            "date":           random_date(month),
            "customer_id":    customer["customer_id"],
            "customer_name":  customer["name"],
            "product_id":     product["product_id"],
            "product_name":   product["name"],
            "category":       product["category"],
            "quantity":       qty,
            "unit_price_kes": unit_price,
            "discount_pct":   discount,
            "revenue_kes":    revenue,
            "cost_kes":       cost,
            "profit_kes":     round(revenue - cost, 2),
            "payment_method": random.choice(["M-Pesa", "Cash", "Bank Transfer", "Credit"]),
            "sales_rep":      random.choice(["Alice Njeri", "Brian Omondi", "Carol Wangari", "David Kipchoge"]),
        })
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def generate_inventory(month: int) -> pd.DataFrame:
    rows = []
    for product in PRODUCTS:
        opening = random.randint(50, 500)
        received = random.randint(0, 300)
        sold = random.randint(10, min(opening + received - 5, 400))
        closing = opening + received - sold
        reorder_level = random.randint(20, 80)
        rows.append({
            "month":           f"2025-{month:02d}",
            "product_id":      product["product_id"],
            "product_name":    product["name"],
            "category":        product["category"],
            "opening_stock":   opening,
            "stock_received":  received,
            "stock_sold":      sold,
            "closing_stock":   closing,
            "reorder_level":   reorder_level,
            "needs_reorder":   "Yes" if closing <= reorder_level else "No",
            "unit_cost_kes":   product["unit_cost"],
            "stock_value_kes": round(closing * product["unit_cost"], 2),
        })
    return pd.DataFrame(rows)


def generate_orders(month: int, n_orders: int) -> pd.DataFrame:
    rows = []
    statuses = ["Delivered", "Delivered", "Delivered", "Pending", "Cancelled"]
    for i in range(1, n_orders + 1):
        customer = random.choice(CUSTOMERS)
        order_date = random_date(month)
        delivery_days = random.randint(1, 14)
        order_dt = datetime.strptime(order_date, "%Y-%m-%d")
        delivery_dt = order_dt + timedelta(days=delivery_days)
        status = random.choice(statuses)
        total = round(random.uniform(5000, 150000), 2)
        rows.append({
            "order_id":         f"ORD-2025{month:02d}-{i:04d}",
            "order_date":       order_date,
            "customer_id":      customer["customer_id"],
            "customer_name":    customer["name"],
            "county":           customer["county"],
            "customer_type":    customer["type"],
            "order_total_kes":  total,
            "status":           status,
            "delivery_date":    delivery_dt.strftime("%Y-%m-%d") if status == "Delivered" else None,
            "delivery_days":    delivery_days if status == "Delivered" else None,
            "items_count":      random.randint(1, 10),
            "notes":            random.choice(["Urgent", "Standard", "", "", ""]),
        })
    return pd.DataFrame(rows)


def generate_supplier_orders(month: int) -> pd.DataFrame:
    rows = []
    for i, supplier in enumerate(SUPPLIERS, 1):
        order_date = random_date(month)
        amount = round(random.uniform(20000, 500000), 2)
        rows.append({
            "po_id":            f"PO-2025{month:02d}-{i:04d}",
            "order_date":       order_date,
            "supplier_id":      supplier["supplier_id"],
            "supplier_name":    supplier["name"],
            "category":         supplier["category"],
            "amount_kes":       amount,
            "lead_time_days":   supplier["lead_days"],
            "status":           random.choice(["Received", "Received", "Pending"]),
            "payment_status":   random.choice(["Paid", "Paid", "Pending"]),
        })
    return pd.DataFrame(rows)


def write_monthly_excel(month: int, month_name: str):
    seasonal_factor = SEASONAL[month]
    n_sales = int(random.randint(80, 150) * seasonal_factor)
    n_orders = int(random.randint(30, 60) * seasonal_factor)

    sales     = generate_sales(month, n_sales)
    inventory = generate_inventory(month)
    orders    = generate_orders(month, n_orders)
    suppliers = generate_supplier_orders(month)

    filename = f"data/raw/2025_{month:02d}_{month_name.lower()}.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        sales.to_excel(writer,     sheet_name="Sales_Transactions", index=False)
        inventory.to_excel(writer, sheet_name="Inventory",          index=False)
        orders.to_excel(writer,    sheet_name="Customer_Orders",    index=False)
        suppliers.to_excel(writer, sheet_name="Supplier_Orders",    index=False)

    print(f"  {month_name:12s} -> {filename}  ({len(sales)} sales, {len(orders)} orders)")
    return len(sales), len(orders)


if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)
    print("Generating Greenleaf Supply monthly Excel files (Jan-Dec 2025)...")
    print("-" * 65)
    total_sales = total_orders = 0
    for month_num, month_name in MONTHS:
        s, o = write_monthly_excel(month_num, month_name)
        total_sales += s
        total_orders += o
    print("-" * 65)
    print(f"Generated 12 Excel files | {total_sales:,} sales | {total_orders:,} orders")
    print("Location: data/raw/")
    print("\nTo use YOUR real Excel files:")
    print("  1. Name them: 2025_01_january.xlsx, 2025_02_february.xlsx ...")
    print("  2. Ensure sheets: Sales_Transactions, Inventory, Customer_Orders, Supplier_Orders")
    print("  3. Drop them in data/raw/ and run python 01_extract.py")
