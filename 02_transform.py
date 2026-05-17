"""
02_transform.py
===============
Phase 2 - TRANSFORM
Cleans, enriches and validates all 4 datasets:
  - Sales: fix types, compute margins, flag high-value transactions
  - Inventory: flag low stock, compute turnover rate
  - Orders: compute delivery performance, flag late orders
  - Suppliers: compute spend by category

Run:
    python 02_transform.py
"""

import os
import logging
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/transform.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

STAGING_DIR   = "data/staging"
PROCESSED_DIR = "data/processed"

MONTH_NAMES = {
    "2025_01": "January",   "2025_02": "February", "2025_03": "March",
    "2025_04": "April",     "2025_05": "May",       "2025_06": "June",
    "2025_07": "July",      "2025_08": "August",    "2025_09": "September",
    "2025_10": "October",   "2025_11": "November",  "2025_12": "December",
}


# ── Sales transformation ──────────────────────────────────────────────────────
def transform_sales(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Transforming Sales...")

    # Fix data types
    numeric_cols = ["quantity", "unit_price_kes", "discount_pct",
                    "revenue_kes", "cost_kes", "profit_kes"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "revenue_kes"])

    # Enrich
    df["month"]        = df["date"].dt.to_period("M").astype(str)
    df["month_name"]   = df["source_month"].map(MONTH_NAMES)
    df["quarter"]      = df["date"].dt.quarter.map({1:"Q1",2:"Q2",3:"Q3",4:"Q4"})
    df["profit_margin_pct"] = (df["profit_kes"] / df["revenue_kes"] * 100).round(2)
    df["is_high_value"] = (df["revenue_kes"] >= 50000).astype(int)
    df["is_discounted"] = (df["discount_pct"] > 0).astype(int)

    # Clean strings
    df["category"]       = df["category"].str.strip().str.title()
    df["payment_method"] = df["payment_method"].str.strip()
    df["customer_name"]  = df["customer_name"].str.strip()

    # Remove duplicates
    df = df.drop_duplicates(subset="transaction_id")
    df = df[df["revenue_kes"] > 0]

    log.info(f"  Sales rows: {len(df):,} | Avg margin: {df['profit_margin_pct'].mean():.1f}%")
    return df


# ── Inventory transformation ──────────────────────────────────────────────────
def transform_inventory(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Transforming Inventory...")

    numeric_cols = ["opening_stock", "stock_received", "stock_sold",
                    "closing_stock", "reorder_level", "unit_cost_kes", "stock_value_kes"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["month_name"]     = df["source_month"].map(MONTH_NAMES)
    df["stock_turnover"] = (df["stock_sold"] / df["opening_stock"].replace(0, np.nan)).round(3)
    df["needs_reorder"]  = (df["closing_stock"] <= df["reorder_level"]).map({True: "Yes", False: "No"})
    df["stockout_risk"]  = (df["closing_stock"] <= df["reorder_level"] * 0.5).map({True: "High", False: "Low"})
    df["category"]       = df["category"].str.strip().str.title()

    log.info(f"  Inventory rows: {len(df):,} | Reorder needed: {(df['needs_reorder']=='Yes').sum()}")
    return df


# ── Orders transformation ─────────────────────────────────────────────────────
def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Transforming Customer Orders...")

    df["order_total_kes"] = pd.to_numeric(df["order_total_kes"], errors="coerce")
    df["delivery_days"]   = pd.to_numeric(df["delivery_days"],   errors="coerce")
    df["order_date"]      = pd.to_datetime(df["order_date"],     errors="coerce")

    df = df.dropna(subset=["order_id", "order_total_kes"])
    df = df.drop_duplicates(subset="order_id")

    df["month_name"]    = df["source_month"].map(MONTH_NAMES)
    df["quarter"]       = df["order_date"].dt.quarter.map({1:"Q1",2:"Q2",3:"Q3",4:"Q4"})
    df["is_delivered"]  = (df["status"] == "Delivered").astype(int)
    df["is_late"]       = (df["delivery_days"] > 7).astype(int)
    df["order_size"]    = pd.cut(
        df["order_total_kes"],
        bins=[0, 10000, 50000, 100000, float("inf")],
        labels=["Small", "Medium", "Large", "Enterprise"]
    )
    df["county"]        = df["county"].str.strip().str.title()
    df["customer_type"] = df["customer_type"].str.strip()

    log.info(f"  Orders rows: {len(df):,} | Delivery rate: {df['is_delivered'].mean()*100:.1f}%")
    return df


# ── Supplier orders transformation ────────────────────────────────────────────
def transform_suppliers(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Transforming Supplier Orders...")

    df["amount_kes"]      = pd.to_numeric(df["amount_kes"],      errors="coerce")
    df["lead_time_days"]  = pd.to_numeric(df["lead_time_days"],  errors="coerce")
    df["order_date"]      = pd.to_datetime(df["order_date"],     errors="coerce")

    df = df.dropna(subset=["po_id", "amount_kes"])
    df = df.drop_duplicates(subset="po_id")

    df["month_name"]   = df["source_month"].map(MONTH_NAMES)
    df["is_paid"]      = (df["payment_status"] == "Paid").astype(int)
    df["is_received"]  = (df["status"] == "Received").astype(int)
    df["category"]     = df["category"].str.strip().str.title()

    log.info(f"  Supplier rows: {len(df):,} | Total spend: KES {df['amount_kes'].sum():,.0f}")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    datasets = {
        "staging_sales.parquet":     ("sales_clean.parquet",     transform_sales),
        "staging_inventory.parquet": ("inventory_clean.parquet", transform_inventory),
        "staging_orders.parquet":    ("orders_clean.parquet",    transform_orders),
        "staging_suppliers.parquet": ("suppliers_clean.parquet", transform_suppliers),
    }

    for in_file, (out_file, transform_fn) in datasets.items():
        in_path  = os.path.join(STAGING_DIR, in_file)
        out_path = os.path.join(PROCESSED_DIR, out_file)
        df = pd.read_parquet(in_path)
        df = transform_fn(df)
        df.to_parquet(out_path, index=False)
        log.info(f"Saved -> {out_path}\n")

    log.info("Transform phase COMPLETE")


if __name__ == "__main__":
    run()
